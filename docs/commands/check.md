# depswiz check

Check dependencies for available updates across all supported languages.

## Usage

```bash
depswiz check [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--md` | Output as Markdown |
| `--html` | Output as HTML |
| `--sarif` | Output as SARIF 2.1 (GitHub Code Scanning, VS Code) |
| `-o`, `--output FILE` | Write output to file |
| `--strict` | Exit with code 1 if outdated packages found |
| `--only LANGS` | Filter by language(s), comma-separated (e.g., `python,rust,golang`) |
| `--shallow` | Scan current directory only (default: recursive) |
| `--prod` | Exclude development dependencies |
| `--strategy` | Update strategy: all, security, patch, minor, major |
| `-p`, `--path PATH` | Project directory to check (default: current directory) |

## Examples

### Basic Usage

```bash
# Check current directory (recursive by default)
depswiz check

# Check specific directory
depswiz check -p /path/to/project
```

### Filter by Language

```bash
# Only check Python
depswiz check --only python

# Check Python and Rust
depswiz check --only python,rust

# Check JavaScript/TypeScript
depswiz check --only javascript
```

### Output Formats

```bash
# JSON output
depswiz check --json

# Save to file
depswiz check --json -o outdated.json

# Markdown for documentation
depswiz check --md -o DEPENDENCIES.md
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
depswiz check --strict

# JSON output for parsing
depswiz check --json

# Combine both
depswiz check --strict --json
```

In CI environments, `--strict` is automatically enabled.

### Scanning Options

```bash
# Recursive scan (default)
depswiz check

# Current directory only
depswiz check --shallow

# Exclude dev dependencies
depswiz check --prod
```

## Output

### CLI Format (Default)

```
depswiz v0.5.0 - Dependency Check

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
| Go | go.mod | go.sum |
| Docker | Dockerfile, docker-compose.yml | - |

## See Also

- [depswiz audit](audit.md) - Scan for vulnerabilities
- [depswiz update](update.md) - Update dependencies
- [depswiz suggest](suggest.md) - AI-powered suggestions
