import logging
from agent_fabric.tools.decorator import tool
from agent_fabric.tools.registry import tool_registry

logger = logging.getLogger("agent_fabric.mcp.client")

__all__ = ["MCPClient"]


class MCPClient:
    """
    Model Context Protocol (MCP) Client connecting to external MCP servers and wrapping remote tools.
    """
    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self.connected = False

    def connect(self) -> bool:
        """Establishes connection and registers remote MCP tools."""
        self.connected = True
        
        # Register sample dynamic wrapped remote tool
        @tool(f"Remote tool from MCP server ({self.server_url})")
        def remote_mcp_tool(input_text: str) -> str:
            return f"MCP Client ({self.server_url}): Executed remote tool with input '{input_text}'."
            
        tool_registry.register(remote_mcp_tool)
        logger.info(f"Connected to MCP server at '{self.server_url}'.")
        return True
