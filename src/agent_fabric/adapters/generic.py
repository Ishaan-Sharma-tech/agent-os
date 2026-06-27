import inspect
import asyncio
import logging
from typing import Any, Optional
from agent_fabric.adapters.base import AgentAdapter
from agent_fabric.runtime.agent import AgentResult
from agent_fabric.core.events import event_bus
from agent_fabric.core.models import Event
from agent_fabric.core.workspace import Workspace
from agent_fabric.memory.engine import memory_engine

logger = logging.getLogger("agent_fabric.adapters.generic")

__all__ = ["GenericAgentAdapter"]


class GenericAgentAdapter(AgentAdapter):
    """
    Adapter wrapping any Python object or callable into an AgentFabric agent with memory & observability.
    Powers the enhance() BYOA wrapper.
    """
    def __init__(self, target_agent: Any, name: Optional[str] = None, memory: bool = True, observe: bool = True) -> None:
        self.target_agent = target_agent
        self.name = name or getattr(target_agent, "__class__", type(target_agent)).__name__
        self.memory = memory
        self.observe = observe

    async def run(self, task: str, **kwargs) -> AgentResult:
        workspace = Workspace.current()
        
        if self.observe:
            await event_bus.publish(Event(
                event_type="AgentStarted",
                actor=f"agent:{self.name}",
                workspace=workspace.name,
                data={"task": task}
            ))
            
        # Determine how to call the underlying agent object
        if hasattr(self.target_agent, "run") and callable(self.target_agent.run):
            fn = self.target_agent.run
        elif callable(self.target_agent):
            fn = self.target_agent
        else:
            raise TypeError(f"Target object '{self.name}' has no callable method 'run' and is not callable.")
            
        if inspect.iscoroutinefunction(fn):
            res_raw = await fn(task, **kwargs)
        else:
            loop = asyncio.get_running_loop()
            res_raw = await loop.run_in_executor(None, lambda: fn(task, **kwargs))
            
        text_res = str(res_raw.content if hasattr(res_raw, "content") else res_raw)
        
        if self.memory:
            await memory_engine.store(text=f"Task: {task} | Output: {text_res}", tags=[self.name, "byoa"])
            
        if self.observe:
            await event_bus.publish(Event(
                event_type="AgentStopped",
                actor=f"agent:{self.name}",
                workspace=workspace.name,
                data={"task": task, "result": text_res}
            ))
            
        return AgentResult(text=text_res)
