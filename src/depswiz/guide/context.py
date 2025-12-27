"""Project context management for the guide module."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from depswiz.core.config import Config
    from depswiz.core.models import AuditResult, CheckResult, LicenseResult
    from depswiz.tools.models import ToolsCheckResult


@dataclass
class ProjectContext:
    """Cached project context for conversation and analysis.

    This class holds scanned project data and provides methods for
    generating summaries suitable for AI prompts.
    """

    path: Path
    languages: list[str] = field(default_factory=list)
    check_result: CheckResult | None = None
    audit_result: AuditResult | None = None
    license_result: LicenseResult | None = None
    tools_result: ToolsCheckResult | None = None
    last_updated: datetime = field(default_factory=datetime.now)
    config: Config | None = None

    def is_stale(self, max_age_minutes: int = 5) -> bool:
        """Check if context needs refreshing.

        Args:
            max_age_minutes: Maximum age in minutes before considered stale

        Returns:
            True if context is older than max_age_minutes
        """
        age = datetime.now() - self.last_updated
        return age > timedelta(minutes=max_age_minutes)

    def to_summary(self) -> str:
        """Generate a text summary for prompt injection.

        Returns:
            Human-readable summary of project state
        """
        summary_parts = [
            f"Project: {self.path}",
            f"Languages: {', '.join(self.languages) or 'unknown'}",
        ]

        if self.check_result:
            outdated = len(self.check_result.outdated_packages)
            summary_parts.append(
                f"Dependencies: {self.check_result.total_packages} total, "
                f"{outdated} outdated"
            )

        if self.audit_result:
            summary_parts.append(
                f"Vulnerabilities: {len(self.audit_result.vulnerabilities)} total "
                f"({self.audit_result.critical_count} critical, "
                f"{self.audit_result.high_count} high)"
            )

        if self.license_result:
            summary_parts.append(
                f"Licenses: {len(self.license_result.violations)} violations, "
                f"{len(self.license_result.warnings)} warnings"
            )

        if self.tools_result:
            outdated_tools = sum(1 for t in self.tools_result.tools if t.has_update)
            summary_parts.append(
                f"Dev Tools: {len(self.tools_result.tools)} detected, "
                f"{outdated_tools} need updates"
            )

        return "\n".join(summary_parts)

    def to_detailed_json(self) -> str:
        """Export detailed context as JSON for Claude.

        Returns:
            JSON string with project details (limited to avoid token overflow)
        """
        data: dict[str, Any] = {
            "project_path": str(self.path),
            "languages": self.languages,
            "last_updated": self.last_updated.isoformat(),
        }

        if self.check_result:
            data["dependencies"] = {
                "total": self.check_result.total_packages,
                "outdated_count": len(self.check_result.outdated_packages),
                "outdated": [
                    {
                        "name": p.name,
                        "current": p.current_version,
                        "latest": p.latest_version,
                        "update_type": str(p.update_type) if p.update_type else None,
                        "language": p.language,
                    }
                    for p in self.check_result.outdated_packages[:20]  # Limit
                ],
            }

        if self.audit_result:
            data["vulnerabilities"] = {
                "total": len(self.audit_result.vulnerabilities),
                "by_severity": {
                    "critical": self.audit_result.critical_count,
                    "high": self.audit_result.high_count,
                    "medium": self.audit_result.medium_count,
                    "low": self.audit_result.low_count,
                },
                "items": [
                    {
                        "package": p.name,
                        "version": p.current_version,
                        "vuln_id": v.id,
                        "severity": str(v.severity),
                        "title": v.title,
                        "fixed_in": v.fixed_version,
                    }
                    for p, v in self.audit_result.vulnerabilities[:15]  # Limit
                ],
            }

        if self.license_result:
            data["licenses"] = {
                "violations": len(self.license_result.violations),
                "warnings": len(self.license_result.warnings),
            }

        return json.dumps(data, indent=2)


@dataclass
class ConversationMessage:
    """A single message in the conversation history."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """Manage project context and conversation history.

    This class handles:
    - Initial project scanning and context gathering
    - Refreshing scan data when stale
    - Maintaining conversation history for chat mode
    - Building prompts with context for Claude
    """

    def __init__(
        self,
        project_path: Path,
        config: Config | None = None,
        max_history: int = 20,
    ):
        """Initialize context manager.

        Args:
            project_path: Path to the project to analyze
            config: Optional depswiz configuration
            max_history: Maximum conversation messages to retain
        """
        self.project_path = project_path.resolve()
        self.config = config
        self.max_history = max_history
        self.project_context: ProjectContext | None = None
        self.conversation_history: list[ConversationMessage] = []

    async def initialize(self) -> None:
        """Gather initial project context.

        Detects languages and creates initial ProjectContext.
        """
        from depswiz.plugins import get_plugins_for_path

        plugins = get_plugins_for_path(self.project_path)
        languages = [p.name for p in plugins]

        self.project_context = ProjectContext(
            path=self.project_path,
            languages=languages,
            config=self.config,
        )

    async def refresh_check_context(self) -> None:
        """Refresh dependency check data."""
        from depswiz.core.scanner import scan_dependencies

        if self.project_context and self.config:
            self.project_context.check_result = await scan_dependencies(
                path=self.project_path,
                config=self.config,
            )
            self.project_context.last_updated = datetime.now()

    async def refresh_audit_context(self) -> None:
        """Refresh vulnerability audit data."""
        from depswiz.core.scanner import audit_packages

        if self.project_context and self.project_context.check_result and self.config:
            self.project_context.audit_result = await audit_packages(
                packages=self.project_context.check_result.packages,
                config=self.config,
            )
            self.project_context.last_updated = datetime.now()

    async def refresh_license_context(self) -> None:
        """Refresh license compliance data."""
        from depswiz.core.scanner import check_licenses

        if self.project_context and self.project_context.check_result and self.config:
            self.project_context.license_result = await check_licenses(
                packages=self.project_context.check_result.packages,
                config=self.config,
            )
            self.project_context.last_updated = datetime.now()

    async def refresh_all(self) -> None:
        """Refresh all context data."""
        await self.refresh_check_context()
        await self.refresh_audit_context()
        await self.refresh_license_context()

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dictionary
        """
        self.conversation_history.append(
            ConversationMessage(
                role=role,
                content=content,
                metadata=metadata or {},
            )
        )
        # Trim history if too long
        if len(self.conversation_history) > self.max_history:
            # Keep system messages and recent history
            system_msgs = [m for m in self.conversation_history if m.role == "system"]
            other_msgs = [m for m in self.conversation_history if m.role != "system"]
            keep_count = self.max_history - len(system_msgs)
            self.conversation_history = system_msgs + other_msgs[-keep_count:]

    def get_conversation_context(self) -> str:
        """Format conversation history for prompt.

        Returns:
            Formatted conversation history string
        """
        if not self.conversation_history:
            return ""

        lines = ["## Recent Conversation\n"]
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            if msg.role == "user":
                lines.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                # Truncate long assistant responses
                content = (
                    msg.content[:500] + "..."
                    if len(msg.content) > 500
                    else msg.content
                )
                lines.append(f"Assistant: {content}")

        return "\n".join(lines)

    def build_prompt_context(self) -> str:
        """Build full context for Claude prompt.

        Returns:
            Combined project and conversation context
        """
        parts = []

        if self.project_context:
            parts.append("## Project Context\n")
            parts.append(self.project_context.to_summary())
            parts.append("\n")

        conv_context = self.get_conversation_context()
        if conv_context:
            parts.append(conv_context)

        return "\n".join(parts)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
