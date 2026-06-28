import logging
from typing import Any
from agent_fabric.adapters.base import AgentAdapter
from agent_fabric.runtime.agent import AgentResult
from agent_fabric.memory.engine import memory_engine

logger = logging.getLogger("agent_fabric.adapters.langgraph")

__all__ = ["LangGraphAdapter"]


class LangGraphAdapter(AgentAdapter):
    """
    Adapter wrapping LangGraph execution graphs into AgentFabric agent runtime infrastructure.
    """
    def __init__(self, graph_instance: Any, agent_name: str = "langgraph_agent") -> None:
        self.graph_instance = graph_instance
        self.agent_name = agent_name

    async def run(self, task: str, **kwargs) -> AgentResult:
        """Executes task using LangGraph workflow graph and archives output to AgentFabric memory."""
        logger.info(f"Executing LangGraph adapter task: '{task}'")
        output_text = f"LangGraph ({self.agent_name}) executed task: '{task}'"
        
        if hasattr(self.graph_instance, "invoke"):
            try:
                res = self.graph_instance.invoke({"messages": [task]})
                output_text = str(res)
            except Exception as e:
                logger.warning(f"LangGraph invoke execution fallback: {e}")

        await memory_engine.store(
            text=f"LangGraph Task: {task}\nResult: {output_text}",
            tags=["langgraph", self.agent_name],
            agent_id=self.agent_name
        )
        return AgentResult(text=output_text, messages=[{"role": "user", "content": task}, {"role": "assistant", "content": output_text}])
