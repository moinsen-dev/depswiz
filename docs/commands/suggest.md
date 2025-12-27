# depswiz suggest

Get AI-powered upgrade suggestions and dependency analysis using Claude Code.

## Usage

```bash
depswiz suggest [OPTIONS] [PATH]
```

## Requirements

This command requires [Claude Code](https://claude.ai/code) to be installed:

```bash
# Install Claude Code
brew install claude-code

# Or via npm
npm install -g @anthropic-ai/claude-code
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | Project directory | Current directory |

## Options

| Option | Description |
|--------|-------------|
| `--focus`, `-f` | Analysis focus: upgrade, security, breaking, quick, toolchain |
| `--timeout`, `-t` | Timeout in seconds (default: 300) |
| `--raw` | Output raw response without formatting |
| `--prompt`, `-p` | Generate an AI coding agent prompt file (no Claude required) |
| `--prompt-output`, `-po` | Output path for the prompt file |
| `--markdown`, `-m` | Output Claude's analysis to a markdown file |

## Focus Modes

| Focus | Description |
|-------|-------------|
| `upgrade` | Full upgrade strategy with priority ordering (default) |
| `security` | Focus on security vulnerabilities and fixes |
| `quick` | Quick health summary with top priorities |
| `toolchain` | Analyze development tools alongside dependencies |

## Examples

### Full Upgrade Strategy

```bash
# Comprehensive upgrade analysis
depswiz suggest
```

Claude Code will:
1. Analyze all manifest files
2. Check for outdated dependencies
3. Look up changelogs and breaking changes
4. Provide prioritized upgrade recommendations

### Security Focus

```bash
# Focus on security vulnerabilities
depswiz suggest --focus security
```

Provides:
- Known CVEs in dependencies
- Severity ratings
- Safe upgrade paths
- Immediate vs. planned remediation

### Quick Health Check

```bash
# Fast summary of project health
depswiz suggest --focus quick
```

Returns:
- Overall dependency health score
- Top 3-5 priorities
- Quick wins vs. major efforts

### Toolchain Analysis

```bash
# Include development tools in analysis
depswiz suggest --focus toolchain
```

Analyzes both:
- Package dependencies
- Development tools (Node, Python, Rust, etc.)

### Generate AI Agent Prompt

```bash
# Generate a prompt file for any AI coding agent (no Claude required)
depswiz suggest --prompt

# Specify custom output path
depswiz suggest --prompt --prompt-output ./prompts/update-deps.md
```

This generates a comprehensive markdown prompt file that can be used with:
- Claude Code
- Cursor
- Aider
- GitHub Copilot
- Any other AI coding assistant

The prompt includes:
- Structured update strategy with priorities
- Commands for each package ecosystem
- Step-by-step execution instructions
- Project-specific context

### Save Analysis to Markdown

```bash
# Save Claude's analysis to a file
depswiz suggest --markdown report.md

# Combine with focus mode
depswiz suggest --focus security --markdown security-report.md
```

This runs Claude's analysis and saves the output as a properly formatted markdown file, useful for:
- Documentation
- Sharing with team members
- Tracking upgrade decisions over time
- CI/CD artifacts

## Output Example

```markdown
## depswiz Upgrade Strategy

### Priority 1: Security Updates (Immediate)

| Package | Current | Target | Reason |
|---------|---------|--------|--------|
| requests | 2.31.0 | 2.32.0 | CVE-2024-35195 (SSRF) |

**Action:** Update immediately. No breaking changes expected.

### Priority 2: Minor Updates (This Sprint)

| Package | Current | Target | Risk |
|---------|---------|--------|------|
| httpx | 0.27.0 | 0.28.1 | Low |
| rich | 13.9.0 | 13.9.4 | Low |

**Action:** Bundle together, run tests.

### Priority 3: Major Updates (Plan Carefully)

| Package | Current | Target | Breaking Changes |
|---------|---------|--------|------------------|
| typer | 0.15.0 | 1.0.0 | API changes in callback system |

**Action:** Review changelog, allocate time for migration.

### Recommendations

1. Start with security updates - they're urgent and low-risk
2. Group patch updates for efficiency
3. Schedule major updates with proper testing time
4. Consider pinning transitive dependencies after updates
```

## How It Works

1. **depswiz invokes Claude Code** with your project context
2. **Claude Code explores** your manifest files (pyproject.toml, package.json, etc.)
3. **Claude analyzes** version requirements, lockfiles, and changelogs
4. **Claude provides** prioritized, actionable recommendations

## Prompt Templates

depswiz uses carefully crafted prompts for each focus mode:

### Upgrade Focus
Analyzes dependencies and provides priority-ordered upgrade strategy with breaking change warnings and batch recommendations.

### Security Focus
Audits dependencies for CVEs and security advisories, prioritizing critical fixes with safe upgrade paths.

### Quick Focus
Provides rapid health assessment with top priorities and overall project dependency score.

### Toolchain Focus
Extends analysis to include development tools, ensuring your entire development environment is current.

## Configuration

Configure Claude integration in `depswiz.toml`:

```toml
[claude]
enabled = true
timeout_seconds = 300
```

## Tips

1. **Run regularly** - Weekly suggest checks catch issues early
2. **Use security focus in CI** - Integrate security checks in pipelines
3. **Combine with update** - Use `depswiz update --ai-suggest` for guided updates
4. **Review before applying** - AI suggestions are recommendations, not commands

## Troubleshooting

### Claude Code not found

```
Claude Code not found.
Install from: https://claude.ai/cli
```

**Solution:** Install Claude Code and ensure it's in your PATH.

### Timeout errors

```
Claude timed out after 300 seconds
```

**Solution:** Increase timeout with `--timeout 600` for large projects.

### Permission issues

Claude Code requires certain permissions. Run:

```bash
claude --help
```

to verify installation.

## See Also

- [depswiz check](check.md) - Check for updates
- [depswiz audit](audit.md) - Security scanning
- [depswiz tools](tools.md) - Development tools checking
- [Claude Code Documentation](https://claude.ai/code)
