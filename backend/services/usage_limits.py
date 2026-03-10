"""
Usage limits & rate limiting for MyMetaView 4.0 (P9).

Per-tenant limits; rate limiting; quota enforcement.
Builds on P3 (Batch API) and P10 (Auth). Uses IP as tenant key until P10 lands.

Configurable via env:
- BATCH_JOBS_PER_HOUR: Max batch jobs per tenant per hour (default 20)
- BATCH_URLS_PER_JOB_MAX: Max URLs per batch (default 50, also in schema)
- BATCH_QUEUE_MAX_DEPTH: Reject new jobs when queue depth exceeds this (default 200)
"""
import os
import logging
from typing import Tuple, Optional
from backend.queue.queue_connection import get_redis_connection
from backend.services.rate_limiter import get_rate_limit_key_for_ip
from rq import Queue

logger = logging.getLogger(__name__)

# Configurable limits (env overrides)
BATCH_JOBS_PER_HOUR = int(os.getenv("BATCH_JOBS_PER_HOUR", "20"))
BATCH_URLS_PER_JOB_MAX = int(os.getenv("BATCH_URLS_PER_JOB_MAX", "50"))
BATCH_QUEUE_MAX_DEPTH = int(os.getenv("BATCH_QUEUE_MAX_DEPTH", "200"))

RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour
RATE_LIMIT_KEY_PREFIX = "batch_jobs"


def get_tenant_key_from_ip(ip: str) -> str:
    """Tenant key for rate limiting. When P10 (Auth) lands, use tenant_id from API key."""
    return get_rate_limit_key_for_ip(ip, RATE_LIMIT_KEY_PREFIX)


def check_batch_job_limit(tenant_key: str) -> Tuple[bool, Optional[int]]:
    """
    Check if tenant can submit a new batch job (jobs/hour limit).

    Returns:
        (allowed, retry_after_seconds): If not allowed, retry_after is seconds until limit resets.
    """
    try:
        redis_client = get_redis_connection()
        key = f"rate_limit:{tenant_key}"
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, RATE_LIMIT_WINDOW_SECONDS)

        if current > BATCH_JOBS_PER_HOUR:
            ttl = redis_client.ttl(key)
            retry_after = max(1, ttl) if ttl > 0 else 60
            logger.warning(
                f"Batch job limit exceeded for {tenant_key}: {current}/{BATCH_JOBS_PER_HOUR}"
            )
            return (False, retry_after)
        return (True, None)
    except Exception as e:
        logger.error(f"Usage limit check failed for {tenant_key}: {e}", exc_info=True)
        return (True, None)  # Fail open


def get_queue_depth() -> int:
    """Return current preview_generation queue depth (queued + started jobs)."""
    try:
        from backend.queue.queue_connection import get_rq_redis_connection
        redis_conn = get_rq_redis_connection()
        queue = Queue("preview_generation", connection=redis_conn)
        return len(queue)
    except Exception as e:
        logger.warning(f"Could not get queue depth: {e}")
        return 0


def check_queue_backpressure() -> Tuple[bool, Optional[int]]:
    """
    Reject new jobs when queue is overloaded (backpressure).

    Returns:
        (allowed, retry_after_seconds): If not allowed, suggest retry after 60s.
    """
    depth = get_queue_depth()
    if depth >= BATCH_QUEUE_MAX_DEPTH:
        logger.warning(f"Queue backpressure: depth={depth} >= max={BATCH_QUEUE_MAX_DEPTH}")
        return (False, 60)
    return (True, None)
