# Docker Support

depswiz can scan Dockerfiles and Docker Compose files for outdated base images, helping you keep your container infrastructure up to date.

## Overview

The Docker plugin detects:

- `Dockerfile` - Standard Docker build files
- `docker-compose.yml` / `docker-compose.yaml` - Multi-container definitions
- Named Dockerfiles (e.g., `Dockerfile.prod`, `Dockerfile.dev`)

## Detection

Docker files are automatically detected when present in your project:

```bash
# Scans Dockerfiles and docker-compose files
depswiz check

# Scan only Docker files
depswiz check --only docker
```

## Dockerfile Parsing

The plugin parses `FROM` instructions to extract base images:

```dockerfile
# These are all detected
FROM python:3.13-slim
FROM node:22-alpine AS builder
FROM golang:1.22
FROM ubuntu:24.04
```

### Multi-Stage Builds

All stages in multi-stage builds are analyzed:

```dockerfile
# Stage 1 - detected
FROM node:22-alpine AS builder
RUN npm ci

# Stage 2 - also detected
FROM node:22-alpine AS runner
COPY --from=builder /app .
```

### ARG Variables

The plugin resolves ARG variables in FROM instructions:

```dockerfile
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim  # Resolves to python:3.13-slim
```

## Docker Compose Support

The plugin scans services defined in Docker Compose files:

```yaml
# docker-compose.yml
services:
  web:
    image: nginx:1.25          # Detected
  db:
    image: postgres:16-alpine  # Detected
  app:
    build: .                   # References Dockerfile - also scanned
```

### Build Contexts

When a service uses `build:`, the plugin scans the referenced Dockerfile:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod  # This file is scanned
```

## Registry Support

The plugin queries Docker Hub for version information:

| Registry | Support |
|----------|---------|
| Docker Hub | Full support |
| GitHub Container Registry | Full support |
| Amazon ECR | Partial (public images) |
| Google Container Registry | Partial (public images) |

## Version Detection

The plugin identifies semantic versions in image tags:

```dockerfile
# Semantic version detected
FROM python:3.13.1-slim  # Current: 3.13.1, Latest: 3.13.x

# Major version only (always "up to date" for major matching)
FROM node:22  # Tracks node:22.x.x

# Named tags
FROM nginx:latest  # No version comparison possible
FROM nginx:stable  # No version comparison possible
```

## Output Example

```
depswiz v0.5.0 - Dependency Check

Detected: Docker (Dockerfile, docker-compose.yml)

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Image           ┃ Current   ┃ Latest    ┃ Update Type      ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ python          │ 3.12-slim │ 3.13-slim │ minor            │
│ node            │ 20-alpine │ 22-alpine │ major            │
│ postgres        │ 15        │ 16        │ major            │
└─────────────────┴───────────┴───────────┴──────────────────┘

3 image(s) have updates available
```

## Vulnerability Scanning

Docker images are also checked for known vulnerabilities:

```bash
# Audit Docker base images
depswiz audit --only docker
```

The plugin checks the base images against vulnerability databases to identify security issues.

## Examples

### Basic Scan

```bash
# Check Docker images in current directory
depswiz check --only docker

# Check recursively (default)
depswiz check --only docker

# Current directory only
depswiz check --only docker --shallow
```

### Combined Scan

```bash
# Check both Python and Docker
depswiz check --only python,docker

# Full comprehensive scan including Docker
depswiz
```

### CI/CD Integration

```yaml
# GitHub Actions
- name: Check Docker Images
  run: depswiz check --only docker --strict
```

## Configuration

Configure Docker scanning in `depswiz.toml`:

```toml
[languages]
enabled = ["python", "docker"]  # Enable Docker scanning

[docker]
# Patterns to scan
patterns = ["Dockerfile*", "docker-compose*.yml", "docker-compose*.yaml"]

# Registries to query
registries = ["docker.io", "ghcr.io"]
```

## Limitations

- **Private registries**: Currently limited to public images
- **Digest references**: `image@sha256:...` references are not version-compared
- **Custom tags**: Non-semantic tags (e.g., `latest`, `stable`) cannot be version-compared

## Best Practices

1. **Use specific versions**: Prefer `python:3.13.1-slim` over `python:latest`
2. **Pin minor versions**: Use `node:22.12-alpine` for stability
3. **Update regularly**: Major image updates may include security fixes
4. **Combine with audit**: Run `depswiz audit --only docker` to check for CVEs

## See Also

- [Check Command](../commands/check.md)
- [Audit Command](../commands/audit.md)
- [Language Support](index.md)
