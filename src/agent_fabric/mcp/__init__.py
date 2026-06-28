"""
AgentFabric Model Context Protocol (MCP) bridge package.
"""
from agent_fabric.mcp.server import MCPServer as MCPServer
from agent_fabric.mcp.client import MCPClient as MCPClient
from agent_fabric.mcp.manager import MCPManager as MCPManager, mcp_manager as mcp_manager

__all__ = ["MCPServer", "MCPClient", "MCPManager", "mcp_manager"]
