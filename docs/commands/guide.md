# guide

Interactive dependency management dashboard with real-time health monitoring.

## Overview

The `depswiz guide` command provides three interaction paradigms:

1. **Dashboard Mode** (default): Full TUI with real-time panels
2. **Wizard Mode**: Step-by-step guided experience
3. **Chat Mode**: Conversational interface with AI

## Usage

```bash
depswiz guide [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project path to analyze | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `--mode` | Interaction mode: `dashboard`, `wizard`, or `chat` |
| `--watch` | Auto-refresh on file changes |
| `--skip-ai` | Disable AI features |
| `--theme` | Color theme: `dark` or `light` |
| `--focus` | Focus area: `security`, `updates`, or `licenses` |

## Dashboard Mode

The default mode displays a real-time TUI dashboard:

```
┌──────────────────────────────────────────────────────────────┐
│  depswiz guide - /path/to/project                    [?] Help │
├──────────────────────────────────────────────────────────────┤
│  HEALTH      │  VULNERABILITIES      │  OUTDATED DEPS        │
│    [87]      │   0 Critical          │   3 Major             │
│   /100       │   2 High              │   5 Minor             │
│   Good       │   1 Medium            │   8 Patch             │
├──────────────┼───────────────────────┴───────────────────────┤
│  LICENSES    │  DEV TOOLS                                    │
│  98% OK      │  Python 3.13.1 ✓  Node 22.0 ✓  uv 0.4.15 ↑   │
├──────────────┴───────────────────────────────────────────────┤
│ [a]Audit [u]Update [l]Licenses [t]Tools [c]Chat [s]AI [q]Quit│
└──────────────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `a` | Show detailed audit/vulnerability screen |
| `u` | Show outdated packages with update options |
| `l` | Show license compliance details |
| `t` | Show development tools status |
| `c` | Open chat interface |
| `s` | Get AI-powered suggestions |
| `r` | Refresh all data |
| `?` | Show help |
| `q` | Quit |

### Health Score Algorithm

The health score (0-100) is calculated based on:

```python
score = 100

# Vulnerabilities (major impact)
score -= critical_vulns * 25
score -= high_vulns * 15
score -= medium_vulns * 5
score -= low_vulns * 1

# Outdated packages (moderate impact)
score -= major_updates * 3
score -= minor_updates * 1

# License violations (moderate impact)
score -= violations * 10
score -= warnings * 2
```

**Score Ranges:**
- 90-100: Excellent
- 80-89: Good
- 60-79: Fair
- 0-59: Poor

## Wizard Mode

Step-by-step guided experience with smart recommendations:

```bash
depswiz guide --mode wizard
```

The wizard walks you through:

1. **Project Scan**: Analyze dependencies, vulnerabilities, licenses
2. **Priority Actions**: Security fixes, critical updates
3. **Decision Tree**: Choose what to address
4. **Execution**: Apply fixes with confirmation
5. **Report**: Summary of changes made

## Chat Mode

Conversational interface powered by Claude Code:

```bash
depswiz guide --mode chat
```

**Example Interactions:**

```
You: What vulnerabilities do I have?
depswiz: Found 3 vulnerabilities:
  - requests 2.31.0: CVE-2024-35195 (CRITICAL) - SSRF bypass
    Fixed in: 2.32.0
  Would you like me to fix the critical ones?

You: Yes, fix them
depswiz: Updating requests to 2.32.0... Done!
```

**Note:** Requires [Claude Code CLI](https://claude.ai/code) to be installed for full functionality. Falls back to rule-based responses when Claude is unavailable.

## Examples

### Basic Dashboard

```bash
# Launch dashboard for current directory
depswiz guide

# Launch for specific project
depswiz guide /path/to/project
```

### Watch Mode

```bash
# Auto-refresh when files change
depswiz guide --watch
```

### Focused Analysis

```bash
# Focus on security issues
depswiz guide --focus security

# Focus on outdated packages
depswiz guide --focus updates
```

### Without AI

```bash
# Disable AI features for faster startup
depswiz guide --skip-ai
```

## Detail Screens

### Audit Screen (`a`)

Shows detailed vulnerability information:
- CVE identifiers and descriptions
- Affected versions and fix versions
- Severity breakdown with color coding
- Links to security advisories

### Updates Screen (`u`)

Shows outdated packages grouped by update type:
- **Major**: Breaking changes likely
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes only

### Licenses Screen (`l`)

Shows license compliance:
- License distribution chart
- Policy violations (denied licenses)
- Warnings (copyleft, unknown licenses)
- Package-by-license breakdown

### Tools Screen (`t`)

Shows development tool versions:
- Current vs latest versions
- Update availability indicators
- Platform-specific upgrade instructions

## Configuration

Configure guide behavior in `depswiz.toml`:

```toml
[guide]
default_mode = "dashboard"
watch = false
skip_ai = false
theme = "dark"
```

## Requirements

- **TUI Mode**: Terminal with 256-color support recommended
- **AI Features**: Claude Code CLI for chat and suggestions
- **Watch Mode**: File system notification support

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Normal exit |
| 1 | Error during analysis |

## See Also

- [check](check.md) - Check for outdated dependencies
- [audit](audit.md) - Vulnerability scanning
- [suggest](suggest.md) - AI-powered suggestions
