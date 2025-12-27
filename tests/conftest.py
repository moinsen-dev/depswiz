"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_path() -> Path:
    """Return the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pyproject(tmp_path: Path) -> Path:
    """Create a sample pyproject.toml file."""
    content = """
[project]
name = "test-project"
version = "0.1.0"
dependencies = [
    "requests>=2.28.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.1.0",
]
"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    return pyproject


@pytest.fixture
def sample_cargo_toml(tmp_path: Path) -> Path:
    """Create a sample Cargo.toml file."""
    content = """
[package]
name = "test-project"
version = "0.1.0"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }

[dev-dependencies]
criterion = "0.5"
"""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text(content)
    return cargo


@pytest.fixture
def sample_package_json(tmp_path: Path) -> Path:
    """Create a sample package.json file."""
    content = """
{
  "name": "test-project",
  "version": "0.1.0",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}
"""
    package = tmp_path / "package.json"
    package.write_text(content)
    return package


@pytest.fixture
def sample_pubspec(tmp_path: Path) -> Path:
    """Create a sample pubspec.yaml file."""
    content = """
name: test_project
version: 0.1.0

environment:
  sdk: ^3.0.0

dependencies:
  http: ^1.0.0
  provider: ^6.0.0

dev_dependencies:
  test: ^1.24.0
"""
    pubspec = tmp_path / "pubspec.yaml"
    pubspec.write_text(content)
    return pubspec
