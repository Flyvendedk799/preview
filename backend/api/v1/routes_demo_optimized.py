"""
Optimized demo route with parallel processing and enhanced brand extraction.

PERFORMANCE IMPROVEMENTS:
1. Parallel screenshot upload + brand extraction
2. Efficient HTML + screenshot capture in single browser session
3. Concurrent R2 uploads
4. Enhanced brand element extraction (logo, colors, hero image)

ENHANCEMENTS:
1. Logo extraction from page
2. Hero image extraction
3. Better brand color detection
4. Improved og:image generation with brand elements

ASYNC PROCESSING:
- Added async job endpoints to work around Railway's 60-second load balancer timeout
- Jobs run in background workers, client polls for status
"""
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from backend.db.session import get_db
from backend.services.rate_limiter import check_rate_limit, get_rate_limit_key_for_ip
from backend.services.activity_logger import get_client_ip, log_activity, get_authenticated_user_id
from backend.utils.url_sanitizer import validate_url_security
from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
from backend.services.demo_quality_profiles import (
    get_cache_prefix_for_mode,
    get_quality_profile,
    resolve_quality_mode,
)
from backend.services.preview_cache import (
    generate_cache_key,
    get_redis_client,
    CacheConfig,
    is_demo_cache_disabled
)
from backend.queue.queue_connection import get_rq_redis_connection
from backend.jobs.demo_preview_job import generate_demo_preview_job
from backend.schemas.demo_schemas import (
    DemoPreviewRequest,
    DemoPreviewResponse,
    DemoJobRequest,
    DemoJobResponse,
    DemoJobStatusResponse,
    ContextItem,
    CredibilityItem,
    BrandElements,
    DesignDNA,
    LayoutBlueprint,
)
from rq import Queue
from rq.job import Job
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo-v2", tags=["demo"])


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=DemoJobResponse)
def create_demo_job(
    request_data: DemoJobRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create an async background job to generate demo preview.
    
    This endpoint returns immediately with a job_id to avoid Railway's 60-second
    load balancer timeout. The client should poll /demo-v2/jobs/{job_id}/status
    to get status updates and the final result.
    
    Rate limited to prevent abuse.
    """
    url_str = str(request_data.url)
    user_id = get_authenticated_user_id(request, db)
    client_ip = get_client_ip(request)

    # Rate limiting
    rate_limit_key = get_rate_limit_key_for_ip(client_ip, "demo_job_v2")
    if not check_rate_limit(rate_limit_key, limit=10, window_seconds=3600):
        log_activity(
            db, user_id=user_id, action="demo.preview.job_created",
            request=request,
            metadata={"url": url_str, "outcome": "rate_limited", "client_ip": client_ip},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

    # Validate URL
    try:
        validate_url_security(url_str)
    except ValueError as e:
        log_activity(
            db, user_id=user_id, action="demo.preview.job_created",
            request=request,
            metadata={"url": url_str, "outcome": "invalid_url", "error": str(e), "client_ip": client_ip},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Enqueue job
    try:
        redis_conn = get_rq_redis_connection()
        queue = Queue("preview_generation", connection=redis_conn)
        job = queue.enqueue(
            generate_demo_preview_job,
            url_str,
            request_data.quality_mode,
            job_timeout='15m'
        )

        logger.info(f"Demo job created: {job.id} for URL: {url_str[:50]}...")

        # Single consolidated log entry for the entire job creation flow
        log_activity(
            db, user_id=user_id, action="demo.preview.job_created",
            request=request,
            metadata={
                "url": url_str,
                "outcome": "queued",
                "job_id": job.id,
                "client_ip": client_ip,
                "quality_mode": request_data.quality_mode,
            },
        )

        return DemoJobResponse(
            job_id=job.id,
            status="queued",
            message="Preview generation started. Poll /demo-v2/jobs/{job_id}/status for updates."
        )
    except Exception as e:
        logger.error(f"Failed to create demo job: {str(e)}", exc_info=True)
        log_activity(
            db, user_id=user_id, action="demo.preview.job_created",
            request=request,
            metadata={"url": url_str, "outcome": "enqueue_failed", "error": str(e), "client_ip": client_ip},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/jobs/{job_id}/status", response_model=DemoJobStatusResponse)
def get_demo_job_status(
    job_id: str,
    request: Request
):
    """
    Get the status of a demo preview generation job.
    
    Returns:
        - status: "queued", "started", "finished", or "failed"
        - result: Preview data if finished, None otherwise
        - error: Error message if failed, None otherwise
        - progress: Estimated progress (0.0 to 1.0) if available
    """
    try:
        redis_conn = get_rq_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)
        
        # Refresh job status to get latest state (important for fast jobs)
        job.refresh()
        
        status_map = {
            'queued': 'queued',
            'started': 'started',
            'finished': 'finished',
            'failed': 'failed',
        }
        
        job_status = status_map.get(job.get_status(), 'unknown')
        
        # Get progress from job meta if available, otherwise estimate based on status
        progress = None
        message = None
        
        try:
            job_meta = job.get_meta(refresh=True)
            if job_meta and 'progress' in job_meta:
                progress = float(job_meta['progress'])
            if job_meta and 'message' in job_meta:
                message = str(job_meta['message'])
        except Exception as e:
            logger.warning(f"Failed to read job meta: {e}")
        
        # Fallback to status-based progress if meta not available
        if progress is None:
            if job_status == 'queued':
                progress = 0.1
            elif job_status == 'started':
                progress = 0.3
            elif job_status == 'finished':
                progress = 1.0
            elif job_status == 'failed':
                progress = 0.0
        
        # Use meta message or default based on status
        if not message:
            if job_status == 'queued':
                message = "Job is in queue"
            elif job_status == 'started':
                message = "Generating preview..."
            elif job_status == 'finished':
                message = "Preview generation complete"
            elif job_status == 'failed':
                message = "Preview generation failed"
        
        result = None
        error = None
        
        if job_status == 'finished':
            try:
                # Try to get result - might need to wait a moment for RQ to save it
                job_result = job.result
                if job_result:
                    # Convert dict result to DemoPreviewResponse
                    result = DemoPreviewResponse(**job_result)
                else:
                    # Result not available yet - might be a race condition
                    logger.warning(f"Job {job_id} finished but result not yet available")
                    # Don't set error, just return None result - frontend will retry
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error parsing job result for {job_id}: {error_msg}", exc_info=True)
                # If it's a deserialization error, the result might not be ready yet
                if "No such key" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"Job {job_id} result not yet available in Redis")
                    # Don't set error, frontend will retry
                else:
                    error = f"Failed to parse result: {error_msg}"
        elif job_status == 'failed':
            try:
                # Extract clean error message from exc_info
                if job.exc_info:
                    exc_info_str = str(job.exc_info)
                    # Try to extract the actual error message (last line usually)
                    lines = exc_info_str.split('\n')
                    error = lines[-1] if lines else exc_info_str
                    # Clean up common prefixes
                    if error.startswith('ValueError: '):
                        error = error.replace('ValueError: ', '')
                    elif error.startswith('Exception: '):
                        error = error.replace('Exception: ', '')
                else:
                    error = "Job failed with unknown error"
            except Exception:
                error = "Job failed with unknown error"
        
        return DemoJobStatusResponse(
            job_id=job_id,
            status=job_status,
            result=result,
            error=error,
            progress=progress,
            message=message
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching job status: {e}", exc_info=True)
        
        # Handle job not found
        if "No such job" in error_msg or "does not exist" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found. It may have expired or never existed."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job status: {error_msg}"
        )


@router.post("/preview", response_model=DemoPreviewResponse)
def generate_demo_preview_optimized(
    request_data: DemoPreviewRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a premium-quality preview with parallel processing and brand extraction.

    OPTIMIZATIONS:
    - Capture screenshot + HTML in single browser session
    - Parallel brand extraction + screenshot upload
    - Concurrent R2 uploads for final images
    - Better brand color/logo/hero image detection

    Reduces processing time by ~30-40% compared to sequential approach.
    """
    try:
        start_time = time.time()
        url_str = str(request_data.url)

        # Check if demo caching is disabled via admin toggle
        cache_disabled = is_demo_cache_disabled()
        
        resolved_mode = resolve_quality_mode("auto", url=url_str)
        cache_key_prefix = get_cache_prefix_for_mode(resolved_mode)
        selected_profile = get_quality_profile(resolved_mode)

        # Get redis client and cache key (needed for both cache check and cache write)
        redis_client = get_redis_client()
        cache_key = generate_cache_key(url_str, cache_key_prefix)

        if cache_disabled:
            logger.info(f"🚫 Cache DISABLED - generating fresh preview for: {url_str[:50]}...")
            # Invalidate any existing cache to ensure fresh results
            from backend.services.preview_cache import invalidate_cache
            invalidate_cache(url_str)
            logger.info(f"🗑️  Cleared existing cache entries for: {url_str[:50]}...")
        else:
            logger.info(f"✅ Cache ENABLED - checking cache first for: {url_str[:50]}...")
            # Check cache first (skip if disabled via admin toggle)
            if redis_client:
                try:
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        logger.info(f"✅ Cache hit for: {url_str[:50]}...")
                        return DemoPreviewResponse(**json.loads(cached_data))
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")

        # Rate limiting
        client_ip = get_client_ip(request)
        rate_limit_key = get_rate_limit_key_for_ip(client_ip, "demo_preview_v2")
        if not check_rate_limit(rate_limit_key, limit=10, window_seconds=3600):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

        # Validate URL
        try:
            validate_url_security(url_str)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # =========================================================================
        # Use unified preview engine
        # =========================================================================
        logger.info(f"🚀 Using unified preview engine for: {url_str}")
        
        config = PreviewEngineConfig(
            is_demo=True,
            enable_brand_extraction=True,
            enable_ai_reasoning=True,
            enable_composited_image=True,
            enable_cache=not cache_disabled,  # Disable cache if admin toggle is enabled
            enable_multi_agent=selected_profile.multi_agent,
            enable_ui_element_extraction=selected_profile.ui_extraction,
            quality_threshold=selected_profile.threshold,
            max_quality_iterations=selected_profile.iterations,
            allow_soft_pass=selected_profile.allow_soft_pass,
            enforce_target_quality=selected_profile.enforce_target_quality,
            min_soft_pass_overall=selected_profile.min_soft_pass_overall,
            min_soft_pass_visual=selected_profile.min_soft_pass_visual,
            min_soft_pass_fidelity=selected_profile.min_soft_pass_fidelity,
        )
        
        engine = PreviewEngine(config)
        engine_result = engine.generate(url_str, cache_key_prefix=cache_key_prefix)
        
        # Convert PreviewEngineResult to DemoPreviewResponse
        response = DemoPreviewResponse(
            url=engine_result.url,
            
            # Content
            title=engine_result.title,
            subtitle=engine_result.subtitle,
            description=engine_result.description,
            tags=engine_result.tags,
            context_items=[
                ContextItem(icon=c["icon"], text=c["text"])
                for c in engine_result.context_items
            ],
            credibility_items=[
                CredibilityItem(type=c["type"], value=c["value"])
                for c in engine_result.credibility_items
            ],
            cta_text=engine_result.cta_text,
            
            # Images
            primary_image_base64=engine_result.primary_image_base64,
            screenshot_url=engine_result.screenshot_url,
            composited_preview_image_url=engine_result.composited_preview_image_url,
            
            # Brand elements
            brand=BrandElements(
                brand_name=engine_result.brand.get("brand_name"),
                logo_base64=engine_result.brand.get("logo_base64"),
                hero_image_base64=engine_result.brand.get("hero_image_base64")
            ),
            
            # Blueprint
            blueprint=LayoutBlueprint(
                template_type=engine_result.blueprint.get("template_type", "article"),
                primary_color=engine_result.blueprint.get("primary_color", "#2563EB"),
                secondary_color=engine_result.blueprint.get("secondary_color", "#1E40AF"),
                accent_color=engine_result.blueprint.get("accent_color", "#F59E0B"),
                coherence_score=engine_result.blueprint.get("coherence_score", 0.0),
                balance_score=engine_result.blueprint.get("balance_score", 0.0),
                clarity_score=engine_result.blueprint.get("clarity_score", 0.0),
                design_fidelity_score=engine_result.blueprint.get("design_fidelity_score"),
                overall_quality=str(engine_result.blueprint.get("overall_quality", "good")),
                layout_reasoning=engine_result.blueprint.get("layout_reasoning", ""),
                composition_notes=engine_result.blueprint.get("composition_notes", "")
            ),
            
            # Design DNA (NEW - for adaptive rendering)
            design_dna=DesignDNA(**engine_result.design_dna) if hasattr(engine_result, 'design_dna') and engine_result.design_dna else None,
            
            # Metrics
            reasoning_confidence=engine_result.reasoning_confidence,
            design_fidelity_score=getattr(engine_result, 'design_fidelity_score', None),
            processing_time_ms=engine_result.processing_time_ms,
            
            # Metadata
            is_demo=True,
            message=f"{engine_result.message} [quality_mode={resolved_mode}]",
            trace_url=engine_result.trace_url
        )

        # Cache the result (skip if disabled via admin toggle)
        if redis_client and not cache_disabled:
            try:
                cache_data = json.dumps(response.model_dump())
                ttl_seconds = CacheConfig.DEFAULT_TTL_HOURS * 3600
                redis_client.setex(cache_key, ttl_seconds, cache_data)
                logger.info(f"✅ Cached result for: {url_str[:50]}...")
            except Exception as e:
                logger.warning(f"⚠️  Failed to cache result: {e}")

        logger.info(f"🎉 Preview generated in {engine_result.processing_time_ms}ms")
        return response
    except HTTPException:
        # Re-raise HTTP exceptions (rate limits, validation errors, etc.)
        raise
    except Exception as e:
        # Log the full error with traceback
        logger.error(f"❌ Fatal error in demo-v2 preview generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}. Please try again."
        )




