"""Logger - Structured logging configuration for the swarm."""

from __future__ import annotations

import logging
import sys
from typing import Optional

import structlog


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the entire swarm.

    Uses structlog for structured/contextual logging with:
    - Colored console output (development)
    - JSON output (production)
    - Optional file output
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "websockets", "uvicorn.access"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event=40,
        )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up formatter for stdlib handler
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Apply to root handler
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
        )
        root_logger.addHandler(file_handler)


def get_logger(name: str = "") -> structlog.stdlib.BoundLogger:
    """Get a named structlog logger."""
    return structlog.get_logger(name)
