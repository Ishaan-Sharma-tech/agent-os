import re
import asyncio
import logging
from typing import Dict, Any, Optional, List, Set
from agent_fabric.core.events import event_bus
from agent_fabric.core.models import Event
from agent_fabric.core.workspace import Workspace
from agent_fabric.pipelines.dag import Pipeline, PipelineNode, PipelineRun, validate_dag
from agent_fabric.pipelines.nodes import execute_node

logger = logging.getLogger("agent_fabric.pipelines.executor")

__all__ = ["PipelineExecutor"]

INTERPOLATION_RE = re.compile(r"\$\{([a-zA-Z0-9_.-]+)\}")


def resolve_interpolation(val: Any, context: Dict[str, Any]) -> Any:
    """
    Recursively resolves variable template expressions like `${step_id.output}` in node inputs.
    """
    if isinstance(val, str):
        matches = INTERPOLATION_RE.findall(val)
        if not matches:
            return val
            
        # Exact single expression match returns raw object if applicable
        if len(matches) == 1 and val.strip() == f"${{{matches[0]}}}":
            path_parts = matches[0].split(".")
            root = path_parts[0]
            curr = context.get(root)
            for part in path_parts[1:]:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                elif hasattr(curr, part):
                    curr = getattr(curr, part)
                elif part == "output":
                    # Fallback if context[root] is the output directly
                    pass
                else:
                    curr = None
                    break
            return curr if curr is not None else val
            
        # Multi-expression or string template substitution
        def replacer(match):
            expr = match.group(1)
            path_parts = expr.split(".")
            root = path_parts[0]
            curr = context.get(root)
            for part in path_parts[1:]:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                elif hasattr(curr, part):
                    curr = getattr(curr, part)
                elif part == "output":
                    pass
                else:
                    curr = ""
                    break
            return str(curr) if curr is not None else ""
            
        return INTERPOLATION_RE.sub(replacer, val)
        
    elif isinstance(val, dict):
        return {k: resolve_interpolation(v, context) for k, v in val.items()}
    elif isinstance(val, list):
        return [resolve_interpolation(v, context) for v in val]
    return val


class PipelineExecutor:
    """
    Executes a DAG Pipeline workflow with topological wave parallelism,
    variable interpolation, retries, and EventBus observability.
    """
    def __init__(self, pipeline: Pipeline) -> None:
        self.pipeline = pipeline

    async def run(self, initial_inputs: Optional[Dict[str, Any]] = None) -> PipelineRun:
        """Execute the pipeline graph asynchronously."""
        validate_dag(self.pipeline)
        workspace = Workspace.current()
        
        run_record = PipelineRun(pipeline_name=self.pipeline.name)
        run_record.status = "running"
        
        context: Dict[str, Any] = dict(initial_inputs or {})
        
        # Publish PipelineStarted Event
        await event_bus.publish(Event(
            event_type="PipelineStarted",
            actor=f"pipeline:{self.pipeline.name}",
            workspace=workspace.name,
            data={"run_id": run_record.run_id}
        ))

        completed_nodes: Set[str] = set()
        node_map = {n.id: n for n in self.pipeline.nodes}
        
        try:
            while len(completed_nodes) < len(self.pipeline.nodes):
                # Find all unexecuted nodes whose dependencies are satisfied
                ready_nodes: List[PipelineNode] = []
                for n_id, node in node_map.items():
                    if n_id not in completed_nodes:
                        if all(dep in completed_nodes for dep in node.depends_on):
                            ready_nodes.append(node)
                            
                if not ready_nodes:
                    raise RuntimeError("Pipeline deadlock encountered: no ready nodes to execute.")
                    
                # Run ready wave nodes in parallel
                async def _run_single_node(node: PipelineNode):
                    run_record.node_statuses[node.id] = "running"
                    await event_bus.publish(Event(
                        event_type="NodeStarted",
                        actor=f"node:{node.id}",
                        workspace=workspace.name,
                        data={"run_id": run_record.run_id, "node_id": node.id}
                    ))
                    
                    # Resolve inputs with interpolated context
                    resolved_inputs = resolve_interpolation(node.inputs, context)
                    resolved_config = resolve_interpolation(node.config, context)
                    
                    retries = 0
                    max_retries = node.retry_policy.max_retries if node.retry_policy else 0
                    delay = node.retry_policy.delay if node.retry_policy else 1.0
                    backoff = node.retry_policy.backoff_factor if node.retry_policy else 2.0
                    
                    last_exc = None
                    while retries <= max_retries:
                        try:
                            if node.timeout:
                                res = await asyncio.wait_for(execute_node(node, resolved_inputs, resolved_config), timeout=node.timeout)
                            else:
                                res = await execute_node(node, resolved_inputs, resolved_config)
                            
                            run_record.node_statuses[node.id] = "completed"
                            run_record.outputs[node.id] = res
                            context[node.id] = res
                            context[f"{node.id}.output"] = res
                            
                            await event_bus.publish(Event(
                                event_type="NodeCompleted",
                                actor=f"node:{node.id}",
                                workspace=workspace.name,
                                data={"run_id": run_record.run_id, "node_id": node.id}
                            ))
                            return node.id, res
                        except Exception as e:
                            last_exc = e
                            retries += 1
                            if retries <= max_retries:
                                logger.warning(f"Retrying node '{node.id}' (attempt {retries}/{max_retries}) after error: {e}")
                                await asyncio.sleep(delay)
                                delay *= backoff
                                
                    run_record.node_statuses[node.id] = "failed"
                    await event_bus.publish(Event(
                        event_type="NodeFailed",
                        actor=f"node:{node.id}",
                        workspace=workspace.name,
                        data={"run_id": run_record.run_id, "node_id": node.id, "error": str(last_exc)}
                    ))
                    raise last_exc

                results = await asyncio.gather(*[_run_single_node(n) for n in ready_nodes], return_exceptions=True)
                
                # Check for wave execution errors
                for n, res in zip(ready_nodes, results):
                    if isinstance(res, Exception):
                        raise res
                    else:
                        completed_nodes.add(n.id)

            run_record.status = "completed"
            await event_bus.publish(Event(
                event_type="PipelineCompleted",
                actor=f"pipeline:{self.pipeline.name}",
                workspace=workspace.name,
                data={"run_id": run_record.run_id, "outputs": run_record.outputs}
            ))
        except Exception as e:
            run_record.status = "failed"
            run_record.error = str(e)
            logger.error(f"Pipeline '{self.pipeline.name}' failed: {e}")
            
        return run_record
