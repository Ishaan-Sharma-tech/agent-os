from typing import List, Optional
from pydantic import BaseModel, Field

__all__ = ["PluginManifest"]


class PluginManifest(BaseModel):
    """Declarative plugin metadata manifest model."""
    name: str
    version: str = "0.1.0"
    description: Optional[str] = None
    author: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    enabled: bool = True
