# depswiz audit

Scan dependencies for known security vulnerabilities using multiple advisory databases.

## Usage

```bash
depswiz audit [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project directory to audit | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `-l`, `--language` | Filter by language |
| `--severity` | Minimum severity to show: low, medium, high, critical |
| `--fail-on` | Exit with code 1 if severity >= threshold |
| `--ignore` | Ignore specific CVE (can be used multiple times) |
| `-f`, `--format` | Output format: cli, json, markdown, html |

## Examples

### Basic Audit

```bash
# Audit current directory
depswiz audit

# Audit specific project
depswiz audit /path/to/project
```

### Filter by Severity

```bash
# Only show high and critical
depswiz audit --severity high

# Only show critical vulnerabilities
depswiz audit --severity critical
```

### CI/CD Integration

```bash
# Fail on high or critical vulnerabilities
depswiz audit --fail-on high

# Fail only on critical
depswiz audit --fail-on critical

# JSON output for further processing
depswiz audit --format json
```

### Ignore Known Issues

```bash
# Ignore specific CVEs (e.g., false positives or accepted risks)
depswiz audit --ignore CVE-2024-12345

# Ignore multiple CVEs
depswiz audit --ignore CVE-2024-12345 --ignore CVE-2024-67890
```

## Vulnerability Sources

depswiz queries multiple vulnerability databases:

| Source | Coverage | Description |
|--------|----------|-------------|
| [OSV](https://osv.dev/) | All ecosystems | Open Source Vulnerabilities database |
| [GitHub Advisory Database](https://github.com/advisories) | All ecosystems | GitHub Security Advisories |
| [RustSec](https://rustsec.org/) | Rust | Rust security advisories |

## Output

### CLI Format (Default)

```
depswiz v0.2.0 - Security Audit

Scanning dependencies...

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package     ┃ CVE               ┃ Severity  ┃ Description                      ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ requests    │ CVE-2024-35195    │ HIGH      │ SSRF via crafted URL             │
│ urllib3     │ CVE-2024-37891    │ MEDIUM    │ Cookie injection vulnerability   │
└─────────────┴───────────────────┴───────────┴──────────────────────────────────┘

Found 2 vulnerabilities (1 high, 1 medium)
```

### JSON Format

```json
{
  "vulnerabilities": [
    {
      "package": "requests",
      "version": "2.31.0",
      "cve": "CVE-2024-35195",
      "severity": "high",
      "description": "SSRF via crafted URL",
      "fixed_version": "2.32.0",
      "references": ["https://nvd.nist.gov/vuln/detail/CVE-2024-35195"]
    }
  ],
  "summary": {
    "total": 2,
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0
  }
}
```

## Severity Levels

| Level | Description |
|-------|-------------|
| `critical` | Immediate action required, severe impact |
| `high` | Significant risk, should be addressed soon |
| `medium` | Moderate risk, plan for remediation |
| `low` | Minor risk, fix when convenient |

## Configuration

Configure audit behavior in `depswiz.toml`:

```toml
[audit]
severity_threshold = "low"
fail_on = "high"
sources = ["osv", "ghsa", "rustsec"]

# Permanently ignore specific CVEs
ignore = [
    "CVE-2024-12345",  # Accepted risk - documented in security review
]
```

## See Also

- [depswiz check](check.md) - Check for updates
- [depswiz licenses](licenses.md) - License compliance
- [depswiz suggest](suggest.md) - AI security recommendations
