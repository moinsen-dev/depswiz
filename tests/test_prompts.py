"""Tests for AI prompts module."""

import pytest

from depswiz.ai.prompts import (
    DEPRECATION_BATCH_FIX_PROMPT,
    DEPRECATION_FIX_PROMPT,
    DEPRECATION_SINGLE_FIX_PROMPT,
    get_batch_deprecation_fix_prompt,
    get_deprecation_fix_prompt,
    get_single_deprecation_fix_prompt,
    get_prompt,
    get_agent_prompt,
    list_prompts,
)


class TestGetPrompt:
    """Tests for get_prompt function."""

    def test_get_prompt_default(self) -> None:
        """Test get_prompt with default focus."""
        prompt = get_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_prompt_security(self) -> None:
        """Test get_prompt with security focus."""
        prompt = get_prompt("security")
        assert isinstance(prompt, str)
        assert "security" in prompt.lower() or "vulnerab" in prompt.lower()

    def test_get_prompt_unknown_focus(self) -> None:
        """Test get_prompt with unknown focus returns upgrade."""
        prompt = get_prompt("unknown_focus")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_list_prompts(self) -> None:
        """Test list_prompts returns available focuses."""
        prompts = list_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        assert "upgrade" in prompts or "security" in prompts


class TestAgentPrompt:
    """Tests for agent prompt function."""

    def test_get_agent_prompt(self) -> None:
        """Test agent prompt retrieval."""
        prompt = get_agent_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain agent instructions
        assert "AI" in prompt or "agent" in prompt.lower()


class TestDeprecationPrompts:
    """Tests for deprecation fix prompts."""

    def test_deprecation_fix_prompt_exists(self) -> None:
        """Test DEPRECATION_FIX_PROMPT is defined."""
        assert DEPRECATION_FIX_PROMPT is not None
        assert "{deprecation_list}" in DEPRECATION_FIX_PROMPT

    def test_deprecation_single_fix_prompt_exists(self) -> None:
        """Test DEPRECATION_SINGLE_FIX_PROMPT is defined."""
        assert DEPRECATION_SINGLE_FIX_PROMPT is not None
        assert "{file_path}" in DEPRECATION_SINGLE_FIX_PROMPT
        assert "{line_number}" in DEPRECATION_SINGLE_FIX_PROMPT

    def test_deprecation_batch_fix_prompt_exists(self) -> None:
        """Test DEPRECATION_BATCH_FIX_PROMPT is defined."""
        assert DEPRECATION_BATCH_FIX_PROMPT is not None
        assert "{deprecation_type}" in DEPRECATION_BATCH_FIX_PROMPT
        assert "{locations}" in DEPRECATION_BATCH_FIX_PROMPT

    def test_get_deprecation_fix_prompt_single(self) -> None:
        """Test deprecation fix prompt with single deprecation."""
        deprecations = [
            {
                "file_path": "lib/main.dart",
                "line": 42,
                "column": 12,
                "message": "FlatButton is deprecated",
                "rule_id": "deprecated_member_use",
                "replacement": "TextButton",
            }
        ]
        prompt = get_deprecation_fix_prompt(deprecations)

        assert "lib/main.dart:42" in prompt
        assert "FlatButton is deprecated" in prompt
        assert "TextButton" in prompt
        assert "deprecated_member_use" in prompt

    def test_get_deprecation_fix_prompt_multiple(self) -> None:
        """Test deprecation fix prompt with multiple deprecations."""
        deprecations = [
            {
                "file_path": "lib/a.dart",
                "line": 10,
                "message": "First deprecation",
                "rule_id": "rule1",
            },
            {
                "file_path": "lib/b.dart",
                "line": 20,
                "message": "Second deprecation",
                "rule_id": "rule2",
                "replacement": "newApi",
            },
            {
                "file_path": "lib/c.dart",
                "line": 30,
                "message": "Third deprecation",
                "rule_id": "rule3",
            },
        ]
        prompt = get_deprecation_fix_prompt(deprecations)

        assert "lib/a.dart:10" in prompt
        assert "lib/b.dart:20" in prompt
        assert "lib/c.dart:30" in prompt
        assert "First deprecation" in prompt
        assert "Second deprecation" in prompt
        assert "Third deprecation" in prompt
        assert "`newApi`" in prompt

    def test_get_deprecation_fix_prompt_empty(self) -> None:
        """Test deprecation fix prompt with empty list."""
        prompt = get_deprecation_fix_prompt([])
        assert isinstance(prompt, str)
        # Should still contain the template structure
        assert "Flutter/Dart" in prompt or "Deprecation" in prompt

    def test_get_deprecation_fix_prompt_missing_fields(self) -> None:
        """Test deprecation fix prompt handles missing fields gracefully."""
        deprecations = [
            {
                "message": "Only message provided",
            }
        ]
        prompt = get_deprecation_fix_prompt(deprecations)

        assert "Only message provided" in prompt
        assert "Unknown" in prompt  # Default for missing file_path
        assert "?" in prompt  # Default for missing line

    def test_get_single_deprecation_fix_prompt(self) -> None:
        """Test single deprecation fix prompt generation."""
        prompt = get_single_deprecation_fix_prompt(
            file_path="lib/widgets/button.dart",
            line_number=42,
            column=12,
            message="FlatButton is deprecated. Use TextButton instead.",
            rule_id="deprecated_member_use",
            replacement="TextButton",
            code_context="  FlatButton(\n    onPressed: () {},\n    child: Text('Click'),\n  )",
        )

        assert "lib/widgets/button.dart" in prompt
        assert "42" in prompt
        assert "12" in prompt
        assert "FlatButton is deprecated" in prompt
        assert "TextButton" in prompt
        assert "deprecated_member_use" in prompt
        assert "FlatButton(" in prompt

    def test_get_single_deprecation_fix_prompt_no_replacement(self) -> None:
        """Test single deprecation fix prompt with no replacement."""
        prompt = get_single_deprecation_fix_prompt(
            file_path="lib/main.dart",
            line_number=10,
            column=1,
            message="API is deprecated",
            rule_id="deprecated_member_use",
            replacement=None,
            code_context="oldApi();",
        )

        assert "lib/main.dart" in prompt
        assert "See migration guide" in prompt  # Default when no replacement

    def test_get_batch_deprecation_fix_prompt(self) -> None:
        """Test batch deprecation fix prompt generation."""
        prompt = get_batch_deprecation_fix_prompt(
            deprecation_type="FlatButton to TextButton",
            locations=[
                "lib/a.dart:10",
                "lib/b.dart:20",
                "lib/c.dart:30",
            ],
            old_api="FlatButton",
            new_api="TextButton",
            before_pattern="FlatButton(onPressed: ..., child: ...)",
            after_pattern="TextButton(onPressed: ..., child: ...)",
            migration_link="https://docs.flutter.dev/breaking-changes",
        )

        assert "FlatButton to TextButton" in prompt
        assert "lib/a.dart:10" in prompt
        assert "lib/b.dart:20" in prompt
        assert "lib/c.dart:30" in prompt
        assert "FlatButton" in prompt
        assert "TextButton" in prompt
        assert "https://docs.flutter.dev/breaking-changes" in prompt
        assert "3" in prompt  # count of locations

    def test_get_batch_deprecation_fix_prompt_default_link(self) -> None:
        """Test batch deprecation fix prompt with default migration link."""
        prompt = get_batch_deprecation_fix_prompt(
            deprecation_type="Test",
            locations=["file:1"],
            old_api="old",
            new_api="new",
            before_pattern="old()",
            after_pattern="new()",
        )

        # Should use default Flutter breaking-changes link
        assert "flutter.dev" in prompt or "breaking-changes" in prompt


class TestDeprecationPromptContent:
    """Tests for deprecation prompt content quality."""

    def test_deprecation_fix_prompt_has_instructions(self) -> None:
        """Test that DEPRECATION_FIX_PROMPT has proper instructions."""
        prompt = DEPRECATION_FIX_PROMPT

        # Should contain task instructions
        assert "Your Task" in prompt or "task" in prompt.lower()

        # Should mention reading files
        assert "Read" in prompt or "read" in prompt.lower()

        # Should mention verification
        assert "analyze" in prompt.lower() or "verify" in prompt.lower()

    def test_deprecation_fix_prompt_has_patterns(self) -> None:
        """Test that DEPRECATION_FIX_PROMPT has common patterns."""
        prompt = DEPRECATION_FIX_PROMPT

        # Should contain Flutter-specific patterns
        assert "FlatButton" in prompt
        assert "TextButton" in prompt
        assert "RaisedButton" in prompt or "ElevatedButton" in prompt

    def test_single_fix_prompt_has_context_section(self) -> None:
        """Test that DEPRECATION_SINGLE_FIX_PROMPT has context section."""
        prompt = DEPRECATION_SINGLE_FIX_PROMPT

        assert "Context" in prompt
        assert "{code_context}" in prompt
        assert "```dart" in prompt

    def test_batch_fix_prompt_has_pattern_section(self) -> None:
        """Test that DEPRECATION_BATCH_FIX_PROMPT has pattern section."""
        prompt = DEPRECATION_BATCH_FIX_PROMPT

        assert "Before" in prompt or "before" in prompt
        assert "After" in prompt or "after" in prompt
        assert "{before_pattern}" in prompt
        assert "{after_pattern}" in prompt
