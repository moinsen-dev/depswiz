# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2025-12-28

### Added

- **Go Language Support**
  - New Go/Golang plugin for go.mod and go.sum parsing
  - Go Module Proxy integration for version checking
  - Workspace support via go.work files
  - Vulnerability scanning via OSV and GHSA (Go ecosystem)

- **SARIF Output Format**
  - New `--sarif` output flag for all check, audit, and licenses commands
  - SARIF 2.1.0 compliant output for GitHub Code Scanning integration
  - VS Code SARIF Viewer support
  - Includes vulnerability severity mapping, CWE references, and fix suggestions

- **NVD Vulnerability Source**
  - National Vulnerability Database (NVD) integration
  - CVSS 3.1/3.0/2.0 score support
  - Optional API key for higher rate limits (NVD_API_KEY env var)
  - Configure via `sources = ["osv", "ghsa", "rustsec", "nvd"]` in config

- **Competitor Comparison Document**
  - New COMPARISON.md with comprehensive feature matrix
  - Comparison with 14 tools: Dependabot, Renovate, Snyk, Trivy, Grype, and more

### Changed

- Updated language support to 6 ecosystems (added Go)
- Expanded vulnerability sources to 4 (added NVD)
- Expanded output formats to 7 (added SARIF)

## [0.4.1] - 2025-12-28

### Added

- **Comprehensive Scan Mode**
  - Run `depswiz` with no arguments to check everything at once
  - Combines dependency check, vulnerability audit, and license compliance
  - Unified output with summary counts and top issues

- **Docker Plugin**
  - Scan Dockerfiles for outdated base images
  - Docker Compose support for multi-container projects
  - Registry integration for version checking

- **Smart CI Detection**
  - Auto-detects 13 CI platforms (GitHub Actions, GitLab CI, CircleCI, etc.)
  - Automatically enables `--strict` mode in CI environments
  - Auto-defaults to JSON output when no format specified in CI

### Changed

- **Recursive Scanning by Default**
  - All commands now recursively scan subdirectories by default
  - Use `--shallow` flag to scan only the current directory

- **Simplified Output Flags**
  - New: `--json`, `--md`, `--html` (replaces `--format <type>`)
  - More intuitive and faster to type

- **Unified Strict Mode**
  - New: `--strict` flag across all commands (replaces `--fail-outdated`, `--fail-on`)
  - For audit: `--strict [LEVEL]` where LEVEL is critical/high/medium/low
  - Consistent exit code behavior across all commands

- **Unified Language Filtering**
  - New: `--only python,rust,docker` (replaces `-l python -l rust`)
  - Comma-separated list for multiple languages
  - Now supports `docker` as a language filter

### Deprecated

- `--format` option (use `--json`, `--md`, `--html` instead)
- `--fail-outdated` option (use `--strict` instead)
- `--fail-on` option (use `--strict [LEVEL]` instead)
- `-l`/`--language` option (use `--only` instead)
- `--recursive` option (now default, use `--shallow` to disable)

## [0.4.0] - 2025-12-27

### Added

- **Interactive Guide** (`depswiz guide`)
  - Full TUI dashboard powered by Textual with real-time health score monitoring
  - Three interaction modes: dashboard (default), wizard, and chat
  - AI-powered suggestions via Claude Code integration
  - Keyboard navigation: `a`=Audit, `u`=Updates, `l`=Licenses, `t`=Tools, `c`=Chat, `s`=AI, `q`=Quit
  - Drill-down screens for detailed vulnerability, update, and license information
  - Health score algorithm (0-100) based on vulnerabilities, outdated deps, and license issues

- **Deprecation Detection** (`depswiz deprecations`)
  - Flutter/Dart deprecation scanning via `dart analyze`
  - Auto-fix support using `dart fix --apply`
  - AI-powered fixing via `--ai-fix` using Claude Code for complex migrations
  - Multiple output formats: CLI, JSON, Markdown, HTML
  - Filtering options: `--fixable-only`, `--package`, `--status`
  - CI integration with `--fail-on deprecated|removal|breaking`
  - Intelligent replacement and package extraction from deprecation messages

- **Guide Module Components**
  - `GuideState` - Reactive state management with subscriptions
  - `ContextManager` - Project context for AI features
  - `WizardEngine` - State machine for guided workflows
  - Custom Textual widgets: HealthScoreWidget, VulnerabilityPanel, UpdatesPanel, LicensePanel, ToolsPanel
  - Six detail screens: AIScreen, AuditScreen, ChatScreen, LicensesScreen, ToolsScreen, UpdatesScreen

### Changed

- Removed placeholder code and "Coming Soon" stubs
- Upgraded Textual integration for smoother TUI experience

### Dependencies

- Added `textual>=0.89.0` (TUI framework)
- Added `inquirerpy>=0.3.4` (interactive prompts)

## [0.3.0] - 2025-12-27

### Added

- **Expanded Test Coverage**
  - Comprehensive CLI command tests for check, audit, and tools commands
  - Unit tests for configuration system, caching, plugin registry, and version utilities
  - 305 passing tests with 48% overall code coverage
  - Key modules now have high coverage: version.py (100%), cache.py (100%), config.py (93%)

- **GHSA Vulnerability Source**
  - GitHub Security Advisories integration for vulnerability scanning
  - GraphQL API support with optional GitHub token for higher rate limits

- **RustSec Vulnerability Source**
  - RustSec Advisory Database integration for Rust packages
  - Local advisory database support

- **Logging Infrastructure**
  - Rich-formatted logging with configurable levels
  - Logging module with Rich handler integration
  - `--verbose` / `-v` global flag for increased output
  - `--quiet` / `-q` global flag for minimal output
  - `--version` / `-V` flag to display version

- **Dogfooding Test Script**
  - Self-testing script at `scripts/dogfood.py`
  - Tests all CLI commands against the project itself
  - Quick mode (`--quick`) skips slow operations

### Fixed

- **CLI Argument Ordering**
  - Fixed Typer argument parsing with `invoke_without_command=True`
  - All CLI options must now precede positional path arguments

- **Vulnerability Constructor**
  - Fixed missing `affected_versions` parameter in test fixtures

- **Version Parsing**
  - Corrected ToolVersion.parse() method usage in tests

### Changed

- Improved error handling across plugin implementations
- Enhanced test fixtures for security vulnerability scanning

## [0.2.0] - 2024-12-27

### Added

- **Development Tools Checking** (`depswiz tools`)
  - Check if development tools (Node.js, Python, Rust, Dart, Flutter, uv, Go, Docker, etc.) are up to date
  - Auto-detection based on project files
  - Platform-specific update instructions (macOS, Linux, Windows)
  - JSON output for CI/CD integration
  - `--upgrade` flag for AI-powered upgrades via Claude Code

- **AI-Powered Suggestions** (`depswiz suggest`)
  - Claude Code integration for intelligent upgrade strategies
  - Multiple focus modes: upgrade, security, breaking, quick, toolchain
  - Analyzes dependencies and development environment together

- **15 Supported Development Tools**
  - Node.js, npm, pnpm, Yarn, Bun, Deno
  - Python, uv, pip
  - Rust, Cargo
  - Dart, Flutter
  - Go, Docker

### Changed

- Improved version detection for tools with non-standard tag formats (Yarn Berry, Bun)
- Added official API support for Dart and Flutter version checking

## [0.1.0] - 2024-12-27

### Added

- Initial release
- **Multi-Language Dependency Checking** (`depswiz check`)
  - Python (pyproject.toml, requirements.txt)
  - Rust (Cargo.toml)
  - Dart/Flutter (pubspec.yaml)
  - JavaScript/TypeScript (package.json)

- **Vulnerability Scanning** (`depswiz audit`)
  - OSV database integration
  - Severity filtering
  - CI/CD exit codes

- **License Compliance** (`depswiz licenses`)
  - SPDX license detection
  - Allow/deny list policies
  - Copyleft warnings

- **SBOM Generation** (`depswiz sbom`)
  - CycloneDX 1.6 format
  - SPDX 3.0 format

- **Interactive Updates** (`depswiz update`)
  - Dry-run mode
  - Strategy selection (all, security, patch, minor, major)
  - Auto-confirm option

- **Plugin Architecture**
  - Entry points for language plugins
  - Extensible design

- **Multiple Output Formats**
  - CLI (Rich tables and colors)
  - JSON
  - Markdown
  - HTML

[Unreleased]: https://github.com/moinsen-dev/depswiz/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/moinsen-dev/depswiz/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/moinsen-dev/depswiz/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/moinsen-dev/depswiz/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/moinsen-dev/depswiz/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/moinsen-dev/depswiz/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/moinsen-dev/depswiz/releases/tag/v0.1.0
