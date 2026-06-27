import logging
from agent_fabric.plugins.manifest import PluginManifest
from agent_fabric.plugins.manager import plugin_manager

logger = logging.getLogger("agent_fabric.plugins.loader")

__all__ = ["load_plugin_manifest"]


def load_plugin_manifest(manifest_dict: dict) -> PluginManifest:
    """Instantiates and registers a plugin manifest from a dictionary definition."""
    manifest = PluginManifest(**manifest_dict)
    plugin_manager._manifests[manifest.name] = manifest
    return manifest
