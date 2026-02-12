"""
Error handling utilities for consistent error management across the app.
"""
import logging
import functools
from typing import Callable, Any, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """Exception that should trigger a retry."""
    pass


class NonRetryableError(Exception):
    """Exception that should NOT trigger a retry."""
    pass


def with_retries(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (RetryableError, ConnectionError, TimeoutError)
):
    """
    Decorator to retry a function on specific exceptions.

    Args:
        max_attempts: Maximum number of attempts (including first try)
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiply delay by this on each retry
        exceptions: Tuple of exception types to retry on

    Example:
        @with_retries(max_attempts=3, delay_seconds=2.0)
        def fetch_data():
            # This will retry up to 3 times with 2s, 4s delays
            response = requests.get("https://api.example.com/data")
            if not response.ok:
                raise RetryableError("API returned non-200")
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay_seconds

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )

                except NonRetryableError as e:
                    # Don't retry, fail immediately
                    logger.error(f"{func.__name__} failed with non-retryable error: {e}")
                    raise

                except Exception as e:
                    # Unexpected exception - log and don't retry
                    logger.error(
                        f"{func.__name__} failed with unexpected error: {e}",
                        exc_info=True
                    )
                    raise

            # All retries exhausted
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    log_error: bool = True,
    reraise: bool = False,
    **kwargs
) -> Any:
    """
    Execute a function and return default value on error.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        default: Value to return on error
        log_error: Whether to log errors
        reraise: Whether to re-raise exceptions after logging
        **kwargs: Keyword arguments for func

    Returns:
        Result of func() or default value on error

    Example:
        # Returns [] if fetch_contracts() fails
        contracts = safe_execute(fetch_contracts, user_id=123, default=[])
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(
                f"safe_execute: {func.__name__} failed: {e}",
                exc_info=True
            )
        if reraise:
            raise
        return default


def log_errors(
    default: Any = None,
    log_level: str = "error",
    reraise: bool = True
):
    """
    Decorator to log errors from a function.

    Args:
        default: Default value to return on error (if not reraising)
        log_level: Log level for errors ("debug", "info", "warning", "error")
        reraise: Whether to re-raise exception after logging

    Example:
        @log_errors(default={}, reraise=False)
        def get_user_data(user_id):
            # Errors are logged and {} is returned
            return db.query(User).filter_by(id=user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, log_level.lower(), logger.error)
                log_func(
                    f"{func.__name__} failed: {e}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Truncate long args
                        "kwargs": str(kwargs)[:200],
                        "error_type": type(e).__name__,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                if reraise:
                    raise
                return default
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for error handling with automatic logging."""

    def __init__(
        self,
        operation: str,
        reraise: bool = True,
        default: Any = None,
        log_level: str = "error"
    ):
        """
        Args:
            operation: Description of the operation (for logging)
            reraise: Whether to re-raise exceptions
            default: Default value to return on error (if not reraising)
            log_level: Log level for errors
        """
        self.operation = operation
        self.reraise = reraise
        self.default = default
        self.log_level = log_level
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log_func = getattr(logger, self.log_level.lower(), logger.error)
            log_func(
                f"Error in {self.operation}: {exc_val}",
                exc_info=True
            )
            if not self.reraise:
                # Suppress exception and return default
                self.result = self.default
                return True  # Suppress exception
        return False  # Don't suppress


# Example usage:
#
# with ErrorContext("sending email", reraise=False, default=False) as ctx:
#     send_email(user.email, "welcome")
#     ctx.result = True
#
# if ctx.result:
#     logger.info("Email sent successfully")
