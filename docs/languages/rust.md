# Rust Support

depswiz provides full support for Rust projects using Cargo.

## Supported Files

### Manifest Files

| File | Description |
|------|-------------|
| `Cargo.toml` | Cargo manifest file |

### Lockfiles

| File | Description |
|------|-------------|
| `Cargo.lock` | Cargo lockfile with exact versions |

## Package Registry

depswiz queries [crates.io](https://crates.io) for package information:

```
GET https://crates.io/api/v1/crates/{package}
```

## Examples

### Check Rust Dependencies

```bash
# Check current directory
depswiz check

# Check only Rust
depswiz check -l rust

# Check specific project
depswiz check /path/to/rust/project
```

### Audit for Vulnerabilities

```bash
depswiz audit -l rust
```

Rust packages are checked against:
- [RustSec Advisory Database](https://rustsec.org/)
- [OSV](https://osv.dev/)
- [GitHub Advisory Database](https://github.com/advisories)

### Generate SBOM

```bash
depswiz sbom -l rust -o rust-sbom.json
```

## Cargo.toml Format

### Basic Dependencies

```toml
[package]
name = "my-project"
version = "1.0.0"
edition = "2021"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }
```

### Dependency Types

```toml
# Regular dependencies
[dependencies]
serde = "1.0"

# Development dependencies
[dev-dependencies]
criterion = "0.5"

# Build dependencies
[build-dependencies]
cc = "1.0"
```

### Version Requirements

| Specifier | Meaning |
|-----------|---------|
| `1.0` | >=1.0.0, <2.0.0 (default caret) |
| `^1.0` | >=1.0.0, <2.0.0 (explicit caret) |
| `~1.0` | >=1.0.0, <1.1.0 (tilde) |
| `=1.0.0` | Exactly 1.0.0 |
| `>=1.0, <2.0` | Version range |
| `*` | Any version |

## Workspace Support

### Cargo Workspaces

```toml
# Cargo.toml (workspace root)
[workspace]
members = [
    "crates/*",
    "examples/*",
]
```

Scan all workspace members:

```bash
depswiz check --workspace
```

### Virtual Workspaces

depswiz handles virtual workspaces (no root package):

```toml
[workspace]
members = ["crates/*"]
resolver = "2"
```

## Update Commands

depswiz generates Cargo update commands:

```bash
# Update specific package
cargo update -p package_name

# Update all packages
cargo update
```

## Features

### Feature Dependencies

depswiz tracks feature-gated dependencies:

```toml
[dependencies]
tokio = { version = "1.0", optional = true }

[features]
default = ["tokio"]
async = ["tokio"]
```

## Common Issues

### MSRV (Minimum Supported Rust Version)

Some updates may require newer Rust versions. Check package MSRV:

```toml
[package]
rust-version = "1.70"
```

### Yanked Versions

depswiz identifies yanked crate versions and recommends updates.

### Build Feature Conflicts

When features conflict, depswiz reports the issue:

```
Feature conflict: package requires feature 'std'
                  but dependency uses 'no_std'
```

## RustSec Integration

depswiz integrates with RustSec for Rust-specific security advisories:

```bash
# Audit with RustSec
depswiz audit -l rust
```

Example output:

```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Crate       ┃ Advisory        ┃ Severity  ┃ Description             ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ openssl     │ RUSTSEC-2024-XX │ HIGH      │ Memory safety issue     │
└─────────────┴─────────────────┴───────────┴─────────────────────────┘
```

## See Also

- [Commands Reference](../commands/index.md)
- [Configuration](../configuration.md)
- [crates.io](https://crates.io)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [RustSec](https://rustsec.org/)
