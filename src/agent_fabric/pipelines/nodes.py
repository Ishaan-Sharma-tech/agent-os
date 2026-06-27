import json
import logging
from typing import Dict, Any, Optional
from agent_fabric.tools.registry import tool_registry
from agent_fabric.runtime.agent import Agent
from agent_fabric.runtime.team import Team
from agent_fabric.pipelines.dag import PipelineNode

logger = logging.getLogger("agent_fabric.pipelines.nodes")

__all__ = ["execute_node"]


async def execute_node(node: PipelineNode, inputs: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Executes a specific pipeline node based on its type (tool, agent, team, conditional, transform, etc.).
    """
    node_type = node.type.lower()
    cfg = config if config is not None else node.config
    
    if node_type == "tool":
        tool_name = cfg.get("tool") or cfg.get("tool_name") or node.name or node.id
        tool_inst = tool_registry.get(tool_name)
        if not tool_inst:
            raise ValueError(f"Tool '{tool_name}' required by node '{node.id}' not found in registry.")
        return await tool_inst.execute(**inputs)

    elif node_type == "agent":
        agent_config = cfg.get("agent")
        if isinstance(agent_config, dict):
            agent = Agent.from_dict(agent_config)
        elif isinstance(agent_config, str):
            agent = Agent(name=agent_config)
        else:
            agent = Agent(name=node.name or node.id)
            
        task = inputs.get("task") or inputs.get("prompt") or (json.dumps(inputs) if inputs else "Execute task")
        res = await agent.run(task)
        return res.text

    elif node_type == "team":
        team_config = cfg.get("team")
        if isinstance(team_config, dict):
            team = Team.from_dict(team_config)
        else:
            team = Team(agents=[Agent(name="worker1"), Agent(name="worker2")], name=node.id)
            
        task = inputs.get("task") or (json.dumps(inputs) if inputs else "Execute task")
        res = await team.run(task)
        return res.text

    elif node_type == "conditional":
        condition_expr = str(cfg.get("condition", "True"))
        eval_globals = {"inputs": inputs, "str": str, "int": int, "len": len}
        try:
            result = bool(eval(condition_expr, eval_globals, dict(inputs)))
        except Exception as e:
            logger.warning(f"Error evaluating condition '{condition_expr}' in node '{node.id}': {e}")
            result = False
        return result

    elif node_type == "transform":
        template = str(cfg.get("template", "{inputs}"))
        if "${" not in template and "{" in template:
            try:
                return template.format(inputs=inputs, **inputs)
            except Exception:
                return template
        return template

    elif node_type == "human_approval":
        logger.info(f"Human approval node '{node.id}' auto-approved in automated mode.")
        return {"approved": True, "inputs": inputs}

    else:
        raise ValueError(f"Unsupported pipeline node type '{node.type}' in node '{node.id}'.")
