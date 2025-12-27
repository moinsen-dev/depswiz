# Contributing

Thank you for your interest in contributing to depswiz! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to be respectful and constructive in all interactions.

## Ways to Contribute

- **Bug Reports**: Found a bug? Open an issue with reproduction steps
- **Feature Requests**: Have an idea? Start a discussion
- **Documentation**: Improve docs, fix typos, add examples
- **Code**: Fix bugs, add features, improve performance
- **Plugins**: Create new language plugins

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Getting Started

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/depswiz.git
cd depswiz

# Install with dev dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Verify setup
pytest
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/bug-description
```

Branch naming:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

### 2. Make Changes

- Follow the coding standards
- Write tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Run tests
pytest

# Run linting
ruff check src/depswiz

# Run type checking
mypy src/depswiz

# Format code
ruff format src/depswiz
```

### 4. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add support for Go language"
git commit -m "fix: handle empty manifest files"
git commit -m "docs: improve installation guide"
```

Commit types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance

### 5. Submit Pull Request

1. Push to your fork
2. Open a PR against `main`
3. Fill out the PR template
4. Wait for CI checks
5. Address review feedback

## Coding Standards

### Python Style

- Follow PEP 8 with line length of 100
- Use type hints for all public APIs
- Write docstrings for public functions
- Use f-strings for formatting

```python
def fetch_package(name: str, version: str | None = None) -> Package:
    """Fetch package information from registry.

    Args:
        name: Package name
        version: Optional version to fetch

    Returns:
        Package object with metadata

    Raises:
        PackageNotFoundError: If package doesn't exist
    """
```

### Testing

- Write tests for all new code
- Maintain or improve coverage
- Use pytest fixtures
- Test edge cases

```python
# tests/test_parser.py

import pytest
from depswiz.plugins.python import parse_pyproject


def test_parse_basic_dependencies():
    content = """
    [project]
    dependencies = ["httpx>=0.27.0"]
    """
    packages = parse_pyproject(content)
    assert len(packages) == 1
    assert packages[0].name == "httpx"


def test_parse_empty_dependencies():
    content = "[project]\n"
    packages = parse_pyproject(content)
    assert packages == []
```

### Documentation

- Update docs for user-facing changes
- Add docstrings to new APIs
- Keep examples up to date

## Project Structure

```
depswiz/
├── src/depswiz/
│   ├── cli/           # CLI commands
│   ├── core/          # Core models and logic
│   ├── plugins/       # Language plugins
│   ├── security/      # Vulnerability scanning
│   ├── tools/         # Development tools checking
│   └── ai/            # Claude integration
├── tests/             # Test suite
├── docs/              # Documentation
└── pyproject.toml     # Project configuration
```

## Adding a Language Plugin

See [Plugin Development Guide](plugins/developing.md).

Quick steps:

1. Create `src/depswiz/plugins/mylang/`
2. Implement `LanguagePlugin` interface
3. Register in `pyproject.toml` entry points
4. Add tests in `tests/test_plugins.py`
5. Add documentation in `docs/languages/`

## Adding a Development Tool

1. Add tool definition in `src/depswiz/tools/definitions.py`:

```python
"mytool": ToolDefinition(
    name="mytool",
    display_name="My Tool",
    version_command=["mytool", "--version"],
    version_regex=r"mytool\s+(\d+\.\d+\.\d+)",
    github_repo="owner/mytool",
    project_indicators=["mytool.config"],
    update_instructions={
        "macos": "brew upgrade mytool",
        "linux": "...",
        "windows": "...",
    },
),
```

2. If needed, add version source in `version_sources.py`
3. Test with `depswiz tools -t mytool`

## Reporting Issues

### Bug Reports

Please include:
- depswiz version (`depswiz --version`)
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages

### Feature Requests

Please describe:
- The problem you're solving
- Your proposed solution
- Alternative approaches

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/moinsen-dev/depswiz/discussions)
- **Bugs**: Open an [Issue](https://github.com/moinsen-dev/depswiz/issues)

## Recognition

Contributors are recognized in:
- Release notes
- CONTRIBUTORS.md file
- GitHub contributor graph

Thank you for contributing!
