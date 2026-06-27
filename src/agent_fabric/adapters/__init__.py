"""
AgentFabric Framework Adapters package.
Wraps external framework agents (OpenAI SDK, LangGraph, CrewAI, custom) into AgentFabric runtime agents.
"""
from agent_fabric.adapters.base import AgentAdapter as AgentAdapter
from agent_fabric.adapters.generic import GenericAgentAdapter as GenericAgentAdapter
from agent_fabric.adapters.openai_agents import OpenAIAdapter as OpenAIAdapter

__all__ = ["AgentAdapter", "GenericAgentAdapter", "OpenAIAdapter"]
