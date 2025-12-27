"""Interactive guide command for depswiz.

This module provides the main entry point for the guide feature,
supporting three interaction modes:
- Dashboard: Full TUI with Textual
- Wizard: Step-by-step InquirerPy prompts
- Chat: Conversational Claude interface
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideState

app = typer.Typer(invoke_without_command=True)
console = Console()


class GuideModeCLI(str, Enum):
    """CLI mode options for the guide command."""

    dashboard = "dashboard"
    wizard = "wizard"
    chat = "chat"


class GuideFocus(str, Enum):
    """Focus area options for the guide."""

    all = "all"
    security = "security"
    updates = "updates"
    licenses = "licenses"


@app.callback(invoke_without_command=True)
def guide(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    mode: GuideModeCLI = typer.Option(
        GuideModeCLI.dashboard,
        "--mode",
        "-m",
        help="Interaction mode: dashboard (TUI), wizard (step-by-step), or chat",
    ),
    focus: GuideFocus = typer.Option(
        GuideFocus.all,
        "--focus",
        "-f",
        help="Focus on specific area",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch for file changes and auto-refresh",
    ),
    quick: bool = typer.Option(
        False,
        "--quick",
        "-q",
        help="Quick mode: use smart defaults, minimal prompts",
    ),
    skip_ai: bool = typer.Option(
        False,
        "--skip-ai",
        help="Skip AI recommendations even if Claude is available",
    ),
    ask: str | None = typer.Option(
        None,
        "--ask",
        "-a",
        help="Ask a single question (non-interactive mode)",
    ),
) -> None:
    """Launch the interactive dependency guide.

    The guide provides three interaction paradigms:

    \b
    DASHBOARD MODE (default):
      Full TUI with real-time panels showing:
      - Health score (0-100)
      - Vulnerability status
      - Outdated dependencies
      - License compliance
      - Development tools

    \b
    WIZARD MODE:
      Step-by-step guided experience with:
      - Project analysis
      - Prioritized recommendations
      - Interactive decision tree
      - Action confirmation and execution

    \b
    CHAT MODE:
      Conversational AI interface:
      - Natural language questions
      - Context-aware responses
      - Action execution via commands

    \b
    Examples:
      depswiz guide                        # Launch dashboard
      depswiz guide --mode wizard          # Step-by-step wizard
      depswiz guide --mode chat            # Conversational mode
      depswiz guide --focus security       # Focus on vulnerabilities
      depswiz guide --ask "What CVEs?"     # Single question
    """
    import asyncio

    from depswiz.ai.claude_client import is_available as claude_available
    from depswiz.core.config import load_config
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideMode, GuideState

    project_path = path.resolve()
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, project_path)

    # Check AI availability
    has_claude = claude_available() and not skip_ai

    if not has_claude:
        console.print(
            Panel(
                "[yellow]Claude Code is not available.[/yellow]\n\n"
                "AI-powered features will use fallback mode.\n"
                "For full AI capabilities, install Claude Code:\n"
                "[link=https://claude.ai/code]https://claude.ai/code[/link]",
                title="AI Features Limited",
                border_style="yellow",
            )
        )

    # Initialize state and context
    state = GuideState(ai_available=has_claude)
    context_manager = ContextManager(project_path, config)

    # Map CLI mode to internal mode
    mode_map = {
        GuideModeCLI.dashboard: GuideMode.DASHBOARD,
        GuideModeCLI.wizard: GuideMode.WIZARD,
        GuideModeCLI.chat: GuideMode.CHAT,
    }
    state.current_mode = mode_map[mode]

    # Handle single question mode
    if ask:
        asyncio.run(_handle_single_question(ask, context_manager, state, has_claude))
        return

    # Launch appropriate mode
    if mode == GuideModeCLI.dashboard:
        _launch_dashboard(project_path, config, state, watch)
    elif mode == GuideModeCLI.wizard:
        # Wizard uses InquirerPy which requires its own event loop
        # So we run the async initialization first, then run the sync wizard
        asyncio.run(context_manager.initialize())
        _launch_wizard_sync(context_manager, state, quick, focus)
    elif mode == GuideModeCLI.chat:
        asyncio.run(_launch_chat(context_manager, state))


def _launch_dashboard(
    project_path: Path,
    config: Any,
    state: GuideState,
    watch: bool,
) -> None:
    """Launch the TUI dashboard mode."""
    from depswiz.guide.app import GuideApp

    guide_app = GuideApp(
        path=project_path,
        config=config,
        state=state,
        watch=watch,
    )
    guide_app.run()


def _launch_wizard_sync(
    context_manager: ContextManager,
    state: GuideState,
    quick: bool,
    focus: GuideFocus,
) -> None:
    """Launch the wizard mode (synchronous).

    The wizard uses InquirerPy which manages its own async event loop,
    so we must run the wizard synchronously to avoid nested event loops.
    """
    from depswiz.guide.engine import WizardEngine

    engine = WizardEngine(
        context_manager=context_manager,
        state=state,
        console=console,
        quick_mode=quick,
        focus=focus.value if focus != GuideFocus.all else None,
    )

    try:
        engine.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Wizard cancelled.[/yellow]")


async def _launch_chat(
    context_manager: ContextManager,
    state: GuideState,
) -> None:
    """Launch the chat mode."""
    from depswiz.guide.chat import ChatSession

    # Initialize context
    await context_manager.initialize()

    session = ChatSession(
        context_manager=context_manager,
        state=state,
        console=console,
    )

    try:
        await session.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")


async def _handle_single_question(
    question: str,
    context_manager: ContextManager,
    state: GuideState,
    has_claude: bool,
) -> None:
    """Handle a single question in non-interactive mode."""
    from depswiz.guide.chat import ChatSession

    # Initialize context
    await context_manager.initialize()

    session = ChatSession(
        context_manager=context_manager,
        state=state,
        console=console,
    )

    response = await session.process_message(question)
    console.print(Panel(response, title="depswiz", border_style="green"))
