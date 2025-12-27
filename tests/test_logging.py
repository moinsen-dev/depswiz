"""Tests for the logging module."""

import logging

from depswiz.core.logging import (
    LOGGER_NAME,
    LogLevel,
    debug,
    error,
    get_logger,
    info,
    setup_logging,
    warning,
)


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_level_values(self) -> None:
        """Test that log levels have correct values."""
        assert LogLevel.DEBUG == logging.DEBUG
        assert LogLevel.VERBOSE == logging.INFO
        assert LogLevel.NORMAL == logging.WARNING
        assert LogLevel.QUIET > logging.WARNING

    def test_log_level_ordering(self) -> None:
        """Test that log levels are ordered correctly."""
        assert LogLevel.DEBUG < LogLevel.VERBOSE
        assert LogLevel.VERBOSE < LogLevel.NORMAL
        assert LogLevel.NORMAL < LogLevel.QUIET


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_returns_logger(self) -> None:
        """Test that setup_logging returns a logger."""
        logger = setup_logging(LogLevel.NORMAL)
        assert logger is not None
        assert logger.name == LOGGER_NAME

    def test_setup_logging_sets_level(self) -> None:
        """Test that setup_logging sets the correct level."""
        logger = setup_logging(LogLevel.DEBUG)
        assert logger.level == LogLevel.DEBUG

        logger = setup_logging(LogLevel.VERBOSE)
        assert logger.level == LogLevel.VERBOSE

        logger = setup_logging(LogLevel.QUIET)
        assert logger.level == LogLevel.QUIET

    def test_setup_logging_clears_existing_handlers(self) -> None:
        """Test that setup_logging clears existing handlers."""
        # Setup once
        logger = setup_logging(LogLevel.NORMAL)
        initial_handlers = len(logger.handlers)

        # Setup again
        logger = setup_logging(LogLevel.DEBUG)
        assert len(logger.handlers) == initial_handlers

    def test_setup_logging_rich_output(self) -> None:
        """Test setup_logging with rich output enabled."""
        logger = setup_logging(LogLevel.NORMAL, rich_output=True)
        assert len(logger.handlers) > 0

    def test_setup_logging_plain_output(self) -> None:
        """Test setup_logging with plain output."""
        logger = setup_logging(LogLevel.NORMAL, rich_output=False)
        assert len(logger.handlers) > 0


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_no_name(self) -> None:
        """Test get_logger without name returns root logger."""
        logger = get_logger()
        assert logger.name == LOGGER_NAME

    def test_get_logger_with_name(self) -> None:
        """Test get_logger with name returns child logger."""
        logger = get_logger("test.module")
        assert logger.name == f"{LOGGER_NAME}.test.module"

    def test_get_logger_hierarchy(self) -> None:
        """Test that child loggers inherit from parent."""
        parent = get_logger()
        child = get_logger("child")
        assert child.parent is not None


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_debug_function(self) -> None:
        """Test debug convenience function."""
        # Should not raise
        debug("Test debug message")

    def test_info_function(self) -> None:
        """Test info convenience function."""
        # Should not raise
        info("Test info message")

    def test_warning_function(self) -> None:
        """Test warning convenience function."""
        # Should not raise
        warning("Test warning message")

    def test_error_function(self) -> None:
        """Test error convenience function."""
        # Should not raise
        error("Test error message")

    def test_convenience_functions_with_args(self) -> None:
        """Test convenience functions with format arguments."""
        # Should not raise
        debug("Test %s with %d args", "message", 2)
        info("Test %s", "info")
        warning("Count: %d", 42)
        error("Error: %s", "test error")
