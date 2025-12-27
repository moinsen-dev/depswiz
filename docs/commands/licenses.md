# depswiz licenses

Check license compliance and generate license reports for your dependencies.

## Usage

```bash
depswiz licenses [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project directory to check | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `-l`, `--language` | Filter by language |
| `--summary` | Show license distribution summary only |
| `--deny` | Deny specific license (can be used multiple times) |
| `--allow` | Allow only specific licenses |
| `--fail-on-unknown` | Exit with code 1 if unknown licenses found |
| `-f`, `--format` | Output format: cli, json, markdown, html |

## Examples

### Basic Usage

```bash
# List all licenses
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

# Fail on unknown licenses (for compliance)
depswiz licenses --fail-on-unknown
```

### CI/CD Integration

```bash
# Strict license compliance check
depswiz licenses --deny GPL-3.0 --deny AGPL-3.0 --fail-on-unknown

# Generate license report
depswiz licenses --format markdown > LICENSES.md
```

## Output

### CLI Format (Default)

```
depswiz v0.2.0 - License Check

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
