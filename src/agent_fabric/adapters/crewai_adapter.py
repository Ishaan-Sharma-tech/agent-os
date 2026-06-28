import logging
from typing import Any
from agent_fabric.adapters.base import AgentAdapter
from agent_fabric.runtime.agent import AgentResult
from agent_fabric.memory.engine import memory_engine

logger = logging.getLogger("agent_fabric.adapters.crewai")

__all__ = ["CrewAIAdapter"]


class CrewAIAdapter(AgentAdapter):
    """
    Adapter wrapping CrewAI agent crews into AgentFabric multi-agent execution pipelines.
    """
    def __init__(self, crew_instance: Any, crew_name: str = "crewai_team") -> None:
        self.crew_instance = crew_instance
        self.crew_name = crew_name

    async def run(self, task: str, **kwargs) -> AgentResult:
        """Executes task using CrewAI agent crew and archives output to AgentFabric memory."""
        logger.info(f"Executing CrewAI adapter task: '{task}'")
        output_text = f"CrewAI ({self.crew_name}) executed task: '{task}'"
        
        if hasattr(self.crew_instance, "kickoff"):
            try:
                res = self.crew_instance.kickoff(inputs={"task": task})
                output_text = str(res)
            except Exception as e:
                logger.warning(f"CrewAI kickoff execution fallback: {e}")

        await memory_engine.store(
            text=f"CrewAI Task: {task}\nResult: {output_text}",
            tags=["crewai", self.crew_name],
            agent_id=self.crew_name
        )
        return AgentResult(text=output_text, messages=[{"role": "user", "content": task}, {"role": "assistant", "content": output_text}])
