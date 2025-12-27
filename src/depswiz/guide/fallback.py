"""Rule-based fallback handler when Claude is unavailable."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from depswiz.guide.context import ContextManager


@dataclass
class FallbackResponse:
    """A fallback response when Claude is unavailable."""

    message: str
    action_suggestion: str | None = None


class FallbackHandler:
    """Handle queries when Claude is unavailable.

    Uses pattern matching to provide helpful responses
    based on the user's question and project context.
    """

    def __init__(self, context_manager: ContextManager):
        """Initialize the fallback handler.

        Args:
            context_manager: Project context manager
        """
        self.context = context_manager
        self.patterns: list[tuple[re.Pattern, Callable[[str], FallbackResponse]]] = [
            (re.compile(r"vulnerabilit", re.I), self._handle_vulnerability_query),
            (re.compile(r"update|upgrade|outdated", re.I), self._handle_update_query),
            (re.compile(r"license", re.I), self._handle_license_query),
            (re.compile(r"health|status|overview", re.I), self._handle_health_query),
            (
                re.compile(r"(what|which|how many).*(package|depend)", re.I),
                self._handle_package_query,
            ),
            (re.compile(r"fix|repair|resolve", re.I), self._handle_fix_query),
            (re.compile(r"tool|python|node|rust|uv", re.I), self._handle_tools_query),
            (re.compile(r"sbom|bill of material", re.I), self._handle_sbom_query),
        ]

    async def handle(self, user_input: str) -> FallbackResponse:
        """Process user input and return appropriate fallback response.

        Args:
            user_input: User's message

        Returns:
            FallbackResponse with message and optional action suggestion
        """
        for pattern, handler in self.patterns:
            if pattern.search(user_input):
                return await handler(user_input)

        return self._default_response()

    async def _handle_vulnerability_query(self, query: str) -> FallbackResponse:
        """Handle vulnerability-related queries."""
        ctx = self.context.project_context
        if not ctx or not ctx.audit_result:
            return FallbackResponse(
                message="I don't have vulnerability data yet. Let me scan first.",
                action_suggestion="Run `depswiz audit` to scan for vulnerabilities.",
            )

        result = ctx.audit_result
        total = len(result.vulnerabilities)

        if total == 0:
            return FallbackResponse(
                message="**Good news!** No known vulnerabilities were found in your dependencies.",
            )

        msg = f"""Found **{total}** vulnerabilities:

| Severity | Count |
|----------|-------|
| Critical | {result.critical_count} |
| High | {result.high_count} |
| Medium | {result.medium_count} |
| Low | {result.low_count} |

"""
        if result.critical_count > 0:
            msg += "**Urgent:** Critical vulnerabilities need immediate attention."
        elif result.high_count > 0:
            msg += "**Recommendation:** Address high severity issues soon."

        return FallbackResponse(
            message=msg,
            action_suggestion="Run `depswiz audit --fix` to see remediation steps.",
        )

    async def _handle_update_query(self, query: str) -> FallbackResponse:
        """Handle update/upgrade queries."""
        ctx = self.context.project_context
        if not ctx or not ctx.check_result:
            return FallbackResponse(
                message="I don't have dependency data yet.",
                action_suggestion="Run `depswiz check` to scan for updates.",
            )

        result = ctx.check_result
        outdated = result.outdated_packages

        if not outdated:
            return FallbackResponse(
                message="**All your dependencies are up to date!**",
            )

        # Count by type
        from depswiz.core.models import UpdateType

        major = sum(1 for p in outdated if p.update_type == UpdateType.MAJOR)
        minor = sum(1 for p in outdated if p.update_type == UpdateType.MINOR)
        patch = sum(1 for p in outdated if p.update_type == UpdateType.PATCH)

        msg = f"""Found **{len(outdated)}** outdated packages:

| Type | Count |
|------|-------|
| Major | {major} |
| Minor | {minor} |
| Patch | {patch} |

**Top outdated packages:**
"""
        for pkg in outdated[:5]:
            msg += f"- {pkg.name}: {pkg.current_version} → {pkg.latest_version}\n"

        return FallbackResponse(
            message=msg,
            action_suggestion="Run `depswiz update --dry-run` to preview updates.",
        )

    async def _handle_license_query(self, query: str) -> FallbackResponse:
        """Handle license-related queries."""
        ctx = self.context.project_context
        if not ctx or not ctx.license_result:
            return FallbackResponse(
                message="I don't have license data yet.",
                action_suggestion="Run `depswiz licenses` to check compliance.",
            )

        result = ctx.license_result
        violations = len(result.violations)
        warnings = len(result.warnings)

        if violations == 0 and warnings == 0:
            return FallbackResponse(
                message="**All licenses are compliant!** No issues found.",
            )

        msg = f"""Found license concerns:

- **{violations}** violations
- **{warnings}** warnings

"""
        if violations > 0:
            msg += "Violations need attention - licenses may conflict with your project.\n"

        return FallbackResponse(
            message=msg,
            action_suggestion="Run `depswiz licenses --summary` for details.",
        )

    async def _handle_health_query(self, query: str) -> FallbackResponse:
        """Handle general health/status queries."""
        ctx = self.context.project_context
        if not ctx:
            return FallbackResponse(
                message="I need to scan your project first.",
                action_suggestion="Run `depswiz guide` to start the analysis.",
            )

        msg = f"""**Project Health Overview**

Project: `{ctx.path.name}`
Languages: {', '.join(ctx.languages) or 'detecting...'}
"""
        if ctx.check_result:
            total = ctx.check_result.total_packages
            outdated = len(ctx.check_result.outdated_packages)
            msg += f"Dependencies: {total} total, {outdated} outdated\n"

        if ctx.audit_result:
            msg += f"Vulnerabilities: {len(ctx.audit_result.vulnerabilities)} found\n"

        if ctx.license_result:
            violations = len(ctx.license_result.violations)
            if violations > 0:
                msg += f"License Issues: {violations} violations\n"

        return FallbackResponse(
            message=msg,
            action_suggestion="For detailed analysis, enable Claude Code for AI-powered insights.",
        )

    async def _handle_package_query(self, query: str) -> FallbackResponse:
        """Handle package count/listing queries."""
        ctx = self.context.project_context
        if not ctx or not ctx.check_result:
            return FallbackResponse(
                message="I need to scan your project first.",
                action_suggestion="Run `depswiz check` to see all dependencies.",
            )

        total = ctx.check_result.total_packages
        langs = len(ctx.languages)
        return FallbackResponse(
            message=f"Your project has **{total}** direct dependencies across {langs} language(s).",
        )

    async def _handle_fix_query(self, query: str) -> FallbackResponse:
        """Handle fix/repair queries."""
        return FallbackResponse(
            message="I recommend using wizard mode for guided remediation.",
            action_suggestion="Run `depswiz guide --mode wizard` for step-by-step fixes.",
        )

    async def _handle_tools_query(self, query: str) -> FallbackResponse:
        """Handle development tools queries."""
        ctx = self.context.project_context
        if not ctx or not ctx.tools_result:
            return FallbackResponse(
                message="I don't have tools data yet.",
                action_suggestion="Run `depswiz tools` to check development tools.",
            )

        tools = ctx.tools_result.tools
        outdated = sum(1 for t in tools if t.has_update)

        msg = f"Found **{len(tools)}** development tools.\n\n"

        if outdated > 0:
            msg += f"**{outdated}** tools have updates available.\n\n"
            for tool in tools:
                if tool.has_update:
                    msg += f"- {tool.name}: {tool.current_version} → {tool.latest_version}\n"
        else:
            msg += "All tools are up to date!"

        return FallbackResponse(message=msg)

    async def _handle_sbom_query(self, query: str) -> FallbackResponse:
        """Handle SBOM-related queries."""
        return FallbackResponse(
            message="I can generate a Software Bill of Materials (SBOM) for your project.\n\n"
            "Supported formats:\n"
            "- **CycloneDX** (recommended)\n"
            "- **SPDX**",
            action_suggestion="Run `depswiz sbom --format cyclonedx -o sbom.json` to generate.",
        )

    def _default_response(self) -> FallbackResponse:
        """Return default response when no pattern matches."""
        return FallbackResponse(
            message="""I can help you with:

- **Vulnerabilities**: "What vulnerabilities do I have?"
- **Updates**: "What packages need updating?"
- **Health**: "How healthy is my project?"
- **Licenses**: "Check my license compliance"
- **Tools**: "What dev tools need updates?"
- **SBOM**: "Generate a software bill of materials"

For more detailed AI analysis, make sure Claude Code is installed.""",
        )
