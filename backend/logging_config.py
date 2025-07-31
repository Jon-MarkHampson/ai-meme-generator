"""
Logging configuration utilities for the AI Meme Generator application.
Provides centralized log level management and formatting.
"""
import logging
from enum import StrEnum

# Detailed format for debug logging - includes file location and function name
LOG_FORMAT_DEBUG = "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"


class LogLevels(StrEnum):
    """
    Enumeration of available log levels for consistent configuration.
    Using StrEnum for easy string comparison and environment variable mapping.
    """
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    debug = "DEBUG"


def configure_logging(log_level: str = LogLevels.error):
    """
    Configure application-wide logging with the specified level.
    
    Args:
        log_level: Desired log level (INFO, WARN, ERROR, DEBUG)
                  Defaults to ERROR for production safety
    """
    log_level = str(log_level).upper()
    log_levels = [level.value for level in LogLevels]

    # Fallback to ERROR level if invalid level provided
    if log_level not in log_levels:
        logging.basicConfig(level=LogLevels.error)
        return

    # Use detailed format for debug mode to help with troubleshooting
    if log_level == LogLevels.debug:
        logging.basicConfig(level=log_level, format=LOG_FORMAT_DEBUG)
        return

    # Standard format for other log levels
    logging.basicConfig(level=log_level)
