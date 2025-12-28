# depswiz sbom

Generate Software Bill of Materials (SBOM) in industry-standard formats.

## Usage

```bash
depswiz sbom [OPTIONS]
```

## Options

| Option | Description |
|--------|-------------|
| `-o`, `--output FILE` | Output file path (required) |
| `--json` | Output as JSON (CycloneDX format) |
| `--spdx` | Use SPDX format instead of CycloneDX |
| `--only LANGS` | Filter by language(s), comma-separated |
| `--shallow` | Scan current directory only (default: recursive) |
| `--dev` | Include development dependencies |
| `-p`, `--path PATH` | Project directory (default: current directory) |

## Examples

### Basic Usage

```bash
# Generate CycloneDX SBOM
depswiz sbom -o sbom.json

# Generate SPDX SBOM
depswiz sbom --spdx -o sbom.spdx.json
```

### Include Development Dependencies

```bash
# Include dev dependencies (excluded by default)
depswiz sbom --dev -o sbom-full.json
```

### Language-Specific SBOM

```bash
# Python dependencies only
depswiz sbom --only python -o python-sbom.json

# Rust dependencies only
depswiz sbom --only rust -o rust-sbom.json
```

### Scanning Options

```bash
# Recursive scan (default)
depswiz sbom -o sbom.json

# Current directory only
depswiz sbom --shallow -o sbom.json
```

## Output Formats

### CycloneDX 1.6 (Default)

[CycloneDX](https://cyclonedx.org/) is an OWASP project providing a lightweight SBOM standard.

```json
{
  "$schema": "http://cyclonedx.org/schema/bom-1.6.schema.json",
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "serialNumber": "urn:uuid:...",
  "version": 1,
  "metadata": {
    "timestamp": "2025-12-28T12:00:00Z",
    "tools": [
      {
        "vendor": "depswiz",
        "name": "depswiz",
        "version": "0.5.0"
      }
    ],
    "component": {
      "type": "application",
      "name": "my-project",
      "version": "1.0.0"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "httpx",
      "version": "0.27.0",
      "purl": "pkg:pypi/httpx@0.27.0",
      "licenses": [
        {
          "license": {
            "id": "BSD-3-Clause"
          }
        }
      ]
    }
  ]
}
```

### SPDX 3.0

[SPDX](https://spdx.dev/) (Software Package Data Exchange) is an ISO standard for communicating software bill of materials.

```json
{
  "spdxVersion": "SPDX-3.0",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "my-project-sbom",
  "creationInfo": {
    "created": "2025-12-28T12:00:00Z",
    "creators": ["Tool: depswiz-0.5.0"]
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-httpx",
      "name": "httpx",
      "versionInfo": "0.27.0",
      "downloadLocation": "https://pypi.org/project/httpx/",
      "licenseConcluded": "BSD-3-Clause"
    }
  ]
}
```

## Use Cases

### Regulatory Compliance

Many regulations now require SBOM generation:

- **Executive Order 14028** (US) - Requires SBOMs for software sold to federal government
- **EU Cyber Resilience Act** - Mandates SBOM for products with digital elements
- **NTIA Minimum Elements** - Defines required SBOM fields

### Supply Chain Security

```bash
# Generate comprehensive SBOM for security review
depswiz sbom --dev -o sbom.json

# Combine with vulnerability scan
depswiz audit --json -o vulnerabilities.json
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate SBOM
  run: depswiz sbom -o sbom.json

- name: Upload SBOM artifact
  uses: actions/upload-artifact@v4
  with:
    name: sbom
    path: sbom.json
```

## Configuration

Configure SBOM generation in `depswiz.toml`:

```toml
[sbom]
format = "cyclonedx"  # or "spdx"
include_dev = false
output_dir = "reports/"
```

## PURL (Package URL)

depswiz generates Package URLs ([PURL](https://github.com/package-url/purl-spec)) for each component:

| Language | PURL Format |
|----------|-------------|
| Python | `pkg:pypi/package@version` |
| Rust | `pkg:cargo/package@version` |
| Dart | `pkg:pub/package@version` |
| JavaScript | `pkg:npm/package@version` |
| Docker | `pkg:docker/image@tag` |

## See Also

- [depswiz licenses](licenses.md) - License compliance
- [depswiz audit](audit.md) - Vulnerability scanning
- [CycloneDX Specification](https://cyclonedx.org/specification/overview/)
- [SPDX Specification](https://spdx.github.io/spdx-spec/)
