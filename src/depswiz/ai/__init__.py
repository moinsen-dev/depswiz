"""AI integration module for depswiz."""

from depswiz.ai.claude_client import (
    is_available,
    find_claude_binary,
    run_claude,
    ClaudeError,
)
from depswiz.ai.prompts import get_prompt

__all__ = [
    "is_available",
    "find_claude_binary",
    "run_claude",
    "ClaudeError",
    "get_prompt",
]
