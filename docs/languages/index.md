# Language Support

depswiz supports dependency management for multiple programming languages through a plugin architecture. Each language plugin understands the ecosystem's manifest files, lockfiles, and package registry.

## Supported Languages

| Language | Plugin | Status |
|----------|--------|--------|
| [Python](python.md) | Built-in | Stable |
| [Rust](rust.md) | Built-in | Stable |
| [Dart/Flutter](dart.md) | Built-in | Stable |
| [JavaScript/TypeScript](javascript.md) | Built-in | Stable |

## Language Detection

depswiz automatically detects languages based on manifest files:

| Language | Detection Files |
|----------|-----------------|
| Python | `pyproject.toml`, `requirements.txt`, `setup.py` |
| Rust | `Cargo.toml` |
| Dart/Flutter | `pubspec.yaml` |
| JavaScript/TypeScript | `package.json` |

## Multi-Language Projects

depswiz handles projects with multiple languages seamlessly:

```bash
# Check all detected languages
depswiz check

# Filter to specific languages
depswiz check -l python -l rust
```

## Workspace Support

Each language plugin understands its ecosystem's workspace conventions:

| Language | Workspace Definition |
|----------|---------------------|
| Python | uv workspaces, poetry workspaces |
| Rust | Cargo workspaces (`[workspace]` in Cargo.toml) |
| Dart/Flutter | Melos workspaces |
| JavaScript | npm/yarn/pnpm workspaces |

Enable workspace scanning:

```bash
depswiz check --workspace
```

## Version Comparison

depswiz uses semantic versioning to compare versions and determine update types:

| Update Type | Version Change | Risk Level |
|-------------|---------------|------------|
| Patch | 1.2.3 → 1.2.4 | Low |
| Minor | 1.2.3 → 1.3.0 | Medium |
| Major | 1.2.3 → 2.0.0 | High |

## Registry APIs

Each plugin queries its ecosystem's package registry:

| Language | Registry | API Endpoint |
|----------|----------|--------------|
| Python | PyPI | `https://pypi.org/pypi/{package}/json` |
| Rust | crates.io | `https://crates.io/api/v1/crates/{package}` |
| Dart | pub.dev | `https://pub.dev/api/packages/{package}` |
| JavaScript | npm | `https://registry.npmjs.org/{package}` |

## Adding Language Support

depswiz's plugin architecture allows adding support for new languages. See [Plugin Development](../plugins/developing.md) for details.

## Configuration

Enable or disable specific languages in `depswiz.toml`:

```toml
[languages]
enabled = ["python", "rust"]  # Only check these languages
```
