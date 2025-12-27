"""Conversational chat mode for the guide module."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

if TYPE_CHECKING:
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideState


class MessageRole(Enum):
    """Role of a chat message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ACTION = "action"


@dataclass
class ChatMessage:
    """A single chat message."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class ChatSession:
    """Interactive chat session for the guide.

    Provides a conversational interface for:
    - Asking questions about dependencies
    - Getting AI-powered recommendations
    - Executing actions via natural language
    """

    SYSTEM_PROMPT = """You are depswiz guide, an intelligent dependency management assistant.
You help developers understand and manage their project's dependencies.

## Your Capabilities

1. **Analyze Dependencies**: You can examine package manifests and provide insights.
2. **Vulnerability Assessment**: You can explain CVEs and security advisories.
3. **License Compliance**: You can identify and explain license concerns.
4. **Upgrade Recommendations**: You can suggest safe upgrade paths.

## Context

{context}

## Response Guidelines

- Be conversational and helpful
- Provide actionable insights
- Use markdown formatting for clarity
- Keep responses focused and concise
- When suggesting actions, be clear about what will happen

If you need to execute an action, format it as:
[ACTION: command] - description of what this will do
"""

    def __init__(
        self,
        context_manager: ContextManager,
        state: GuideState,
        console: Console | None = None,
    ):
        """Initialize the chat session.

        Args:
            context_manager: Project context manager
            state: Shared guide state
            console: Rich console for output
        """
        self.context = context_manager
        self.state = state
        self.console = console or Console()
        self.history: list[ChatMessage] = []

    async def run(self) -> None:
        """Run the interactive chat loop."""
        self._show_welcome()

        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")

                if user_input.lower() in ("exit", "quit", "bye", "q"):
                    self.console.print("[dim]Goodbye![/dim]")
                    break

                if not user_input.strip():
                    continue

                # Add to history
                self.history.append(ChatMessage(role=MessageRole.USER, content=user_input))

                # Process and respond
                response = await self.process_message(user_input)

                # Display response
                self.console.print(
                    Panel(Markdown(response), title="depswiz", border_style="green")
                )

                # Add to history
                self.history.append(ChatMessage(role=MessageRole.ASSISTANT, content=response))

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use 'exit' to quit.[/dim]")
                continue

    async def process_message(self, message: str) -> str:
        """Process a user message and return response.

        Args:
            message: User's message

        Returns:
            Response string
        """
        # Add to context manager history
        self.context.add_message("user", message)

        # Check if Claude is available
        if self.state.ai_available:
            response = await self._get_claude_response(message)
        else:
            response = await self._get_fallback_response(message)

        # Add response to context manager
        self.context.add_message("assistant", response)

        return response

    async def _get_claude_response(self, message: str) -> str:
        """Get response from Claude Code CLI.

        Args:
            message: User's message

        Returns:
            Claude's response
        """
        from depswiz.ai.claude_client import run_claude

        # Build prompt with context
        context = self.context.build_prompt_context()
        system = self.SYSTEM_PROMPT.format(context=context)

        # Include recent conversation history
        history_text = ""
        for msg in self.history[-6:]:
            if msg.role == MessageRole.USER:
                history_text += f"User: {msg.content}\n"
            elif msg.role == MessageRole.ASSISTANT:
                content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
                history_text += f"Assistant: {content}\n"

        full_prompt = f"{system}\n\n{history_text}\nUser: {message}"

        try:
            # Run in executor to not block
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: run_claude(full_prompt, timeout=120, cwd=self.context.project_path),
            )
            return response
        except Exception as e:
            return f"I encountered an error: {e}\n\nTry rephrasing your question."

    async def _get_fallback_response(self, message: str) -> str:
        """Get rule-based fallback response when Claude unavailable.

        Args:
            message: User's message

        Returns:
            Fallback response
        """
        from depswiz.guide.fallback import FallbackHandler

        handler = FallbackHandler(self.context)
        result = await handler.handle(message)

        response = result.message
        if result.action_suggestion:
            response += f"\n\n*Tip: {result.action_suggestion}*"

        return response

    def _show_welcome(self) -> None:
        """Display welcome message."""
        self.console.print(
            Panel(
                "[bold]Welcome to depswiz guide[/bold]\n\n"
                "Ask me anything about your dependencies:\n"
                "  • 'What vulnerabilities do I have?'\n"
                "  • 'Should I update Flask?'\n"
                "  • 'Why is my project unhealthy?'\n"
                "  • 'Fix all critical vulnerabilities'\n\n"
                "[dim]Type 'exit' or 'quit' to leave.[/dim]",
                title="depswiz chat",
                border_style="cyan",
            )
        )
