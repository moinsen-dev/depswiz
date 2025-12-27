# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

We take the security of depswiz seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@moinsen.dev** (or create a private security advisory on GitHub).

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information:

- Type of issue (e.g., command injection, path traversal, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### What to Expect

- A response acknowledging your report within 48 hours
- An assessment of the vulnerability and its impact
- A timeline for addressing the issue
- Credit in the security advisory (unless you prefer to remain anonymous)

### Security Best Practices

When using depswiz:

1. **Keep depswiz updated**: Run `pip install --upgrade depswiz` regularly
2. **Review audit results**: Pay attention to `depswiz audit` findings
3. **Use trusted registries**: Be cautious with packages from unknown sources
4. **Check SBOM outputs**: Review generated SBOMs for unexpected dependencies

## Security Features

depswiz includes several security-focused features:

- **Vulnerability Scanning**: Integration with OSV database for known vulnerabilities
- **License Compliance**: SPDX-based license checking to avoid legal issues
- **SBOM Generation**: CycloneDX and SPDX formats for supply chain transparency
- **Secure Defaults**: Conservative defaults for security-related options

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new versions and publish security advisories
