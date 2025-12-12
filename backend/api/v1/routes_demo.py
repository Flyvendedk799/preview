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
from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig
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


class BrandElements(BaseModel):
    """Extracted brand elements."""
    brand_name: Optional[str] = None
    logo_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None


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
    
    # Use unified preview engine
    logger.info(f"🚀 Using unified preview engine for: {url_str}")
    
    config = PreviewEngineConfig(
        is_demo=True,
        enable_brand_extraction=True,
        enable_ai_reasoning=True,
        enable_composited_image=True,
        enable_cache=True
    )
    
    engine = PreviewEngine(config)
    engine_result = engine.generate(url_str, cache_key_prefix="demo:preview:")
    
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
            overall_quality=engine_result.blueprint.get("overall_quality", 0.0),
            layout_reasoning=engine_result.blueprint.get("layout_reasoning", ""),
            composition_notes=engine_result.blueprint.get("composition_notes", "")
        ),
        
        # Metrics
        reasoning_confidence=engine_result.reasoning_confidence,
        processing_time_ms=engine_result.processing_time_ms,
        
        # Metadata
        is_demo=True,
        message=engine_result.message
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
