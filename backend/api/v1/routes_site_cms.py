"""Site CMS API routes for managing site content."""
import re
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, func
from backend.db.session import get_db
from backend.core.deps import get_current_user, get_current_org, role_required
from backend.models.user import User
from backend.models.organization import Organization
from backend.models.organization_member import OrganizationRole
from backend.models.published_site import PublishedSite
from backend.models.site_post import SitePost
from backend.models.site_category import SiteCategory
from backend.models.site_page import SitePage
from backend.models.site_menu import SiteMenu, SiteMenuItem
from backend.models.site_media import SiteMedia
from backend.models.site_branding import SiteBranding
from backend.models.site_settings import SiteSettings
from backend.schemas.site import (
    SitePostCreate, SitePostUpdate, SitePost, SitePostListItem, PaginatedSitePosts,
    SiteCategoryCreate, SiteCategoryUpdate, SiteCategory,
    SitePageCreate, SitePageUpdate, SitePage,
    SiteMenuCreate, SiteMenuUpdate, SiteMenu, SiteMenuItemCreate, SiteMenuItemUpdate, SiteMenuItem,
    SiteMediaCreate, SiteMediaUpdate, SiteMedia,
    SiteBrandingCreate, SiteBrandingUpdate, SiteBranding,
    SiteSettingsCreate, SiteSettingsUpdate, SiteSettings
)
from backend.services.site_service import (
    get_site_by_id, create_default_branding, create_default_settings
)
from backend.services.activity_logger import log_activity

router = APIRouter(prefix="/sites/{site_id}", tags=["site-cms"])


# ============================================================================
# Helper Functions
# ============================================================================

def generate_slug(text: str, max_length: int = 250) -> str:
    """Generate URL-friendly slug from text."""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    return slug[:max_length]


def ensure_unique_post_slug(db: Session, site_id: int, slug: str, exclude_id: Optional[int] = None) -> str:
    """Ensure post slug is unique within site."""
    original_slug = slug
    counter = 1
    while True:
        query = db.query(SitePost).filter(SitePost.site_id == site_id, SitePost.slug == slug)
        if exclude_id:
            query = query.filter(SitePost.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{original_slug}-{counter}"
        counter += 1


def ensure_unique_category_slug(db: Session, site_id: int, slug: str, exclude_id: Optional[int] = None) -> str:
    """Ensure category slug is unique within site."""
    original_slug = slug
    counter = 1
    while True:
        query = db.query(SiteCategory).filter(SiteCategory.site_id == site_id, SiteCategory.slug == slug)
        if exclude_id:
            query = query.filter(SiteCategory.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{original_slug}-{counter}"
        counter += 1


def ensure_unique_page_slug(db: Session, site_id: int, slug: str, exclude_id: Optional[int] = None) -> str:
    """Ensure page slug is unique within site."""
    original_slug = slug
    counter = 1
    while True:
        query = db.query(SitePage).filter(SitePage.site_id == site_id, SitePage.slug == slug)
        if exclude_id:
            query = query.filter(SitePage.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{original_slug}-{counter}"
        counter += 1


def calculate_read_time(content: str) -> int:
    """Calculate estimated reading time in minutes."""
    word_count = len(content.split())
    return max(1, round(word_count / 225))


# ============================================================================
# Site Dependency
# ============================================================================

def get_site_dependency(
    site_id: int,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_org)
) -> PublishedSite:
    """Dependency to get and verify site access."""
    site = get_site_by_id(db, site_id, current_org.id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site with ID {site_id} not found"
        )
    return site


# ============================================================================
# Posts Routes
# ============================================================================

@router.get("/posts", response_model=PaginatedSitePosts)
def list_posts(
    site_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """List posts for a site."""
    query = db.query(SitePost).filter(SitePost.site_id == site_id)
    
    if status_filter:
        query = query.filter(SitePost.status == status_filter)
    
    if category_id:
        query = query.filter(SitePost.category_id == category_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                SitePost.title.ilike(search_term),
                SitePost.excerpt.ilike(search_term),
                SitePost.content.ilike(search_term)
            )
        )
    
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    query = query.order_by(desc(SitePost.is_pinned), desc(SitePost.created_at))
    offset = (page - 1) * per_page
    posts = query.offset(offset).limit(per_page).all()
    
    items = [SitePostListItem.model_validate(post) for post in posts]
    
    return PaginatedSitePosts(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.post("/posts", response_model=SitePost, status_code=status.HTTP_201_CREATED)
def create_post(
    site_id: int,
    post_in: SitePostCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Create a new post."""
    slug = post_in.slug if post_in.slug else generate_slug(post_in.title)
    slug = ensure_unique_post_slug(db, site_id, slug)
    
    post = SitePost(
        **post_in.model_dump(exclude={'slug'}),
        site_id=site_id,
        slug=slug,
        author_id=current_user.id,
        read_time_minutes=calculate_read_time(post_in.content),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    if post.status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.post.created",
        metadata={"site_id": site_id, "post_id": post.id, "post_title": post.title},
        request=request
    )
    
    return post


@router.get("/posts/{post_id}", response_model=SitePost)
def get_post(
    site_id: int,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Get a post by ID."""
    post = db.query(SitePost).filter(
        SitePost.id == post_id,
        SitePost.site_id == site_id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return post


@router.put("/posts/{post_id}", response_model=SitePost)
def update_post(
    site_id: int,
    post_id: int,
    post_in: SitePostUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update a post."""
    post = db.query(SitePost).filter(
        SitePost.id == post_id,
        SitePost.site_id == site_id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    update_data = post_in.model_dump(exclude_unset=True)
    
    if 'slug' in update_data and update_data['slug']:
        update_data['slug'] = ensure_unique_post_slug(db, site_id, update_data['slug'], exclude_id=post_id)
    elif 'title' in update_data and update_data['title'] != post.title:
        new_slug = generate_slug(update_data['title'])
        update_data['slug'] = ensure_unique_post_slug(db, site_id, new_slug, exclude_id=post_id)
    
    if 'content' in update_data:
        update_data['read_time_minutes'] = calculate_read_time(update_data['content'])
    
    for key, value in update_data.items():
        setattr(post, key, value)
    
    if post.status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.post.updated",
        metadata={"site_id": site_id, "post_id": post.id},
        request=request
    )
    
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    site_id: int,
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Delete a post."""
    post = db.query(SitePost).filter(
        SitePost.id == post_id,
        SitePost.site_id == site_id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.post.deleted",
        metadata={"site_id": site_id, "post_id": post_id},
        request=request
    )


# ============================================================================
# Categories Routes
# ============================================================================

@router.get("/categories", response_model=List[SiteCategory])
def list_categories(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """List categories for a site."""
    categories = db.query(SiteCategory).filter(
        SiteCategory.site_id == site_id
    ).order_by(asc(SiteCategory.sort_order), asc(SiteCategory.name)).all()
    
    result = []
    for cat in categories:
        post_count = db.query(func.count(SitePost.id)).filter(
            SitePost.category_id == cat.id
        ).scalar()
        cat_dict = SiteCategory.model_validate(cat).model_dump()
        cat_dict['post_count'] = post_count
        result.append(cat_dict)
    
    return result


@router.post("/categories", response_model=SiteCategory, status_code=status.HTTP_201_CREATED)
def create_category(
    site_id: int,
    category_in: SiteCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Create a new category."""
    slug = category_in.slug if category_in.slug else generate_slug(category_in.name, max_length=120)
    slug = ensure_unique_category_slug(db, site_id, slug)
    
    category = SiteCategory(
        **category_in.model_dump(exclude={'slug'}),
        site_id=site_id,
        slug=slug,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.category.created",
        metadata={"site_id": site_id, "category_id": category.id},
        request=request
    )
    
    return category


@router.put("/categories/{category_id}", response_model=SiteCategory)
def update_category(
    site_id: int,
    category_id: int,
    category_in: SiteCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update a category."""
    category = db.query(SiteCategory).filter(
        SiteCategory.id == category_id,
        SiteCategory.site_id == site_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_in.model_dump(exclude_unset=True)
    
    if 'slug' in update_data and update_data['slug']:
        update_data['slug'] = ensure_unique_category_slug(db, site_id, update_data['slug'], exclude_id=category_id)
    elif 'name' in update_data and update_data['name'] != category.name:
        new_slug = generate_slug(update_data['name'], max_length=120)
        update_data['slug'] = ensure_unique_category_slug(db, site_id, new_slug, exclude_id=category_id)
    
    for key, value in update_data.items():
        setattr(category, key, value)
    
    category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(category)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.category.updated",
        metadata={"site_id": site_id, "category_id": category_id},
        request=request
    )
    
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    site_id: int,
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Delete a category."""
    category = db.query(SiteCategory).filter(
        SiteCategory.id == category_id,
        SiteCategory.site_id == site_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Set posts to uncategorized
    db.query(SitePost).filter(SitePost.category_id == category_id).update(
        {SitePost.category_id: None}
    )
    
    db.delete(category)
    db.commit()
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.category.deleted",
        metadata={"site_id": site_id, "category_id": category_id},
        request=request
    )


# ============================================================================
# Pages Routes
# ============================================================================

@router.get("/pages", response_model=List[SitePage])
def list_pages(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """List pages for a site."""
    pages = db.query(SitePage).filter(
        SitePage.site_id == site_id
    ).order_by(asc(SitePage.sort_order), asc(SitePage.title)).all()
    
    return pages


@router.post("/pages", response_model=SitePage, status_code=status.HTTP_201_CREATED)
def create_page(
    site_id: int,
    page_in: SitePageCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Create a new page."""
    slug = page_in.slug if page_in.slug else generate_slug(page_in.title)
    slug = ensure_unique_page_slug(db, site_id, slug)
    
    # If this is set as homepage, unset others
    if page_in.is_homepage:
        db.query(SitePage).filter(
            SitePage.site_id == site_id,
            SitePage.is_homepage == True
        ).update({SitePage.is_homepage: False})
    
    page = SitePage(
        **page_in.model_dump(exclude={'slug'}),
        site_id=site_id,
        slug=slug,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    if page.status == "published" and not page.published_at:
        page.published_at = datetime.utcnow()
    
    db.add(page)
    db.commit()
    db.refresh(page)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.page.created",
        metadata={"site_id": site_id, "page_id": page.id},
        request=request
    )
    
    return page


@router.get("/pages/{page_id}", response_model=SitePage)
def get_page(
    site_id: int,
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Get a page by ID."""
    page = db.query(SitePage).filter(
        SitePage.id == page_id,
        SitePage.site_id == site_id
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page


@router.put("/pages/{page_id}", response_model=SitePage)
def update_page(
    site_id: int,
    page_id: int,
    page_in: SitePageUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update a page."""
    page = db.query(SitePage).filter(
        SitePage.id == page_id,
        SitePage.site_id == site_id
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    update_data = page_in.model_dump(exclude_unset=True)
    
    if 'slug' in update_data and update_data['slug']:
        update_data['slug'] = ensure_unique_page_slug(db, site_id, update_data['slug'], exclude_id=page_id)
    elif 'title' in update_data and update_data['title'] != page.title:
        new_slug = generate_slug(update_data['title'])
        update_data['slug'] = ensure_unique_page_slug(db, site_id, new_slug, exclude_id=page_id)
    
    # Handle homepage flag
    if 'is_homepage' in update_data and update_data['is_homepage']:
        db.query(SitePage).filter(
            SitePage.site_id == site_id,
            SitePage.is_homepage == True,
            SitePage.id != page_id
        ).update({SitePage.is_homepage: False})
    
    for key, value in update_data.items():
        setattr(page, key, value)
    
    if page.status == "published" and not page.published_at:
        page.published_at = datetime.utcnow()
    
    page.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(page)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.page.updated",
        metadata={"site_id": site_id, "page_id": page_id},
        request=request
    )
    
    return page


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    site_id: int,
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Delete a page."""
    page = db.query(SitePage).filter(
        SitePage.id == page_id,
        SitePage.site_id == site_id
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    db.delete(page)
    db.commit()
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.page.deleted",
        metadata={"site_id": site_id, "page_id": page_id},
        request=request
    )


# ============================================================================
# Menus Routes
# ============================================================================

@router.get("/menus", response_model=List[SiteMenu])
def list_menus(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """List menus for a site."""
    menus = db.query(SiteMenu).filter(
        SiteMenu.site_id == site_id
    ).order_by(asc(SiteMenu.location), asc(SiteMenu.name)).all()
    
    return menus


@router.post("/menus", response_model=SiteMenu, status_code=status.HTTP_201_CREATED)
def create_menu(
    site_id: int,
    menu_in: SiteMenuCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Create a new menu."""
    menu = SiteMenu(
        **menu_in.model_dump(exclude={'items'}),
        site_id=site_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(menu)
    db.flush()
    
    # Create menu items
    if menu_in.items:
        for item_data in menu_in.items:
            item = SiteMenuItem(
                **item_data.model_dump(),
                menu_id=menu.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(item)
    
    db.commit()
    db.refresh(menu)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.menu.created",
        metadata={"site_id": site_id, "menu_id": menu.id},
        request=request
    )
    
    return menu


@router.get("/menus/{menu_id}", response_model=SiteMenu)
def get_menu(
    site_id: int,
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Get a menu by ID."""
    menu = db.query(SiteMenu).filter(
        SiteMenu.id == menu_id,
        SiteMenu.site_id == site_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    return menu


@router.put("/menus/{menu_id}", response_model=SiteMenu)
def update_menu(
    site_id: int,
    menu_id: int,
    menu_in: SiteMenuUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update a menu."""
    menu = db.query(SiteMenu).filter(
        SiteMenu.id == menu_id,
        SiteMenu.site_id == site_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    update_data = menu_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(menu, key, value)
    
    menu.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(menu)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.menu.updated",
        metadata={"site_id": site_id, "menu_id": menu_id},
        request=request
    )
    
    return menu


@router.delete("/menus/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    site_id: int,
    menu_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Delete a menu."""
    menu = db.query(SiteMenu).filter(
        SiteMenu.id == menu_id,
        SiteMenu.site_id == site_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    db.delete(menu)
    db.commit()
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.menu.deleted",
        metadata={"site_id": site_id, "menu_id": menu_id},
        request=request
    )


# Menu Items Routes
@router.post("/menus/{menu_id}/items", response_model=SiteMenuItem, status_code=status.HTTP_201_CREATED)
def create_menu_item(
    site_id: int,
    menu_id: int,
    item_in: SiteMenuItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Create a menu item."""
    # Verify menu belongs to site
    menu = db.query(SiteMenu).filter(
        SiteMenu.id == menu_id,
        SiteMenu.site_id == site_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    item = SiteMenuItem(
        **item_in.model_dump(),
        menu_id=menu_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return item


@router.put("/menus/{menu_id}/items/{item_id}", response_model=SiteMenuItem)
def update_menu_item(
    site_id: int,
    menu_id: int,
    item_id: int,
    item_in: SiteMenuItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update a menu item."""
    item = db.query(SiteMenuItem).join(SiteMenu).filter(
        SiteMenuItem.id == item_id,
        SiteMenu.id == menu_id,
        SiteMenu.site_id == site_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    update_data = item_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(item, key, value)
    
    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/menus/{menu_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    site_id: int,
    menu_id: int,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Delete a menu item."""
    item = db.query(SiteMenuItem).join(SiteMenu).filter(
        SiteMenuItem.id == item_id,
        SiteMenu.id == menu_id,
        SiteMenu.site_id == site_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    db.delete(item)
    db.commit()


# ============================================================================
# Media Routes
# ============================================================================

@router.get("/media", response_model=List[SiteMedia])
def list_media(
    site_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """List media for a site."""
    offset = (page - 1) * per_page
    media_items = db.query(SiteMedia).filter(
        SiteMedia.site_id == site_id
    ).order_by(desc(SiteMedia.uploaded_at)).offset(offset).limit(per_page).all()
    
    return media_items


@router.post("/media", response_model=SiteMedia, status_code=status.HTTP_201_CREATED)
def create_media(
    site_id: int,
    media_in: SiteMediaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Create a media entry."""
    media = SiteMedia(
        **media_in.model_dump(),
        site_id=site_id,
        uploaded_by_id=current_user.id,
        uploaded_at=datetime.utcnow()
    )
    
    db.add(media)
    db.commit()
    db.refresh(media)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.media.created",
        metadata={"site_id": site_id, "media_id": media.id},
        request=request
    )
    
    return media


@router.put("/media/{media_id}", response_model=SiteMedia)
def update_media(
    site_id: int,
    media_id: int,
    media_in: SiteMediaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.EDITOR])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update media metadata."""
    media = db.query(SiteMedia).filter(
        SiteMedia.id == media_id,
        SiteMedia.site_id == site_id
    ).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    update_data = media_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(media, key, value)
    
    db.commit()
    db.refresh(media)
    
    return media


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    site_id: int,
    media_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Delete a media item."""
    media = db.query(SiteMedia).filter(
        SiteMedia.id == media_id,
        SiteMedia.site_id == site_id
    ).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    db.delete(media)
    db.commit()
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.media.deleted",
        metadata={"site_id": site_id, "media_id": media_id},
        request=request
    )


# ============================================================================
# Branding Routes
# ============================================================================

@router.get("/branding", response_model=SiteBranding)
def get_branding(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Get branding for a site."""
    branding = db.query(SiteBranding).filter(
        SiteBranding.site_id == site_id
    ).first()
    
    if not branding:
        # Create default branding
        branding = create_default_branding(db, site_id)
    
    return branding


@router.put("/branding", response_model=SiteBranding)
def update_branding(
    site_id: int,
    branding_in: SiteBrandingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update branding for a site."""
    branding = db.query(SiteBranding).filter(
        SiteBranding.site_id == site_id
    ).first()
    
    if not branding:
        # Create if doesn't exist
        branding = SiteBranding(
            site_id=site_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(branding)
        db.flush()
    
    update_data = branding_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(branding, key, value)
    
    branding.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(branding)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.branding.updated",
        metadata={"site_id": site_id},
        request=request
    )
    
    return branding


# ============================================================================
# Settings Routes
# ============================================================================

@router.get("/settings", response_model=SiteSettings)
def get_settings(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Get settings for a site."""
    settings = db.query(SiteSettings).filter(
        SiteSettings.site_id == site_id
    ).first()
    
    if not settings:
        # Create default settings
        settings = create_default_settings(db, site_id)
    
    return settings


@router.put("/settings", response_model=SiteSettings)
def update_settings(
    site_id: int,
    settings_in: SiteSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    current_role: OrganizationRole = Depends(role_required([OrganizationRole.OWNER, OrganizationRole.ADMIN])),
    site: PublishedSite = Depends(get_site_dependency)
):
    """Update settings for a site."""
    settings = db.query(SiteSettings).filter(
        SiteSettings.site_id == site_id
    ).first()
    
    if not settings:
        # Create if doesn't exist
        settings = SiteSettings(
            site_id=site_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(settings)
        db.flush()
    
    update_data = settings_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="site.settings.updated",
        metadata={"site_id": site_id},
        request=request
    )
    
    return settings

