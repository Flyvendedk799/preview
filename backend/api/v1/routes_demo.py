"""Demo/landing page routes for marketing campaigns."""
from uuid import uuid4
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from backend.db.session import get_db
from backend.services.rate_limiter import check_rate_limit, get_rate_limit_key_for_ip
from backend.services.activity_logger import get_client_ip
from backend.utils.url_sanitizer import validate_url_security
from backend.services.playwright_screenshot import capture_screenshot
from backend.services.r2_client import upload_file_to_r2
from backend.services.preview_reasoning import generate_reasoned_preview
from backend.services.preview_image_generator import generate_and_upload_preview_image
from backend.services.preview_cache import (
    generate_cache_key,
    get_redis_client,
    CacheConfig
)
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoPreviewRequest(BaseModel):
    """Schema for demo preview generation request."""
    url: HttpUrl


# =============================================================================
# Response Schema - Multi-Stage Reasoned Preview
# =============================================================================

class ContextItem(BaseModel):
    """Context item like location, date, etc."""
    icon: str
    text: str


class CredibilityItem(BaseModel):
    """Credibility item like rating, review count."""
    type: str
    value: str


class LayoutBlueprint(BaseModel):
    """Layout blueprint with full reasoning."""
    template_type: str  # profile, product, landing, article, service
    primary_color: str
    secondary_color: str
    accent_color: str
    
    # Quality scores from Stage 6
    coherence_score: float
    balance_score: float
    clarity_score: float
    overall_quality: str  # excellent, good, fair, poor
    
    # Reasoning chain
    layout_reasoning: str
    composition_notes: str


class DemoPreviewResponse(BaseModel):
    """
    Multi-stage reasoned preview response.
    
    This provides structured content ready for rendering, along with
    the full reasoning chain that led to these decisions.
    """
    # Source URL
    url: str
    
    # ===== RENDERED CONTENT =====
    # These are the final values to display
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
    composited_preview_image_url: Optional[str] = None  # Final og:image with all elements
    
    # ===== LAYOUT BLUEPRINT =====
    blueprint: LayoutBlueprint
    
    # ===== QUALITY METRICS =====
    reasoning_confidence: float
    processing_time_ms: int
    
    # ===== DEMO METADATA =====
    is_demo: bool = True
    message: str = "AI-reconstructed preview using multi-stage reasoning."


@router.post("/preview", response_model=DemoPreviewResponse)
def generate_demo_preview(
    request_data: DemoPreviewRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a premium-quality preview using multi-stage reasoning.
    
    The system follows a rigorous 6-stage process:
    1. SEGMENTATION: Identify distinct UI regions
    2. PURPOSE ANALYSIS: Determine each region's communication role
    3. PRIORITY ASSIGNMENT: Rank by visual importance
    4. COMPOSITION DECISION: What to keep, reorder, or remove
    5. LAYOUT SYNTHESIS: Generate optimized structure
    6. COHERENCE CHECK: Validate balance and flow
    
    IMPROVEMENT: Added caching for repeated URLs to improve performance.
    Rate limited to prevent abuse.
    """
    url_str = str(request_data.url)
    
    # IMPROVEMENT: Check cache first for repeated URLs (e.g., subpay.dk)
    redis_client = get_redis_client()
    cache_key = generate_cache_key(url_str, "demo:preview:")
    cached_result = None
    
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for demo preview: {url_str[:50]}...")
                cached_result = json.loads(cached_data)
                # Return cached result immediately
                return DemoPreviewResponse(**cached_result)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
    
    # Rate limiting: 10 previews per hour per IP
    client_ip = get_client_ip(request)
    rate_limit_key = get_rate_limit_key_for_ip(client_ip, "demo_preview")
    if not check_rate_limit(rate_limit_key, limit=10, window_seconds=3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Validate URL security
    try:
        validate_url_security(url_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Step 1: Capture screenshot
    screenshot_bytes = None
    try:
        logger.info(f"Capturing screenshot for: {url_str}")
        screenshot_bytes = capture_screenshot(url_str)
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture page screenshot. Please try again."
        )
    
    # Step 2: Upload full screenshot to R2 (as fallback)
    screenshot_url = None
    try:
        filename = f"screenshots/demo/{uuid4()}.png"
        screenshot_url = upload_file_to_r2(screenshot_bytes, filename, "image/png")
        logger.info(f"Demo screenshot uploaded: {screenshot_url}")
    except Exception as e:
        logger.warning(f"Screenshot upload failed: {e}")
    
    # Step 3: Run multi-stage reasoning
    try:
        logger.info(f"Running multi-stage reasoning for: {url_str}")
        result = generate_reasoned_preview(screenshot_bytes, url_str)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Preview reasoning failed: {error_msg}", exc_info=True)
        
        # Check if it's a rate limit error
        if "429" in error_msg or "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OpenAI rate limit reached. Please wait a moment and try again."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze page: {error_msg}. Please try again."
        )
    
    # Step 4: Generate designed og:image (matching React component card design)
    composited_image_url = None
    try:
        logger.info("Generating designed og:image matching React component")
        
        # Create a beautifully designed preview image that matches the React component:
        # - White card background with accent bar
        # - Icon/image, title, subtitle, description
        # - Tags as features with checkmarks
        # - Context items (if available)
        # - CTA button at bottom
        # This creates an image that matches the AI Reconstructed Preview component
        composited_image_url = generate_and_upload_preview_image(
            screenshot_bytes=screenshot_bytes,
            url=str(request_data.url),
            title=result.title,
            subtitle=result.subtitle,
            description=result.description,
            cta_text=result.cta_text,
            blueprint={
                "primary_color": result.blueprint.primary_color,
                "secondary_color": result.blueprint.secondary_color,
                "accent_color": result.blueprint.accent_color
            },
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
            primary_image_base64=result.primary_image_base64
        )
        if composited_image_url:
            logger.info(f"Designed og:image generated: {composited_image_url}")
    except Exception as e:
        logger.warning(f"Failed to generate og:image: {e}", exc_info=True)
        # Fallback to raw screenshot URL if available
        if screenshot_url:
            composited_image_url = screenshot_url
            logger.info(f"Using raw screenshot as fallback: {screenshot_url}")
    
    # Step 5: Build response
    response = DemoPreviewResponse(
        url=url_str,
        
        # Rendered content
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
        composited_preview_image_url=composited_image_url,  # This is the og:image
        
        # Layout blueprint
        blueprint=LayoutBlueprint(
            template_type=result.blueprint.template_type,
            primary_color=result.blueprint.primary_color,
            secondary_color=result.blueprint.secondary_color,
            accent_color=result.blueprint.accent_color,
            coherence_score=result.blueprint.coherence_score,
            balance_score=result.blueprint.balance_score,
            clarity_score=result.blueprint.clarity_score,
            overall_quality=result.blueprint.overall_quality,
            layout_reasoning=result.blueprint.layout_reasoning,
            composition_notes=result.blueprint.composition_notes
        ),
        
        # Quality metrics
        reasoning_confidence=result.reasoning_confidence,
        processing_time_ms=result.processing_time_ms,
        
        # Demo metadata
        is_demo=True,
        message="AI-reconstructed preview using multi-stage reasoning."
    )
    
    # IMPROVEMENT: Cache the result for future requests (24 hour TTL)
    if redis_client:
        try:
            # Convert response to dict for caching
            response_dict = response.model_dump()
            cache_data = json.dumps(response_dict)
            ttl_seconds = CacheConfig.DEFAULT_TTL_HOURS * 3600
            redis_client.setex(cache_key, ttl_seconds, cache_data)
            logger.info(f"Cached demo preview result for: {url_str[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    return response
