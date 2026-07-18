"""
logger.py - Simple logging setup for CodeMentor AI

Provides a get_logger function that creates loggers with
consistent formatting across the entire application.
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Create a logger with a given name.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")

    Args:
        name: Usually __name__ of the module using the logger

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)

    # Only add handler if logger doesn't have one yet
    # (prevents duplicate log lines)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Log to console (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Format: timestamp - module name - level - message
        log_format = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)

    return logger
