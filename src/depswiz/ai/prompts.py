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


# Deprecation Fix Prompts
DEPRECATION_FIX_PROMPT = """
# Flutter/Dart Deprecation Fix Task

You are an AI coding agent tasked with fixing deprecated API usage in this Flutter/Dart project.

## Deprecations Found

{deprecation_list}

## Your Task

For each deprecation above:

1. **Understand the Context**: Read the file and understand how the deprecated API is being used
2. **Research the Replacement**: Look up the recommended replacement API in Flutter/Dart docs
3. **Apply the Fix**: Modify the code to use the new API
4. **Preserve Behavior**: Ensure the fix maintains the same functionality
5. **Handle Edge Cases**: Check for any type changes or parameter differences

## Common Flutter Deprecation Patterns

### Widget Replacements
- `FlatButton` → `TextButton`
- `RaisedButton` → `ElevatedButton`
- `OutlineButton` → `OutlinedButton`
- `ButtonTheme` → `ButtonStyle` + specific button themes
- `Scaffold.of(context).showSnackBar` → `ScaffoldMessenger.of(context).showSnackBar`

### State Management
- `MaterialState` → `WidgetState`
- `MaterialStateProperty` → `WidgetStateProperty`

### Text & Styling
- `TextStyle.headline1` (etc.) → Use `Theme.of(context).textTheme.displayLarge`
- `accentColor` → `colorScheme.secondary`
- `primaryColorBrightness` → Use `colorScheme.brightness`

### Navigation
- `Navigator.of(context).pushNamed` parameters changed
- `WillPopScope` → `PopScope` with `canPop` parameter

### Layout
- `RenderObjectElement.insertChildRenderObject` signature changes
- `Scrollbar` thumb visibility parameters

## Execution Steps

1. **Read each affected file** to understand the full context
2. **Apply fixes one file at a time** to maintain consistency
3. **Run `dart analyze`** after each fix to verify no new issues
4. **Run `flutter test`** if tests exist to ensure nothing breaks

## Output Requirements

For each fix applied, provide:
- File path and line numbers affected
- Before/after code snippet
- Explanation of why this replacement is correct
- Any caveats or additional changes needed

If a deprecation cannot be automatically fixed (requires architectural changes), explain why and provide guidance.

Begin by analyzing the deprecations and planning your fixes.
"""

DEPRECATION_SINGLE_FIX_PROMPT = """
# Fix Specific Deprecation

## Deprecation Details

- **File**: {file_path}
- **Line**: {line_number}
- **Column**: {column}
- **Message**: {message}
- **Rule**: {rule_id}
- **Suggested Replacement**: {replacement}

## Context

```dart
{code_context}
```

## Your Task

1. Read the file at {file_path}
2. Find the deprecated usage at line {line_number}
3. Replace it with the modern equivalent: {replacement}
4. Ensure the fix compiles and maintains the same behavior
5. Run `dart analyze {file_path}` to verify the fix

## Important

- Preserve all existing functionality
- Keep the same code style as the rest of the file
- If the replacement requires importing a new package, add the import
- If the fix affects related code (e.g., a callback signature), update that too

Apply the fix now.
"""

DEPRECATION_BATCH_FIX_PROMPT = """
# Batch Fix Deprecations by Type

## Deprecation Type: {deprecation_type}

All these deprecations are of the same type and can be fixed with a consistent pattern.

## Affected Locations

{locations}

## Replacement Pattern

**Old API**: {old_api}
**New API**: {new_api}
**Migration Guide**: {migration_link}

## Your Task

1. Apply the same fix pattern across all locations
2. Use find-and-replace where possible, but verify each change
3. Run `dart analyze` after completing all fixes
4. Report any locations that needed special handling

## Fix Pattern

```dart
// Before
{before_pattern}

// After
{after_pattern}
```

Apply this fix to all {count} locations.
"""


def get_deprecation_fix_prompt(deprecations: list[dict]) -> str:
    """Generate prompt for fixing multiple deprecations.

    Args:
        deprecations: List of deprecation dictionaries with keys:
            - file_path, line, column, message, rule_id, replacement

    Returns:
        Formatted prompt string for Claude
    """
    # Build the deprecation list
    lines = []
    for i, dep in enumerate(deprecations, 1):
        lines.append(f"### {i}. {dep.get('file_path', 'Unknown')}:{dep.get('line', '?')}")
        lines.append(f"- **Message**: {dep.get('message', 'No message')}")
        if dep.get('replacement'):
            lines.append(f"- **Suggested**: `{dep['replacement']}`")
        lines.append(f"- **Rule**: `{dep.get('rule_id', 'unknown')}`")
        lines.append("")

    deprecation_list = "\n".join(lines)
    return DEPRECATION_FIX_PROMPT.format(deprecation_list=deprecation_list)


def get_single_deprecation_fix_prompt(
    file_path: str,
    line_number: int,
    column: int,
    message: str,
    rule_id: str,
    replacement: str | None,
    code_context: str,
) -> str:
    """Generate prompt for fixing a single deprecation with context.

    Args:
        file_path: Path to the file
        line_number: Line number of the deprecation
        column: Column number
        message: Deprecation message
        rule_id: The analyzer rule ID
        replacement: Suggested replacement (if known)
        code_context: Surrounding code context

    Returns:
        Formatted prompt string for Claude
    """
    return DEPRECATION_SINGLE_FIX_PROMPT.format(
        file_path=file_path,
        line_number=line_number,
        column=column,
        message=message,
        rule_id=rule_id,
        replacement=replacement or "See migration guide",
        code_context=code_context,
    )


def get_batch_deprecation_fix_prompt(
    deprecation_type: str,
    locations: list[str],
    old_api: str,
    new_api: str,
    before_pattern: str,
    after_pattern: str,
    migration_link: str = "https://docs.flutter.dev/release/breaking-changes",
) -> str:
    """Generate prompt for batch fixing same-type deprecations.

    Args:
        deprecation_type: Type of deprecation (e.g., "FlatButton to TextButton")
        locations: List of file:line locations
        old_api: The deprecated API
        new_api: The replacement API
        before_pattern: Example code before fix
        after_pattern: Example code after fix
        migration_link: Link to migration guide

    Returns:
        Formatted prompt string for Claude
    """
    locations_text = "\n".join(f"- {loc}" for loc in locations)
    return DEPRECATION_BATCH_FIX_PROMPT.format(
        deprecation_type=deprecation_type,
        locations=locations_text,
        old_api=old_api,
        new_api=new_api,
        migration_link=migration_link,
        before_pattern=before_pattern,
        after_pattern=after_pattern,
        count=len(locations),
    )
