"""Redis connection helper for RQ job queue."""
import redis
from backend.core.config import settings


def get_redis_connection() -> redis.Redis:
    """
    Get Redis connection for RQ job queue.
    
    Returns:
        Redis client instance
    """
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

