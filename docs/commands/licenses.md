# depswiz licenses

Check license compliance and generate license reports for your dependencies.

## Usage

```bash
depswiz licenses [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--md` | Output as Markdown |
| `--html` | Output as HTML |
| `--sarif` | Output as SARIF 2.1 (GitHub Code Scanning, VS Code) |
| `-o`, `--output FILE` | Write output to file |
| `--strict` | Exit with code 1 if license violations found |
| `--only LANGS` | Filter by language(s), comma-separated |
| `--shallow` | Scan current directory only (default: recursive) |
| `--summary` | Show license distribution summary only |
| `--deny LICENSE` | Deny specific license (can be used multiple times) |
| `--allow LICENSE` | Allow only specific licenses |
| `-p`, `--path PATH` | Project directory to check (default: current directory) |

## Examples

### Basic Usage

```bash
# List all licenses (recursive by default)
depswiz licenses

# Show summary only
depswiz licenses --summary
```

### License Policies

```bash
# Deny GPL licenses
depswiz licenses --deny GPL-3.0 --deny AGPL-3.0

# Allow only permissive licenses
depswiz licenses --allow MIT --allow Apache-2.0 --allow BSD-3-Clause
```

### CI/CD Integration

```bash
# Strict license compliance check
depswiz licenses --strict

# Deny specific licenses with strict mode
depswiz licenses --strict --deny GPL-3.0 --deny AGPL-3.0

# Generate license report
depswiz licenses --md -o LICENSES.md
```

In CI environments, `--strict` is automatically enabled.

### Scanning Options

```bash
# Recursive scan (default)
depswiz licenses

# Current directory only
depswiz licenses --shallow

# Filter by language
depswiz licenses --only python,rust
```

## Output

### CLI Format (Default)

```
depswiz v0.5.0 - License Check

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Package         ┃ Version        ┃ License             ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ httpx           │ 0.27.0         │ BSD-3-Clause        │
│ rich            │ 13.9.0         │ MIT                 │
│ typer           │ 0.15.0         │ MIT                 │
│ pyyaml          │ 6.0.2          │ MIT                 │
└─────────────────┴────────────────┴─────────────────────┘

License Summary:
  MIT: 12 packages
  BSD-3-Clause: 3 packages
  Apache-2.0: 2 packages
```

### Summary Mode

```bash
$ depswiz licenses --summary

License Distribution:
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ License         ┃ Count    ┃ Percentage┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│ MIT             │ 12       │ 70.6%     │
│ BSD-3-Clause    │ 3        │ 17.6%     │
│ Apache-2.0      │ 2        │ 11.8%     │
└─────────────────┴──────────┴───────────┘
```

### JSON Format

```json
{
  "packages": [
    {
      "name": "httpx",
      "version": "0.27.0",
      "license": "BSD-3-Clause",
      "spdx_id": "BSD-3-Clause"
    }
  ],
  "summary": {
    "MIT": 12,
    "BSD-3-Clause": 3,
    "Apache-2.0": 2
  }
}
```

## License Categories

| Category | Licenses | Policy Recommendation |
|----------|----------|----------------------|
| Permissive | MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC | Generally safe for commercial use |
| Weak Copyleft | LGPL-2.1, LGPL-3.0, MPL-2.0 | Review linking requirements |
| Strong Copyleft | GPL-2.0, GPL-3.0, AGPL-3.0 | May require source disclosure |
| Public Domain | CC0-1.0, Unlicense | No restrictions |

## Configuration

Configure license policies in `depswiz.toml`:

```toml
[licenses]
policy_mode = "allow"  # or "deny"

# Allowlist mode - only these licenses are accepted
allowed = ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC"]

# Denylist mode - these licenses are rejected
denied = ["GPL-3.0", "AGPL-3.0"]

# Warn about copyleft licenses
warn_copyleft = true
```

## SPDX License Identifiers

depswiz uses [SPDX license identifiers](https://spdx.org/licenses/) for consistent license naming. Common mappings:

| Common Name | SPDX ID |
|-------------|---------|
| MIT License | MIT |
| Apache License 2.0 | Apache-2.0 |
| BSD 3-Clause | BSD-3-Clause |
| GNU GPL v3 | GPL-3.0-only |
| ISC License | ISC |

## See Also

- [depswiz audit](audit.md) - Security scanning
- [depswiz sbom](sbom.md) - Generate SBOM with license info
