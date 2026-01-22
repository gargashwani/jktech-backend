"""
Logging Decorators for automatic try-catch logging
"""

import functools
import traceback
from typing import Callable, Any

from app.core.logging import get_logger


def log_exceptions(logger_name: str = "app", log_args: bool = False):
    """
    Decorator to automatically log exceptions with try-catch
    
    Usage:
        @log_exceptions()
        def my_function():
            # code that might raise exceptions
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            try:
                if log_args:
                    logger.debug(
                        f"Calling {func.__name__}",
                        context={"args": str(args), "kwargs": str(kwargs)},
                    )
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}",
                    e,
                    context={
                        "function": func.__name__,
                        "args": str(args) if log_args else "hidden",
                        "kwargs": str(kwargs) if log_args else "hidden",
                    },
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            try:
                if log_args:
                    logger.debug(
                        f"Calling {func.__name__}",
                        context={"args": str(args), "kwargs": str(kwargs)},
                    )
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}",
                    e,
                    context={
                        "function": func.__name__,
                        "args": str(args) if log_args else "hidden",
                        "kwargs": str(kwargs) if log_args else "hidden",
                    },
                )
                raise

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
