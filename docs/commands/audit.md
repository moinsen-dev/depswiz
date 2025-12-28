# depswiz audit

Scan dependencies for known security vulnerabilities using multiple advisory databases.

## Usage

```bash
depswiz audit [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--md` | Output as Markdown |
| `--html` | Output as HTML |
| `--sarif` | Output as SARIF 2.1 (GitHub Code Scanning, VS Code) |
| `-o`, `--output FILE` | Write output to file |
| `--strict [LEVEL]` | Exit with code 1 if severity >= LEVEL (default: high) |
| `--only LANGS` | Filter by language(s), comma-separated |
| `--shallow` | Scan current directory only (default: recursive) |
| `--severity LEVEL` | Minimum severity to show: low, medium, high, critical |
| `--ignore CVE` | Ignore specific CVE (can be used multiple times) |
| `-p`, `--path PATH` | Project directory to audit (default: current directory) |

## Examples

### Basic Audit

```bash
# Audit current directory (recursive by default)
depswiz audit

# Audit specific project
depswiz audit -p /path/to/project
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
depswiz audit --strict

# Fail only on critical
depswiz audit --strict critical

# JSON output for parsing
depswiz audit --json

# SARIF output for GitHub Code Scanning
depswiz audit --sarif -o results.sarif
```

In CI environments, `--strict` is automatically enabled.

### Ignore Known Issues

```bash
# Ignore specific CVEs (e.g., false positives or accepted risks)
depswiz audit --ignore CVE-2024-12345

# Ignore multiple CVEs
depswiz audit --ignore CVE-2024-12345 --ignore CVE-2024-67890
```

### Scanning Options

```bash
# Recursive scan (default)
depswiz audit

# Current directory only
depswiz audit --shallow

# Filter by language
depswiz audit --only python,rust
```

## Vulnerability Sources

depswiz queries multiple vulnerability databases:

| Source | Coverage | Description |
|--------|----------|-------------|
| [OSV](https://osv.dev/) | All ecosystems | Open Source Vulnerabilities database |
| [GitHub Advisory Database](https://github.com/advisories) | All ecosystems | GitHub Security Advisories |
| [RustSec](https://rustsec.org/) | Rust | Rust security advisories |
| [NVD](https://nvd.nist.gov/) | All ecosystems | National Vulnerability Database (CVSS scores) |

### NVD API Key

For higher rate limits with NVD, set the `NVD_API_KEY` environment variable:

```bash
export NVD_API_KEY=your-api-key
depswiz audit
```

Request an API key at [NVD API Key Request](https://nvd.nist.gov/developers/request-an-api-key).

## Output

### CLI Format (Default)

```
depswiz v0.5.0 - Security Audit

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
sources = ["osv", "ghsa", "rustsec", "nvd"]

# Permanently ignore specific CVEs
ignore = [
    "CVE-2024-12345",  # Accepted risk - documented in security review
]
```

## See Also

- [depswiz check](check.md) - Check for updates
- [depswiz licenses](licenses.md) - License compliance
- [depswiz suggest](suggest.md) - AI security recommendations
