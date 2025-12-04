"""
Structured logging configuration using Python logging module.

Provides JSON-formatted logs for observability and debugging.
Constitutional compliance: Principle V - Observability & Debuggability
"""

import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with JSON formatter.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create JSON formatter
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    formatter = jsonlogger.JsonFormatter(log_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)

    # Clear existing handlers and add JSON handler
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pybatfish").setLevel(logging.INFO)

    logging.info(
        "Structured logging initialized",
        extra={"log_level": log_level}
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
