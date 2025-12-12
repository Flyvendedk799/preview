"""
Preview Timeout Handler - Enforces Timeout Limits for Preview Generation

Ensures preview generation doesn't run indefinitely and provides timeout handling.
"""

import signal
import logging
from typing import Callable, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when preview generation exceeds timeout."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """
    Context manager that raises TimeoutError if operation exceeds timeout.
    
    Args:
        seconds: Timeout in seconds
        
    Yields:
        None
        
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Preview generation exceeded {seconds} second timeout")
    
    # Set up signal handler (Unix only)
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows doesn't support SIGALRM - use threading timeout instead
        import threading
        
        timeout_occurred = threading.Event()
        
        def timeout_thread():
            timeout_occurred.wait(seconds)
            if timeout_occurred.is_set():
                return
            timeout_occurred.set()
            logger.warning(f"Timeout occurred after {seconds} seconds")
        
        timer = threading.Timer(seconds, lambda: timeout_occurred.set())
        timer.start()
        
        try:
            yield
            timer.cancel()
        except Exception as e:
            timer.cancel()
            if timeout_occurred.is_set():
                raise TimeoutError(f"Preview generation exceeded {seconds} second timeout")
            raise


def with_timeout(timeout_seconds: int):
    """
    Decorator to enforce timeout on a function.
    
    Args:
        timeout_seconds: Timeout in seconds
        
    Returns:
        Decorated function that raises TimeoutError on timeout
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with timeout_context(timeout_seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator

