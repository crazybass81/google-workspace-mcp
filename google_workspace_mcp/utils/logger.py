"""Logging configuration for Google Workspace MCP Server."""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Setup logger with consistent formatting.

    Args:
        name: Logger name
        level: Logging level (defaults to INFO)

    Returns:
        Configured logger instance
    """
    if level is None:
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler - MUST use stderr for MCP stdio servers
    # Writing to stdout corrupts JSON-RPC protocol messages
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


# Default logger for the application
default_logger = setup_logger('google_workspace_mcp')
