"""Logging configuration for depswiz."""

import logging
import sys
from enum import IntEnum

from rich.console import Console
from rich.logging import RichHandler

# Global console instance for consistent output
console = Console(stderr=True)

# Logger name prefix
LOGGER_NAME = "depswiz"


class LogLevel(IntEnum):
    """Log levels for depswiz."""

    QUIET = logging.WARNING + 10  # Only errors
    NORMAL = logging.WARNING  # Warnings and errors
    VERBOSE = logging.INFO  # Info, warnings, errors
    DEBUG = logging.DEBUG  # Everything


def setup_logging(
    level: LogLevel = LogLevel.NORMAL,
    *,
    rich_output: bool = True,
) -> logging.Logger:
    """Configure logging for depswiz.

    Args:
        level: The logging level to use
        rich_output: Whether to use Rich for formatted output

    Returns:
        The configured root logger for depswiz
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    handler: logging.Handler
    if rich_output:
        handler = RichHandler(
            console=console,
            show_time=False,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=level == LogLevel.DEBUG,
            markup=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(name)s: %(message)s"))

    handler.setLevel(level)
    logger.addHandler(handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger for a depswiz module.

    Args:
        name: Optional module name (will be prefixed with 'depswiz.')

    Returns:
        A logger instance

    Example:
        >>> logger = get_logger("plugins.python")
        >>> logger.warning("Could not parse version: %s", version)
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


# Convenience functions for quick logging
def debug(msg: str, *args, **kwargs) -> None:
    """Log a debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """Log an info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log a warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log an error message."""
    get_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    """Log an exception with traceback."""
    get_logger().exception(msg, *args, **kwargs)
