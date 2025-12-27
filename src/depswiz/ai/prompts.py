"""Prompt templates for Claude Code integration."""

UPGRADE_PROMPT = """
Analyze this project's dependencies and suggest an upgrade strategy.

Look at the project's manifest files (pyproject.toml, package.json, Cargo.toml, pubspec.yaml)
and determine which dependencies need updating.

For each outdated package, provide:
1. **Priority Order**: Which packages to update first and why
2. **Breaking Changes**: Warn about major version bumps with potential issues
3. **Batch Strategy**: Group packages that should be updated together
4. **Risk Assessment**: Rate the risk of each update (low/medium/high)
5. **Migration Tips**: Specific steps for major upgrades

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
Give me a quick summary of this project's dependency health:

1. How many dependencies are outdated?
2. Are there any security vulnerabilities?
3. What are the top 3 most urgent updates?

Be concise - just the key facts.
"""


def get_prompt(focus: str = "upgrade") -> str:
    """Get the appropriate prompt template.

    Args:
        focus: The focus area - "upgrade", "security", "breaking", or "quick"

    Returns:
        The prompt template string
    """
    prompts = {
        "upgrade": UPGRADE_PROMPT,
        "security": SECURITY_PROMPT,
        "breaking": BREAKING_CHANGES_PROMPT,
        "quick": QUICK_CHECK_PROMPT,
    }
    return prompts.get(focus, UPGRADE_PROMPT)


def list_prompts() -> list[str]:
    """List available prompt types.

    Returns:
        List of prompt type names
    """
    return ["upgrade", "security", "breaking", "quick"]
