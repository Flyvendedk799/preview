"""Site management routes."""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from backend.schemas.site import PublishedSite, PublishedSiteCreate, PublishedSiteUpdate
from backend.models.published_site import PublishedSite as PublishedSiteModel
from backend.models.domain import Domain as DomainModel
from backend.models.user import User
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_current_org, role_required, get_paid_user
from backend.models.organization import Organization
from backend.models.organization_member import OrganizationRole
from backend.services.activity_logger import log_activity
from backend.services.site_service import (
    check_site_limit, generate_slug, ensure_unique_slug, get_site_by_id,
    create_default_branding, create_default_settings, publish_site, unpublish_site, get_site_stats
)

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=List[PublishedSite])
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Get all sites for the current organization."""
    sites = db.query(PublishedSiteModel).filter(
        PublishedSiteModel.organization_id == current_org.id
    ).order_by(PublishedSiteModel.created_at.desc()).all()
    return sites


@router.post("", response_model=PublishedSite, status_code=status.HTTP_201_CREATED)
def create_site(
    site_in: PublishedSiteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """Create a new site for the current organization (owner/admin only)."""
    # Check plan limits
    can_create, error_msg = check_site_limit(current_org, db)
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Verify domain exists and belongs to organization
    domain = db.query(DomainModel).filter(
        DomainModel.id == site_in.domain_id,
        DomainModel.organization_id == current_org.id
    ).first()
    
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found or not owned by this organization"
        )
    
    # Check if domain is already used by another site
    existing_site = db.query(PublishedSiteModel).filter(
        PublishedSiteModel.domain_id == site_in.domain_id
    ).first()
    
    if existing_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain is already used by another site"
        )
    
    # Generate slug if not provided
    slug = site_in.slug if site_in.slug else generate_slug(site_in.name)
    slug = ensure_unique_slug(db, slug)
    
    # Create site
    db_site = PublishedSiteModel(
        name=site_in.name,
        slug=slug,
        domain_id=site_in.domain_id,
        organization_id=current_org.id,
        template_id=site_in.template_id,
        status=site_in.status,
        is_active=site_in.is_active,
        meta_title=site_in.meta_title,
        meta_description=site_in.meta_description,
        meta_keywords=site_in.meta_keywords,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    
    # Link domain to site
    domain.site_id = db_site.id
    db.commit()
    
    # If site is published, set published_at timestamp
    if db_site.status == 'published' and not db_site.published_at:
        db_site.published_at = datetime.utcnow()
        db.commit()
        db.refresh(db_site)
    
    # Create default branding and settings
    create_default_branding(db, db_site.id)
    create_default_settings(db, db_site.id)
    
    # Log site creation
    log_activity(
        db,
        user_id=current_user.id,
        action="site.created",
        metadata={"site_id": db_site.id, "site_name": db_site.name, "domain_id": site_in.domain_id},
        request=request
    )
    
    return db_site


@router.get("/{site_id}", response_model=PublishedSite)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Get a site by ID for the current organization."""
    site = get_site_by_id(db, site_id, current_org.id)
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    return site


@router.get("/{site_id}/stats")
def get_site_statistics(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org)
):
    """Get statistics for a site."""
    site = get_site_by_id(db, site_id, current_org.id)
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    
    return get_site_stats(db, site_id)


@router.put("/{site_id}", response_model=PublishedSite)
def update_site(
    site_id: int,
    site_in: PublishedSiteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """Update a site (owner/admin only)."""
    site = get_site_by_id(db, site_id, current_org.id)
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    
    # Update fields
    update_data = site_in.model_dump(exclude_unset=True)
    
    # Handle slug update
    if 'slug' in update_data and update_data['slug']:
        update_data['slug'] = ensure_unique_slug(db, update_data['slug'], exclude_id=site_id)
    elif 'name' in update_data and update_data['name'] != site.name:
        # Regenerate slug if name changed and no explicit slug provided
        new_slug = generate_slug(update_data['name'])
        update_data['slug'] = ensure_unique_slug(db, new_slug, exclude_id=site_id)
    
    for key, value in update_data.items():
        setattr(site, key, value)
    
    site.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(site)
    
    # Log site update
    log_activity(
        db,
        user_id=current_user.id,
        action="site.updated",
        metadata={"site_id": site.id, "site_name": site.name},
        request=request
    )
    
    return site


@router.delete("/{site_id}")
def delete_site(
    site_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """Delete a site (owner/admin only)."""
    site = get_site_by_id(db, site_id, current_org.id)
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    
    site_name = site.name
    
    # Unlink domain from site
    if site.domain:
        site.domain.site_id = None
        db.commit()
    
    # Delete site (cascade will handle related records)
    db.delete(site)
    db.commit()
    
    # Log site deletion
    log_activity(
        db,
        user_id=current_user.id,
        action="site.deleted",
        metadata={"site_id": site_id, "site_name": site_name},
        request=request
    )
    
    return {"success": True}


@router.post("/{site_id}/publish", response_model=PublishedSite)
def publish_site_endpoint(
    site_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """Publish a site (owner/admin only)."""
    site = get_site_by_id(db, site_id, current_org.id)
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    
    try:
        updated_site = publish_site(db, site)
        
        # Log site publish
        log_activity(
            db,
            user_id=current_user.id,
            action="site.published",
            metadata={"site_id": site.id, "site_name": site.name},
            request=request
        )
        
        return updated_site
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{site_id}/unpublish", response_model=PublishedSite)
def unpublish_site_endpoint(
    site_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN]))
):
    """Unpublish a site (owner/admin only)."""
    site = get_site_by_id(db, site_id, current_org.id)
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    
    updated_site = unpublish_site(db, site)
    
    # Log site unpublish
    log_activity(
        db,
        user_id=current_user.id,
        action="site.unpublished",
        metadata={"site_id": site.id, "site_name": site.name},
        request=request
    )
    
    return updated_site

