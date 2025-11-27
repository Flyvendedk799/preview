"""Redis connection helper for RQ job queue."""
import redis
from backend.core.config import settings


def get_redis_connection(decode_responses: bool = True) -> redis.Redis:
    """
    Get Redis connection.
    
    Args:
        decode_responses: If True, decode responses as UTF-8 strings.
                         If False, return raw bytes (needed for RQ job queue).
    
    Returns:
        Redis client instance
    """
    return redis.from_url(settings.REDIS_URL, decode_responses=decode_responses)


def get_rq_redis_connection() -> redis.Redis:
    """
    Get Redis connection specifically for RQ job queue.
    
    RQ requires decode_responses=False because it stores pickled Python objects
    (which can contain binary data) that cannot be decoded as UTF-8.
    
    Returns:
        Redis client instance with decode_responses=False
    """
    return redis.from_url(settings.REDIS_URL, decode_responses=False)

