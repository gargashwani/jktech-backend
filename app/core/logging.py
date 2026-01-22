"""
Laravel-like Logging System
Creates log files in storage/logs directory with date-based rotation
"""

import logging
import os
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from config import settings


class LaravelLogger:
    """Laravel-like logger that writes to storage/logs directory"""

    def __init__(self, name: str = "app"):
        self.name = name
        self.log_dir = Path("storage/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file and console handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Daily log file (Laravel style: laravel-2024-01-22.log)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{self.name}-{today}.log"

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter (Laravel-like format)
        formatter = logging.Formatter(
            "[%(asctime)s] %(name)s.%(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _log(self, level: str, message: str, context: Optional[dict] = None):
        """Internal logging method"""
        try:
            log_message = message
            if context:
                import json
                log_message += f" | Context: {json.dumps(context, default=str)}"

            getattr(self.logger, level.lower())(log_message)
        except Exception as e:
            # Fallback to print if logging fails
            print(f"Logging error: {e} | Original message: {message}")

    def info(self, message: str, context: Optional[dict] = None):
        """Log info message"""
        self._log("info", message, context)

    def error(self, message: str, context: Optional[dict] = None, exc_info: bool = False):
        """Log error message"""
        try:
            if exc_info:
                self.logger.error(message, exc_info=True)
            else:
                self._log("error", message, context)
        except Exception as e:
            print(f"Error logging failed: {e} | Original: {message}")

    def warning(self, message: str, context: Optional[dict] = None):
        """Log warning message"""
        self._log("warning", message, context)

    def debug(self, message: str, context: Optional[dict] = None):
        """Log debug message"""
        self._log("debug", message, context)

    def critical(self, message: str, context: Optional[dict] = None):
        """Log critical message"""
        self._log("critical", message, context)

    def exception(self, message: str, exc: Exception, context: Optional[dict] = None):
        """Log exception with full traceback"""
        try:
            error_context = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            if context:
                error_context.update(context)

            self.logger.error(f"{message} | {error_context}", exc_info=True)
        except Exception as e:
            print(f"Exception logging failed: {e} | Original: {message}")


# Global logger instances
_loggers: dict[str, LaravelLogger] = {}


def get_logger(name: str = "app") -> LaravelLogger:
    """Get or create a logger instance"""
    if name not in _loggers:
        _loggers[name] = LaravelLogger(name)
    return _loggers[name]


def log_info(message: str, context: Optional[dict] = None, channel: str = "app"):
    """Convenience function for info logging"""
    try:
        logger = get_logger(channel)
        logger.info(message, context)
    except Exception as e:
        print(f"Log info failed: {e}")


def log_error(
    message: str,
    context: Optional[dict] = None,
    exc: Optional[Exception] = None,
    channel: str = "app",
):
    """Convenience function for error logging"""
    try:
        logger = get_logger(channel)
        if exc:
            logger.exception(message, exc, context)
        else:
            logger.error(message, context)
    except Exception as e:
        print(f"Log error failed: {e}")


def log_warning(message: str, context: Optional[dict] = None, channel: str = "app"):
    """Convenience function for warning logging"""
    try:
        logger = get_logger(channel)
        logger.warning(message, context)
    except Exception as e:
        print(f"Log warning failed: {e}")


def log_debug(message: str, context: Optional[dict] = None, channel: str = "app"):
    """Convenience function for debug logging"""
    try:
        logger = get_logger(channel)
        logger.debug(message, context)
    except Exception as e:
        print(f"Log debug failed: {e}")
