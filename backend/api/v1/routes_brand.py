"""Brand settings routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.schemas.brand import BrandSettings, BrandSettingsUpdate
from backend.models.brand import BrandSettings as BrandSettingsModel
from backend.models.user import User
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_current_org, role_required
from backend.models.organization import Organization
from backend.models.organization_member import OrganizationRole
from backend.services.cache import (
    get_cached_brand_settings,
    set_cached_brand_settings,
    invalidate_brand_settings
)

router = APIRouter(prefix="/brand", tags=["brand"])


@router.get("", response_model=BrandSettings)
def get_brand_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Get brand settings for the current organization."""
    # Try cache first
    cached = get_cached_brand_settings(current_org.id)
    if cached:
        return BrandSettings(**cached)
    
    settings = db.query(BrandSettingsModel).filter(
        BrandSettingsModel.organization_id == current_org.id
    ).first()
    
    # If no settings exist, create default ones for this organization
    if not settings:
        settings = BrandSettingsModel(
            primary_color="#2979FF",
            secondary_color="#0A1A3C",
            accent_color="#3FFFD3",
            font_family="Inter",
            logo_url=None,
            user_id=current_user.id,
            organization_id=current_org.id,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Cache the result
    settings_dict = {
        "id": settings.id,
        "primary_color": settings.primary_color,
        "secondary_color": settings.secondary_color,
        "accent_color": settings.accent_color,
        "font_family": settings.font_family,
        "logo_url": settings.logo_url,
    }
    set_cached_brand_settings(current_org.id, settings_dict)
    
    return settings


@router.put("", response_model=BrandSettings)
def update_brand_settings(
    settings_update: BrandSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR]))
):
    """Update brand settings for the current organization (owner/admin/editor only)."""
    settings = db.query(BrandSettingsModel).filter(
        BrandSettingsModel.organization_id == current_org.id
    ).first()
    
    # If no settings exist, create them first
    if not settings:
        settings = BrandSettingsModel(
            primary_color=settings_update.primary_color or "#2979FF",
            secondary_color=settings_update.secondary_color or "#0A1A3C",
            accent_color=settings_update.accent_color or "#3FFFD3",
            font_family=settings_update.font_family or "Inter",
            logo_url=settings_update.logo_url,
            user_id=current_user.id,
            organization_id=current_org.id,
        )
        db.add(settings)
    else:
        # Update existing settings
        update_data = settings_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    
    # Invalidate cache
    invalidate_brand_settings(current_org.id)
    
    return settings

