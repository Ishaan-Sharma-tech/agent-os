import json
import logging
from typing import Dict, Any, List
from agent_fabric.tools.registry import tool_registry

logger = logging.getLogger("agent_fabric.mcp.server")

__all__ = ["MCPServer"]


class MCPServer:
    """
    Model Context Protocol (MCP) Server exposing AgentFabric tools over JSON-RPC / SSE.
    """
    def __init__(self, server_name: str = "agentfabric-mcp-server") -> None:
        self.server_name = server_name

    def list_tools(self) -> List[Dict[str, Any]]:
        """List registered tools formatted according to MCP tool specification."""
        mcp_tools = []
        for t_inst in tool_registry.list_all():
            mcp_tools.append({
                "name": getattr(t_inst, "name", "unknown"),
                "description": getattr(t_inst, "description", ""),
                "inputSchema": getattr(t_inst, "parameters", {})
            })
        return mcp_tools

    async def handle_jsonrpc_request(self, raw_request: str) -> str:
        """Handle incoming JSON-RPC 2.0 requests from MCP clients (Cursor, Claude Desktop)."""
        try:
            req = json.loads(raw_request)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                res = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.server_name, "version": "1.0.0"}
                }
            elif method == "tools/list":
                res = {"tools": self.list_tools()}
            elif method == "tools/call":
                t_name = params.get("name")
                t_args = params.get("arguments", {})
                t_inst = tool_registry.get(t_name)
                if not t_inst:
                    raise ValueError(f"Tool '{t_name}' not found on MCP server.")
                output = await t_inst.execute(**t_args)
                res = {"content": [{"type": "text", "text": str(output)}]}
            else:
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method '{method}' not found."}})

            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": res})
        except Exception as e:
            logger.error(f"MCP Server error processing request: {e}")
            return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}})
