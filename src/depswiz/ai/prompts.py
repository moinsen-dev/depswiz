"""Prompt templates for Claude Code integration."""

UPGRADE_PROMPT = """
Analyze this project's dependencies and development environment.

## Part 1: Dependencies
Look at the project's manifest files (pyproject.toml, package.json, Cargo.toml, pubspec.yaml)
and determine which dependencies need updating.

For each outdated package, provide:
1. **Priority Order**: Which packages to update first and why
2. **Breaking Changes**: Warn about major version bumps with potential issues
3. **Batch Strategy**: Group packages that should be updated together
4. **Risk Assessment**: Rate the risk of each update (low/medium/high)
5. **Migration Tips**: Specific steps for major upgrades

## Part 2: Development Toolchain
Check the installed versions of development tools used by this project:
- For Python projects: python, uv, pip versions
- For Node.js projects: node, npm/pnpm/yarn versions
- For Rust projects: rustc, cargo versions
- For Dart/Flutter projects: dart, flutter versions
- Any other relevant tools (docker, go, etc.)

Report which tools might need updating and why (security, performance, compatibility).

Check for security vulnerabilities using OSV or similar sources.
Prioritize security updates over feature updates.
Format your response as clear, actionable markdown.
"""

SECURITY_PROMPT = """
Audit this project's dependencies for security vulnerabilities.

1. Check all manifest files for dependencies
2. Look up known CVEs and security advisories for each package
3. Identify packages with critical or high severity issues
4. Provide specific upgrade recommendations for vulnerable packages
5. Suggest safe upgrade paths that minimize breaking changes

Format your response as markdown with clear severity ratings.
"""

BREAKING_CHANGES_PROMPT = """
Analyze the major version updates available for this project's dependencies.

For each major version bump available:
1. Identify what breaking changes are documented
2. Assess the impact on this specific codebase
3. Provide step-by-step migration instructions
4. Estimate effort required (quick fix, moderate, significant refactor)

Focus on practical, actionable guidance.
"""

QUICK_CHECK_PROMPT = """
Give me a quick summary of this project's health:

1. How many dependencies are outdated?
2. Are there any security vulnerabilities?
3. What are the top 3 most urgent updates?
4. Are the development tools (python/node/rust/etc.) up to date?

Be concise - just the key facts.
"""

AI_AGENT_PROMPT = """
# Dependency Update Task

You are an AI coding agent tasked with updating dependencies for this project.

## Project Analysis

First, analyze the project structure and dependencies:

1. **Identify manifest files**: Look for pyproject.toml, package.json, Cargo.toml, pubspec.yaml
2. **Check current versions**: Read the lockfiles to understand exact installed versions
3. **Query registries**: Determine which packages have updates available

## Update Strategy

Follow this priority order for updates:

### Priority 1: Security Vulnerabilities
- Check for known CVEs using OSV or security advisories
- Update any packages with HIGH or CRITICAL vulnerabilities immediately
- Document the CVE being fixed in commit messages

### Priority 2: Patch Updates (x.y.Z)
- These are typically safe and include bug fixes
- Apply all patch updates in a single batch
- Run tests after applying

### Priority 3: Minor Updates (x.Y.z)
- Review changelogs for breaking changes (despite semver, some happen)
- Apply in smaller batches, testing between each
- Pay attention to deprecation warnings

### Priority 4: Major Updates (X.y.z)
- Research migration guides before applying
- Apply one at a time with thorough testing
- May require code changes

## Execution Steps

For each update batch:

1. **Create a backup**: Ensure you can revert if needed
2. **Update manifest**: Modify version constraints appropriately
3. **Update lockfile**: Run the package manager's lock/update command
4. **Run tests**: Execute the full test suite
5. **Fix issues**: Address any breaking changes or deprecations
6. **Commit**: Create a clear commit message describing the updates

## Commands by Ecosystem

- **Python (uv)**: `uv lock --upgrade-package <pkg>` or `uv add <pkg>@latest`
- **Python (pip)**: `pip install --upgrade <pkg>`
- **Rust**: `cargo update -p <pkg>`
- **Dart/Flutter**: `dart pub upgrade <pkg>` or `flutter pub upgrade <pkg>`
- **JavaScript (npm)**: `npm install <pkg>@latest`
- **JavaScript (pnpm)**: `pnpm update <pkg>`
- **JavaScript (yarn)**: `yarn upgrade <pkg>`

## Output Requirements

After completing updates, provide:

1. Summary of all packages updated with old → new versions
2. Any breaking changes encountered and how they were resolved
3. Test results
4. Recommendations for packages that couldn't be updated (and why)

Begin by analyzing the project and creating your update plan.
"""

TOOLCHAIN_PROMPT = """
Analyze the development toolchain for this project.

Check which development tools are installed and their versions:
- Python: python3 --version, pip --version, uv --version (if present)
- Node.js: node --version, npm --version, pnpm/yarn versions
- Rust: rustc --version, cargo --version
- Dart/Flutter: dart --version, flutter --version
- Go: go version
- Docker: docker --version

For each installed tool:
1. Report the current version
2. Check if a newer version is available
3. Explain the benefits of upgrading (security, performance, new features)
4. Provide the upgrade command for macOS/Linux

Focus on tools actually used by this project (based on manifest files present).
Format your response as clear, actionable markdown.
"""


def get_prompt(focus: str = "upgrade") -> str:
    """Get the appropriate prompt template.

    Args:
        focus: The focus area - "upgrade", "security", "breaking", "quick", "toolchain", or "agent"

    Returns:
        The prompt template string
    """
    prompts = {
        "upgrade": UPGRADE_PROMPT,
        "security": SECURITY_PROMPT,
        "breaking": BREAKING_CHANGES_PROMPT,
        "quick": QUICK_CHECK_PROMPT,
        "toolchain": TOOLCHAIN_PROMPT,
        "agent": AI_AGENT_PROMPT,
    }
    return prompts.get(focus, UPGRADE_PROMPT)


def list_prompts() -> list[str]:
    """List available prompt types.

    Returns:
        List of prompt type names
    """
    return ["upgrade", "security", "breaking", "quick", "toolchain"]


def get_agent_prompt() -> str:
    """Get the AI coding agent prompt template.

    Returns:
        The agent prompt template string
    """
    return AI_AGENT_PROMPT
