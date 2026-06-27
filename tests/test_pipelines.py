import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from agent_fabric.pipelines.dag import Pipeline, PipelineNode, PipelineEdge, validate_dag
from agent_fabric.pipelines.executor import PipelineExecutor, resolve_interpolation
from agent_fabric.pipelines.yaml import load_pipeline_from_yaml
from agent_fabric.server.app import create_app


@pytest.fixture(autouse=True)
def mock_openai_environment():
    with patch("agent_fabric.providers.openai.OPENAI_AVAILABLE", True), \
         patch("agent_fabric.providers.openai.AsyncOpenAI", create=True) as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_dag_validation_and_cycles():
    """Verify DAG validation catches duplicate nodes, missing dependencies, and cycles."""
    # Duplicate node IDs
    p_dup = Pipeline(name="dup", nodes=[PipelineNode(id="n1", type="transform"), PipelineNode(id="n1", type="transform")])
    with pytest.raises(ValueError, match="Duplicate node ID"):
        validate_dag(p_dup)
        
    # Missing dependency
    p_missing = Pipeline(name="missing", nodes=[PipelineNode(id="n1", type="transform", depends_on=["ghost"])])
    with pytest.raises(ValueError, match="non-existent node"):
        validate_dag(p_missing)
        
    # Cyclic dependency
    p_cycle = Pipeline(name="cycle", nodes=[
        PipelineNode(id="n1", type="transform", depends_on=["n2"]),
        PipelineNode(id="n2", type="transform", depends_on=["n1"])
    ])
    with pytest.raises(ValueError, match="Cyclic dependency"):
        validate_dag(p_cycle)


def test_variable_interpolation():
    """Verify template expression resolution in pipeline context."""
    context = {
        "step1": "Hello World",
        "step2": {"status": "success", "count": 42}
    }
    
    res1 = resolve_interpolation("${step1}", context)
    assert res1 == "Hello World"
    
    res2 = resolve_interpolation("Result: ${step2.status}", context)
    assert res2 == "Result: success"


@pytest.mark.asyncio
async def test_pipeline_execution_flow():
    """Verify parallel DAG execution and variable context passing."""
    pipeline = Pipeline(
        name="test_flow",
        nodes=[
            PipelineNode(id="start", type="transform", config={"template": "start_val"}, inputs={}),
            PipelineNode(id="branch_a", type="transform", depends_on=["start"], config={"template": "A_${start.output}"}, inputs={}),
            PipelineNode(id="branch_b", type="transform", depends_on=["start"], config={"template": "B_${start.output}"}, inputs={}),
            PipelineNode(id="merge", type="transform", depends_on=["branch_a", "branch_b"], config={"template": "${branch_a.output}+${branch_b.output}"}, inputs={})
        ]
    )
    
    executor = PipelineExecutor(pipeline)
    run_rec = await executor.run()
    
    assert run_rec.status == "completed"
    assert run_rec.outputs["start"] == "start_val"
    assert run_rec.outputs["branch_a"] == "A_start_val"
    assert run_rec.outputs["branch_b"] == "B_start_val"
    assert run_rec.outputs["merge"] == "A_start_val+B_start_val"


def test_pipeline_yaml_parsing():
    """Verify loading pipelines from YAML strings."""
    yaml_content = """
name: briefing_pipeline
nodes:
  - id: fetch_data
    type: transform
    config:
      template: "raw_data"
  - id: process_data
    type: transform
    depends_on: [fetch_data]
    config:
      template: "processed_${fetch_data.output}"
"""
    pipeline = load_pipeline_from_yaml(yaml_content)
    assert pipeline.name == "briefing_pipeline"
    assert len(pipeline.nodes) == 2
    assert pipeline.nodes[1].depends_on == ["fetch_data"]


def test_api_pipeline_run_endpoint():
    """Verify POST /pipelines/run REST endpoint."""
    app = create_app()
    client = TestClient(app)
    
    response = client.post("/pipelines/run", json={
        "pipeline": {
            "name": "api_pipeline",
            "nodes": [
                {"id": "node1", "type": "transform", "config": {"template": "API OK"}}
            ]
        },
        "inputs": {}
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["outputs"]["node1"] == "API OK"
