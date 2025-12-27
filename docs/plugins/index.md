# Plugin System

depswiz uses a plugin architecture to support multiple programming languages. Each language is implemented as a plugin that can be built-in or installed separately.

## Overview

Plugins provide:
- **Manifest parsing** - Read dependency specifications from project files
- **Lockfile parsing** - Read resolved dependency versions
- **Registry integration** - Query package registries for latest versions
- **Vulnerability sources** - Check language-specific security advisories
- **Update commands** - Generate appropriate update commands

## Built-in Plugins

depswiz includes these plugins out of the box:

| Plugin | Language | Manifest Files |
|--------|----------|---------------|
| `python` | Python | pyproject.toml, requirements.txt |
| `rust` | Rust | Cargo.toml |
| `dart` | Dart/Flutter | pubspec.yaml |
| `javascript` | JavaScript/TypeScript | package.json |

## Plugin Discovery

depswiz uses Python entry points for plugin discovery:

```toml
# pyproject.toml
[project.entry-points."depswiz.languages"]
python = "depswiz.plugins.python:PythonPlugin"
rust = "depswiz.plugins.rust:RustPlugin"
dart = "depswiz.plugins.dart:DartPlugin"
javascript = "depswiz.plugins.javascript:JavaScriptPlugin"
```

## Using Plugins

### List Available Plugins

```bash
depswiz plugins list
```

Output:

```
Available Plugins:

┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name          ┃ Version   ┃ Manifest Files                ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ python        │ 0.2.0     │ pyproject.toml, requirements  │
│ rust          │ 0.2.0     │ Cargo.toml                    │
│ dart          │ 0.2.0     │ pubspec.yaml                  │
│ javascript    │ 0.2.0     │ package.json                  │
└───────────────┴───────────┴───────────────────────────────┘
```

### Plugin Information

```bash
depswiz plugins info python
```

Output:

```
Plugin: python

Display Name: Python
Version: 0.2.0
Description: Python dependency management for pyproject.toml and requirements.txt

Manifest Files:
  - pyproject.toml
  - requirements.txt
  - setup.py

Lockfiles:
  - uv.lock
  - poetry.lock
  - Pipfile.lock

Registry: https://pypi.org/
Vulnerability Sources: OSV, GitHub Advisories
```

### Filter by Plugin

```bash
# Use specific plugin
depswiz check -l python
depswiz check -l rust -l javascript
```

## Configuration

Enable or disable specific plugins:

```toml
# depswiz.toml
[languages]
enabled = ["python", "rust"]  # Only use these plugins
```

## Next Steps

- [Developing Plugins](developing.md) - Create your own language plugin
- [Plugin API Reference](api.md) - Complete API documentation
