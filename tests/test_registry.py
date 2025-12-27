"""Tests for plugin registry and discovery."""

from pathlib import Path

import pytest

from depswiz.plugins.registry import (
    discover_plugins,
    get_all_plugins,
    get_plugin,
    get_plugins_for_path,
    list_plugins,
)


class TestDiscoverPlugins:
    """Tests for discover_plugins function."""

    def test_discover_plugins_returns_dict(self) -> None:
        """Test that discover_plugins returns a dictionary."""
        plugins = discover_plugins()
        assert isinstance(plugins, dict)

    def test_discover_plugins_finds_builtin(self) -> None:
        """Test that built-in plugins are discovered."""
        plugins = discover_plugins()
        # Should find at least the built-in plugins
        assert "python" in plugins
        assert "rust" in plugins
        assert "dart" in plugins
        assert "javascript" in plugins

    def test_discover_plugins_is_cached(self) -> None:
        """Test that plugin discovery is cached."""
        plugins1 = discover_plugins()
        plugins2 = discover_plugins()
        assert plugins1 is plugins2


class TestGetPlugin:
    """Tests for get_plugin function."""

    def test_get_python_plugin(self) -> None:
        """Test getting the Python plugin."""
        plugin = get_plugin("python")
        assert plugin is not None
        assert plugin.name == "python"

    def test_get_rust_plugin(self) -> None:
        """Test getting the Rust plugin."""
        plugin = get_plugin("rust")
        assert plugin is not None
        assert plugin.name == "rust"

    def test_get_dart_plugin(self) -> None:
        """Test getting the Dart plugin."""
        plugin = get_plugin("dart")
        assert plugin is not None
        assert plugin.name == "dart"

    def test_get_javascript_plugin(self) -> None:
        """Test getting the JavaScript plugin."""
        plugin = get_plugin("javascript")
        assert plugin is not None
        assert plugin.name == "javascript"

    def test_get_nonexistent_plugin(self) -> None:
        """Test getting a non-existent plugin returns None."""
        plugin = get_plugin("nonexistent-plugin")
        assert plugin is None

    def test_get_plugin_caches_instances(self) -> None:
        """Test that plugin instances are cached."""
        plugin1 = get_plugin("python")
        plugin2 = get_plugin("python")
        assert plugin1 is plugin2


class TestGetAllPlugins:
    """Tests for get_all_plugins function."""

    def test_get_all_plugins_returns_list(self) -> None:
        """Test that get_all_plugins returns a list."""
        plugins = get_all_plugins()
        assert isinstance(plugins, list)

    def test_get_all_plugins_contains_builtin(self) -> None:
        """Test that get_all_plugins includes built-in plugins."""
        plugins = get_all_plugins()
        names = [p.name for p in plugins]
        assert "python" in names
        assert "rust" in names
        assert "dart" in names
        assert "javascript" in names


class TestGetPluginsForPath:
    """Tests for get_plugins_for_path function."""

    @pytest.fixture
    def python_project(self, tmp_path: Path) -> Path:
        """Create a Python project directory."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        return tmp_path

    @pytest.fixture
    def rust_project(self, tmp_path: Path) -> Path:
        """Create a Rust project directory."""
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "test"\n')
        return tmp_path

    @pytest.fixture
    def mixed_project(self, tmp_path: Path) -> Path:
        """Create a mixed Python+JS project directory."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "package.json").write_text('{"name": "test"}\n')
        return tmp_path

    def test_detect_python_project(self, python_project: Path) -> None:
        """Test detecting a Python project."""
        plugins = get_plugins_for_path(python_project)
        names = [p.name for p in plugins]
        assert "python" in names

    def test_detect_rust_project(self, rust_project: Path) -> None:
        """Test detecting a Rust project."""
        plugins = get_plugins_for_path(rust_project)
        names = [p.name for p in plugins]
        assert "rust" in names

    def test_detect_mixed_project(self, mixed_project: Path) -> None:
        """Test detecting a mixed project."""
        plugins = get_plugins_for_path(mixed_project)
        names = [p.name for p in plugins]
        assert "python" in names
        assert "javascript" in names

    def test_detect_empty_directory(self, tmp_path: Path) -> None:
        """Test detecting an empty directory returns no plugins."""
        plugins = get_plugins_for_path(tmp_path)
        assert plugins == []


class TestListPlugins:
    """Tests for list_plugins function."""

    def test_list_plugins_returns_list(self) -> None:
        """Test that list_plugins returns a list."""
        plugins = list_plugins()
        assert isinstance(plugins, list)

    def test_list_plugins_has_metadata(self) -> None:
        """Test that listed plugins have required metadata."""
        plugins = list_plugins()
        for plugin in plugins:
            assert "name" in plugin
            assert "display_name" in plugin
            assert "manifest_patterns" in plugin
            assert "lockfile_patterns" in plugin
            assert "supports_workspaces" in plugin

    def test_list_plugins_includes_python(self) -> None:
        """Test that Python plugin is in the list."""
        plugins = list_plugins()
        names = [p["name"] for p in plugins]
        assert "python" in names

    def test_list_plugins_python_details(self) -> None:
        """Test Python plugin metadata details."""
        plugins = list_plugins()
        python_plugin = next(p for p in plugins if p["name"] == "python")
        assert python_plugin["display_name"] == "Python"
        assert "pyproject.toml" in python_plugin["manifest_patterns"]
