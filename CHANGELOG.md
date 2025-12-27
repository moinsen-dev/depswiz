# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/moinsen-dev/depswiz/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/moinsen-dev/depswiz/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/moinsen-dev/depswiz/releases/tag/v0.1.0
