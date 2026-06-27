import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

__all__ = [
    "RetryPolicy", 
    "PipelineNode", 
    "PipelineEdge", 
    "Pipeline", 
    "PipelineRun", 
    "validate_dag"
]


class RetryPolicy(BaseModel):
    """Execution retry policy for pipeline nodes."""
    max_retries: int = 0
    delay: float = 1.0
    backoff_factor: float = 2.0


class PipelineNode(BaseModel):
    """Individual execution step node inside a pipeline graph."""
    id: str
    type: str  # tool, skill, agent, team, conditional, human_approval, transform
    name: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    retry_policy: Optional[RetryPolicy] = None
    timeout: Optional[float] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class PipelineEdge(BaseModel):
    """Directed edge connection between nodes in a pipeline."""
    source: str
    target: str
    condition: Optional[str] = None


class Pipeline(BaseModel):
    """Complete DAG workflow pipeline definition."""
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    nodes: List[PipelineNode] = Field(default_factory=list)


class PipelineRun(BaseModel):
    """Execution state tracking record for a pipeline run."""
    run_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    pipeline_name: str
    status: str = "pending"  # pending, running, completed, failed
    node_statuses: Dict[str, str] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


def validate_dag(pipeline: Pipeline) -> None:
    """
    Validates that a pipeline forms a valid Directed Acyclic Graph (DAG).
    Verifies node ID uniqueness, dependency references, and absence of cycles.
    """
    node_ids = set()
    node_map = {}
    for node in pipeline.nodes:
        if node.id in node_ids:
            raise ValueError(f"Duplicate node ID '{node.id}' in pipeline '{pipeline.name}'.")
        node_ids.add(node.id)
        node_map[node.id] = node
        
    for node in pipeline.nodes:
        for dep in node.depends_on:
            if dep not in node_ids:
                raise ValueError(f"Node '{node.id}' depends on non-existent node '{dep}'.")

    # Cycle detection using DFS depth stack
    visited = set()
    rec_stack = set()

    def dfs(node_id: str):
        visited.add(node_id)
        rec_stack.add(node_id)
        node = node_map[node_id]
        
        for dep in node.depends_on:
            if dep not in visited:
                dfs(dep)
            elif dep in rec_stack:
                raise ValueError(f"Cyclic dependency detected involving node '{dep}' and '{node_id}'.")
                
        rec_stack.remove(node_id)

    for n_id in node_ids:
        if n_id not in visited:
            dfs(n_id)
