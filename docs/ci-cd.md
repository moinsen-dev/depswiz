# CI/CD Integration

depswiz is designed for seamless integration with CI/CD pipelines. This guide covers common patterns for GitHub Actions, GitLab CI, and other platforms.

## GitHub Actions

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
        run: depswiz audit --fail-on high --format json > audit-results.json

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

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install depswiz
        run: pip install depswiz

      - name: Check Dependencies
        run: depswiz check --format markdown >> $GITHUB_STEP_SUMMARY
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
        run: |
          depswiz licenses \
            --deny GPL-3.0 \
            --deny AGPL-3.0 \
            --fail-on-unknown
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
          depswiz sbom --format cyclonedx -o sbom.json
          depswiz sbom --format spdx -o sbom.spdx.json

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

      - name: Check for Updates
        run: depswiz check --format json > check-results.json
        continue-on-error: true

      - name: Security Audit
        run: depswiz audit --fail-on high

      - name: License Compliance
        run: depswiz licenses --deny GPL-3.0

      - name: Generate SBOM
        run: depswiz sbom -o sbom.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: depswiz-results
          path: |
            check-results.json
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
    - depswiz audit --fail-on high --format json > audit.json
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
    - depswiz licenses --deny GPL-3.0 --format json > licenses.json
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

  - script: depswiz audit --fail-on high
    displayName: 'Security Audit'

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

        stage('Security Audit') {
            steps {
                sh 'depswiz audit --fail-on high'
            }
        }

        stage('License Check') {
            steps {
                sh 'depswiz licenses --deny GPL-3.0'
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

### JSON Output

Best for programmatic parsing:

```bash
depswiz check --format json
depswiz audit --format json
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, no issues |
| 1 | Issues found (vulnerabilities, policy violations) |
| 2 | Configuration or input error |

Use `--fail-*` flags to control when to fail:

```bash
# Fail on high+ severity vulnerabilities
depswiz audit --fail-on high

# Fail if any outdated packages
depswiz check --fail-outdated

# Fail on unknown licenses
depswiz licenses --fail-on-unknown
```

## Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: depswiz-audit
        name: Security Audit
        entry: depswiz audit --fail-on critical
        language: system
        pass_filenames: false
        files: ^(pyproject\.toml|requirements\.txt|Cargo\.toml|package\.json)$
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
    key: depswiz-${{ hashFiles('**/pyproject.toml', '**/Cargo.toml', '**/package.json') }}
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
