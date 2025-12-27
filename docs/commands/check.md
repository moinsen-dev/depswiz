# depswiz check

Check dependencies for available updates across all supported languages.

## Usage

```bash
depswiz check [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project directory to check | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `-l`, `--language` | Filter by language (can be used multiple times) |
| `-w`, `--workspace` | Check all workspace members |
| `-r`, `--recursive` | Recursively check subdirectories |
| `--strategy` | Update strategy: all, security, patch, minor, major |
| `--fail-outdated` | Exit with code 1 if outdated packages found |
| `-f`, `--format` | Output format: cli, json, markdown, html |

## Examples

### Basic Usage

```bash
# Check current directory
depswiz check

# Check specific directory
depswiz check /path/to/project
```

### Filter by Language

```bash
# Only check Python
depswiz check -l python

# Check Python and Rust
depswiz check -l python -l rust

# Check JavaScript/TypeScript
depswiz check -l javascript
```

### Workspace Mode

```bash
# Check all workspace members
depswiz check --workspace

# Combine with language filter
depswiz check --workspace -l rust
```

### Update Strategies

```bash
# Show all updates (default)
depswiz check --strategy all

# Only show security updates
depswiz check --strategy security

# Only show patch updates
depswiz check --strategy patch

# Only show minor updates
depswiz check --strategy minor
```

### CI/CD Usage

```bash
# Fail if any outdated packages
depswiz check --fail-outdated

# JSON output for parsing
depswiz check --format json

# Combine both
depswiz check --fail-outdated --format json
```

## Output

### CLI Format (Default)

```
depswiz v0.2.0 - Dependency Check

Detected: Python (pyproject.toml)

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Package         ┃ Current   ┃ Latest    ┃ Update Type      ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ httpx           │ 0.27.0    │ 0.28.1    │ minor            │
│ rich            │ 13.9.0    │ 13.9.4    │ patch            │
│ typer           │ 0.15.0    │ 0.15.1    │ patch            │
└─────────────────┴───────────┴───────────┴──────────────────┘

3 package(s) have updates available
```

### JSON Format

```json
{
  "packages": [
    {
      "name": "httpx",
      "current_version": "0.27.0",
      "latest_version": "0.28.1",
      "update_type": "minor",
      "language": "python"
    }
  ],
  "summary": {
    "total": 10,
    "outdated": 3,
    "up_to_date": 7
  }
}
```

## Supported Languages

| Language | Manifest Files | Lockfiles |
|----------|---------------|-----------|
| Python | pyproject.toml, requirements.txt | uv.lock, poetry.lock |
| Rust | Cargo.toml | Cargo.lock |
| Dart/Flutter | pubspec.yaml | pubspec.lock |
| JavaScript/TypeScript | package.json | package-lock.json, yarn.lock |

## See Also

- [depswiz audit](audit.md) - Scan for vulnerabilities
- [depswiz update](update.md) - Update dependencies
- [depswiz suggest](suggest.md) - AI-powered suggestions
