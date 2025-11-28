"""Demo/landing page routes for marketing campaigns."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from backend.db.session import get_db
from backend.services.preview_generator import generate_ai_preview
from backend.services.rate_limiter import check_rate_limit, get_rate_limit_key_for_ip
from backend.services.activity_logger import get_client_ip
from backend.utils.url_sanitizer import validate_url_security
from backend.schemas.brand import BrandSettings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoPreviewRequest(BaseModel):
    """Schema for demo preview generation request."""
    url: HttpUrl


class DemoPreviewResponse(BaseModel):
    """Schema for demo preview response (read-only, limited scope)."""
    title: str
    description: str | None
    image_url: str | None
    type: str
    url: str
    is_demo: bool = True
    message: str = "This is a sample preview. Sign up for full access to generate unlimited previews."


@router.post("/preview", response_model=DemoPreviewResponse)
def generate_demo_preview(
    request_data: DemoPreviewRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate a demo preview for any URL (public endpoint, no auth/domain required).
    This is a limited preview intended for marketing/demo purposes.
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
    
    # Use default brand settings for demo (id is not used by generate_ai_preview)
    default_brand = BrandSettings(
        id=0,  # Dummy ID, not used by the function
        primary_color="#2979FF",
        secondary_color="#0A1A3C",
        accent_color="#3FFFD3",
        font_family="Inter",
        logo_url=None
    )
    
    # Generate AI preview (this doesn't require domain ownership)
    try:
        ai_result = generate_ai_preview(str(request_data.url), default_brand)
    except Exception as e:
        logger.error(f"Failed to generate demo preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview. Please try again later."
        )
    
    # Determine preview type based on URL
    url_lower = str(request_data.url).lower()
    if "/product" in url_lower or "/shop" in url_lower:
        preview_type = "product"
    elif "/blog" in url_lower or "/post" in url_lower:
        preview_type = "blog"
    else:
        preview_type = "landing"
    
    return DemoPreviewResponse(
        title=ai_result.get("title") or "Untitled Page",
        description=ai_result.get("description"),
        image_url=ai_result.get("image_url"),
        type=preview_type,
        url=str(request_data.url),
        is_demo=True,
        message="This is a sample preview. Sign up for full access to generate unlimited previews."
    )

