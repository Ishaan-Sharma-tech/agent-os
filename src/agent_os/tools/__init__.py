"""
AgentOS Tools system.
Provides a simple decorator to wrap Python functions into tools, auto-generates JSON Schema,
and executes tools within capability-based security boundaries.
"""
from agent_os.tools.decorator import tool
from agent_os.tools.registry import tool_registry
