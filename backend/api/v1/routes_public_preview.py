"""Public preview API routes (no authentication required)."""
from urllib.parse import urlparse
from fastapi import APIRouter, Query, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from backend.schemas.public_preview import PublicPreview
from backend.models.domain import Domain as DomainModel
from backend.models.preview import Preview as PreviewModel
from backend.models.preview_variant import PreviewVariant as PreviewVariantModel
from backend.db.session import get_db
from backend.core.config import settings
from backend.services.cache import (
    get_cached_domain_by_name,
    set_cached_domain_by_name,
    get_cached_preview_metadata,
    set_cached_preview_metadata,
)
from backend.services.rate_limiter import check_rate_limit, get_rate_limit_key_for_ip
from backend.services.activity_logger import get_client_ip

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/preview", response_model=PublicPreview)
def get_public_preview(
    full_url: str = Query(..., description="Full URL to generate preview for"),
    variant: str = Query(None, description="Variant key: 'a', 'b', or 'c' (optional)"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get preview metadata for a given URL.
    This endpoint is public and does not require authentication.
    
    If variant is provided, returns variant metadata instead of main preview.
    """
    # Rate limiting: 200 requests per 5 minutes per IP
    client_ip = get_client_ip(request)
    rate_limit_key = get_rate_limit_key_for_ip(client_ip, "public_preview")
    if not check_rate_limit(rate_limit_key, limit=200, window_seconds=300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Validate URL security
    from backend.utils.url_sanitizer import validate_url_security
    try:
        validate_url_security(full_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return _get_preview_logic(full_url, db, variant)


def _get_preview_logic(full_url: str, db: Session, variant: str = None) -> PublicPreview:
    """Core logic for getting preview metadata."""
    try:
        parsed = urlparse(full_url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        
        # Remove port if present (e.g., "example.com:8000" -> "example.com")
        if ':' in hostname:
            hostname = hostname.split(':')[0]
        
        # Remove www. prefix for matching (optional, but helps with matching)
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        
        # Try cache first for domain lookup (we need org_id for cache key, so check cache after domain lookup)
        # Look up domain by hostname
        domain = db.query(DomainModel).filter(
            DomainModel.name == hostname
        ).first()
        
        # Cache domain if found
        if domain and domain.organization_id:
            domain_cache_data = {
                "id": domain.id,
                "name": domain.name,
                "status": domain.status,
                "organization_id": domain.organization_id,
            }
            set_cached_domain_by_name(domain.organization_id, hostname, domain_cache_data)
        
        if not domain:
            # No matching domain found - return fallback with placeholder
            return PublicPreview(
                url=full_url,
                title=hostname or "Untitled Page",
                description="Preview not configured yet.",
                image_url=settings.PLACEHOLDER_IMAGE_URL,
                site_name=hostname
            )
        
        # Domain found - check if verified
        if domain.status != "verified":
            # Domain not verified - return fallback with placeholder
            return PublicPreview(
                url=full_url,
                title=hostname or "Untitled Page",
                description="Domain not verified.",
                image_url=settings.PLACEHOLDER_IMAGE_URL,
                site_name=hostname,
                type=None
            )
        
        # Domain found - get organization_id
        organization_id = domain.organization_id
        
        if organization_id is None:
            # Domain exists but has no organization (legacy data) - return fallback with placeholder
            return PublicPreview(
                url=full_url,
                title=hostname or "Untitled Page",
                description="Preview not configured yet.",
                image_url=settings.PLACEHOLDER_IMAGE_URL,
                site_name=hostname
            )
        
        # Try cache first for preview metadata
        preview = None
        preview_cache_key = None
        
        # Try to find a matching preview for this organization and URL
        # Match on exact URL or path-only
        preview = db.query(PreviewModel).filter(
            PreviewModel.organization_id == organization_id,
            PreviewModel.url == full_url
        ).first()
        
        # If no exact match, try matching on path only
        if not preview and parsed.path:
            path_only = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            preview = db.query(PreviewModel).filter(
                PreviewModel.organization_id == organization_id,
                PreviewModel.url == path_only
            ).first()
        
        if preview:
            # Cache preview metadata
            preview_cache_data = {
                "id": preview.id,
                "title": preview.title,
                "description": preview.description,
                "image_url": preview.image_url,
                "type": preview.type,
            }
            set_cached_preview_metadata(preview.id, preview_cache_data)
            # Check if variant is requested
            if variant and variant.lower() in ['a', 'b', 'c']:
                variant_obj = db.query(PreviewVariantModel).filter(
                    PreviewVariantModel.preview_id == preview.id,
                    PreviewVariantModel.variant_key == variant.lower()
                ).first()
                
                if variant_obj:
                    # Use variant data
                    return PublicPreview(
                        url=full_url,
                        title=variant_obj.title,
                        description=variant_obj.description if variant_obj.description else "No preview description available.",
                        image_url=variant_obj.image_url or preview.highlight_image_url or preview.image_url or settings.PLACEHOLDER_IMAGE_URL,
                        site_name=domain.name,
                        type=preview.type
                    )
                # Variant not found, fall through to main preview
            
            # Use main preview data
            return PublicPreview(
                url=full_url,
                title=preview.title,
                description=preview.description if preview.description else "No preview description available.",
                image_url=preview.image_url if preview.image_url else settings.PLACEHOLDER_IMAGE_URL,
                site_name=domain.name,
                type=preview.type
            )
        else:
            # Domain exists but no preview found - return fallback with placeholder
            path_display = parsed.path if parsed.path else "/"
            return PublicPreview(
                url=full_url,
                title=hostname or "Untitled Page",
                description="Preview not generated yet.",
                image_url=settings.PLACEHOLDER_IMAGE_URL,
                site_name=hostname
            )
            
    except Exception as e:
        # On any error, return a safe fallback with placeholder
        return PublicPreview(
            url=full_url,
            title="Untitled Page",
            description="Preview not available.",
            image_url=settings.PLACEHOLDER_IMAGE_URL,
            site_name=None
        )

