import json
import pytest
from unittest.mock import MagicMock
import agent_fabric.tools.builtin  # noqa
from agent_fabric.mcp.server import MCPServer
from agent_fabric.mcp.client import MCPClient
from agent_fabric.mcp.manager import mcp_manager
from agent_fabric.adapters.langgraph_adapter import LangGraphAdapter
from agent_fabric.adapters.crewai_adapter import CrewAIAdapter


@pytest.mark.asyncio
async def test_mcp_server_jsonrpc():
    """Verify MCP Server JSON-RPC dispatch methods."""
    from agent_fabric.tools.decorator import tool
    from agent_fabric.tools.registry import tool_registry
    
    @tool(name="mcp_test_tool", description="Test MCP tool")
    def mcp_test_tool(query: str) -> str:
        return f"MCP Output for {query}"
        
    tool_registry.register(mcp_test_tool)
    server = MCPServer()
    
    # Method: initialize
    req_init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    res_init = json.loads(await server.handle_jsonrpc_request(req_init))
    assert res_init["result"]["serverInfo"]["name"] == "agentfabric-mcp-server"
    
    # Method: tools/list
    req_list = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    res_list = json.loads(await server.handle_jsonrpc_request(req_list))
    assert isinstance(res_list["result"]["tools"], list)
    
    # Method: tools/call
    req_call = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "mcp_test_tool", "arguments": {"query": "test"}}})
    res_call = json.loads(await server.handle_jsonrpc_request(req_call))
    assert "content" in res_call["result"]


def test_mcp_client_and_manager():
    """Verify MCP Client connection and Manager tracking."""
    url = "http://localhost:8000/mcp"
    client = mcp_manager.connect_server(url)
    assert client.connected is True
    assert url in mcp_manager.list_connected()


@pytest.mark.asyncio
async def test_langgraph_adapter():
    """Verify LangGraph framework adapter execution flow."""
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = "LangGraph Graph Output"
    
    adapter = LangGraphAdapter(graph_instance=mock_graph, agent_name="test_langgraph")
    result = await adapter.run("Run graph execution")
    assert "LangGraph Graph Output" in result.text


@pytest.mark.asyncio
async def test_crewai_adapter():
    """Verify CrewAI framework adapter execution flow."""
    mock_crew = MagicMock()
    mock_crew.kickoff.return_value = "CrewAI Crew Output"
    
    adapter = CrewAIAdapter(crew_instance=mock_crew, crew_name="test_crewai")
    result = await adapter.run("Run crew kickoff")
    assert "CrewAI Crew Output" in result.text
