"""SQLAlchemy ORM model for Blog Posts."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.db import Base


class BlogCategory(Base):
    """Blog category model for organizing posts."""
    __tablename__ = "blog_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(20), default="#f97316")  # Hex color for UI
    icon = Column(String(50), nullable=True)  # Icon identifier
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # SEO fields
    meta_title = Column(String(70), nullable=True)  # SEO title (max 60-70 chars)
    meta_description = Column(String(160), nullable=True)  # SEO description (max 155-160 chars)
    
    # Relationships
    posts = relationship("BlogPost", back_populates="category")


class BlogPost(Base):
    """Blog post model with comprehensive SEO and content management features."""
    __tablename__ = "blog_posts"
    
    # Add indexes for common queries
    __table_args__ = (
        Index('ix_blog_posts_status_published', 'status', 'published_at'),
        Index('ix_blog_posts_featured_published', 'is_featured', 'published_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Core content fields
    title = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, index=True, nullable=False)
    excerpt = Column(Text, nullable=True)  # Short summary for listings (150-200 chars ideal)
    content = Column(Text, nullable=False)  # Full post content (Markdown supported)
    
    # Media
    featured_image = Column(String(500), nullable=True)  # URL to featured image
    featured_image_alt = Column(String(200), nullable=True)  # Alt text for accessibility/SEO
    og_image = Column(String(500), nullable=True)  # Open Graph image (1200x630 recommended)
    
    # Author (links to admin user)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_name = Column(String(100), nullable=True)  # Display name override
    author_bio = Column(Text, nullable=True)  # Brief author bio for this post
    author_avatar = Column(String(500), nullable=True)  # Author avatar URL
    
    # Category
    category_id = Column(Integer, ForeignKey("blog_categories.id"), nullable=True)
    
    # Tags (comma-separated for simplicity, can be normalized later)
    tags = Column(Text, nullable=True)  # Comma-separated tags
    
    # Status and visibility
    status = Column(String(20), default="draft", nullable=False)  # draft, published, scheduled, archived
    is_featured = Column(Boolean, default=False, nullable=False)  # Featured on homepage
    is_pinned = Column(Boolean, default=False, nullable=False)  # Pinned to top of listings
    
    # Reading/engagement
    read_time_minutes = Column(Integer, nullable=True)  # Estimated reading time
    views_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)  # When post went live
    scheduled_at = Column(DateTime, nullable=True)  # For scheduled publishing
    
    # SEO Meta Fields
    meta_title = Column(String(70), nullable=True)  # SEO title (overrides title if set)
    meta_description = Column(String(160), nullable=True)  # SEO meta description
    meta_keywords = Column(String(300), nullable=True)  # Comma-separated keywords
    canonical_url = Column(String(500), nullable=True)  # Canonical URL if different
    no_index = Column(Boolean, default=False, nullable=False)  # Prevent indexing
    
    # Structured data (JSON-LD)
    schema_type = Column(String(50), default="Article")  # Article, NewsArticle, BlogPosting, etc.
    
    # Social sharing
    twitter_title = Column(String(70), nullable=True)  # Twitter card title
    twitter_description = Column(String(200), nullable=True)  # Twitter card description
    twitter_image = Column(String(500), nullable=True)  # Twitter card image
    
    # Related content (comma-separated post IDs)
    related_post_ids = Column(String(200), nullable=True)
    
    # Relationships
    author = relationship("User", backref="blog_posts")
    category = relationship("BlogCategory", back_populates="posts")
    
    def calculate_read_time(self):
        """Calculate estimated reading time based on word count."""
        if self.content:
            # Average reading speed: 200-250 words per minute
            word_count = len(self.content.split())
            self.read_time_minutes = max(1, round(word_count / 225))
        return self.read_time_minutes
    
    def generate_excerpt(self, max_length: int = 160):
        """Generate excerpt from content if not set."""
        if not self.excerpt and self.content:
            # Strip markdown and get first paragraph
            import re
            clean_content = re.sub(r'[#*_\[\]()]', '', self.content)
            clean_content = re.sub(r'\n+', ' ', clean_content).strip()
            if len(clean_content) > max_length:
                self.excerpt = clean_content[:max_length-3].rsplit(' ', 1)[0] + '...'
            else:
                self.excerpt = clean_content
        return self.excerpt


