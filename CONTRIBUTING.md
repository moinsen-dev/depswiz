# Contributing to depswiz

Thank you for your interest in contributing to depswiz! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/depswiz.git
   cd depswiz
   ```

2. Install development dependencies:
   ```bash
   # Using uv (recommended)
   uv sync --dev

   # Or using pip
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Verify your setup:
   ```bash
   # Run tests
   pytest

   # Run linting
   ruff check src/depswiz

   # Run type checking
   mypy src/depswiz
   ```

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Making Changes

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes, following our coding standards

3. Write or update tests as needed

4. Run the test suite:
   ```bash
   pytest
   ```

5. Run linting and type checking:
   ```bash
   ruff check src/depswiz
   ruff format src/depswiz
   mypy src/depswiz
   ```

6. Commit your changes with a clear message:
   ```bash
   git commit -m "feat: add support for XYZ"
   ```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Pull Request Process

1. Push your branch to your fork
2. Create a Pull Request against `main`
3. Fill out the PR template
4. Wait for CI checks to pass
5. Request a review

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) with a line length of 100
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Use f-strings for string formatting

### Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Use pytest fixtures for common test data
- Test edge cases and error conditions

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new public APIs
- Update CHANGELOG.md for notable changes

## Adding a New Language Plugin

1. Create a new directory under `src/depswiz/plugins/`:
   ```
   src/depswiz/plugins/mylang/
   ├── __init__.py
   └── plugin.py
   ```

2. Implement the `LanguagePlugin` interface:
   ```python
   from depswiz.plugins.base import LanguagePlugin

   class MyLangPlugin(LanguagePlugin):
       @property
       def name(self) -> str:
           return "mylang"

       @property
       def display_name(self) -> str:
           return "My Language"

       # ... implement other required methods
   ```

3. Register in `pyproject.toml`:
   ```toml
   [project.entry-points."depswiz.languages"]
   mylang = "depswiz.plugins.mylang:MyLangPlugin"
   ```

4. Add tests in `tests/test_plugins.py`

## Adding a New Development Tool

1. Add the tool definition in `src/depswiz/tools/definitions.py`:
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

2. If the tool needs special version fetching, add a handler in `version_sources.py`

3. Test with `depswiz tools -t mytool`

## Reporting Issues

### Bug Reports

Please include:
- depswiz version (`depswiz version`)
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant error messages or logs

### Feature Requests

Please describe:
- The problem you're trying to solve
- Your proposed solution
- Alternative solutions you've considered

## Questions?

- Open a [Discussion](https://github.com/moinsen-dev/depswiz/discussions) for questions
- Check existing [Issues](https://github.com/moinsen-dev/depswiz/issues) for known problems

Thank you for contributing!
