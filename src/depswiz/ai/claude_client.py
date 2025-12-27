"""Claude Code CLI client for depswiz."""

import shutil
import subprocess
from pathlib import Path


class ClaudeError(Exception):
    """Error from Claude Code CLI."""

    pass


def find_claude_binary() -> Path | None:
    """Find Claude Code CLI binary in PATH.

    Returns:
        Path to the claude binary, or None if not found
    """
    binary = shutil.which("claude")
    if binary:
        return Path(binary)

    # Check common installation locations
    common_paths = [
        Path.home() / ".local" / "bin" / "claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".npm-global" / "bin" / "claude",
    ]

    for path in common_paths:
        if path.exists() and path.is_file():
            return path

    return None


def is_available() -> bool:
    """Check if Claude Code CLI is installed and accessible.

    Returns:
        True if Claude Code is available, False otherwise
    """
    return find_claude_binary() is not None


def run_claude(prompt: str, timeout: int = 300, cwd: Path | None = None) -> str:
    """Execute Claude Code CLI and return response.

    Args:
        prompt: The prompt to send to Claude
        timeout: Timeout in seconds (default: 300 = 5 minutes)
        cwd: Working directory to run Claude in (default: current directory)

    Returns:
        Claude's response text

    Raises:
        ClaudeError: If Claude CLI fails or returns an error
        subprocess.TimeoutExpired: If the command times out
        FileNotFoundError: If Claude binary is not found
    """
    binary = find_claude_binary()
    if not binary:
        raise FileNotFoundError("Claude Code CLI not found in PATH")

    cmd = [
        str(binary),
        "--dangerously-skip-permissions",
        "--verbose",
        "--print",
        prompt,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise ClaudeError(f"Claude returned error: {error_msg}")

        return result.stdout

    except subprocess.TimeoutExpired:
        raise
    except FileNotFoundError as err:
        raise ClaudeError(f"Could not execute Claude binary at {binary}") from err
    except Exception as e:
        raise ClaudeError(f"Error running Claude: {e}") from e
