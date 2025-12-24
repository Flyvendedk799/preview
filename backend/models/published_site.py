"""SQLAlchemy ORM models for Published Sites and related content."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from backend.db import Base


class PublishedSite(Base):
    """Main published site model - represents a user's hosted blog/news site."""
    __tablename__ = "published_sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # Site name/title
    slug = Column(String(200), unique=True, index=True, nullable=False)  # URL-friendly identifier
    domain_id = Column(Integer, ForeignKey("domains.id"), unique=True, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Template and status
    template_id = Column(String(100), nullable=False, default="default")  # Template identifier
    status = Column(String(20), default="draft", nullable=False)  # draft, published, archived
    is_active = Column(Boolean, default=True, nullable=False)
    
    # SEO and metadata
    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    meta_keywords = Column(String(300), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    domain = relationship("Domain", backref="published_site")
    organization = relationship("Organization", backref="published_sites")
    posts = relationship("SitePost", back_populates="site", cascade="all, delete-orphan")
    categories = relationship("SiteCategory", back_populates="site", cascade="all, delete-orphan")
    pages = relationship("SitePage", back_populates="site", cascade="all, delete-orphan")
    menus = relationship("SiteMenu", back_populates="site", cascade="all, delete-orphan")
    media_items = relationship("SiteMedia", back_populates="site", cascade="all, delete-orphan")
    branding = relationship("SiteBranding", back_populates="site", uselist=False, cascade="all, delete-orphan")
    settings = relationship("SiteSettings", back_populates="site", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_published_sites_org_status', 'organization_id', 'status'),
        Index('ix_published_sites_domain', 'domain_id'),
    )


class SitePost(Base):
    """Blog posts for published sites."""
    __tablename__ = "site_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), nullable=False, index=True)
    
    # Content
    title = Column(String(200), nullable=False)
    slug = Column(String(250), nullable=False, index=True)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Markdown supported
    
    # Media
    featured_image = Column(String(500), nullable=True)
    featured_image_alt = Column(String(200), nullable=True)
    og_image = Column(String(500), nullable=True)
    
    # Author
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_name = Column(String(100), nullable=True)
    author_bio = Column(Text, nullable=True)
    author_avatar = Column(String(500), nullable=True)
    
    # Category
    category_id = Column(Integer, ForeignKey("site_categories.id"), nullable=True, index=True)
    
    # Tags
    tags = Column(Text, nullable=True)  # Comma-separated
    
    # Status
    status = Column(String(20), default="draft", nullable=False)  # draft, published, scheduled, archived
    is_featured = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    # Engagement
    read_time_minutes = Column(Integer, nullable=True)
    views_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    
    # SEO
    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    meta_keywords = Column(String(300), nullable=True)
    canonical_url = Column(String(500), nullable=True)
    no_index = Column(Boolean, default=False, nullable=False)
    schema_type = Column(String(50), default="Article")
    
    # Social
    twitter_title = Column(String(70), nullable=True)
    twitter_description = Column(String(200), nullable=True)
    twitter_image = Column(String(500), nullable=True)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="posts")
    category = relationship("SiteCategory", back_populates="posts")
    author = relationship("User", backref="site_posts")
    
    __table_args__ = (
        Index('ix_site_posts_site_slug', 'site_id', 'slug'),
        Index('ix_site_posts_status_published', 'status', 'published_at'),
        Index('ix_site_posts_featured_published', 'is_featured', 'published_at'),
    )


class SiteCategory(Base):
    """Categories for organizing site posts."""
    __tablename__ = "site_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    slug = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(20), default="#f97316")
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    
    # SEO
    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="categories")
    posts = relationship("SitePost", back_populates="category")
    
    __table_args__ = (
        Index('ix_site_categories_site_slug', 'site_id', 'slug'),
    )


class SitePage(Base):
    """Static pages (About, Contact, etc.) for published sites."""
    __tablename__ = "site_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    slug = Column(String(250), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Markdown/HTML
    
    # Status
    status = Column(String(20), default="draft", nullable=False)  # draft, published
    is_homepage = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)
    
    # SEO
    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    meta_keywords = Column(String(300), nullable=True)
    no_index = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="pages")
    
    __table_args__ = (
        Index('ix_site_pages_site_slug', 'site_id', 'slug'),
        Index('ix_site_pages_status', 'status'),
    )


class SiteMenu(Base):
    """Navigation menus for published sites."""
    __tablename__ = "site_menus"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)  # e.g., "Main Menu", "Footer Menu"
    location = Column(String(50), nullable=False, index=True)  # header, footer, sidebar
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="menus")
    items = relationship("SiteMenuItem", back_populates="menu", cascade="all, delete-orphan", order_by="SiteMenuItem.sort_order")
    
    __table_args__ = (
        Index('ix_site_menus_site_location', 'site_id', 'location'),
    )


class SiteMenuItem(Base):
    """Menu items with hierarchy support."""
    __tablename__ = "site_menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("site_menus.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("site_menu_items.id"), nullable=True, index=True)
    
    label = Column(String(100), nullable=False)
    url = Column(String(500), nullable=True)  # External URL or internal path
    type = Column(String(20), default="link", nullable=False)  # link, post, page, category
    target_id = Column(Integer, nullable=True)  # ID of post/page/category if type is not "link"
    
    icon = Column(String(50), nullable=True)
    css_class = Column(String(200), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    open_in_new_tab = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    menu = relationship("SiteMenu", back_populates="items")
    parent = relationship("SiteMenuItem", remote_side=[id], backref="children")
    
    __table_args__ = (
        Index('ix_site_menu_items_menu_order', 'menu_id', 'sort_order'),
        Index('ix_site_menu_items_parent', 'parent_id'),
    )


class SiteMedia(Base):
    """Media library for published sites."""
    __tablename__ = "site_media"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # R2 path or URL
    file_size = Column(Integer, nullable=False)  # Bytes
    mime_type = Column(String(100), nullable=False)
    
    # Image-specific
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    alt_text = Column(String(200), nullable=True)
    
    # Metadata
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="media_items")
    uploaded_by = relationship("User", backref="site_media")
    
    __table_args__ = (
        Index('ix_site_media_site_uploaded', 'site_id', 'uploaded_at'),
    )


class SiteBranding(Base):
    """Branding configuration for published sites."""
    __tablename__ = "site_branding"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), unique=True, nullable=False, index=True)
    
    # Logo
    logo_url = Column(String(500), nullable=True)
    logo_alt = Column(String(200), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    
    # Colors
    primary_color = Column(String(7), default="#f97316", nullable=False)  # Hex
    secondary_color = Column(String(7), nullable=True)
    accent_color = Column(String(7), nullable=True)
    background_color = Column(String(7), default="#ffffff", nullable=False)
    text_color = Column(String(7), default="#1f2937", nullable=False)
    
    # Typography
    font_family = Column(String(200), nullable=True)  # e.g., "Inter, sans-serif"
    heading_font = Column(String(200), nullable=True)
    body_font = Column(String(200), nullable=True)
    
    # Additional styling (JSON for flexibility)
    custom_css = Column(Text, nullable=True)
    theme_config = Column(JSON, nullable=True)  # Additional theme settings
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="branding")


class SiteSettings(Base):
    """Site-wide settings for published sites."""
    __tablename__ = "site_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("published_sites.id"), unique=True, nullable=False, index=True)
    
    # General
    site_description = Column(Text, nullable=True)
    language = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Contact
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Social Links
    social_links = Column(JSON, nullable=True)  # {platform: url}
    
    # Analytics
    google_analytics_id = Column(String(50), nullable=True)
    google_tag_manager_id = Column(String(50), nullable=True)
    facebook_pixel_id = Column(String(50), nullable=True)
    
    # SEO
    robots_txt = Column(Text, nullable=True)
    sitemap_enabled = Column(Boolean, default=True, nullable=False)
    
    # Features
    comments_enabled = Column(Boolean, default=False, nullable=False)
    newsletter_enabled = Column(Boolean, default=False, nullable=False)
    search_enabled = Column(Boolean, default=True, nullable=False)
    
    # Custom code
    header_code = Column(Text, nullable=True)  # Custom HTML/JS for <head>
    footer_code = Column(Text, nullable=True)  # Custom HTML/JS for </body>
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    site = relationship("PublishedSite", back_populates="settings")

