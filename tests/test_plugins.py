"""Tests for language plugins."""

from pathlib import Path

from depswiz.plugins.dart.plugin import DartPlugin
from depswiz.plugins.javascript.plugin import JavaScriptPlugin
from depswiz.plugins.python.plugin import PythonPlugin
from depswiz.plugins.rust.plugin import RustPlugin


class TestPythonPlugin:
    """Tests for the Python plugin."""

    def test_name(self):
        plugin = PythonPlugin()
        assert plugin.name == "python"
        assert plugin.display_name == "Python"

    def test_manifest_patterns(self):
        plugin = PythonPlugin()
        assert "pyproject.toml" in plugin.manifest_patterns
        assert "requirements.txt" in plugin.manifest_patterns

    def test_detect(self, sample_pyproject: Path):
        plugin = PythonPlugin()
        assert plugin.detect(sample_pyproject.parent)

    def test_detect_no_manifest(self, tmp_path: Path):
        plugin = PythonPlugin()
        assert not plugin.detect(tmp_path)

    def test_parse_manifest(self, sample_pyproject: Path):
        plugin = PythonPlugin()
        packages = plugin.parse_manifest(sample_pyproject)

        assert len(packages) >= 3
        names = [p.name for p in packages]
        assert "requests" in names
        assert "httpx" in names
        assert "pydantic" in names

    def test_parse_requirements_string(self):
        plugin = PythonPlugin()

        # Simple package
        pkg = plugin._parse_requirement_string("requests>=2.28.0")
        assert pkg is not None
        assert pkg.name == "requests"
        assert pkg.constraint == ">=2.28.0"

        # Package with extras
        pkg = plugin._parse_requirement_string("httpx[http2]>=0.25.0")
        assert pkg is not None
        assert pkg.name == "httpx"
        assert pkg.extras == ["http2"]


class TestRustPlugin:
    """Tests for the Rust plugin."""

    def test_name(self):
        plugin = RustPlugin()
        assert plugin.name == "rust"
        assert plugin.display_name == "Rust"

    def test_manifest_patterns(self):
        plugin = RustPlugin()
        assert plugin.manifest_patterns == ["Cargo.toml"]

    def test_detect(self, sample_cargo_toml: Path):
        plugin = RustPlugin()
        assert plugin.detect(sample_cargo_toml.parent)

    def test_parse_manifest(self, sample_cargo_toml: Path):
        plugin = RustPlugin()
        packages = plugin.parse_manifest(sample_cargo_toml)

        assert len(packages) >= 2
        names = [p.name for p in packages]
        assert "serde" in names
        assert "tokio" in names


class TestDartPlugin:
    """Tests for the Dart plugin."""

    def test_name(self):
        plugin = DartPlugin()
        assert plugin.name == "dart"
        assert plugin.display_name == "Dart/Flutter"

    def test_manifest_patterns(self):
        plugin = DartPlugin()
        assert plugin.manifest_patterns == ["pubspec.yaml"]

    def test_detect(self, sample_pubspec: Path):
        plugin = DartPlugin()
        assert plugin.detect(sample_pubspec.parent)

    def test_parse_manifest(self, sample_pubspec: Path):
        plugin = DartPlugin()
        packages = plugin.parse_manifest(sample_pubspec)

        assert len(packages) >= 2
        names = [p.name for p in packages]
        assert "http" in names
        assert "provider" in names


class TestJavaScriptPlugin:
    """Tests for the JavaScript plugin."""

    def test_name(self):
        plugin = JavaScriptPlugin()
        assert plugin.name == "javascript"
        assert plugin.display_name == "JavaScript/TypeScript"

    def test_manifest_patterns(self):
        plugin = JavaScriptPlugin()
        assert plugin.manifest_patterns == ["package.json"]

    def test_detect(self, sample_package_json: Path):
        plugin = JavaScriptPlugin()
        assert plugin.detect(sample_package_json.parent)

    def test_parse_manifest(self, sample_package_json: Path):
        plugin = JavaScriptPlugin()
        packages = plugin.parse_manifest(sample_package_json)

        assert len(packages) >= 4
        names = [p.name for p in packages]
        assert "express" in names
        assert "lodash" in names
        assert "typescript" in names
        assert "jest" in names
