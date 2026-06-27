from abc import ABC, abstractmethod
from agent_fabric.runtime.agent import AgentResult

__all__ = ["AgentAdapter"]


class AgentAdapter(ABC):
    """
    Abstract Base Class for wrapping external agent frameworks (LangGraph, CrewAI, OpenAI SDK, custom)
    into an AgentFabric-compatible Agent interface.
    """
    @abstractmethod
    async def run(self, task: str, **kwargs) -> AgentResult:
        """Execute task on wrapped agent framework instance."""
        pass
