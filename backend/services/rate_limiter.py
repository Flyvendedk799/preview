"""Redis-based rate limiting service."""
import logging
from typing import Optional
from backend.queue.queue_connection import get_redis_connection

logger = logging.getLogger(__name__)


def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """
    Check if a rate limit has been exceeded.
    
    Args:
        key: Unique identifier for the rate limit (e.g., "ip:1.2.3.4" or "org:123")
        limit: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        
    Returns:
        True if under limit (allowed), False if exceeded (blocked)
    """
    try:
        redis_client = get_redis_connection()
        rate_limit_key = f"rate_limit:{key}"
        
        # Increment counter
        current_count = redis_client.incr(rate_limit_key)
        
        # Set expiration on first request
        if current_count == 1:
            redis_client.expire(rate_limit_key, window_seconds)
        
        # Check if exceeded
        if current_count > limit:
            logger.warning(f"Rate limit exceeded for key: {key} ({current_count}/{limit})")
            return False
        
        return True
    except Exception as e:
        # If Redis fails, allow the request (fail open for availability)
        # Log the error but don't block legitimate users
        logger.error(f"Rate limiter error for key {key}: {e}", exc_info=True)
        return True  # Fail open


def get_rate_limit_key_for_ip(ip_address: str, prefix: str = "ip") -> str:
    """Generate rate limit key for IP address."""
    return f"{prefix}:{ip_address}"


def get_rate_limit_key_for_org(org_id: int) -> str:
    """Generate rate limit key for organization."""
    return f"org:{org_id}"


def get_rate_limit_key_for_ip_and_domain(ip_address: str, domain: str) -> str:
    """Generate rate limit key for IP + domain combination."""
    return f"ip_domain:{ip_address}:{domain}"

