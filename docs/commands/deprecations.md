# deprecations

Detect and fix deprecated API usage in Flutter/Dart projects.

## Overview

The `depswiz deprecations` command scans Flutter/Dart codebases for deprecated API usage and can automatically fix many issues using `dart fix`.

## Usage

```bash
depswiz deprecations [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project path to analyze | Current directory |

## Options

### Filtering

| Option | Description |
|--------|-------------|
| `--fixable-only` | Show only auto-fixable deprecations |
| `--package`, `-p` | Filter by source package (e.g., `flutter`) |
| `--status`, `-s` | Filter by status: `all`, `deprecated`, `removal`, `breaking` |
| `--include-internal` / `--no-internal` | Include deprecations from same package |

### Output

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--md` | Output as Markdown |
| `--html` | Output as HTML |
| `-o`, `--output` | Write output to file |

### Actions

| Option | Description |
|--------|-------------|
| `--fix` | Apply auto-fixes using `dart fix` |
| `--dry-run` | Preview fixes without applying |
| `--ai-fix` | Use Claude Code for intelligent deprecation fixing |

### CI Integration

| Option | Description |
|--------|-------------|
| `--fail-on` | Exit 1 if found: `deprecated`, `removal`, `breaking` |

## How It Works

1. **Detection**: Runs `dart analyze --format=machine` to find deprecation warnings
2. **Parsing**: Extracts rule ID, message, file location, and severity
3. **Enrichment**: Identifies replacement suggestions and source packages
4. **Fix Check**: Runs `dart fix --dry-run` to determine which issues are auto-fixable
5. **Reporting**: Outputs results in the specified format

## Deprecation Status Levels

| Status | Description |
|--------|-------------|
| `deprecated` | Marked `@Deprecated`, still works |
| `removal` | Has scheduled removal version |
| `breaking` | Will break in next major version |

## Examples

### Basic Scan

```bash
# Scan current directory
depswiz deprecations

# Scan specific project
depswiz deprecations /path/to/flutter/project
```

### Filtering

```bash
# Show only fixable issues
depswiz deprecations --fixable-only

# Filter by package
depswiz deprecations --package flutter

# Exclude internal deprecations
depswiz deprecations --no-internal
```

### Auto-Fix with dart fix

```bash
# Preview what would be fixed
depswiz deprecations --fix --dry-run

# Apply fixes
depswiz deprecations --fix
```

### AI-Powered Fixing with Claude Code

For deprecations that `dart fix` cannot handle automatically, use Claude Code for intelligent analysis and fixing:

```bash
# Let Claude Code analyze and fix deprecations
depswiz deprecations --ai-fix

# Fix only issues from a specific package
depswiz deprecations --package flutter --ai-fix

# Focus on breaking changes only
depswiz deprecations --status breaking --ai-fix
```

Claude Code provides:

- **Context-aware fixes**: Understands surrounding code for accurate replacements
- **Complex migrations**: Handles multi-step API changes that require code restructuring
- **Behavioral preservation**: Ensures fixes maintain original functionality
- **Validation**: Runs `dart analyze` after fixes to verify correctness

### Output Formats

```bash
# JSON output
depswiz deprecations --json

# Save to file
depswiz deprecations --md -o report.md

# HTML report
depswiz deprecations --html -o report.html
```

### CI/CD Integration

```bash
# Fail on any deprecation
depswiz deprecations --fail-on deprecated

# Fail only on breaking changes
depswiz deprecations --fail-on breaking
```

## Output Examples

### CLI Output

```
╭──────────────────────────────────────────────────────────────╮
│  depswiz deprecations - my_app                               │
╰──────────────────────────────────────────────────────────────╯

  Summary
  ├─ Total deprecations: 23
  ├─ Auto-fixable: 18 (78%)
  └─ By status:
     ├─ deprecated: 15
     ├─ removal_planned: 6
     └─ breaking_soon: 2

  By Package
  ├─ flutter: 12
  ├─ http: 5
  ├─ provider: 4
  └─ my_app (internal): 2

  Top Issues
  ┌─────────────────────────────────────────────────────────────┐
  │ [!] FlatButton → TextButton (12 occurrences)               │
  │     lib/widgets/button.dart:45, lib/screens/home.dart:23   │
  │     ✓ Auto-fixable with: dart fix --apply                  │
  └─────────────────────────────────────────────────────────────┘

  Quick Fix: depswiz deprecations --fix .
```

### JSON Output

```json
{
  "version": "0.5.0",
  "command": "deprecations",
  "timestamp": "2025-12-27T22:30:00Z",
  "project": {
    "path": "/path/to/my_app",
    "dart_version": "3.2.0",
    "flutter_version": "3.16.0"
  },
  "summary": {
    "total": 23,
    "fixable": 18,
    "by_status": {
      "deprecated": 15,
      "removal_planned": 6,
      "breaking_soon": 2
    }
  },
  "deprecations": [
    {
      "rule_id": "deprecated_member_use",
      "message": "FlatButton is deprecated, use TextButton instead",
      "file": "lib/widgets/button.dart",
      "line": 45,
      "column": 12,
      "package": "flutter",
      "replacement": "TextButton",
      "fix_available": true,
      "status": "deprecated"
    }
  ]
}
```

## Detected Rules

| Rule ID | Description |
|---------|-------------|
| `deprecated_member_use` | Using a deprecated API from an external package |
| `deprecated_member_use_from_same_package` | Using a deprecated API from the same package |

## Common Deprecations

### Flutter Widget Migrations

| Deprecated | Replacement |
|------------|-------------|
| `FlatButton` | `TextButton` |
| `RaisedButton` | `ElevatedButton` |
| `OutlineButton` | `OutlinedButton` |
| `MaterialState` | `WidgetState` |

### Dart SDK Changes

| Deprecated | Replacement |
|------------|-------------|
| `List.filled(n, null)` | Type-specific constructors |
| Legacy null-safety patterns | Sound null safety |

## Configuration

Configure deprecation scanning in `depswiz.toml`:

```toml
[deprecations]
# Detection settings
include_internal = true
min_status = "deprecated"

# CI settings
fail_on = "breaking"

# Ignore patterns
ignore_rules = [
    "deprecated_member_use_from_same_package"
]
ignore_packages = [
    "legacy_package"
]
```

## Requirements

- **Dart SDK**: Must be installed and in PATH
- **Flutter SDK**: Required for Flutter projects
- **Analysis Options**: Project should have valid `analysis_options.yaml`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or no deprecations when using `--fail-on`) |
| 1 | Deprecations found matching `--fail-on` criteria |

## Future Roadmap

Support for additional languages is planned:

| Language | Detection Method | Fix Tool |
|----------|------------------|----------|
| Python | `pyupgrade`, deprecation warnings | `pyupgrade --apply` |
| JavaScript | ESLint deprecation rules | ESLint `--fix` |
| Rust | `cargo clippy` | `cargo fix` |

## See Also

- [check](check.md) - Check for outdated dependencies
- [audit](audit.md) - Vulnerability scanning
- [guide](guide.md) - Interactive dashboard
