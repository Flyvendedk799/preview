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
from backend.services.preview_reconstruction import reconstruct_preview
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoPreviewRequest(BaseModel):
    """Schema for demo preview generation request."""
    url: HttpUrl


# =============================================================================
# Reconstruction Schema
# =============================================================================

class BoundingBox(BaseModel):
    """Normalized bounding box coordinates."""
    x: float
    y: float
    width: float
    height: float


class ExtractedElement(BaseModel):
    """A single extracted UI element."""
    id: str
    type: str
    content: str
    bounding_box: BoundingBox
    priority: int
    include_in_preview: bool
    text_content: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    font_weight: Optional[str] = None
    is_image: bool = False
    image_crop_data: Optional[str] = None  # Base64 of cropped region
    confidence: float = 0.8


class LayoutSection(BaseModel):
    """A section in the reconstructed layout."""
    name: str
    element_ids: List[str]
    layout_direction: str  # horizontal, vertical, grid
    alignment: str  # left, center, right
    spacing: str  # tight, normal, loose
    emphasis: str  # primary, secondary, tertiary


class LayoutPlan(BaseModel):
    """Complete layout plan for reconstruction."""
    template: str  # profile_card, product_card, landing_hero, etc.
    page_type: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_style: str
    font_style: str
    sections: List[LayoutSection]
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    cta_text: Optional[str] = None
    layout_rationale: str


class DemoPreviewResponse(BaseModel):
    """
    Semantic reconstruction response.
    
    This provides structured data for the frontend to render a reconstructed
    preview using actual page elements - not just a cropped screenshot.
    """
    # URL info
    url: str
    
    # Layout plan for reconstruction
    layout_plan: LayoutPlan
    
    # Extracted elements with content
    elements: List[ExtractedElement]
    
    # Key images (base64 encoded, cropped from screenshot)
    profile_image_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    logo_base64: Optional[str] = None
    
    # Full screenshot URL (fallback)
    screenshot_url: Optional[str] = None
    
    # Quality metrics
    extraction_confidence: float
    reconstruction_quality: str  # excellent, good, fair, fallback
    processing_time_ms: int
    
    # Demo metadata
    is_demo: bool = True
    message: str = "AI-reconstructed preview using semantic element extraction."


@router.post("/preview", response_model=DemoPreviewResponse)
def generate_demo_preview(
    request_data: DemoPreviewRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a semantically reconstructed preview for any URL.
    
    This goes beyond screenshot cropping to:
    - Extract individual UI components (images, text, buttons, etc.)
    - Generate an optimal layout plan for reconstruction
    - Provide structured data for the frontend to render a redesigned preview
    
    The preview uses ONLY existing content from the page - no fabrication.
    
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
    
    # Step 2: Upload full screenshot to R2 (as fallback)
    screenshot_url = None
    try:
        filename = f"screenshots/demo/{uuid4()}.png"
        screenshot_url = upload_file_to_r2(screenshot_bytes, filename, "image/png")
        logger.info(f"Demo screenshot uploaded: {screenshot_url}")
    except Exception as e:
        logger.warning(f"Screenshot upload failed: {e}")
    
    # Step 3: Perform semantic reconstruction
    try:
        logger.info(f"Running semantic reconstruction for: {request_data.url}")
        reconstruction = reconstruct_preview(screenshot_bytes, str(request_data.url))
    except Exception as e:
        logger.error(f"Preview reconstruction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reconstruct preview. Please try again."
        )
    
    # Step 4: Build response
    layout_plan = reconstruction.layout_plan
    elements = reconstruction.elements
    
    return DemoPreviewResponse(
        url=str(request_data.url),
        
        # Layout plan
        layout_plan=LayoutPlan(
            template=layout_plan.template.value if hasattr(layout_plan.template, 'value') else str(layout_plan.template),
            page_type=layout_plan.page_type,
            primary_color=layout_plan.primary_color,
            secondary_color=layout_plan.secondary_color,
            accent_color=layout_plan.accent_color,
            background_style=layout_plan.background_style,
            font_style=layout_plan.font_style,
            sections=[
                LayoutSection(
                    name=s.name,
                    element_ids=s.element_ids,
                    layout_direction=s.layout_direction,
                    alignment=s.alignment,
                    spacing=s.spacing,
                    emphasis=s.emphasis
                ) for s in layout_plan.sections
            ],
            title=layout_plan.title,
            subtitle=layout_plan.subtitle,
            description=layout_plan.description,
            cta_text=layout_plan.cta_text,
            layout_rationale=layout_plan.layout_rationale
        ),
        
        # Extracted elements
        elements=[
            ExtractedElement(
                id=e.id,
                type=e.type.value if hasattr(e.type, 'value') else str(e.type),
                content=e.content,
                bounding_box=BoundingBox(
                    x=e.bounding_box.x,
                    y=e.bounding_box.y,
                    width=e.bounding_box.width,
                    height=e.bounding_box.height
                ),
                priority=e.priority,
                include_in_preview=e.include_in_preview,
                text_content=e.text_content,
                background_color=e.background_color,
                text_color=e.text_color,
                font_weight=e.font_weight,
                is_image=e.is_image,
                image_crop_data=e.image_crop_data,
                confidence=e.confidence
            ) for e in elements
        ],
        
        # Key images
        profile_image_base64=reconstruction.profile_image_base64,
        hero_image_base64=reconstruction.hero_image_base64,
        logo_base64=reconstruction.logo_base64,
        
        # Screenshot fallback
        screenshot_url=screenshot_url,
        
        # Quality metrics
        extraction_confidence=reconstruction.extraction_confidence,
        reconstruction_quality=reconstruction.reconstruction_quality,
        processing_time_ms=reconstruction.processing_time_ms,
        
        # Demo metadata
        is_demo=True,
        message="AI-reconstructed preview using semantic element extraction."
    )

