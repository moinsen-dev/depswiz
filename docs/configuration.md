# Configuration

depswiz can be configured using a `depswiz.toml` file in your project root, or via `[tool.depswiz]` in your `pyproject.toml`.

## Configuration File

Create a `depswiz.toml` in your project root:

```toml
[depswiz]
default_format = "cli"

[languages]
enabled = ["python", "rust", "dart", "javascript"]

[check]
recursive = false
workspace = true
strategy = "all"
warn_breaking = true

[audit]
severity_threshold = "low"
fail_on = "high"
sources = ["osv"]

[licenses]
policy_mode = "allow"
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]
denied = ["GPL-3.0", "AGPL-3.0"]
warn_copyleft = true

[sbom]
format = "cyclonedx"
include_transitive = true

[claude]
enabled = true
timeout_seconds = 300
```

## Using pyproject.toml

Alternatively, add configuration to your `pyproject.toml`:

```toml
[tool.depswiz]
default_format = "cli"

[tool.depswiz.check]
recursive = false
workspace = true

[tool.depswiz.audit]
fail_on = "high"

[tool.depswiz.licenses]
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause"]
```

## Configuration Sections

### [depswiz]

Global settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_format` | string | `"cli"` | Default output format: cli, json, markdown, html |

### [languages]

Language plugin settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | list | all | Languages to enable |

Example:

```toml
[languages]
# Only check Python and Rust projects
enabled = ["python", "rust"]
```

### [check]

Settings for `depswiz check` command.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `recursive` | bool | `false` | Recursively check subdirectories |
| `workspace` | bool | `true` | Check workspace members |
| `strategy` | string | `"all"` | Update strategy: all, security, patch, minor, major |
| `warn_breaking` | bool | `true` | Warn about potential breaking changes |

### [audit]

Settings for `depswiz audit` command.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `severity_threshold` | string | `"low"` | Minimum severity to display |
| `fail_on` | string | `null` | Fail if severity >= threshold |
| `sources` | list | `["osv"]` | Vulnerability sources: osv, ghsa, rustsec |
| `ignore` | list | `[]` | CVEs to ignore |

Example:

```toml
[audit]
severity_threshold = "medium"
fail_on = "high"
sources = ["osv", "ghsa"]

# Ignore accepted risks (document reason in comments)
ignore = [
    "CVE-2024-12345",  # False positive - not applicable to our usage
]
```

### [licenses]

Settings for `depswiz licenses` command.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `policy_mode` | string | `"allow"` | Policy mode: allow or deny |
| `allowed` | list | `[]` | Allowed licenses (when policy_mode = "allow") |
| `denied` | list | `[]` | Denied licenses (when policy_mode = "deny") |
| `warn_copyleft` | bool | `true` | Warn about copyleft licenses |
| `fail_on_unknown` | bool | `false` | Fail on unknown licenses |

Example - Allowlist mode:

```toml
[licenses]
policy_mode = "allow"
allowed = [
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "CC0-1.0",
    "Unlicense",
]
```

Example - Denylist mode:

```toml
[licenses]
policy_mode = "deny"
denied = [
    "GPL-2.0",
    "GPL-3.0",
    "AGPL-3.0",
    "LGPL-2.1",
    "LGPL-3.0",
]
warn_copyleft = true
```

### [sbom]

Settings for `depswiz sbom` command.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `format` | string | `"cyclonedx"` | SBOM format: cyclonedx, spdx |
| `include_transitive` | bool | `true` | Include transitive dependencies |
| `output_dir` | string | `"."` | Default output directory |

### [claude]

Settings for Claude Code integration.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable Claude Code integration |
| `timeout_seconds` | int | `300` | Timeout for Claude responses |

## Environment Variables

Some settings can be overridden with environment variables:

| Variable | Description |
|----------|-------------|
| `DEPSWIZ_CONFIG` | Path to config file |
| `DEPSWIZ_FORMAT` | Default output format |
| `DEPSWIZ_NO_COLOR` | Disable colored output |

## Configuration Precedence

Settings are applied in this order (later overrides earlier):

1. Built-in defaults
2. `depswiz.toml` in project root
3. `pyproject.toml` `[tool.depswiz]` section
4. Environment variables
5. Command-line arguments

## Example Configurations

### Strict Enterprise

```toml
[depswiz]
default_format = "json"

[audit]
fail_on = "medium"
sources = ["osv", "ghsa"]

[licenses]
policy_mode = "allow"
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause"]
fail_on_unknown = true

[sbom]
format = "cyclonedx"
include_transitive = true
```

### Open Source Project

```toml
[depswiz]
default_format = "cli"

[check]
workspace = true

[audit]
severity_threshold = "low"

[licenses]
warn_copyleft = false  # Copyleft is fine for OSS
```

### Monorepo

```toml
[depswiz]
default_format = "cli"

[check]
workspace = true
recursive = true

[languages]
enabled = ["python", "rust", "javascript"]
```

## Validation

depswiz validates configuration on startup. Invalid options will produce warnings:

```
Warning: Unknown config option 'audit.unknown_option'
Warning: Invalid severity 'very_high', using 'high'
```

## See Also

- [Commands Reference](commands/index.md)
- [CI/CD Integration](ci-cd.md)
