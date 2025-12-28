# Go

depswiz provides full support for Go modules, including dependency checking, vulnerability scanning, and workspace support.

## Detection

depswiz detects Go projects by looking for:

- `go.mod` - Go module manifest file
- `go.sum` - Go module checksums (lockfile)
- `go.work` - Go workspace file (multi-module support)

## Manifest Parsing

### go.mod

depswiz parses the `go.mod` file to extract:

- Module path
- Go version requirement
- Direct dependencies (`require` block)
- Indirect dependencies (marked with `// indirect`)
- Replace directives
- Exclude directives

```go
module github.com/example/myproject

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/spf13/cobra v1.8.0
    golang.org/x/sync v0.6.0 // indirect
)

replace github.com/old/module => github.com/new/module v1.0.0
```

### go.sum

The `go.sum` file provides checksums for all dependencies (direct and transitive). depswiz uses this to:

- Verify the complete dependency tree
- Detect all transitive dependencies
- Ensure integrity of dependency versions

## Version Checking

depswiz queries the [Go Module Proxy](https://proxy.golang.org) to check for latest versions:

```bash
# Check Go dependencies
depswiz check --only golang

# Include in multi-language check
depswiz check --only golang,python
```

### Module Path Escaping

Go module paths with uppercase letters require special handling. depswiz automatically escapes these paths when querying the proxy (e.g., `GitHub.com` becomes `!github.com`).

## Vulnerability Scanning

depswiz scans Go dependencies against multiple vulnerability databases:

| Source | Description |
|--------|-------------|
| [OSV](https://osv.dev/) | Open Source Vulnerabilities (Go ecosystem) |
| [GitHub Advisory Database](https://github.com/advisories) | GitHub Security Advisories |
| [NVD](https://nvd.nist.gov/) | National Vulnerability Database |

```bash
# Audit Go dependencies
depswiz audit --only golang

# Include all sources
depswiz audit --only golang  # Uses all configured sources
```

## Workspace Support

Go 1.18+ introduced workspaces via `go.work` files. depswiz detects and respects workspace configurations:

```go
// go.work
go 1.21

use (
    ./app
    ./lib
    ./tools
)
```

When scanning recursively, depswiz will find all modules in the workspace.

## Examples

### Basic Check

```bash
# Check for outdated Go dependencies
depswiz check -p /path/to/go/project

# JSON output
depswiz check --only golang --json
```

### Security Audit

```bash
# Scan for vulnerabilities
depswiz audit --only golang

# Fail on high or critical
depswiz audit --only golang --strict
```

### License Compliance

```bash
# Check licenses of Go dependencies
depswiz licenses --only golang
```

## Configuration

Configure Go-specific settings in `depswiz.toml`:

```toml
[languages]
enabled = ["golang"]  # Or include with other languages

[check]
recursive = true  # Scan all modules in subdirectories
```

## CLI Filter

Use the `--only` flag to filter to Go projects:

```bash
depswiz check --only golang
depswiz audit --only golang
depswiz licenses --only golang
```

## See Also

- [Language Support](index.md) - Overview of all supported languages
- [depswiz check](../commands/check.md) - Check for updates
- [depswiz audit](../commands/audit.md) - Vulnerability scanning
