"""Tests for tool definitions."""

from depswiz.tools.definitions import (
    TOOL_DEFINITIONS,
    get_all_tool_names,
    get_tool_definition,
    get_tools_for_project_files,
)


class TestToolDefinitions:
    """Tests for tool definitions registry."""

    def test_all_tools_have_required_fields(self) -> None:
        """Test that all tool definitions have required fields."""
        for name, defn in TOOL_DEFINITIONS.items():
            assert defn.name, f"{name} missing name"
            assert defn.display_name, f"{name} missing display_name"
            assert defn.version_command, f"{name} missing version_command"
            assert defn.version_regex, f"{name} missing version_regex"

    def test_tool_definitions_count(self) -> None:
        """Test that we have the expected number of tools."""
        # Should have at least 20 tools
        assert len(TOOL_DEFINITIONS) >= 20

    def test_common_tools_exist(self) -> None:
        """Test that common tools are defined."""
        expected_tools = [
            "node",
            "python",
            "rust",
            "dart",
            "flutter",
            "go",
            "docker",
            "java",
            "ruby",
            "php",
        ]
        for tool in expected_tools:
            assert tool in TOOL_DEFINITIONS, f"Missing tool: {tool}"

    def test_tools_have_update_instructions(self) -> None:
        """Test that tools have update instructions for at least one platform."""
        for name, defn in TOOL_DEFINITIONS.items():
            assert defn.update_instructions, f"{name} missing update_instructions"
            # Should have instructions for at least macos or linux
            assert "macos" in defn.update_instructions or "linux" in defn.update_instructions


class TestGetToolDefinition:
    """Tests for get_tool_definition function."""

    def test_get_existing_tool(self) -> None:
        """Test getting an existing tool definition."""
        node = get_tool_definition("node")
        assert node is not None
        assert node.name == "node"
        assert node.display_name == "Node.js"

    def test_get_nonexistent_tool(self) -> None:
        """Test getting a non-existent tool returns None."""
        result = get_tool_definition("nonexistent-tool")
        assert result is None

    def test_get_tool_case_insensitive(self) -> None:
        """Test that tool lookup is case-insensitive."""
        assert get_tool_definition("NODE") is not None
        assert get_tool_definition("Python") is not None
        assert get_tool_definition("RUST") is not None


class TestGetAllToolNames:
    """Tests for get_all_tool_names function."""

    def test_returns_list(self) -> None:
        """Test that function returns a list."""
        names = get_all_tool_names()
        assert isinstance(names, list)

    def test_returns_all_tools(self) -> None:
        """Test that function returns all tool names."""
        names = get_all_tool_names()
        assert len(names) == len(TOOL_DEFINITIONS)

    def test_all_names_are_strings(self) -> None:
        """Test that all returned names are strings."""
        names = get_all_tool_names()
        assert all(isinstance(name, str) for name in names)


class TestGetToolsForProjectFiles:
    """Tests for get_tools_for_project_files function."""

    def test_detect_python_project(self) -> None:
        """Test detection of Python tools from project files."""
        files = ["pyproject.toml", "README.md"]
        tools = get_tools_for_project_files(files)
        assert "python" in tools
        assert "uv" in tools  # Related tool

    def test_detect_node_project(self) -> None:
        """Test detection of Node.js tools from project files."""
        files = ["package.json", "README.md"]
        tools = get_tools_for_project_files(files)
        assert "node" in tools
        assert "npm" in tools or "pnpm" in tools or "yarn" in tools

    def test_detect_rust_project(self) -> None:
        """Test detection of Rust tools from project files."""
        files = ["Cargo.toml", "README.md"]
        tools = get_tools_for_project_files(files)
        assert "rust" in tools
        assert "cargo" in tools

    def test_detect_dart_project(self) -> None:
        """Test detection of Dart tools from project files."""
        files = ["pubspec.yaml", "README.md"]
        tools = get_tools_for_project_files(files)
        assert "dart" in tools or "flutter" in tools

    def test_detect_go_project(self) -> None:
        """Test detection of Go tools from project files."""
        files = ["go.mod", "go.sum"]
        tools = get_tools_for_project_files(files)
        assert "go" in tools

    def test_detect_docker_project(self) -> None:
        """Test detection of Docker from project files."""
        files = ["Dockerfile", "docker-compose.yml"]
        tools = get_tools_for_project_files(files)
        assert "docker" in tools

    def test_detect_java_project(self) -> None:
        """Test detection of Java tools from project files."""
        files = ["pom.xml"]
        tools = get_tools_for_project_files(files)
        assert "java" in tools
        assert "maven" in tools

    def test_detect_ruby_project(self) -> None:
        """Test detection of Ruby tools from project files."""
        files = ["Gemfile"]
        tools = get_tools_for_project_files(files)
        assert "ruby" in tools
        assert "bundler" in tools

    def test_detect_php_project(self) -> None:
        """Test detection of PHP tools from project files."""
        files = ["composer.json"]
        tools = get_tools_for_project_files(files)
        assert "php" in tools
        assert "composer" in tools

    def test_detect_multi_language_project(self) -> None:
        """Test detection with multiple languages."""
        files = ["pyproject.toml", "package.json", "Dockerfile"]
        tools = get_tools_for_project_files(files)
        assert "python" in tools
        assert "node" in tools
        assert "docker" in tools

    def test_no_matching_files(self) -> None:
        """Test with no matching project files."""
        files = ["README.md", "LICENSE"]
        tools = get_tools_for_project_files(files)
        assert tools == []

    def test_returns_sorted_list(self) -> None:
        """Test that results are sorted."""
        files = ["package.json", "pyproject.toml"]
        tools = get_tools_for_project_files(files)
        assert tools == sorted(tools)
