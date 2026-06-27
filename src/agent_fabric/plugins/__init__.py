"""
AgentFabric Plugins package.
Provides discovery, registration, and lifecycle management for external and built-in plugins.
"""
from agent_fabric.plugins.manifest import PluginManifest as PluginManifest
from agent_fabric.plugins.manager import PluginManager as PluginManager, plugin_manager as plugin_manager
from agent_fabric.plugins.loader import load_plugin_manifest as load_plugin_manifest

__all__ = ["PluginManifest", "PluginManager", "plugin_manager", "load_plugin_manifest"]
