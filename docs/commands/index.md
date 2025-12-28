# Commands Reference

depswiz provides a comprehensive set of commands for dependency management across multiple languages.

## Quick Start

```bash
# Just run depswiz - comprehensive scan of everything
depswiz
```

## Command Overview

| Command | Description |
|---------|-------------|
| `depswiz` | Comprehensive scan (check + audit + licenses) |
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
| `--json` | Output as JSON |
| `--md` | Output as Markdown |
| `--html` | Output as HTML |
| `-o`, `--output FILE` | Write output to file |
| `--strict` | Exit with code 1 on issues (auto-enabled in CI) |
| `--only LANGS` | Filter by language(s), comma-separated |
| `--shallow` | Scan current directory only (default: recursive) |
| `--prod` | Exclude development dependencies |
| `-v`, `--verbose` | Show detailed output |
| `-q`, `--quiet` | Suppress non-essential output |
| `-V`, `--version` | Show version and exit |
| `--help` | Show help message and exit |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - no issues found |
| 1 | Issues found (with `--strict` or auto-enabled in CI) |
| 2 | Invalid arguments or configuration |

## Examples

### Comprehensive Scan

```bash
# Full scan: dependencies + vulnerabilities + licenses
depswiz

# Save comprehensive report
depswiz --json -o report.json

# Fail on any issues
depswiz --strict
```

### CI/CD Pipeline

```bash
# In CI, just run depswiz - strict mode auto-enabled
depswiz

# Or be explicit
depswiz audit --strict
depswiz licenses --strict
```

### Multi-Language Project

```bash
# Check specific languages
depswiz check --only python,rust

# Check entire workspace (recursive by default)
depswiz check
```

### Output Formats

```bash
# JSON for machine processing
depswiz check --json

# Markdown for documentation
depswiz audit --md -o SECURITY.md

# HTML report
depswiz licenses --html -o licenses.html
```
