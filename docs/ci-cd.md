# CI/CD Integration

depswiz is designed for zero-configuration CI/CD integration. It automatically detects CI environments and adjusts its behavior accordingly.

## Zero-Configuration CI

When running in a CI environment, depswiz automatically:

- **Enables strict mode**: Fails the build on issues (no `--strict` flag needed)
- **Defaults to JSON output**: Machine-readable output by default
- **Scans recursively**: Checks your entire project tree

### Detected CI Platforms

depswiz auto-detects 13 CI platforms:

| Platform | Environment Variable |
|----------|---------------------|
| GitHub Actions | `GITHUB_ACTIONS` |
| GitLab CI | `GITLAB_CI` |
| CircleCI | `CIRCLECI` |
| Travis CI | `TRAVIS` |
| Jenkins | `JENKINS_HOME` |
| Azure Pipelines | `TF_BUILD` |
| Bitbucket Pipelines | `BITBUCKET_PIPELINE` |
| TeamCity | `TEAMCITY_VERSION` |
| Buildkite | `BUILDKITE` |
| Drone | `DRONE` |
| Woodpecker | `CI=woodpecker` |
| Codeship | `CI_NAME=codeship` |
| Semaphore | `SEMAPHORE` |

## GitHub Actions

### Simple One-Liner

```yaml
# .github/workflows/security.yml
name: Security Check

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install depswiz
      - run: depswiz  # That's it! Comprehensive scan with auto-strict mode
```

### Security Audit

```yaml
# .github/workflows/security.yml
name: Security Audit

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install depswiz
        run: uv tool install depswiz

      - name: Security Audit
        run: depswiz audit --json -o audit-results.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-audit
          path: audit-results.json
```

### Dependency Check

```yaml
# .github/workflows/deps.yml
name: Dependency Check

on:
  pull_request:
    paths:
      - 'pyproject.toml'
      - 'requirements.txt'
      - 'Cargo.toml'
      - 'package.json'
      - 'pubspec.yaml'
      - 'Dockerfile'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install depswiz
        run: pip install depswiz

      - name: Check Dependencies
        run: depswiz check --md >> $GITHUB_STEP_SUMMARY
```

### License Compliance

```yaml
# .github/workflows/license.yml
name: License Compliance

on:
  push:
    branches: [main]
  pull_request:

jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install depswiz
        run: pip install depswiz

      - name: License Check
        run: depswiz licenses --deny GPL-3.0 --deny AGPL-3.0
```

### SBOM Generation

```yaml
# .github/workflows/sbom.yml
name: Generate SBOM

on:
  release:
    types: [published]

jobs:
  sbom:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Install depswiz
        run: pip install depswiz

      - name: Generate SBOM
        run: |
          depswiz sbom -o sbom.json
          depswiz sbom --spdx -o sbom.spdx.json

      - name: Upload to Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            sbom.json
            sbom.spdx.json
```

### Complete Workflow

```yaml
# .github/workflows/depswiz.yml
name: Dependency Management

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 6 * * 1'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install depswiz
        run: pip install depswiz

      - name: Comprehensive Scan
        run: depswiz --json -o comprehensive.json

      - name: Generate SBOM
        run: depswiz sbom -o sbom.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: depswiz-results
          path: |
            comprehensive.json
            sbom.json
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - security
  - compliance

security-audit:
  stage: security
  image: python:3.13
  script:
    - pip install depswiz
    - depswiz audit --json -o audit.json
  artifacts:
    paths:
      - audit.json
    reports:
      sast: audit.json

license-check:
  stage: compliance
  image: python:3.13
  script:
    - pip install depswiz
    - depswiz licenses --deny GPL-3.0 --json -o licenses.json
  artifacts:
    paths:
      - licenses.json

sbom:
  stage: compliance
  image: python:3.13
  script:
    - pip install depswiz
    - depswiz sbom -o sbom.json
  artifacts:
    paths:
      - sbom.json
```

## Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.13'

  - script: pip install depswiz
    displayName: 'Install depswiz'

  - script: depswiz
    displayName: 'Comprehensive Scan'

  - script: depswiz sbom -o $(Build.ArtifactStagingDirectory)/sbom.json
    displayName: 'Generate SBOM'

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: $(Build.ArtifactStagingDirectory)
      artifactName: 'depswiz-results'
```

## Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Install') {
            steps {
                sh 'pip install depswiz'
            }
        }

        stage('Comprehensive Scan') {
            steps {
                sh 'depswiz'
            }
        }

        stage('SBOM') {
            steps {
                sh 'depswiz sbom -o sbom.json'
                archiveArtifacts artifacts: 'sbom.json'
            }
        }
    }
}
```

## Output Formats for CI

### Simplified Flags

```bash
# JSON output
depswiz check --json

# Markdown for reports
depswiz audit --md

# HTML for archiving
depswiz licenses --html -o report.html
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - no issues found |
| 1 | Issues found (with `--strict` or auto-enabled in CI) |
| 2 | Configuration or input error |

Use `--strict` to explicitly fail on issues:

```bash
# Fail on any issues
depswiz --strict

# Fail on high+ severity vulnerabilities
depswiz audit --strict

# Fail on critical only
depswiz audit --strict critical

# Fail on license violations
depswiz licenses --strict
```

## Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: depswiz-audit
        name: Security Audit
        entry: depswiz audit --strict critical
        language: system
        pass_filenames: false
        files: ^(pyproject\.toml|requirements\.txt|Cargo\.toml|package\.json|Dockerfile)$
```

## Scheduled Checks

Run weekly security scans:

```yaml
# GitHub Actions cron
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 6 AM UTC
```

## Caching

Speed up CI runs by caching:

```yaml
- name: Cache depswiz
  uses: actions/cache@v4
  with:
    path: ~/.cache/depswiz
    key: depswiz-${{ hashFiles('**/pyproject.toml', '**/Cargo.toml', '**/package.json', '**/Dockerfile') }}
```

## Notifications

### Slack Notification

```yaml
- name: Notify on Failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Security audit failed! Check: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      }
```

## See Also

- [Commands Reference](commands/index.md)
- [Configuration](configuration.md)
