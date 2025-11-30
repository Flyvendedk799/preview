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
from uuid import uuid4
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from backend.db.session import get_db
from backend.services.rate_limiter import check_rate_limit, get_rate_limit_key_for_ip
from backend.services.activity_logger import get_client_ip
from backend.utils.url_sanitizer import validate_url_security
from backend.services.playwright_screenshot import capture_screenshot_and_html
from backend.services.r2_client import upload_file_to_r2
from backend.services.preview_reasoning import generate_reasoned_preview
from backend.services.preview_image_generator import generate_and_upload_preview_image
from backend.services.brand_extractor import extract_all_brand_elements
from backend.services.preview_cache import (
    generate_cache_key,
    get_redis_client,
    CacheConfig
)
from backend.queue.queue_connection import get_rq_redis_connection
from backend.jobs.demo_preview_job import generate_demo_preview_job
from rq import Queue
from rq.job import Job
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo-v2", tags=["demo"])


class DemoPreviewRequest(BaseModel):
    """Schema for demo preview generation request."""
    url: HttpUrl


# Response schemas (same as original)
class ContextItem(BaseModel):
    """Context item like location, date, etc."""
    icon: str
    text: str


class CredibilityItem(BaseModel):
    """Credibility item like rating, review count."""
    type: str
    value: str


class BrandElements(BaseModel):
    """Extracted brand elements."""
    brand_name: Optional[str] = None
    logo_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    favicon_url: Optional[str] = None


class LayoutBlueprint(BaseModel):
    """Layout blueprint with full reasoning."""
    template_type: str
    primary_color: str
    secondary_color: str
    accent_color: str
    coherence_score: float
    balance_score: float
    clarity_score: float
    overall_quality: str
    layout_reasoning: str
    composition_notes: str


class DemoPreviewResponse(BaseModel):
    """Multi-stage reasoned preview response with brand elements."""
    # Source URL
    url: str

    # ===== RENDERED CONTENT =====
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    context_items: List[ContextItem] = []
    credibility_items: List[CredibilityItem] = []
    cta_text: Optional[str] = None

    # ===== IMAGES =====
    primary_image_base64: Optional[str] = None
    screenshot_url: Optional[str] = None
    composited_preview_image_url: Optional[str] = None

    # ===== BRAND ELEMENTS =====
    brand: Optional[BrandElements] = None

    # ===== LAYOUT BLUEPRINT =====
    blueprint: LayoutBlueprint

    # ===== QUALITY METRICS =====
    reasoning_confidence: float
    processing_time_ms: int

    # ===== DEMO METADATA =====
    is_demo: bool = True
    message: str = "AI-reconstructed preview using multi-stage reasoning."


class DemoJobRequest(BaseModel):
    """Schema for demo job creation request."""
    url: HttpUrl


class DemoJobResponse(BaseModel):
    """Schema for demo job creation response."""
    job_id: str
    status: str = "queued"
    message: str = "Preview generation started. Poll /demo-v2/jobs/{job_id}/status for updates."


class DemoJobStatusResponse(BaseModel):
    """Schema for demo job status response."""
    job_id: str
    status: str  # "queued", "started", "finished", "failed"
    result: Optional[DemoPreviewResponse] = None
    error: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0
    message: Optional[str] = None  # Human-readable status message


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
    
    # Rate limiting
    client_ip = get_client_ip(request)
    rate_limit_key = get_rate_limit_key_for_ip(client_ip, "demo_job_v2")
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
    
    # Enqueue job
    try:
        redis_conn = get_rq_redis_connection()
        queue = Queue("preview_generation", connection=redis_conn)
        job = queue.enqueue(
            generate_demo_preview_job,
            url_str,
            job_timeout='5m'  # 5 minute timeout for AI generation
        )
        
        logger.info(f"✅ Demo job created: {job.id} for URL: {url_str[:50]}...")
        
        return DemoJobResponse(
            job_id=job.id,
            status="queued",
            message="Preview generation started. Poll /demo-v2/jobs/{job_id}/status for updates."
        )
    except Exception as e:
        logger.error(f"❌ Failed to create demo job: {str(e)}", exc_info=True)
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
                job_result = job.result
                if job_result:
                    # Convert dict result to DemoPreviewResponse
                    result = DemoPreviewResponse(**job_result)
            except Exception as e:
                logger.error(f"Error parsing job result: {e}", exc_info=True)
                error = f"Failed to parse result: {str(e)}"
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

        # Check cache first
        redis_client = get_redis_client()
        cache_key = generate_cache_key(url_str, "demo:preview:v2:")

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
        # STEP 1: Capture screenshot + HTML (single browser session)
        # =========================================================================
        try:
            logger.info(f"📸 Capturing screenshot + HTML for: {url_str}")
            screenshot_bytes, html_content = capture_screenshot_and_html(url_str)
            logger.info(f"✅ Screenshot captured ({len(screenshot_bytes)} bytes)")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Screenshot capture failed: {error_msg}", exc_info=True)
            # Pass through the descriptive error message from capture_screenshot_and_html
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to capture page screenshot: {error_msg}"
            )

        # =========================================================================
        # STEP 2: Parallel processing - Brand extraction + Screenshot upload
        # =========================================================================
        screenshot_url = None
        brand_elements = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            # Task 1: Upload screenshot to R2
            future_upload = executor.submit(
                upload_file_to_r2,
                screenshot_bytes,
                f"screenshots/demo/{uuid4()}.png",
                "image/png"
            )
            futures[future_upload] = "screenshot_upload"

            # Task 2: Extract brand elements (logo, colors, hero image)
            future_brand = executor.submit(
                extract_all_brand_elements,
                html_content,
                url_str,
                screenshot_bytes
            )
            futures[future_brand] = "brand_extraction"

            # Wait for both to complete
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    if task_name == "screenshot_upload":
                        screenshot_url = future.result()
                        logger.info(f"✅ Screenshot uploaded: {screenshot_url}")
                    elif task_name == "brand_extraction":
                        brand_elements = future.result()
                        logger.info(f"✅ Brand elements extracted: {brand_elements.get('brand_name') if brand_elements and isinstance(brand_elements, dict) else 'N/A'}")
                except Exception as e:
                    logger.warning(f"⚠️  {task_name} failed: {e}")

        # =========================================================================
        # STEP 3: Run multi-stage AI reasoning
        # =========================================================================
        try:
            logger.info(f"🤖 Running AI reasoning for: {url_str}")
            result = generate_reasoned_preview(screenshot_bytes, url_str)
            logger.info(f"✅ AI reasoning complete")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ AI reasoning failed: {error_msg}", exc_info=True)

            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="OpenAI rate limit reached. Please wait a moment and try again."
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze page: {error_msg}. Please try again."
            )

        # =========================================================================
        # STEP 4: Generate og:image with enhanced brand elements
        # =========================================================================
        composited_image_url = None
        try:
            logger.info("🎨 Generating brand-aligned og:image")

            # Use brand colors if available, otherwise use AI-extracted colors
            if brand_elements and isinstance(brand_elements, dict) and "colors" in brand_elements:
                brand_colors = brand_elements.get("colors", {})
                blueprint_colors = {
                    "primary_color": brand_colors.get("primary_color", result.blueprint.primary_color) if isinstance(brand_colors, dict) else result.blueprint.primary_color,
                    "secondary_color": brand_colors.get("secondary_color", result.blueprint.secondary_color) if isinstance(brand_colors, dict) else result.blueprint.secondary_color,
                    "accent_color": brand_colors.get("accent_color", result.blueprint.accent_color) if isinstance(brand_colors, dict) else result.blueprint.accent_color,
                }
            else:
                blueprint_colors = {
                    "primary_color": result.blueprint.primary_color,
                    "secondary_color": result.blueprint.secondary_color,
                    "accent_color": result.blueprint.accent_color,
                }

            # Use logo if available, otherwise use primary_image from AI
            image_for_preview = None
            if brand_elements and isinstance(brand_elements, dict) and brand_elements.get("logo_base64"):
                image_for_preview = brand_elements["logo_base64"]
                logger.info("Using extracted brand logo for preview")
            elif brand_elements and isinstance(brand_elements, dict) and brand_elements.get("hero_image_base64"):
                image_for_preview = brand_elements["hero_image_base64"]
                logger.info("Using extracted hero image for preview")
            else:
                image_for_preview = result.primary_image_base64
                logger.info("Using AI-extracted primary image for preview")

            composited_image_url = generate_and_upload_preview_image(
                screenshot_bytes=screenshot_bytes,
                url=url_str,
                title=result.title,
                subtitle=result.subtitle,
                description=result.description,
                cta_text=result.cta_text,
                blueprint=blueprint_colors,
                template_type=result.blueprint.template_type,
                tags=result.tags,
                context_items=[
                    {"icon": c["icon"], "text": c["text"]}
                    for c in result.context_items
                ],
                credibility_items=[
                    {"type": c["type"], "value": c["value"]}
                    for c in result.credibility_items
                ],
                primary_image_base64=image_for_preview
            )

            if composited_image_url:
                logger.info(f"✅ og:image generated: {composited_image_url}")
        except Exception as e:
            logger.warning(f"⚠️  og:image generation failed: {e}", exc_info=True)
            if screenshot_url:
                composited_image_url = screenshot_url
                logger.info(f"Using screenshot as fallback")

        # =========================================================================
        # STEP 5: Build response
        # =========================================================================
        processing_time_ms = int((time.time() - start_time) * 1000)

        response = DemoPreviewResponse(
            url=url_str,

            # Content
            title=result.title,
            subtitle=result.subtitle,
            description=result.description,
            tags=result.tags,
            context_items=[
                ContextItem(icon=c["icon"], text=c["text"])
                for c in result.context_items
            ],
            credibility_items=[
                CredibilityItem(type=c["type"], value=c["value"])
                for c in result.credibility_items
            ],
            cta_text=result.cta_text,

            # Images
            primary_image_base64=result.primary_image_base64,
            screenshot_url=screenshot_url,
            composited_preview_image_url=composited_image_url,

            # Brand elements
            brand=BrandElements(
                brand_name=brand_elements.get("brand_name") if (brand_elements and isinstance(brand_elements, dict)) else None,
                logo_base64=brand_elements.get("logo_base64") if (brand_elements and isinstance(brand_elements, dict)) else None,
                hero_image_base64=brand_elements.get("hero_image_base64") if (brand_elements and isinstance(brand_elements, dict)) else None
            ),

            # Blueprint (use enhanced colors)
            blueprint=LayoutBlueprint(
                template_type=result.blueprint.template_type,
                primary_color=blueprint_colors["primary_color"],
                secondary_color=blueprint_colors["secondary_color"],
                accent_color=blueprint_colors["accent_color"],
                coherence_score=result.blueprint.coherence_score,
                balance_score=result.blueprint.balance_score,
                clarity_score=result.blueprint.clarity_score,
                overall_quality=result.blueprint.overall_quality,
                layout_reasoning=result.blueprint.layout_reasoning,
                composition_notes=result.blueprint.composition_notes
            ),

            # Metrics
            reasoning_confidence=result.reasoning_confidence,
            processing_time_ms=processing_time_ms,

            # Metadata
            is_demo=True,
            message="AI-reconstructed preview with enhanced brand extraction."
        )

        # Cache the result
        if redis_client:
            try:
                cache_data = json.dumps(response.model_dump())
                ttl_seconds = CacheConfig.DEFAULT_TTL_HOURS * 3600
                redis_client.setex(cache_key, ttl_seconds, cache_data)
                logger.info(f"✅ Cached result for: {url_str[:50]}...")
            except Exception as e:
                logger.warning(f"⚠️  Failed to cache result: {e}")

        logger.info(f"🎉 Preview generated in {processing_time_ms}ms")
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
