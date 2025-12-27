"""Interactive guide module for depswiz.

This module provides three interaction paradigms:
1. TUI Dashboard - Real-time Textual-based terminal UI
2. Smart Wizard - Step-by-step InquirerPy-powered decision trees
3. Conversational Chat - Natural language interface powered by Claude Code

Usage:
    depswiz guide [path] [--mode dashboard|wizard|chat]
"""

from depswiz.guide.context import ContextManager, ProjectContext
from depswiz.guide.state import GuideMode, GuideState

__all__ = [
    "ContextManager",
    "GuideMode",
    "GuideState",
    "ProjectContext",
]
