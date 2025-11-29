"""
Enhanced retry utilities with jitter, error classification, and circuit breaker integration.

IMPROVEMENTS OVER BASIC RETRY:
1. Jitter to prevent thundering herd
2. Error classification (transient vs permanent)
3. Circuit breaker integration
4. Detailed metrics and logging
5. Configurable per-operation policies
"""
import time
import random
import logging
from typing import Callable, TypeVar, Optional, Tuple, Type
from functools import wraps
from enum import Enum
from dataclasses import dataclass
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, InternalServerError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorType(str, Enum):
    """Classification of error types for retry decisions."""
    TRANSIENT = "transient"      # Temporary issues, worth retrying (e.g., rate limits, timeouts)
    PERMANENT = "permanent"      # Permanent issues, don't retry (e.g., invalid input, auth)
    UNKNOWN = "unknown"          # Unknown error, use conservative retry


# =============================================================================
# ERROR CLASSIFICATION
# =============================================================================

@dataclass
class ErrorClassification:
    """Result of error classification."""
    error_type: ErrorType
    should_retry: bool
    reason: str


def classify_openai_error(exception: Exception) -> ErrorClassification:
    """
    Classify OpenAI errors for retry decisions.

    Args:
        exception: The exception to classify

    Returns:
        ErrorClassification with retry decision
    """
    # Rate limit errors - definitely retry (transient)
    if isinstance(exception, RateLimitError):
        return ErrorClassification(
            error_type=ErrorType.TRANSIENT,
            should_retry=True,
            reason="OpenAI rate limit - will retry with backoff"
        )

    # Timeout errors - retry (transient)
    if isinstance(exception, APITimeoutError):
        return ErrorClassification(
            error_type=ErrorType.TRANSIENT,
            should_retry=True,
            reason="OpenAI timeout - will retry"
        )

    # Connection errors - retry (transient)
    if isinstance(exception, APIConnectionError):
        return ErrorClassification(
            error_type=ErrorType.TRANSIENT,
            should_retry=True,
            reason="OpenAI connection error - will retry"
        )

    # Internal server errors - retry (transient)
    if isinstance(exception, InternalServerError):
        return ErrorClassification(
            error_type=ErrorType.TRANSIENT,
            should_retry=True,
            reason="OpenAI internal server error - will retry"
        )

    # Check error message for common patterns
    error_msg = str(exception).lower()

    # Authentication/authorization errors - don't retry (permanent)
    if any(keyword in error_msg for keyword in ['authentication', 'unauthorized', 'invalid api key', 'forbidden']):
        return ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            reason="Authentication error - won't retry"
        )

    # Invalid request errors - don't retry (permanent)
    if any(keyword in error_msg for keyword in ['invalid request', 'bad request', 'validation error']):
        return ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            reason="Invalid request - won't retry"
        )

    # Model not found - don't retry (permanent)
    if 'model not found' in error_msg or 'does not exist' in error_msg:
        return ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            reason="Model not found - won't retry"
        )

    # Default: treat as transient and retry conservatively
    return ErrorClassification(
        error_type=ErrorType.UNKNOWN,
        should_retry=True,
        reason="Unknown error - will retry conservatively"
    )


def classify_error(exception: Exception, retry_on: Tuple[Type[Exception], ...]) -> ErrorClassification:
    """
    Classify any error for retry decisions.

    Args:
        exception: The exception to classify
        retry_on: Tuple of exception types that are retryable

    Returns:
        ErrorClassification with retry decision
    """
    # First check if it's an OpenAI error (specific classification)
    try:
        from openai import OpenAIError
        if isinstance(exception, OpenAIError):
            return classify_openai_error(exception)
    except ImportError:
        pass

    # Check if exception type is in retry_on list
    if isinstance(exception, retry_on):
        return ErrorClassification(
            error_type=ErrorType.TRANSIENT,
            should_retry=True,
            reason=f"Exception type {type(exception).__name__} is retryable"
        )

    # Default: don't retry unknown exceptions
    return ErrorClassification(
        error_type=ErrorType.PERMANENT,
        should_retry=False,
        reason=f"Exception type {type(exception).__name__} is not in retry list"
    )


# =============================================================================
# BACKOFF STRATEGIES
# =============================================================================

def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    Calculate delay with exponential backoff and optional jitter.

    Jitter helps prevent thundering herd problem when many requests
    retry simultaneously.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential growth
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    # Calculate exponential delay
    delay = base_delay * (exponential_base ** attempt)
    delay = min(delay, max_delay)

    # Add jitter: randomize between 0% and 100% of calculated delay
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)  # Between 50% and 100%

    return delay


# =============================================================================
# ENHANCED RETRY DECORATORS
# =============================================================================

def enhanced_sync_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker: Optional[str] = None
):
    """
    Enhanced synchronous retry decorator with jitter and error classification.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exception types to retry on
        circuit_breaker: Name of circuit breaker to use (optional)

    Example:
        @enhanced_sync_retry(
            max_attempts=3,
            jitter=True,
            retry_on=(RateLimitError, APITimeoutError),
            circuit_breaker="openai"
        )
        def call_openai_api():
            return client.chat.completions.create(...)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    # If circuit breaker is specified, check it
                    if circuit_breaker:
                        from backend.services.circuit_breaker import get_circuit_breaker
                        cb = get_circuit_breaker(circuit_breaker)
                        return cb.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Classify error
                    classification = classify_error(e, retry_on)

                    # Log the error classification
                    logger.info(
                        f"Error classified for {func.__name__}: {classification.reason}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "error_type": classification.error_type.value,
                            "should_retry": classification.should_retry,
                            "exception_type": type(e).__name__,
                            "exception_message": str(e)[:200]
                        }
                    )

                    # If error is permanent, don't retry
                    if not classification.should_retry:
                        logger.warning(
                            f"Permanent error detected for {func.__name__}, not retrying: {str(e)[:200]}"
                        )
                        raise

                    # If this is the last attempt, raise
                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}: {str(e)[:200]}"
                        )
                        raise

                    # Calculate delay with jitter
                    delay = exponential_backoff_with_jitter(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter
                    )

                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s (jitter={'on' if jitter else 'off'}): {str(e)[:200]}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay_seconds": delay,
                            "jitter_enabled": jitter,
                            "error_type": classification.error_type.value
                        }
                    )

                    time.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise Exception(f"Unexpected retry failure for {func.__name__}")

        return wrapper
    return decorator


def enhanced_async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker: Optional[str] = None
):
    """
    Enhanced asynchronous retry decorator with jitter and error classification.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_on: Tuple of exception types to retry on
        circuit_breaker: Name of circuit breaker to use (optional)

    Example:
        @enhanced_async_retry(
            max_attempts=3,
            jitter=True,
            retry_on=(RateLimitError, APITimeoutError),
            circuit_breaker="openai"
        )
        async def call_openai_api():
            return await async_client.chat.completions.create(...)
    """
    import asyncio

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    # Note: Circuit breaker is sync, so we can't use it directly in async
                    # For async, consider using async circuit breaker implementation
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Classify error
                    classification = classify_error(e, retry_on)

                    # Log the error classification
                    logger.info(
                        f"Error classified for {func.__name__}: {classification.reason}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "error_type": classification.error_type.value,
                            "should_retry": classification.should_retry,
                            "exception_type": type(e).__name__,
                            "exception_message": str(e)[:200]
                        }
                    )

                    # If error is permanent, don't retry
                    if not classification.should_retry:
                        logger.warning(
                            f"Permanent error detected for {func.__name__}, not retrying: {str(e)[:200]}"
                        )
                        raise

                    # If this is the last attempt, raise
                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}: {str(e)[:200]}"
                        )
                        raise

                    # Calculate delay with jitter
                    delay = exponential_backoff_with_jitter(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter
                    )

                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s (jitter={'on' if jitter else 'off'}): {str(e)[:200]}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay_seconds": delay,
                            "jitter_enabled": jitter,
                            "error_type": classification.error_type.value
                        }
                    )

                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise Exception(f"Unexpected retry failure for {func.__name__}")

        return wrapper
    return decorator
