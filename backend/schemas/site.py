"""Pydantic schemas for Published Sites and related content."""
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from backend.schemas.domain import Domain


# ============================================================================
# PublishedSite Schemas
# ============================================================================

class PublishedSiteBase(BaseModel):
    """Base schema for published site."""
    name: str = Field(..., max_length=200, description="Site name/title")
    slug: Optional[str] = Field(None, max_length=200, description="URL-friendly identifier")
    domain_id: int = Field(..., description="Domain ID")
    template_id: str = Field("default", max_length=100, description="Template identifier")
    status: str = Field("draft", pattern="^(draft|published|archived)$")
    is_active: bool = Field(True)
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    meta_keywords: Optional[str] = Field(None, max_length=300)


class PublishedSiteCreate(PublishedSiteBase):
    """Schema for creating a new site."""
    pass


class PublishedSiteUpdate(BaseModel):
    """Schema for updating a site."""
    name: Optional[str] = Field(None, max_length=200)
    slug: Optional[str] = Field(None, max_length=200)
    template_id: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    is_active: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    meta_keywords: Optional[str] = Field(None, max_length=300)


class PublishedSite(PublishedSiteBase):
    """Published site schema with all fields."""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    domain: Optional["Domain"] = None  # Domain relationship
    
    class Config:
        from_attributes = True


# ============================================================================
# SitePost Schemas
# ============================================================================

class SitePostBase(BaseModel):
    """Base schema for site post."""
    title: str = Field(..., max_length=200)
    slug: Optional[str] = Field(None, max_length=250)
    excerpt: Optional[str] = None
    content: str
    featured_image: Optional[str] = Field(None, max_length=500)
    featured_image_alt: Optional[str] = Field(None, max_length=200)
    og_image: Optional[str] = Field(None, max_length=500)
    author_name: Optional[str] = Field(None, max_length=100)
    author_bio: Optional[str] = None
    author_avatar: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    tags: Optional[str] = None
    status: str = Field("draft", pattern="^(draft|published|scheduled|archived)$")
    is_featured: bool = False
    is_pinned: bool = False
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    canonical_url: Optional[str] = Field(None, max_length=500)
    no_index: bool = False
    schema_type: str = Field("Article", max_length=50)
    twitter_title: Optional[str] = Field(None, max_length=70)
    twitter_description: Optional[str] = Field(None, max_length=200)
    twitter_image: Optional[str] = Field(None, max_length=500)


class SitePostCreate(SitePostBase):
    """Schema for creating a new post."""
    pass


class SitePostUpdate(BaseModel):
    """Schema for updating a post."""
    title: Optional[str] = Field(None, max_length=200)
    slug: Optional[str] = Field(None, max_length=250)
    excerpt: Optional[str] = None
    content: Optional[str] = None
    featured_image: Optional[str] = Field(None, max_length=500)
    featured_image_alt: Optional[str] = Field(None, max_length=200)
    og_image: Optional[str] = Field(None, max_length=500)
    author_name: Optional[str] = Field(None, max_length=100)
    author_bio: Optional[str] = None
    author_avatar: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    tags: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|scheduled|archived)$")
    is_featured: Optional[bool] = None
    is_pinned: Optional[bool] = None
    scheduled_at: Optional[datetime] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    canonical_url: Optional[str] = Field(None, max_length=500)
    no_index: Optional[bool] = None
    schema_type: Optional[str] = Field(None, max_length=50)
    twitter_title: Optional[str] = Field(None, max_length=70)
    twitter_description: Optional[str] = Field(None, max_length=200)
    twitter_image: Optional[str] = Field(None, max_length=500)


class SitePostListItem(BaseModel):
    """Lightweight post list item."""
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    author_name: Optional[str]
    category_id: Optional[int]
    status: str
    is_featured: bool
    is_pinned: bool
    read_time_minutes: Optional[int]
    views_count: int
    published_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SitePost(SitePostBase):
    """Site post schema with all fields."""
    id: int
    site_id: int
    author_id: int
    read_time_minutes: Optional[int]
    views_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaginatedSitePosts(BaseModel):
    """Paginated posts response."""
    items: List[SitePostListItem]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ============================================================================
# SiteCategory Schemas
# ============================================================================

class SiteCategoryBase(BaseModel):
    """Base schema for site category."""
    name: str = Field(..., max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    color: str = Field("#f97316", max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    sort_order: int = 0
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)


class SiteCategoryCreate(SiteCategoryBase):
    """Schema for creating a new category."""
    pass


class SiteCategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)


class SiteCategory(SiteCategoryBase):
    """Site category schema with all fields."""
    id: int
    site_id: int
    created_at: datetime
    updated_at: datetime
    post_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ============================================================================
# SitePage Schemas
# ============================================================================

class SitePageBase(BaseModel):
    """Base schema for site page."""
    title: str = Field(..., max_length=200)
    slug: Optional[str] = Field(None, max_length=250)
    content: str
    status: str = Field("draft", pattern="^(draft|published)$")
    is_homepage: bool = False
    sort_order: int = 0
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    no_index: bool = False


class SitePageCreate(SitePageBase):
    """Schema for creating a new page."""
    pass


class SitePageUpdate(BaseModel):
    """Schema for updating a page."""
    title: Optional[str] = Field(None, max_length=200)
    slug: Optional[str] = Field(None, max_length=250)
    content: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published)$")
    is_homepage: Optional[bool] = None
    sort_order: Optional[int] = None
    meta_title: Optional[str] = Field(None, max_length=70)
    meta_description: Optional[str] = Field(None, max_length=160)
    meta_keywords: Optional[str] = Field(None, max_length=300)
    no_index: Optional[bool] = None


class SitePage(SitePageBase):
    """Site page schema with all fields."""
    id: int
    site_id: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# SiteMenu Schemas
# ============================================================================

class SiteMenuItemBase(BaseModel):
    """Base schema for menu item."""
    label: str = Field(..., max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    type: str = Field("link", pattern="^(link|post|page|category)$")
    target_id: Optional[int] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = Field(None, max_length=50)
    css_class: Optional[str] = Field(None, max_length=200)
    sort_order: int = 0
    is_active: bool = True
    open_in_new_tab: bool = False


class SiteMenuItemCreate(SiteMenuItemBase):
    """Schema for creating a menu item."""
    pass


class SiteMenuItemUpdate(BaseModel):
    """Schema for updating a menu item."""
    label: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    type: Optional[str] = Field(None, pattern="^(link|post|page|category)$")
    target_id: Optional[int] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = Field(None, max_length=50)
    css_class: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    open_in_new_tab: Optional[bool] = None


class SiteMenuItem(SiteMenuItemBase):
    """Menu item schema with all fields."""
    id: int
    menu_id: int
    created_at: datetime
    updated_at: datetime
    children: Optional[List['SiteMenuItem']] = []
    
    class Config:
        from_attributes = True


class SiteMenuBase(BaseModel):
    """Base schema for site menu."""
    name: str = Field(..., max_length=100)
    location: str = Field(..., pattern="^(header|footer|sidebar)$")
    is_active: bool = True


class SiteMenuCreate(SiteMenuBase):
    """Schema for creating a menu."""
    items: Optional[List[SiteMenuItemCreate]] = []


class SiteMenuUpdate(BaseModel):
    """Schema for updating a menu."""
    name: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, pattern="^(header|footer|sidebar)$")
    is_active: Optional[bool] = None


class SiteMenu(SiteMenuBase):
    """Site menu schema with all fields."""
    id: int
    site_id: int
    items: List[SiteMenuItem] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SiteMedia Schemas
# ============================================================================

class SiteMediaBase(BaseModel):
    """Base schema for site media."""
    filename: str = Field(..., max_length=255)
    original_filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_size: int
    mime_type: str = Field(..., max_length=100)
    width: Optional[int] = None
    height: Optional[int] = None
    alt_text: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    caption: Optional[str] = None


class SiteMediaCreate(SiteMediaBase):
    """Schema for creating media."""
    pass


class SiteMediaUpdate(BaseModel):
    """Schema for updating media."""
    alt_text: Optional[str] = Field(None, max_length=200)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    caption: Optional[str] = None


class SiteMedia(SiteMediaBase):
    """Site media schema with all fields."""
    id: int
    site_id: int
    uploaded_at: datetime
    uploaded_by_id: int
    
    class Config:
        from_attributes = True


# ============================================================================
# SiteBranding Schemas
# ============================================================================

class SiteBrandingBase(BaseModel):
    """Base schema for site branding."""
    logo_url: Optional[str] = Field(None, max_length=500)
    logo_alt: Optional[str] = Field(None, max_length=200)
    favicon_url: Optional[str] = Field(None, max_length=500)
    primary_color: str = Field("#f97316", max_length=7)
    secondary_color: Optional[str] = Field(None, max_length=7)
    accent_color: Optional[str] = Field(None, max_length=7)
    background_color: str = Field("#ffffff", max_length=7)
    text_color: str = Field("#1f2937", max_length=7)
    font_family: Optional[str] = Field(None, max_length=200)
    heading_font: Optional[str] = Field(None, max_length=200)
    body_font: Optional[str] = Field(None, max_length=200)
    custom_css: Optional[str] = None
    theme_config: Optional[Dict[str, Any]] = None


class SiteBrandingCreate(SiteBrandingBase):
    """Schema for creating branding."""
    pass


class SiteBrandingUpdate(BaseModel):
    """Schema for updating branding."""
    logo_url: Optional[str] = Field(None, max_length=500)
    logo_alt: Optional[str] = Field(None, max_length=200)
    favicon_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)
    secondary_color: Optional[str] = Field(None, max_length=7)
    accent_color: Optional[str] = Field(None, max_length=7)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)
    font_family: Optional[str] = Field(None, max_length=200)
    heading_font: Optional[str] = Field(None, max_length=200)
    body_font: Optional[str] = Field(None, max_length=200)
    custom_css: Optional[str] = None
    theme_config: Optional[Dict[str, Any]] = None


class SiteBranding(SiteBrandingBase):
    """Site branding schema with all fields."""
    id: int
    site_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SiteSettings Schemas
# ============================================================================

class SiteSettingsBase(BaseModel):
    """Base schema for site settings."""
    site_description: Optional[str] = None
    language: str = Field("en", max_length=10)
    timezone: str = Field("UTC", max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    google_analytics_id: Optional[str] = Field(None, max_length=50)
    google_tag_manager_id: Optional[str] = Field(None, max_length=50)
    facebook_pixel_id: Optional[str] = Field(None, max_length=50)
    robots_txt: Optional[str] = None
    sitemap_enabled: bool = True
    comments_enabled: bool = False
    newsletter_enabled: bool = False
    search_enabled: bool = True
    header_code: Optional[str] = None
    footer_code: Optional[str] = None


class SiteSettingsCreate(SiteSettingsBase):
    """Schema for creating settings."""
    pass


class SiteSettingsUpdate(BaseModel):
    """Schema for updating settings."""
    site_description: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    google_analytics_id: Optional[str] = Field(None, max_length=50)
    google_tag_manager_id: Optional[str] = Field(None, max_length=50)
    facebook_pixel_id: Optional[str] = Field(None, max_length=50)
    robots_txt: Optional[str] = None
    sitemap_enabled: Optional[bool] = None
    comments_enabled: Optional[bool] = None
    newsletter_enabled: Optional[bool] = None
    search_enabled: Optional[bool] = None
    header_code: Optional[str] = None
    footer_code: Optional[str] = None


class SiteSettings(SiteSettingsBase):
    """Site settings schema with all fields."""
    id: int
    site_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

