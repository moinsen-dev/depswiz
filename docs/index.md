# depswiz

**Dependency Wizard** - A multi-language dependency management CLI tool for modern development workflows.

<div class="grid cards" markdown>

-   :material-language-python: **Multi-Language**

    ---

    Check dependencies across Python, Rust, Dart/Flutter, and JavaScript/TypeScript ecosystems

-   :material-shield-check: **Security First**

    ---

    Scan for vulnerabilities using OSV, GitHub Advisories, and RustSec databases

-   :material-file-document: **SBOM Generation**

    ---

    Generate CycloneDX 1.6 and SPDX 3.0 Software Bills of Materials

-   :material-tools: **Tools Checking**

    ---

    Verify your development tools (Node, Python, Rust, etc.) are up to date

-   :material-monitor-dashboard: **Interactive Guide**

    ---

    TUI dashboard with real-time health monitoring, step-by-step wizard, and AI-powered chat

-   :material-alert-decagram: **Deprecation Detection**

    ---

    Find and auto-fix deprecated APIs in Flutter/Dart projects using `dart analyze` and `dart fix`

</div>

## Quick Install

=== "pip"

    ```bash
    pip install depswiz
    ```

=== "uv"

    ```bash
    uv add depswiz
    ```

=== "From source"

    ```bash
    git clone https://github.com/moinsen-dev/depswiz.git
    cd depswiz
    pip install -e .
    ```

## Quick Start

```bash
# Check for outdated dependencies
depswiz check

# Scan for security vulnerabilities
depswiz audit

# Check development tools
depswiz tools

# Get AI-powered suggestions (requires Claude Code)
depswiz suggest

# Launch interactive dashboard
depswiz guide

# Scan for deprecated APIs (Flutter/Dart)
depswiz deprecations
```

## Features

### Multi-Language Dependency Management

depswiz understands the package ecosystems of multiple languages:

| Language | Manifest Files | Lockfiles | Registry |
|----------|---------------|-----------|----------|
| Python | `pyproject.toml`, `requirements.txt` | `uv.lock`, `poetry.lock` | PyPI |
| Rust | `Cargo.toml` | `Cargo.lock` | crates.io |
| Dart/Flutter | `pubspec.yaml` | `pubspec.lock` | pub.dev |
| JavaScript/TypeScript | `package.json` | `package-lock.json`, `yarn.lock` | npm |

### Development Tools Checking

Keep your development environment up to date with 15 supported tools:

- **JavaScript**: Node.js, npm, pnpm, Yarn, Bun, Deno
- **Python**: Python, uv, pip
- **Rust**: Rust, Cargo
- **Dart/Flutter**: Dart, Flutter
- **Other**: Go, Docker

```bash
depswiz tools --all
```

### AI-Powered Suggestions

When you have [Claude Code](https://claude.ai/code) installed, depswiz can provide intelligent upgrade strategies:

```bash
depswiz suggest --focus security
```

## Why depswiz?

- **One tool for all languages**: No need to remember different commands for each ecosystem
- **Security focused**: Vulnerability scanning is built-in, not an afterthought
- **Modern CLI**: Beautiful output with Rich, intuitive commands with Typer
- **Extensible**: Plugin architecture allows adding new language support
- **AI-ready**: Optional Claude Code integration for smart upgrade decisions
