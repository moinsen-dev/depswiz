# Changelog

All notable changes to depswiz are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Pages documentation site
- Comprehensive command reference documentation
- Language-specific guides for Python, Rust, Dart, and JavaScript

## [0.2.0] - 2024-12-27

### Added
- **Development Tools Checking** (`depswiz tools`)
  - Support for 15 development tools: Node.js, npm, pnpm, Yarn, Bun, Deno, Python, uv, pip, Rust, Cargo, Dart, Flutter, Go, Docker
  - Auto-detection of relevant tools based on project files
  - Platform-specific update instructions (macOS, Linux, Windows)
  - `--upgrade` option for Claude Code assisted updates
- **AI-Powered Suggestions** (`depswiz suggest`)
  - Claude Code integration for intelligent upgrade recommendations
  - Focus modes: upgrade, security, quick, toolchain
  - Detailed analysis with priority ordering and risk assessment
- Enhanced `depswiz update` with `--ai-suggest` option

### Changed
- Improved version fetching for Yarn Berry and Bun
- Better handling of pip version format (2 and 3-part versions)
- Official API integration for Dart and Flutter version checking

### Fixed
- Yarn Berry tag parsing for `@yarnpkg/cli/X.Y.Z` format
- Bun tag parsing for `bun-vX.Y.Z` format
- pip version regex now handles versions like `24.0`

## [0.1.0] - 2024-12-01

### Added
- Initial release
- **Multi-language dependency checking** (`depswiz check`)
  - Python (pyproject.toml, requirements.txt)
  - Rust (Cargo.toml)
  - Dart/Flutter (pubspec.yaml)
  - JavaScript/TypeScript (package.json)
- **Vulnerability scanning** (`depswiz audit`)
  - OSV integration
  - GitHub Advisory Database
  - RustSec for Rust packages
  - Severity filtering and fail-on thresholds
- **License compliance** (`depswiz licenses`)
  - SPDX-based license detection
  - Allow/deny list support
  - Copyleft warnings
- **SBOM generation** (`depswiz sbom`)
  - CycloneDX 1.6 format
  - SPDX 3.0 format
  - Transitive dependency support
- **Interactive update** (`depswiz update`)
  - Dry-run mode
  - Update strategies (patch, minor, major, security)
  - Auto-confirm option
- **Plugin architecture**
  - Python entry points for language plugins
  - Extensible design
- **Multiple output formats**
  - CLI (Rich tables)
  - JSON
  - Markdown
  - HTML
- **Configuration**
  - depswiz.toml support
  - pyproject.toml [tool.depswiz] section
- **Workspace/monorepo support**
  - Auto-detect workspaces per ecosystem
  - Aggregated reporting

[Unreleased]: https://github.com/moinsen-dev/depswiz/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/moinsen-dev/depswiz/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/moinsen-dev/depswiz/releases/tag/v0.1.0
