"""Plugin system for depswiz."""

from depswiz.plugins.base import LanguagePlugin
from depswiz.plugins.registry import (
    discover_plugins,
    get_all_plugins,
    get_plugin,
    get_plugins_for_path,
    list_plugins,
)

__all__ = [
    "LanguagePlugin",
    "discover_plugins",
    "get_all_plugins",
    "get_plugin",
    "get_plugins_for_path",
    "list_plugins",
]
