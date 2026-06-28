import logging
from typing import Dict, List
from agent_fabric.mcp.client import MCPClient

logger = logging.getLogger("agent_fabric.mcp.manager")

__all__ = ["MCPManager", "mcp_manager"]


class MCPManager:
    """
    Manager tracking active MCP client connections and servers.
    """
    def __init__(self) -> None:
        self.active_clients: Dict[str, MCPClient] = {}

    def connect_server(self, url: str) -> MCPClient:
        """Connect to an external MCP server URL."""
        if url in self.active_clients:
            return self.active_clients[url]
            
        client = MCPClient(server_url=url)
        client.connect()
        self.active_clients[url] = client
        return client

    def list_connected(self) -> List[str]:
        """List active connected MCP server URLs."""
        return list(self.active_clients.keys())


mcp_manager = MCPManager()
