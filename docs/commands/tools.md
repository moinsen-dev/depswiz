# depswiz tools

Check development tools for available updates. Supports 15 common development tools.

## Usage

```bash
depswiz tools [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project directory (for auto-detection) | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `-t`, `--tool` | Check specific tool (can be used multiple times) |
| `--all` | Check all 15 supported tools |
| `--updates-only` | Only show tools with available updates |
| `--list` | List all supported tools |
| `--upgrade` | Use Claude Code to perform intelligent upgrades |
| `--timeout` | Timeout in seconds (default: 300) |
| `--json` | Output as JSON |

## Supported Tools

| Category | Tools |
|----------|-------|
| **JavaScript** | Node.js, npm, pnpm, Yarn, Bun, Deno |
| **Python** | Python, uv, pip |
| **Rust** | Rust, Cargo |
| **Dart/Flutter** | Dart, Flutter |
| **Other** | Go, Docker |

## Examples

### Auto-Detect Project Tools

```bash
# Detect and check relevant tools based on project files
depswiz tools
```

This automatically detects:
- `package.json` → Node.js, npm
- `pyproject.toml` → Python, uv
- `Cargo.toml` → Rust, Cargo
- `pubspec.yaml` → Dart, Flutter

### Check All Tools

```bash
# Check all 15 supported tools
depswiz tools --all
```

### Check Specific Tools

```bash
# Check only Node and Python
depswiz tools -t node -t python

# Check Rust toolchain
depswiz tools -t rust -t cargo
```

### Show Only Updates

```bash
# Only display tools that have updates available
depswiz tools --updates-only
```

### List Supported Tools

```bash
# Show all supported tools and their detection criteria
depswiz tools --list
```

### Upgrade Tools with Claude Code

```bash
# Use Claude Code to perform intelligent upgrades
depswiz tools --upgrade
```

This invokes Claude Code to:
1. Analyze which tools need updating
2. Determine the safest upgrade path
3. Execute platform-specific upgrade commands

### CI/CD Integration

```bash
# JSON output for parsing
depswiz tools --json

# Check for updates in CI
depswiz tools --updates-only --json
```

## Output

### CLI Format (Default)

```
depswiz v0.5.0 - Development Tools Check

Platform: macos

┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Tool      ┃ Installed  ┃ Latest     ┃ Status            ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Node.js   │ 20.10.0    │ 22.12.0    │ update available  │
│ Python    │ 3.13.1     │ 3.13.1     │ ok                │
│ uv        │ 0.5.10     │ 0.5.24     │ update available  │
│ Rust      │ 1.83.0     │ 1.84.0     │ update available  │
│ Docker    │ 27.4.0     │ 27.4.0     │ ok                │
└───────────┴────────────┴────────────┴───────────────────┘

3 update(s) available

Update Instructions:
  Node.js: brew upgrade node
  uv: brew upgrade uv
  Rust: rustup update stable
```

### JSON Format

```json
{
  "platform": "macos",
  "tools": [
    {
      "name": "node",
      "display_name": "Node.js",
      "installed_version": "20.10.0",
      "latest_version": "22.12.0",
      "status": "update_available",
      "update_instruction": "brew upgrade node"
    },
    {
      "name": "python",
      "display_name": "Python",
      "installed_version": "3.13.1",
      "latest_version": "3.13.1",
      "status": "up_to_date"
    }
  ],
  "summary": {
    "total_checked": 5,
    "up_to_date": 2,
    "updates_available": 3,
    "not_installed": 0
  }
}
```

## Update Instructions

depswiz provides platform-specific update instructions:

### macOS

| Tool | Update Command |
|------|----------------|
| Node.js | `brew upgrade node` |
| Python | `brew upgrade python` |
| uv | `brew upgrade uv` |
| Rust | `rustup update stable` |
| Docker | `brew upgrade --cask docker` |

### Linux

| Tool | Update Command |
|------|----------------|
| Node.js | `nvm install node` or package manager |
| Python | Package manager specific |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Rust | `rustup update stable` |

### Windows

| Tool | Update Command |
|------|----------------|
| Node.js | `winget upgrade OpenJS.NodeJS` |
| Python | `winget upgrade Python.Python.3.13` |
| Rust | `rustup update stable` |

## Version Sources

depswiz fetches latest versions from:

| Tool | Source |
|------|--------|
| Node.js | nodejs.org API |
| Python | GitHub Releases |
| uv | GitHub Releases |
| Rust | GitHub Releases |
| Dart | Google Storage API |
| Flutter | Flutter Releases JSON |
| Others | GitHub Releases |

## See Also

- [depswiz suggest](suggest.md) - AI-powered analysis including tools
- [depswiz check](check.md) - Check package dependencies
