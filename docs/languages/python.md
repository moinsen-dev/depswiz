# Python Support

depswiz provides comprehensive support for Python projects using various package managers and dependency specification formats.

## Supported Files

### Manifest Files

| File | Description |
|------|-------------|
| `pyproject.toml` | Modern Python project configuration (PEP 517/518/621) |
| `requirements.txt` | pip requirements format |
| `setup.py` | Legacy setuptools configuration |

### Lockfiles

| File | Package Manager |
|------|-----------------|
| `uv.lock` | uv |
| `poetry.lock` | Poetry |
| `Pipfile.lock` | Pipenv |

## Package Registry

depswiz queries [PyPI](https://pypi.org) for package information:

```
GET https://pypi.org/pypi/{package}/json
```

## Examples

### Check Python Dependencies

```bash
# Check current directory
depswiz check

# Check only Python
depswiz check -l python

# Check specific project
depswiz check /path/to/python/project
```

### Audit for Vulnerabilities

```bash
depswiz audit -l python
```

Python packages are checked against:
- [OSV](https://osv.dev/) - Open Source Vulnerabilities
- [GitHub Advisory Database](https://github.com/advisories)
- [PyPI Security Advisories](https://pypi.org/security/)

### Generate SBOM

```bash
depswiz sbom -l python -o python-sbom.json
```

## Dependency Specification

### pyproject.toml (PEP 621)

```toml
[project]
name = "my-project"
version = "1.0.0"
dependencies = [
    "httpx>=0.27.0",
    "rich>=13.9.0",
    "typer>=0.15.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "mypy>=1.13.0",
]
```

### requirements.txt

```
httpx>=0.27.0
rich>=13.9.0
typer>=0.15.0
```

## Version Specifiers

depswiz understands PEP 440 version specifiers:

| Specifier | Meaning |
|-----------|---------|
| `==1.2.3` | Exact version |
| `>=1.2.0` | Minimum version |
| `>=1.2,<2.0` | Version range |
| `~=1.2.0` | Compatible release (>=1.2.0, <1.3.0) |
| `^1.2.0` | Poetry-style compatible (>=1.2.0, <2.0.0) |

## Workspace Support

### uv Workspaces

```toml
# pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]
```

### Poetry Workspaces

```toml
# pyproject.toml
[tool.poetry]
packages = [
    { include = "package_a", from = "packages" },
]
```

Scan all workspace members:

```bash
depswiz check --workspace
```

## Update Commands

depswiz generates appropriate update commands:

| Package Manager | Update Command |
|-----------------|----------------|
| uv | `uv add package@version` |
| pip | `pip install package==version` |
| poetry | `poetry add package@version` |

## Common Issues

### Multiple Python Versions

depswiz uses the Python version from your environment. Ensure you're in the correct virtual environment:

```bash
# Activate venv first
source .venv/bin/activate
depswiz check
```

### Private Package Indices

For private PyPI servers, depswiz respects pip configuration:

```ini
# ~/.pip/pip.conf
[global]
index-url = https://private.pypi.example.com/simple/
```

### Version Conflicts

When dependencies have conflicting version requirements, depswiz reports them:

```
Conflict: package-a requires httpx>=0.28.0
          package-b requires httpx<0.28.0
```

## See Also

- [Commands Reference](../commands/index.md)
- [Configuration](../configuration.md)
- [PyPI](https://pypi.org)
- [PEP 621](https://peps.python.org/pep-0621/) - Project metadata
- [PEP 440](https://peps.python.org/pep-0440/) - Version specifiers
