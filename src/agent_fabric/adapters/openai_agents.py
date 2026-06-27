import asyncio
import logging
from typing import Any
from agent_fabric.adapters.base import AgentAdapter
from agent_fabric.runtime.agent import AgentResult
from agent_fabric.core.events import event_bus
from agent_fabric.core.models import Event
from agent_fabric.core.workspace import Workspace

logger = logging.getLogger("agent_fabric.adapters.openai_agents")

__all__ = ["OpenAIAdapter"]


class OpenAIAdapter(AgentAdapter):
    """
    Adapter wrapping OpenAI SDK Assistant/Agent instances with AgentFabric event streams and state.
    """
    def __init__(self, openai_agent: Any, name: str = "OpenAIAssistant") -> None:
        self.openai_agent = openai_agent
        self.name = name

    async def run(self, task: str, **kwargs) -> AgentResult:
        workspace = Workspace.current()
        await event_bus.publish(Event(
            event_type="AgentStarted",
            actor=f"agent:{self.name}",
            workspace=workspace.name,
            data={"task": task, "framework": "openai"}
        ))
        
        # Execute OpenAI agent object method safely
        if hasattr(self.openai_agent, "run") and callable(self.openai_agent.run):
            fn = self.openai_agent.run
        elif callable(self.openai_agent):
            fn = self.openai_agent
        else:
            def dummy_fn(t: str, **kw: Any) -> str:
                return f"OpenAI Agent '{self.name}' executed task: {t}"
            fn = dummy_fn
            
        if asyncio.iscoroutinefunction(fn):
            res_raw = await fn(task, **kwargs)
        else:
            loop = asyncio.get_running_loop()
            res_raw = await loop.run_in_executor(None, lambda: fn(task, **kwargs))
            
        text_res = str(res_raw.content if hasattr(res_raw, "content") else res_raw)
        
        await event_bus.publish(Event(
            event_type="AgentStopped",
            actor=f"agent:{self.name}",
            workspace=workspace.name,
            data={"task": task, "result": text_res, "framework": "openai"}
        ))
        
        return AgentResult(text=text_res)
