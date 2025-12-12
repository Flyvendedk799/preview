"""
Error Recovery - Graceful Degradation System.

PHASE 2 IMPLEMENTATION:
Provides comprehensive error recovery for the preview generation pipeline.

Features:
- Timeout handling with configurable limits
- Graceful degradation at every stage
- Fallback chains for each component
- Contextual error logging
- Recovery strategies based on error type
"""

import logging
import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# ERROR TYPES
# =============================================================================

class ErrorType(str, Enum):
    """Types of errors that can occur in the pipeline."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    """Actions to take on error."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FAIL = "fail"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ErrorContext:
    """Context for an error occurrence."""
    error_type: ErrorType
    component: str
    operation: str
    message: str
    original_error: Optional[Exception] = None
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "component": self.component,
            "operation": self.operation,
            "message": self.message,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }


@dataclass
class RecoveryResult(Generic[T]):
    """Result of a recovery attempt."""
    success: bool
    value: Optional[T] = None
    action_taken: RecoveryAction = RecoveryAction.FALLBACK
    error_context: Optional[ErrorContext] = None
    fallback_used: bool = False
    warnings: list = field(default_factory=list)


# =============================================================================
# ERROR CLASSIFICATION
# =============================================================================

def classify_error(error: Exception) -> ErrorType:
    """
    Classify an exception into an error type.
    
    Args:
        error: Exception to classify
        
    Returns:
        ErrorType classification
    """
    error_str = str(error).lower()
    error_name = type(error).__name__.lower()
    
    # Timeout errors
    if any(x in error_str for x in ['timeout', 'timed out', 'deadline']):
        return ErrorType.TIMEOUT
    if 'timeout' in error_name:
        return ErrorType.TIMEOUT
    
    # Rate limit errors
    if any(x in error_str for x in ['429', 'rate limit', 'too many requests', 'quota']):
        return ErrorType.RATE_LIMIT
    
    # Network errors
    if any(x in error_str for x in ['connection', 'network', 'unreachable', 'dns', 'ssl']):
        return ErrorType.NETWORK
    if any(x in error_name for x in ['connection', 'url', 'http']):
        return ErrorType.NETWORK
    
    # API errors
    if any(x in error_str for x in ['401', '403', '500', '502', '503', 'unauthorized', 'forbidden']):
        return ErrorType.API_ERROR
    
    # Parse errors
    if any(x in error_str for x in ['json', 'parse', 'decode', 'syntax', 'invalid']):
        return ErrorType.PARSE_ERROR
    if any(x in error_name for x in ['json', 'parse', 'decode']):
        return ErrorType.PARSE_ERROR
    
    # Validation errors
    if any(x in error_str for x in ['validation', 'invalid', 'required', 'missing']):
        return ErrorType.VALIDATION_ERROR
    if 'validation' in error_name:
        return ErrorType.VALIDATION_ERROR
    
    # Resource errors
    if any(x in error_str for x in ['memory', 'disk', 'space', 'resource', 'file not found']):
        return ErrorType.RESOURCE_ERROR
    if any(x in error_name for x in ['file', 'io', 'os']):
        return ErrorType.RESOURCE_ERROR
    
    return ErrorType.UNKNOWN


def get_recovery_action(error_type: ErrorType, retry_count: int) -> RecoveryAction:
    """
    Determine recovery action based on error type and retry count.
    
    Args:
        error_type: Type of error
        retry_count: Number of retries already attempted
        
    Returns:
        Recommended recovery action
    """
    max_retries = {
        ErrorType.TIMEOUT: 2,
        ErrorType.RATE_LIMIT: 1,  # Wait then retry once
        ErrorType.NETWORK: 2,
        ErrorType.API_ERROR: 1,
        ErrorType.PARSE_ERROR: 0,  # No retry for parse errors
        ErrorType.VALIDATION_ERROR: 0,  # No retry for validation
        ErrorType.RESOURCE_ERROR: 0,  # No retry for resources
        ErrorType.UNKNOWN: 1
    }
    
    max_retry = max_retries.get(error_type, 1)
    
    if retry_count < max_retry:
        return RecoveryAction.RETRY
    elif error_type in [ErrorType.PARSE_ERROR, ErrorType.VALIDATION_ERROR]:
        return RecoveryAction.FALLBACK
    elif error_type == ErrorType.RESOURCE_ERROR:
        return RecoveryAction.FAIL
    else:
        return RecoveryAction.FALLBACK


# =============================================================================
# RECOVERY DECORATOR
# =============================================================================

def with_recovery(
    component: str,
    operation: str,
    fallback_value: Any = None,
    fallback_fn: Optional[Callable[..., Any]] = None,
    max_retries: int = 2,
    timeout: Optional[float] = None,
    log_errors: bool = True
):
    """
    Decorator for functions that should have error recovery.
    
    Args:
        component: Name of the component (e.g., "brand_extractor")
        operation: Name of the operation (e.g., "extract_logo")
        fallback_value: Static fallback value to return on failure
        fallback_fn: Function to call for fallback (receives original args)
        max_retries: Maximum number of retries
        timeout: Optional timeout in seconds
        log_errors: Whether to log errors
        
    Usage:
        @with_recovery("brand_extractor", "extract_logo", fallback_value=None)
        def extract_logo(screenshot_bytes):
            # ... extraction logic
            return logo
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> RecoveryResult:
            retry_count = 0
            last_error = None
            
            while retry_count <= max_retries:
                try:
                    # Execute with timeout if specified
                    if timeout:
                        import signal
                        
                        def timeout_handler(signum, frame):
                            raise TimeoutError(f"Operation timed out after {timeout}s")
                        
                        # Only set signal on Unix systems
                        try:
                            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                            signal.alarm(int(timeout))
                            try:
                                result = func(*args, **kwargs)
                            finally:
                                signal.alarm(0)
                                signal.signal(signal.SIGALRM, old_handler)
                        except (ValueError, AttributeError):
                            # signal.alarm not available (Windows)
                            result = func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    return RecoveryResult(
                        success=True,
                        value=result,
                        action_taken=RecoveryAction.RETRY if retry_count > 0 else RecoveryAction.SKIP,
                        warnings=[f"Succeeded after {retry_count} retries"] if retry_count > 0 else []
                    )
                    
                except Exception as e:
                    last_error = e
                    error_type = classify_error(e)
                    
                    error_ctx = ErrorContext(
                        error_type=error_type,
                        component=component,
                        operation=operation,
                        message=str(e),
                        original_error=e,
                        retry_count=retry_count
                    )
                    
                    if log_errors:
                        logger.warning(
                            f"⚠️ [{component}.{operation}] Error (attempt {retry_count + 1}): "
                            f"{error_type.value} - {str(e)[:100]}"
                        )
                    
                    action = get_recovery_action(error_type, retry_count)
                    
                    if action == RecoveryAction.RETRY:
                        retry_count += 1
                        # Exponential backoff for rate limits
                        if error_type == ErrorType.RATE_LIMIT:
                            wait_time = 2 ** retry_count
                            logger.info(f"Rate limited, waiting {wait_time}s before retry")
                            time.sleep(wait_time)
                        else:
                            time.sleep(0.5 * retry_count)  # Brief delay
                        continue
                    else:
                        break
            
            # All retries exhausted, use fallback
            error_ctx = ErrorContext(
                error_type=classify_error(last_error) if last_error else ErrorType.UNKNOWN,
                component=component,
                operation=operation,
                message=str(last_error) if last_error else "Unknown error",
                original_error=last_error,
                retry_count=retry_count
            )
            
            if log_errors:
                logger.error(
                    f"❌ [{component}.{operation}] Failed after {retry_count} retries, using fallback"
                )
            
            # Try fallback function first
            if fallback_fn:
                try:
                    fallback_result = fallback_fn(*args, **kwargs)
                    return RecoveryResult(
                        success=True,
                        value=fallback_result,
                        action_taken=RecoveryAction.FALLBACK,
                        error_context=error_ctx,
                        fallback_used=True,
                        warnings=[f"Used fallback after {retry_count} retries"]
                    )
                except Exception as fallback_error:
                    logger.warning(f"Fallback function also failed: {fallback_error}")
            
            # Return static fallback value
            return RecoveryResult(
                success=fallback_value is not None,
                value=fallback_value,
                action_taken=RecoveryAction.FALLBACK,
                error_context=error_ctx,
                fallback_used=True,
                warnings=[f"Used static fallback after {retry_count} retries"]
            )
        
        return wrapper
    return decorator


# =============================================================================
# FALLBACK CHAINS
# =============================================================================

class FallbackChain:
    """
    Chain of fallback functions to try in order.
    
    Usage:
        chain = FallbackChain("logo_extraction")
        chain.add(extract_with_ai, priority=1)
        chain.add(extract_from_html, priority=2)
        chain.add(return_default_logo, priority=3)
        
        result = chain.execute(screenshot_bytes, html_content)
    """
    
    def __init__(self, name: str):
        self.name = name
        self._handlers: list = []
    
    def add(
        self,
        handler: Callable,
        priority: int = 100,
        name: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """Add a handler to the chain."""
        handler_name = name or handler.__name__
        self._handlers.append({
            "handler": handler,
            "priority": priority,
            "name": handler_name,
            "timeout": timeout
        })
        # Sort by priority
        self._handlers.sort(key=lambda x: x["priority"])
    
    def execute(self, *args, **kwargs) -> RecoveryResult:
        """
        Execute the fallback chain.
        
        Tries each handler in priority order until one succeeds.
        """
        errors = []
        
        for handler_info in self._handlers:
            handler = handler_info["handler"]
            handler_name = handler_info["name"]
            
            try:
                logger.debug(f"Trying fallback handler: {handler_name}")
                result = handler(*args, **kwargs)
                
                if result is not None:
                    return RecoveryResult(
                        success=True,
                        value=result,
                        action_taken=RecoveryAction.FALLBACK,
                        fallback_used=handler_info["priority"] > 1,
                        warnings=[f"Succeeded with handler: {handler_name}"]
                    )
                    
            except Exception as e:
                logger.warning(f"Handler {handler_name} failed: {e}")
                errors.append((handler_name, e))
                continue
        
        # All handlers failed
        return RecoveryResult(
            success=False,
            value=None,
            action_taken=RecoveryAction.FAIL,
            error_context=ErrorContext(
                error_type=ErrorType.UNKNOWN,
                component=self.name,
                operation="fallback_chain",
                message=f"All {len(self._handlers)} handlers failed",
                metadata={"errors": [(n, str(e)) for n, e in errors]}
            ),
            warnings=[f"All handlers failed: {[n for n, _ in errors]}"]
        )


# =============================================================================
# GRACEFUL DEGRADATION HELPERS
# =============================================================================

def graceful_extract(
    primary_fn: Callable,
    fallback_fn: Callable,
    *args,
    component: str = "extraction",
    **kwargs
) -> Any:
    """
    Try primary extraction, fall back to secondary on failure.
    
    Args:
        primary_fn: Primary extraction function
        fallback_fn: Fallback extraction function
        *args: Arguments for both functions
        component: Component name for logging
        **kwargs: Keyword arguments for both functions
        
    Returns:
        Result from primary or fallback function
    """
    try:
        result = primary_fn(*args, **kwargs)
        if result is not None:
            return result
    except Exception as e:
        logger.warning(f"[{component}] Primary extraction failed: {e}")
    
    try:
        return fallback_fn(*args, **kwargs)
    except Exception as e:
        logger.error(f"[{component}] Fallback extraction also failed: {e}")
        return None


def safe_get(
    data: Dict[str, Any],
    *keys,
    default: Any = None
) -> Any:
    """
    Safely get nested values from a dictionary.
    
    Args:
        data: Dictionary to get value from
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Value at the nested key path, or default
        
    Usage:
        value = safe_get(response, "data", "user", "name", default="Unknown")
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, (list, tuple)) and isinstance(key, int):
            try:
                current = current[key]
            except IndexError:
                return default
        else:
            return default
        
        if current is None:
            return default
    
    return current


# =============================================================================
# TIMEOUT CONTEXT MANAGER
# =============================================================================

class TimeoutContext:
    """
    Context manager for operations that should timeout.
    
    Usage:
        with TimeoutContext(5.0, "extract_logo"):
            result = extract_logo(screenshot)
    """
    
    def __init__(self, timeout_seconds: float, operation: str = "operation"):
        self.timeout = timeout_seconds
        self.operation = operation
        self._old_handler = None
    
    def __enter__(self):
        import signal
        
        def handler(signum, frame):
            raise TimeoutError(f"{self.operation} timed out after {self.timeout}s")
        
        try:
            self._old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(self.timeout))
        except (ValueError, AttributeError):
            # signal.alarm not available on Windows
            pass
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import signal
        
        try:
            signal.alarm(0)
            if self._old_handler:
                signal.signal(signal.SIGALRM, self._old_handler)
        except (ValueError, AttributeError):
            pass
        
        return False  # Don't suppress exceptions

