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
from backend.services.ux_intelligence import generate_intelligent_preview
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoPreviewRequest(BaseModel):
    """Schema for demo preview generation request."""
    url: HttpUrl


class EmphasisZone(BaseModel):
    """Visual emphasis zone in the preview."""
    x: float
    y: float
    width: float
    height: float
    priority: int
    reason: str
    content_type: str


class PreviewVariant(BaseModel):
    """A variant of the preview content."""
    title: str
    description: str


class VisualGuidance(BaseModel):
    """Visual composition guidance."""
    focal_point: Dict[str, float]
    crop_region: Dict[str, float]
    emphasis_zones: List[EmphasisZone]
    style: str
    overlay_position: str


class ContentExtraction(BaseModel):
    """Extracted content from the page."""
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    cta: Optional[str] = None
    features: List[str] = []
    social_proof: Optional[str] = None


class QualityMetrics(BaseModel):
    """Quality assessment of the page design."""
    hierarchy_score: float
    clarity_score: float
    clutter: str


class DemoPreviewResponse(BaseModel):
    """Enhanced demo preview response with UI/UX intelligence."""
    # Core preview data
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    type: str
    url: str
    
    # Design intent
    design_intent: str
    primary_message: str
    value_proposition: str
    
    # Variants for A/B testing
    variants: Dict[str, PreviewVariant]
    
    # Visual guidance for rendering
    visual_guidance: VisualGuidance
    
    # Extracted content
    content: ContentExtraction
    
    # Quality metrics
    quality: QualityMetrics
    
    # AI reasoning (for transparency)
    reasoning: str
    confidence: float
    
    # Demo metadata
    is_demo: bool = True
    message: str = "This is an AI-powered preview analysis. Sign up for full access."


@router.post("/preview", response_model=DemoPreviewResponse)
def generate_demo_preview(
    request_data: DemoPreviewRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate an intelligent demo preview for any URL (public endpoint, no auth required).
    
    This uses advanced UI/UX analysis to:
    - Interpret design intent and visual hierarchy
    - Extract key content with context awareness
    - Provide multiple content variants for A/B testing
    - Generate visual guidance for preview composition
    
    Rate limited to prevent abuse.
    """
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
        validate_url_security(str(request_data.url))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Step 1: Capture screenshot
    screenshot_bytes = None
    try:
        logger.info(f"Capturing screenshot for: {request_data.url}")
        screenshot_bytes = capture_screenshot(str(request_data.url))
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture page screenshot. Please try again."
        )
    
    # Step 2: Upload screenshot to R2
    image_url = None
    try:
        filename = f"screenshots/demo/{uuid4()}.png"
        image_url = upload_file_to_r2(screenshot_bytes, filename, "image/png")
        logger.info(f"Demo screenshot uploaded: {image_url}")
    except Exception as e:
        logger.warning(f"Screenshot upload failed: {e}")
        # Continue without image - analysis can still work
    
    # Step 3: Generate intelligent preview with UX analysis
    try:
        logger.info(f"Running UX intelligence analysis for: {request_data.url}")
        preview_data = generate_intelligent_preview(screenshot_bytes, str(request_data.url))
    except Exception as e:
        logger.error(f"UX intelligence analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze page. Please try again."
        )
    
    # Step 4: Build response
    variants = preview_data.get("variants", {})
    visual_guidance = preview_data.get("visual_guidance", {})
    content = preview_data.get("content", {})
    quality = preview_data.get("quality", {})
    analysis = preview_data.get("analysis", {})
    
    return DemoPreviewResponse(
        # Core preview
        title=preview_data.get("title", "Untitled Page"),
        description=preview_data.get("description"),
        image_url=image_url,
        type=preview_data.get("type", "unknown"),
        url=str(request_data.url),
        
        # Design intelligence
        design_intent=analysis.get("design_intent", "unknown"),
        primary_message=analysis.get("primary_message", ""),
        value_proposition=analysis.get("value_proposition", ""),
        
        # Variants
        variants={
            "action_oriented": PreviewVariant(
                title=variants.get("action_oriented", {}).get("title", ""),
                description=variants.get("action_oriented", {}).get("description", "")
            ),
            "benefit_focused": PreviewVariant(
                title=variants.get("benefit_focused", {}).get("title", ""),
                description=variants.get("benefit_focused", {}).get("description", "")
            ),
            "emotional": PreviewVariant(
                title=variants.get("emotional", {}).get("title", ""),
                description=variants.get("emotional", {}).get("description", "")
            )
        },
        
        # Visual guidance
        visual_guidance=VisualGuidance(
            focal_point=visual_guidance.get("focal_point", {"x": 0.5, "y": 0.3}),
            crop_region=visual_guidance.get("crop_region", {"x": 0, "y": 0, "width": 1, "height": 0.6}),
            emphasis_zones=[
                EmphasisZone(**zone) for zone in visual_guidance.get("emphasis_zones", [])[:5]
            ],
            style=visual_guidance.get("style", "professional"),
            overlay_position=visual_guidance.get("overlay_position", "bottom")
        ),
        
        # Content
        content=ContentExtraction(
            headline=content.get("headline"),
            subheadline=content.get("subheadline"),
            cta=content.get("cta"),
            features=content.get("features", [])[:5],
            social_proof=content.get("social_proof")
        ),
        
        # Quality
        quality=QualityMetrics(
            hierarchy_score=quality.get("hierarchy_score", 0.5),
            clarity_score=quality.get("clarity_score", 0.5),
            clutter=quality.get("clutter", "moderate")
        ),
        
        # Metadata
        reasoning=preview_data.get("reasoning", ""),
        confidence=preview_data.get("confidence", 0.5),
        is_demo=True,
        message="AI-powered preview analysis. Sign up for full access to generate unlimited previews."
    )

