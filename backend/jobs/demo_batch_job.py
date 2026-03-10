"""
Background job for batch demo preview generation (MyMetaView 4.0 P3).
Processes multiple URLs in a single job, stores results in Redis.
P8: Webhooks on job completion (success or partial).
"""
from typing import Dict, Any, List, Optional
from uuid import uuid4
import json
import logging
import time
import urllib.request
import urllib.error
from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
from backend.services.demo_quality_profiles import get_quality_profile
from backend.services.preview_cache import (
    get_redis_client,
    is_demo_cache_disabled,
)
from backend.queue.queue_connection import get_rq_redis_connection

logger = logging.getLogger(__name__)

BATCH_PREFIX = "demo:batch:"
BATCH_TTL = 86400  # 24 hours
WEBHOOK_RETRIES = 3
WEBHOOK_BACKOFF_BASE = 1.0  # seconds


def _get_batch_key(batch_id: str) -> str:
    return f"{BATCH_PREFIX}{batch_id}"


def get_batch_data(batch_id: str) -> Optional[Dict[str, Any]]:
    """Load batch status/results from Redis. Returns None if not found."""
    redis_client = get_redis_client()
    if not redis_client:
        return None
    key = _get_batch_key(batch_id)
    raw = redis_client.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _update_batch_status(
    redis_client,
    batch_id: str,
    status: str,
    total: int,
    completed: int,
    failed: int,
    results: List[Dict[str, Any]],
) -> None:
    """Persist batch status to Redis."""
    key = _get_batch_key(batch_id)
    data = {
        "status": status,
        "total": total,
        "completed": completed,
        "failed": failed,
        "results": results,
    }
    redis_client.setex(key, BATCH_TTL, json.dumps(data))


def _deliver_webhook(
    callback_url: str,
    payload: Dict[str, Any],
) -> None:
    """
    POST webhook payload to callback_url. Retries up to 3 times with exponential backoff.
    Logs failures; does not raise (best-effort delivery).
    """
    for attempt in range(WEBHOOK_RETRIES):
        try:
            req = urllib.request.Request(
                callback_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    logger.info(f"Webhook delivered to {callback_url[:60]}... (attempt {attempt + 1})")
                    return
                logger.warning(
                    f"Webhook returned HTTP {resp.status} from {callback_url[:50]}... (attempt {attempt + 1})"
                )
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
            logger.warning(
                f"Webhook delivery attempt {attempt + 1}/{WEBHOOK_RETRIES} failed: {e}"
            )
        if attempt < WEBHOOK_RETRIES - 1:
            time.sleep(WEBHOOK_BACKOFF_BASE * (2 ** attempt))


def generate_demo_batch_job(
    batch_id: str,
    urls: List[str],
    quality_mode: str = "balanced",
    callback_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background job to generate previews for multiple URLs.

    Args:
        batch_id: Unique batch job identifier
        urls: List of URLs to process
        quality_mode: Quality profile (fast, balanced, ultra)
        callback_url: Optional webhook URL. POST on completion (P8).

    Returns:
        Final batch status dict
    """
    redis_client = get_redis_client()
    if not redis_client:
        raise RuntimeError("Redis unavailable for batch job storage")

    total = len(urls)
    completed = 0
    failed = 0
    results: List[Dict[str, Any]] = []

    _update_batch_status(redis_client, batch_id, "running", total, 0, 0, [])

    cache_disabled = is_demo_cache_disabled()
    profile = get_quality_profile(quality_mode, urls[0] if urls else "")

    config = PreviewEngineConfig(
        is_demo=True,
        enable_brand_extraction=True,
        enable_ai_reasoning=True,
        enable_composited_image=True,
        enable_cache=not cache_disabled,
        enable_multi_agent=profile.multi_agent,
        enable_ui_element_extraction=profile.ui_extraction,
        quality_threshold=profile.threshold,
        max_quality_iterations=profile.iterations,
        allow_soft_pass=profile.allow_soft_pass,
        enforce_target_quality=profile.enforce_target_quality,
        min_soft_pass_overall=profile.min_soft_pass_overall,
        min_soft_pass_visual=profile.min_soft_pass_visual,
        min_soft_pass_fidelity=profile.min_soft_pass_fidelity,
    )
    engine = PreviewEngine(config)
    cache_prefix = f"demo:preview:v3:{quality_mode}:"

    for i, url_str in enumerate(urls):
        try:
            logger.info(f"Batch {batch_id}: processing URL {i+1}/{total}: {url_str[:60]}...")
            result = engine.generate(url_str, cache_key_prefix=cache_prefix)

            results.append({
                "url": url_str,
                "preview_image_url": result.composited_preview_image_url,
                "screenshot_url": result.screenshot_url,
                "title": result.title,
                "error": None,
            })
            completed += 1
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Batch {batch_id}: URL failed {url_str[:50]}...: {error_msg}")
            results.append({
                "url": url_str,
                "preview_image_url": None,
                "screenshot_url": None,
                "title": None,
                "error": error_msg[:500],
            })
            failed += 1

        _update_batch_status(
            redis_client, batch_id, "running", total, completed, failed, results
        )

    final_status = "completed" if failed == 0 else "completed"  # Partial success still "completed"
    if completed == 0:
        final_status = "failed"

    _update_batch_status(
        redis_client, batch_id, final_status, total, completed, failed, results
    )

    logger.info(f"Batch {batch_id}: done. completed={completed}, failed={failed}")

    # P8: Webhook on completion (success or partial)
    if callback_url:
        result_urls = [
            r.get("preview_image_url") or r.get("screenshot_url")
            for r in results
            if r.get("error") is None and (r.get("preview_image_url") or r.get("screenshot_url"))
        ]
        failed_urls = [r["url"] for r in results if r.get("error")]
        error_summary = f"{failed} of {total} URLs failed" if failed else None
        payload = {
            "job_id": batch_id,
            "status": final_status,
            "result_urls": result_urls,
            "failed_urls": failed_urls,
            "error_summary": error_summary,
        }
        _deliver_webhook(callback_url, payload)

    return {
        "job_id": batch_id,
        "status": final_status,
        "total": total,
        "completed": completed,
        "failed": failed,
        "results": results,
    }
