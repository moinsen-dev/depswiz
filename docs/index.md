# depswiz

**Dependency Wizard** - One command to check everything. Multi-language dependency management for modern development workflows.

<div class="grid cards" markdown>

-   :material-rocket-launch: **Zero Configuration**

    ---

    Just run `depswiz` - that's it. One command checks dependencies, vulnerabilities, and licenses across your entire project.

-   :material-language-python: **Multi-Language**

    ---

    Check dependencies across Python, Rust, Dart/Flutter, JavaScript/TypeScript, Go, and Docker ecosystems

-   :material-shield-check: **Security First**

    ---

    Scan for vulnerabilities using OSV, GitHub Advisories, RustSec, and NVD databases

-   :material-docker: **Docker Support**

    ---

    Scan Dockerfiles and docker-compose.yml for outdated base images

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

-   :material-cog-sync: **Zero-Config CI/CD**

    ---

    Auto-detects CI environments and enables strict mode. Works out of the box with GitHub Actions, GitLab CI, and more.

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
# Check everything at once (dependencies + vulnerabilities + licenses)
depswiz

# Or use individual commands
depswiz check       # Check for outdated dependencies
depswiz audit       # Scan for security vulnerabilities
depswiz licenses    # Check license compliance
depswiz tools       # Check development tools
depswiz suggest     # Get AI-powered suggestions (requires Claude Code)
depswiz guide       # Launch interactive dashboard
depswiz deprecations  # Scan for deprecated APIs (Flutter/Dart)
```

## CI/CD Integration

depswiz automatically detects CI environments and adjusts its behavior:

```yaml
# GitHub Actions - just one line!
- run: depswiz  # Strict mode auto-enabled in CI
```

**Auto-detected platforms:** GitHub Actions, GitLab CI, CircleCI, Travis CI, Jenkins, Azure Pipelines, and more.

## Features

### Multi-Language Dependency Management

depswiz understands the package ecosystems of multiple languages:

| Language | Manifest Files | Lockfiles | Registry |
|----------|---------------|-----------|----------|
| Python | `pyproject.toml`, `requirements.txt` | `uv.lock`, `poetry.lock` | PyPI |
| Rust | `Cargo.toml` | `Cargo.lock` | crates.io |
| Dart/Flutter | `pubspec.yaml` | `pubspec.lock` | pub.dev |
| JavaScript/TypeScript | `package.json` | `package-lock.json`, `yarn.lock` | npm |
| Go | `go.mod` | `go.sum` | Go Module Proxy |
| Docker | `Dockerfile`, `docker-compose.yml` | - | Docker Hub |

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
- **Zero configuration**: Recursive scanning, strict mode in CI - all automatic
- **Security focused**: Vulnerability scanning is built-in, not an afterthought
- **Modern CLI**: Beautiful output with Rich, intuitive commands with Typer
- **Extensible**: Plugin architecture allows adding new language support
- **AI-ready**: Optional Claude Code integration for smart upgrade decisions
