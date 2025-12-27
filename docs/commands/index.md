# Commands Reference

depswiz provides a comprehensive set of commands for dependency management across multiple languages.

## Command Overview

| Command | Description |
|---------|-------------|
| [check](check.md) | Check dependencies for available updates |
| [audit](audit.md) | Scan for security vulnerabilities |
| [licenses](licenses.md) | Check license compliance |
| [sbom](sbom.md) | Generate Software Bill of Materials |
| [update](update.md) | Update dependencies interactively |
| [tools](tools.md) | Check development tools for updates |
| [suggest](suggest.md) | Get AI-powered upgrade suggestions |
| [guide](guide.md) | Interactive TUI dashboard with wizard and chat |
| [deprecations](deprecations.md) | Detect and fix deprecated API usage |

## Global Options

All commands support these global options:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit |
| `--format`, `-f` | Output format: cli, json, markdown, html |
| `--quiet`, `-q` | Suppress non-essential output |
| `--verbose`, `-v` | Show detailed output |

## Exit Codes

depswiz uses standard exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Vulnerabilities, violations, or errors found (with `--fail-*` flags) |
| 2 | Invalid arguments or configuration |

## Examples

### Quick Health Check

```bash
# Check everything in current directory
depswiz check
depswiz audit
depswiz licenses
```

### CI/CD Pipeline

```bash
# Fail on security issues
depswiz audit --fail-on high

# Check license compliance
depswiz licenses --deny GPL-3.0

# Generate SBOM for compliance
depswiz sbom -o sbom.json
```

### Multi-Language Project

```bash
# Check specific languages
depswiz check -l python -l rust

# Check entire workspace
depswiz check --workspace
```
