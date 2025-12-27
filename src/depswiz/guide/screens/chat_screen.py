"""Chat screen for conversational AI interaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markdown import Markdown
from rich.panel import Panel
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Static

if TYPE_CHECKING:
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideState


class ChatScreen(ModalScreen):
    """Modal screen for chat-based interaction."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    CSS = """
    ChatScreen {
        align: center middle;
    }

    #chat-container {
        width: 90%;
        height: 90%;
        background: $surface;
        border: solid $primary;
    }

    #chat-header {
        dock: top;
        height: 3;
        padding: 1;
        background: $primary;
        text-align: center;
    }

    #chat-messages {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }

    #chat-input-container {
        dock: bottom;
        height: 3;
        padding: 0 1;
    }

    #chat-input {
        width: 100%;
    }

    .user-message {
        margin: 1 0;
        padding: 1;
        background: $primary-darken-2;
    }

    .assistant-message {
        margin: 1 0;
        padding: 1;
        background: $surface-darken-1;
    }
    """

    def __init__(
        self,
        state: GuideState,
        context_manager: ContextManager,
    ) -> None:
        """Initialize the chat screen.

        Args:
            state: Guide state
            context_manager: Project context manager
        """
        super().__init__()
        self.state = state
        self.context_manager = context_manager
        self.messages: list[tuple[str, str]] = []  # (role, content)

    def compose(self) -> ComposeResult:
        """Compose the chat screen layout."""
        with Vertical(id="chat-container"):
            yield Static("depswiz Chat - Ask anything about your dependencies", id="chat-header")
            yield ScrollableContainer(
                Static(self._render_welcome(), id="chat-welcome"),
                id="chat-messages",
            )
            with Vertical(id="chat-input-container"):
                yield Input(placeholder="Ask a question...", id="chat-input")
        yield Footer()

    def _render_welcome(self) -> Panel:
        """Render the welcome message."""
        content = """Welcome to depswiz chat!

Ask me anything about your project's dependencies:
- "What vulnerabilities do I have?"
- "Which packages need updating?"
- "Are my licenses compliant?"
- "How healthy is my project?"

Type your question below and press Enter."""

        return Panel(Markdown(content), title="Welcome", border_style="green")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input
        event.input.value = ""

        # Add user message to display
        messages_container = self.query_one("#chat-messages", ScrollableContainer)

        # Add user message
        user_widget = Static(
            Panel(user_input, title="You", border_style="blue"),
            classes="user-message",
        )
        messages_container.mount(user_widget)

        # Get response
        response = await self._get_response(user_input)

        # Add assistant message
        assistant_widget = Static(
            Panel(Markdown(response), title="depswiz", border_style="green"),
            classes="assistant-message",
        )
        messages_container.mount(assistant_widget)

        # Scroll to bottom
        messages_container.scroll_end()

    async def _get_response(self, user_input: str) -> str:
        """Get response for user input."""
        # Check for exit commands
        if user_input.lower() in ("exit", "quit", "bye"):
            self.app.pop_screen()
            return "Goodbye!"

        # Use fallback handler for now (can be extended with Claude)
        from depswiz.guide.fallback import FallbackHandler

        handler = FallbackHandler(self.context_manager)
        response = await handler.handle(user_input)

        result = response.message
        if response.action_suggestion:
            result += f"\n\n**Suggestion:** {response.action_suggestion}"

        return result

    def action_dismiss(self) -> None:
        """Close the screen."""
        self.app.pop_screen()
