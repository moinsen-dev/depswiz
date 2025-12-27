"""Plugin registry and discovery."""

from importlib.metadata import entry_points

from depswiz.plugins.base import LanguagePlugin

# Cache for discovered plugins
_plugins: dict[str, type[LanguagePlugin]] | None = None
_plugin_instances: dict[str, LanguagePlugin] = {}


def discover_plugins() -> dict[str, type[LanguagePlugin]]:
    """Discover all installed language plugins.

    Plugins are discovered via the 'depswiz.languages' entry point group.
    Each entry point should point to a LanguagePlugin subclass.

    Returns:
        Dictionary mapping plugin names to plugin classes
    """
    global _plugins

    if _plugins is not None:
        return _plugins

    _plugins = {}

    # Get all entry points in the depswiz.languages group
    eps = entry_points(group="depswiz.languages")

    for ep in eps:
        try:
            plugin_class = ep.load()
            if isinstance(plugin_class, type) and issubclass(plugin_class, LanguagePlugin):
                _plugins[ep.name] = plugin_class
        except Exception as e:
            # Log warning but continue loading other plugins
            import warnings

            warnings.warn(f"Failed to load plugin '{ep.name}': {e}")

    return _plugins


def get_plugin(name: str) -> LanguagePlugin | None:
    """Get a plugin instance by name.

    Args:
        name: Plugin name (e.g., 'python', 'rust')

    Returns:
        Plugin instance, or None if not found
    """
    if name in _plugin_instances:
        return _plugin_instances[name]

    plugins = discover_plugins()
    if name not in plugins:
        return None

    instance = plugins[name]()
    _plugin_instances[name] = instance
    return instance


def get_all_plugins() -> list[LanguagePlugin]:
    """Get instances of all available plugins.

    Returns:
        List of plugin instances
    """
    plugins = discover_plugins()
    result: list[LanguagePlugin] = []
    for name in plugins:
        plugin = get_plugin(name)
        if plugin is not None:
            result.append(plugin)
    return result


def get_plugins_for_path(path) -> list[LanguagePlugin]:
    """Get plugins that apply to a given path.

    Args:
        path: Path to check

    Returns:
        List of plugins that detect manifest files at the path
    """
    from pathlib import Path

    path = Path(path)

    applicable = []
    for plugin in get_all_plugins():
        if plugin.detect(path):
            applicable.append(plugin)

    return applicable


def list_plugins() -> list[dict]:
    """List all available plugins with metadata.

    Returns:
        List of plugin info dictionaries
    """
    plugins = discover_plugins()
    result = []

    for name, _plugin_class in plugins.items():
        instance = get_plugin(name)
        if instance:
            result.append(
                {
                    "name": instance.name,
                    "display_name": instance.display_name,
                    "manifest_patterns": instance.manifest_patterns,
                    "lockfile_patterns": instance.lockfile_patterns,
                    "supports_workspaces": instance.supports_workspaces(),
                }
            )

    return result
