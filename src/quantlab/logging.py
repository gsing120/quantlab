"""Structured logging setup for QuantLab.

All logging goes through structlog. Two output modes:
- "console": human-readable, colored, for development
- "json": machine-parseable, for production and queryable storage

Every log entry automatically includes timestamp, level, logger name, and
any structured context (key=value pairs) passed as kwargs.

Usage:
    from quantlab.logging import get_logger

    logger = get_logger(__name__)

    logger.info("event_name", ticker="AAPL", price=150.25)
    logger.error("polygon_api_failure", status_code=429, retry_in_s=60)

Every LLM call must log with at minimum:
    logger.info(
        "llm_call",
        model=settings.anthropic.opus_model,
        prompt_version="rates_lens_v1",
        input_tokens=...,
        output_tokens=...,
        latency_ms=...,
    )
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from quantlab.config import LogFormat, settings


def _drop_color_message_key(_: Any, __: str, event_dict: EventDict) -> EventDict:  # noqa: ANN401
    """Drop the 'color_message' key that uvicorn/starlette sometimes injects."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """Configure structlog and stdlib logging to work together.

    Idempotent: safe to call multiple times. Applies settings from
    `quantlab.config.settings` (log_level, log_format).
    """
    log_level = getattr(logging, settings.log_level.value)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        _drop_color_message_key,
    ]

    # Format-specific renderer
    if settings.log_format == LogFormat.JSON:
        renderer: Processor = structlog.processors.JSONRenderer()
        shared_processors.append(structlog.processors.format_exc_info)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())
        shared_processors.append(structlog.processors.format_exc_info)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Reset stdlib root handlers and wire through structlog
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(log_level)

    # Quiet some noisy third-party loggers by default
    for noisy in ("urllib3", "httpx", "asyncio", "ib_insync.wrapper", "ib_insync.client"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to the given name.

    Args:
        name: Logger name, typically `__name__` from the calling module.

    Returns:
        A structlog BoundLogger ready for structured logging calls.
    """
    return structlog.stdlib.get_logger(name)


# Configure on import so every module gets consistent logging without ceremony.
configure_logging()
