import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from agent_fabric.plugins.manifest import PluginManifest
from agent_fabric.plugins.manager import plugin_manager
from agent_fabric.plugins.loader import load_plugin_manifest
from agent_fabric.adapters.generic import GenericAgentAdapter
from agent_fabric.adapters.openai_agents import OpenAIAdapter
from agent_fabric.server.app import create_app


@pytest.fixture(autouse=True)
def mock_openai_environment():
    with patch("agent_fabric.providers.openai.OPENAI_AVAILABLE", True), \
         patch("agent_fabric.providers.openai.AsyncOpenAI", create=True) as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_plugin_manifest_and_loader():
    """Verify parsing plugin manifests and registering via loader."""
    manifest_dict = {
        "name": "custom_plugin",
        "version": "1.2.0",
        "description": "Test plugin",
        "tools": ["custom_tool_1"]
    }
    manifest = load_plugin_manifest(manifest_dict)
    assert manifest.name == "custom_plugin"
    assert manifest.version == "1.2.0"
    
    p = plugin_manager.get_plugin("custom_plugin")
    assert p is not None
    assert p.tools == ["custom_tool_1"]


def test_plugin_manager_lifecycle():
    """Verify listing, enabling, and disabling plugins."""
    plugins = plugin_manager.list_plugins()
    assert len(plugins) >= 2  # Builtins hackernews & github
    
    plugin_manager.disable_plugin("hackernews")
    p_hn = plugin_manager.get_plugin("hackernews")
    assert p_hn.enabled is False
    
    plugin_manager.enable_plugin("hackernews")
    assert p_hn.enabled is True


@pytest.mark.asyncio
async def test_generic_agent_adapter():
    """Verify GenericAgentAdapter wrapping a raw custom Python bot class."""
    class CustomBot:
        def run(self, task: str):
            return f"CustomBot processed: {task}"
            
    bot = CustomBot()
    adapter = GenericAgentAdapter(target_agent=bot, name="test_bot", memory=False, observe=False)
    res = await adapter.run("Analyze dataset")
    assert res.text == "CustomBot processed: Analyze dataset"


@pytest.mark.asyncio
async def test_openai_agent_adapter():
    """Verify OpenAIAdapter wrapping an OpenAI agent instance."""
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value="OpenAI Assistant output")
    
    adapter = OpenAIAdapter(openai_agent=mock_agent, name="mock_assistant")
    res = await adapter.run("Summarize paper")
    assert res.text == "OpenAI Assistant output"


def test_api_plugin_endpoints():
    """Verify REST API routes for plugin management."""
    app = create_app()
    client = TestClient(app)
    
    # GET /plugins
    res_list = client.get("/plugins")
    assert res_list.status_code == 200
    plugins = res_list.json()
    assert any(p["name"] == "github" for p in plugins)
    
    # POST /plugins/github/disable
    res_dis = client.post("/plugins/github/disable")
    assert res_dis.status_code == 200
    
    # POST /plugins/github/enable
    res_en = client.post("/plugins/github/enable")
    assert res_en.status_code == 200
