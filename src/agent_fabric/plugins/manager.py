import logging
from typing import List, Dict, Optional
from agent_fabric.plugins.manifest import PluginManifest
# Import builtins so tools register automatically
import agent_fabric.plugins.builtin.hackernews # noqa
import agent_fabric.plugins.builtin.github_tools # noqa

logger = logging.getLogger("agent_fabric.plugins.manager")

__all__ = ["PluginManager", "plugin_manager"]


class PluginManager:
    """
    Manager for discovering, registering, enabling, and disabling AgentFabric plugins.
    """
    def __init__(self) -> None:
        self._manifests: Dict[str, PluginManifest] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        hn = PluginManifest(
            name="hackernews",
            version="1.0.0",
            description="Built-in HackerNews top story fetcher tool.",
            tools=["fetch_hackernews_top"]
        )
        gh = PluginManifest(
            name="github",
            version="1.0.0",
            description="Built-in GitHub public repository metadata tool.",
            tools=["get_github_repo_info"]
        )
        self._manifests[hn.name] = hn
        self._manifests[gh.name] = gh

    def list_plugins(self) -> List[PluginManifest]:
        return list(self._manifests.values())

    def get_plugin(self, name: str) -> Optional[PluginManifest]:
        return self._manifests.get(name)

    def enable_plugin(self, name: str) -> None:
        if name in self._manifests:
            self._manifests[name].enabled = True

    def disable_plugin(self, name: str) -> None:
        if name in self._manifests:
            self._manifests[name].enabled = False


plugin_manager = PluginManager()
