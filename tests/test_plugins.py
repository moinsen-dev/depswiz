"""Tests for language plugins."""

from pathlib import Path

from depswiz.plugins.dart.plugin import DartPlugin
from depswiz.plugins.docker.plugin import DockerPlugin
from depswiz.plugins.docker.dockerfile import DockerImage, parse_dockerfile
from depswiz.plugins.docker.compose import parse_compose_file
from depswiz.plugins.docker.registry import compare_tags
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


class TestDockerPlugin:
    """Tests for the Docker plugin."""

    def test_name(self):
        plugin = DockerPlugin()
        assert plugin.name == "docker"
        assert plugin.display_name == "Docker"

    def test_manifest_patterns(self):
        plugin = DockerPlugin()
        assert "Dockerfile" in plugin.manifest_patterns
        assert "docker-compose.yml" in plugin.manifest_patterns
        assert "compose.yaml" in plugin.manifest_patterns

    def test_lockfile_patterns(self):
        plugin = DockerPlugin()
        assert plugin.lockfile_patterns == []

    def test_detect(self, sample_dockerfile: Path):
        plugin = DockerPlugin()
        assert plugin.detect(sample_dockerfile.parent)

    def test_detect_compose(self, sample_compose_file: Path):
        plugin = DockerPlugin()
        assert plugin.detect(sample_compose_file.parent)

    def test_detect_no_manifest(self, tmp_path: Path):
        plugin = DockerPlugin()
        assert not plugin.detect(tmp_path)

    def test_parse_manifest_dockerfile(self, sample_dockerfile: Path):
        plugin = DockerPlugin()
        packages = plugin.parse_manifest(sample_dockerfile)

        assert len(packages) == 2
        names = [p.name for p in packages]
        assert "python" in names
        # Both FROM statements use python:3.11-slim
        for pkg in packages:
            assert pkg.current_version == "3.11-slim"

    def test_parse_manifest_compose(self, sample_compose_file: Path):
        plugin = DockerPlugin()
        packages = plugin.parse_manifest(sample_compose_file)

        assert len(packages) == 3
        names = [p.name for p in packages]
        assert "nginx" in names
        assert "postgres" in names
        assert "redis" in names

        # Check versions
        versions = {p.name: p.current_version for p in packages}
        assert versions["nginx"] == "1.24"
        assert versions["postgres"] == "15"
        assert versions["redis"] == "latest"


class TestDockerfileParser:
    """Tests for Dockerfile parsing."""

    def test_parse_simple_from(self, tmp_path: Path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.13\n")

        images = parse_dockerfile(dockerfile)
        assert len(images) == 1
        assert images[0].name == "python"
        assert images[0].tag == "3.13"

    def test_parse_multistage(self, tmp_path: Path):
        content = """
FROM golang:1.21 AS builder
RUN go build -o app

FROM alpine:3.19
COPY --from=builder /app /app
"""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(content)

        images = parse_dockerfile(dockerfile)
        assert len(images) == 2
        assert images[0].name == "golang"
        assert images[0].tag == "1.21"
        assert images[0].stage_name == "builder"
        assert images[1].name == "alpine"
        assert images[1].tag == "3.19"

    def test_parse_with_digest(self, tmp_path: Path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python@sha256:abc123def456\n")

        images = parse_dockerfile(dockerfile)
        assert len(images) == 1
        assert images[0].name == "python"
        assert images[0].digest == "sha256:abc123def456"
        assert images[0].tag is None

    def test_parse_with_platform(self, tmp_path: Path):
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM --platform=linux/amd64 python:3.13\n")

        images = parse_dockerfile(dockerfile)
        assert len(images) == 1
        assert images[0].name == "python"
        assert images[0].tag == "3.13"

    def test_skip_scratch(self, tmp_path: Path):
        content = """
FROM golang:1.21 AS builder
RUN go build -o app

FROM scratch
COPY --from=builder /app /app
"""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(content)

        images = parse_dockerfile(dockerfile)
        assert len(images) == 1
        assert images[0].name == "golang"

    def test_parse_official_image(self):
        image = DockerImage(name="python", tag="3.13")
        assert image.is_official
        assert image.namespace == "library"
        assert image.repository == "python"
        assert image.registry == "docker.io"

    def test_parse_user_image(self):
        image = DockerImage(name="myuser/myapp", tag="latest")
        assert not image.is_official
        assert image.namespace == "myuser"
        assert image.repository == "myapp"
        assert image.registry == "docker.io"

    def test_parse_custom_registry(self):
        image = DockerImage(name="gcr.io/project/image", tag="v1.0")
        assert not image.is_official
        assert image.registry == "gcr.io"
        assert image.repository == "image"


class TestComposeParser:
    """Tests for Docker Compose parsing."""

    def test_parse_services(self, sample_compose_file: Path):
        images = parse_compose_file(sample_compose_file)

        assert len(images) == 3
        names = {i.name for i in images}
        assert names == {"nginx", "postgres", "redis"}

    def test_parse_with_build_only(self, tmp_path: Path):
        content = """
version: '3.8'
services:
  app:
    build: .
  db:
    image: postgres:15
"""
        compose = tmp_path / "docker-compose.yml"
        compose.write_text(content)

        images = parse_compose_file(compose)
        assert len(images) == 1
        assert images[0].name == "postgres"

    def test_parse_empty_file(self, tmp_path: Path):
        compose = tmp_path / "docker-compose.yml"
        compose.write_text("")

        images = parse_compose_file(compose)
        assert images == []


class TestTagComparison:
    """Tests for Docker tag comparison."""

    def test_compare_semver_tags(self):
        assert compare_tags("3.11", "3.13") is True
        assert compare_tags("3.13", "3.11") is False
        assert compare_tags("3.13", "3.13") is False

    def test_compare_with_suffix(self):
        assert compare_tags("3.11-slim", "3.13-slim") is True
        assert compare_tags("1.24", "1.25") is True

    def test_compare_none_tags(self):
        assert compare_tags(None, "3.13") is False
        assert compare_tags("3.11", None) is False
        assert compare_tags(None, None) is False

    def test_compare_latest_tag(self):
        # latest vs semver can't be compared
        assert compare_tags("latest", "3.13") is False
