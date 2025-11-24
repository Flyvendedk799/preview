"""Centralized retry utilities with exponential backoff."""
import time
import logging
import os
from typing import Callable, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Default max retries from env or fallback
DEFAULT_MAX_RETRIES = int(os.getenv("PREVIEW_MAX_RETRIES", "3"))

T = TypeVar('T')


def sync_retry(
    max_attempts: Optional[int] = None,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: tuple = (Exception,)
):
    """
    Decorator for synchronous functions with retry logic and exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (defaults to PREVIEW_MAX_RETRIES env var or 3)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: Tuple of exception types to retry on (defaults to all exceptions)
    """
    if max_attempts is None:
        max_attempts = DEFAULT_MAX_RETRIES
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                            f"after {delay:.2f}s: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        # Last attempt failed
                        logger.error(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}: {str(e)}"
                        )
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise Exception(f"Unexpected retry failure for {func.__name__}")
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: Optional[int] = None,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: tuple = (Exception,)
):
    """
    Decorator for async functions with retry logic and exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (defaults to PREVIEW_MAX_RETRIES env var or 3)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: Tuple of exception types to retry on (defaults to all exceptions)
    """
    import asyncio
    
    if max_attempts is None:
        max_attempts = DEFAULT_MAX_RETRIES
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                            f"after {delay:.2f}s: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        # Last attempt failed
                        logger.error(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}: {str(e)}"
                        )
                        raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise Exception(f"Unexpected retry failure for {func.__name__}")
        
        return wrapper
    return decorator

