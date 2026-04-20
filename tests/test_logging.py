"""Tests for quantlab.logging."""

from __future__ import annotations

import logging

from quantlab.logging import configure_logging, get_logger


class TestLoggingSetup:
    """Verify structlog is wired up and producing structured output."""

    def test_get_logger_returns_usable_logger(self) -> None:
        logger = get_logger("test")
        # structlog returns a lazy proxy that resolves on first use.
        # Verify it has the methods we expect without depending on proxy vs bound class.
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "bind")

    def test_configure_logging_is_idempotent(self) -> None:
        # Calling multiple times must not raise or duplicate handlers
        configure_logging()
        configure_logging()
        configure_logging()

        root = logging.getLogger()
        # Exactly one handler after repeated configuration
        assert len(root.handlers) == 1

    def test_logger_accepts_structured_kwargs(self) -> None:
        """Structured logging is the whole point — key/value pairs must be preserved."""
        logger = get_logger("test_structured")
        # This must not raise — structlog accepts arbitrary kwargs
        logger.info("test_event", ticker="AAPL", price=150.25, retry_count=0)

    def test_noisy_loggers_are_quieted(self) -> None:
        configure_logging()
        for name in ("urllib3", "httpx", "asyncio"):
            assert logging.getLogger(name).level >= logging.WARNING
