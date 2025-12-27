# Quick Start Guide

This guide will help you get started with depswiz in just a few minutes.

## Basic Usage

### Check for Outdated Dependencies

Navigate to your project directory and run:

```bash
depswiz check
```

depswiz will automatically detect your project type and check all dependencies:

```
depswiz v0.2.0 - Dependency Wizard

Detected: Python (pyproject.toml)

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Package         ┃ Current   ┃ Latest    ┃ Status           ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ httpx           │ 0.27.0    │ 0.28.1    │ minor update     │
│ rich            │ 13.9.0    │ 13.9.4    │ patch update     │
│ typer           │ 0.15.0    │ 0.15.1    │ patch update     │
└─────────────────┴───────────┴───────────┴──────────────────┘

3 package(s) have updates available
```

### Scan for Vulnerabilities

Check your dependencies for known security vulnerabilities:

```bash
depswiz audit
```

Example output:

```
depswiz v0.2.0 - Security Audit

Scanning Python dependencies...

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package     ┃ CVE               ┃ Severity  ┃ Description             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ requests    │ CVE-2024-XXXXX    │ HIGH      │ SSRF vulnerability      │
└─────────────┴───────────────────┴───────────┴─────────────────────────┘

1 vulnerability found
```

### Check Your Development Tools

See if your development tools are up to date:

```bash
depswiz tools
```

Output:

```
depswiz v0.2.0 - Development Tools Check

Platform: macos

┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Tool      ┃ Installed  ┃ Latest     ┃ Status            ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Node.js   │ 20.10.0    │ 22.12.0    │ update available  │
│ Python    │ 3.13.1     │ 3.13.1     │ ok                │
│ uv        │ 0.5.10     │ 0.5.24     │ update available  │
└───────────┴────────────┴────────────┴───────────────────┘
```

## Multi-Language Projects

depswiz automatically detects and handles multiple languages in the same project:

```bash
# Check a project with Python, Rust, and JavaScript
cd my-monorepo
depswiz check
```

You can also filter by language:

```bash
# Only check Python dependencies
depswiz check -l python

# Check Python and Rust
depswiz check -l python -l rust
```

## Workspaces and Monorepos

For monorepo projects, use the `--workspace` flag:

```bash
depswiz check --workspace
```

This scans all workspace members and provides aggregated results.

## Output Formats

depswiz supports multiple output formats:

```bash
# Terminal output (default)
depswiz check

# JSON for CI/CD
depswiz check --format json

# Markdown for reports
depswiz check --format markdown

# HTML report
depswiz check --format html > report.html
```

## AI-Powered Suggestions

If you have [Claude Code](https://claude.ai/code) installed, get intelligent upgrade recommendations:

```bash
# Full upgrade strategy
depswiz suggest

# Focus on security
depswiz suggest --focus security

# Quick health check
depswiz suggest --focus quick
```

## Common Workflows

### Pre-commit Security Check

```bash
# Fail if high severity vulnerabilities exist
depswiz audit --fail-on high
```

### CI/CD Integration

```bash
# Check for outdated packages and fail if any found
depswiz check --fail-outdated --format json
```

### Generate SBOM

```bash
# CycloneDX format
depswiz sbom -o sbom.json

# SPDX format
depswiz sbom --format spdx -o sbom.spdx.json
```

## Next Steps

- [Commands Reference](../commands/index.md) - Detailed command documentation
- [Configuration](../configuration.md) - Customize behavior with depswiz.toml
- [CI/CD Integration](../ci-cd.md) - Set up automated checks
