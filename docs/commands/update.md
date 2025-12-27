# depswiz update

Update dependencies interactively with preview and confirmation.

## Usage

```bash
depswiz update [OPTIONS] [PATH]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project directory | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `-l`, `--language` | Filter by language |
| `--strategy` | Update strategy: all, security, patch, minor, major |
| `--dry-run` | Preview changes without applying |
| `-y`, `--yes` | Auto-confirm all updates |
| `--ai-suggest` | Get AI suggestions before updating |

## Examples

### Interactive Update

```bash
# Interactive mode (default)
depswiz update
```

This will:
1. Scan for outdated packages
2. Show available updates
3. Ask for confirmation before applying

### Dry Run

```bash
# Preview what would be updated
depswiz update --dry-run
```

### Update Strategies

```bash
# Only apply patch updates (safest)
depswiz update --strategy patch

# Only security-related updates
depswiz update --strategy security

# Only minor updates
depswiz update --strategy minor

# All updates including major versions
depswiz update --strategy all
```

### Auto-Confirm

```bash
# Apply all updates without confirmation
depswiz update -y

# Combine with strategy
depswiz update --strategy patch -y
```

### AI-Assisted Updates

```bash
# Get AI recommendations before updating
depswiz update --ai-suggest
```

This invokes Claude Code to analyze your dependencies and provide:
- Priority order for updates
- Breaking change warnings
- Risk assessment
- Migration tips

## Output

### Interactive Mode

```
depswiz v0.2.0 - Dependency Update

Scanning for updates...

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Package         ┃ Current   ┃ Latest    ┃ Update Type   ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ httpx           │ 0.27.0    │ 0.28.1    │ ⚠️  minor     │
│ rich            │ 13.9.0    │ 13.9.4    │ ✓ patch       │
│ typer           │ 0.15.0    │ 0.15.1    │ ✓ patch       │
└─────────────────┴───────────┴───────────┴───────────────┘

⚠️  1 minor update may contain breaking changes

Apply updates? [y/N]: y

Updating packages...
✓ Updated rich 13.9.0 → 13.9.4
✓ Updated typer 0.15.0 → 0.15.1
✓ Updated httpx 0.27.0 → 0.28.1

3 packages updated successfully
```

### Dry Run Mode

```
depswiz v0.2.0 - Dependency Update (Dry Run)

The following updates would be applied:

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Package         ┃ Current   ┃ Latest    ┃ Command                  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ httpx           │ 0.27.0    │ 0.28.1    │ uv add httpx@0.28.1      │
│ rich            │ 13.9.0    │ 13.9.4    │ uv add rich@13.9.4       │
└─────────────────┴───────────┴───────────┴──────────────────────────┘

No changes applied (dry run)
```

## Update Strategies

| Strategy | Description | Risk Level |
|----------|-------------|------------|
| `patch` | Only patch versions (x.y.Z) | Low |
| `minor` | Patch and minor versions (x.Y.z) | Medium |
| `major` | All versions including major (X.y.z) | High |
| `security` | Only packages with known vulnerabilities | Varies |
| `all` | All available updates | Varies |

## Language-Specific Commands

depswiz generates the appropriate update command for each language:

| Language | Package Manager | Update Command |
|----------|-----------------|----------------|
| Python | uv | `uv add package@version` |
| Python | pip | `pip install package==version` |
| Rust | cargo | `cargo update -p package` |
| Dart | pub | `dart pub upgrade package` |
| JavaScript | npm | `npm install package@version` |

## Best Practices

1. **Always run tests after updating**
   ```bash
   depswiz update --strategy patch -y && pytest
   ```

2. **Review major updates carefully**
   ```bash
   depswiz update --strategy major --dry-run
   ```

3. **Use AI assistance for complex updates**
   ```bash
   depswiz update --ai-suggest
   ```

4. **Update security issues first**
   ```bash
   depswiz update --strategy security -y
   ```

## See Also

- [depswiz check](check.md) - Check for updates
- [depswiz suggest](suggest.md) - AI-powered suggestions
- [depswiz audit](audit.md) - Security scanning
