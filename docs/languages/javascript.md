# JavaScript/TypeScript Support

depswiz provides comprehensive support for JavaScript and TypeScript projects using npm, yarn, pnpm, and other package managers.

## Supported Files

### Manifest Files

| File | Description |
|------|-------------|
| `package.json` | npm package manifest |

### Lockfiles

| File | Package Manager |
|------|-----------------|
| `package-lock.json` | npm |
| `yarn.lock` | Yarn |
| `pnpm-lock.yaml` | pnpm |
| `bun.lockb` | Bun |

## Package Registry

depswiz queries the [npm registry](https://www.npmjs.com/) for package information:

```
GET https://registry.npmjs.org/{package}
```

## Examples

### Check JavaScript Dependencies

```bash
# Check current directory
depswiz check

# Check only JavaScript
depswiz check -l javascript

# Check specific project
depswiz check /path/to/js/project
```

### Audit for Vulnerabilities

```bash
depswiz audit -l javascript
```

JavaScript packages are checked against:
- [OSV](https://osv.dev/)
- [GitHub Advisory Database](https://github.com/advisories)
- [npm Security Advisories](https://www.npmjs.com/advisories)

### Generate SBOM

```bash
depswiz sbom -l javascript -o js-sbom.json
```

## package.json Format

### Basic Dependencies

```json
{
  "name": "my-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "jest": "^29.7.0"
  }
}
```

### Dependency Types

```json
{
  "dependencies": {},
  "devDependencies": {},
  "peerDependencies": {},
  "optionalDependencies": {}
}
```

### Version Ranges

| Specifier | Meaning |
|-----------|---------|
| `^1.2.3` | >=1.2.3, <2.0.0 (caret - default) |
| `~1.2.3` | >=1.2.3, <1.3.0 (tilde) |
| `1.2.3` | Exactly 1.2.3 |
| `>=1.2.0` | Minimum version |
| `1.2.x` | Any patch in 1.2 |
| `*` | Any version |

## Workspace Support

### npm Workspaces

```json
{
  "workspaces": [
    "packages/*",
    "apps/*"
  ]
}
```

### Yarn Workspaces

```json
{
  "workspaces": {
    "packages": ["packages/*"],
    "nohoist": ["**/react-native"]
  }
}
```

### pnpm Workspaces

```yaml
# pnpm-workspace.yaml
packages:
  - "packages/*"
  - "apps/*"
```

Scan all workspace members:

```bash
depswiz check --workspace
```

## Update Commands

depswiz generates appropriate update commands:

| Package Manager | Update Command |
|-----------------|----------------|
| npm | `npm install package@version` |
| yarn | `yarn add package@version` |
| pnpm | `pnpm add package@version` |
| bun | `bun add package@version` |

## TypeScript Support

depswiz handles TypeScript projects:

```json
{
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0"
  }
}
```

Type definition packages (`@types/*`) are tracked alongside regular packages.

## Common Issues

### Peer Dependency Conflicts

depswiz identifies peer dependency issues:

```
Peer dependency conflict:
  package-a requires react@^17.0.0
  package-b requires react@^18.0.0
```

### Deprecated Packages

depswiz warns about deprecated packages:

```
Warning: request@2.88.2 is deprecated
  → Use node-fetch or axios instead
```

### Private Registries

For private npm registries, depswiz respects `.npmrc`:

```ini
# .npmrc
registry=https://npm.example.com/
//npm.example.com/:_authToken=${NPM_TOKEN}
```

### Scoped Packages

depswiz correctly handles scoped packages:

```json
{
  "dependencies": {
    "@organization/package": "^1.0.0"
  }
}
```

## Tools Version Checking

Use `depswiz tools` to check Node.js and package manager versions:

```bash
depswiz tools -t node -t npm -t pnpm -t yarn
```

Output:

```
┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Tool      ┃ Installed  ┃ Latest     ┃ Status           ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ Node.js   │ 20.10.0    │ 22.12.0    │ update available │
│ npm       │ 10.2.0     │ 10.9.0     │ update available │
│ pnpm      │ 8.15.0     │ 9.1.0      │ update available │
│ Yarn      │ 4.0.0      │ 4.1.0      │ update available │
└───────────┴────────────┴────────────┴──────────────────┘
```

## Engine Requirements

depswiz tracks engine requirements:

```json
{
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

## See Also

- [Commands Reference](../commands/index.md)
- [Configuration](../configuration.md)
- [npm](https://www.npmjs.com/)
- [yarn](https://yarnpkg.com/)
- [pnpm](https://pnpm.io/)
