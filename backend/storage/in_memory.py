"""
DEPRECATED: In-memory data storage.

This module is no longer used. The application now uses SQLAlchemy with SQLite/PostgreSQL.
Kept for reference only. All routes now use database-backed storage via backend/db/session.py.
"""
from datetime import datetime
from typing import List, Optional, Dict
from backend.schemas.domain import Domain, DomainCreate
from backend.schemas.brand import BrandSettings, BrandSettingsUpdate
from backend.schemas.preview import Preview
from backend.schemas.analytics import AnalyticsSummary, TopDomain


# In-memory storage
DOMAINS: List[Dict] = [
    {
        "id": 1,
        "name": "example.com",
        "environment": "production",
        "status": "active",
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "monthly_clicks": 1234,
    },
    {
        "id": 2,
        "name": "mysite.io",
        "environment": "production",
        "status": "active",
        "created_at": datetime(2024, 1, 10, 10, 0, 0),
        "monthly_clicks": 892,
    },
    {
        "id": 3,
        "name": "test.dev",
        "environment": "staging",
        "status": "pending",
        "created_at": datetime(2024, 1, 20, 10, 0, 0),
        "monthly_clicks": 0,
    },
    {
        "id": 4,
        "name": "demo.app",
        "environment": "production",
        "status": "active",
        "created_at": datetime(2024, 1, 5, 10, 0, 0),
        "monthly_clicks": 456,
    },
]

BRAND_SETTINGS: Dict = {
    "id": 1,
    "primary_color": "#2979FF",
    "secondary_color": "#0A1A3C",
    "accent_color": "#3FFFD3",
    "font_family": "Inter",
    "logo_url": None,
}

PREVIEWS: List[Dict] = [
    {
        "id": 1,
        "url": "https://example.com/product",
        "domain": "example.com",
        "title": "Product Page",
        "type": "product",
        "image_url": "https://example.com/images/product.jpg",
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "monthly_clicks": 1234,
    },
    {
        "id": 2,
        "url": "https://example.com/blog",
        "domain": "example.com",
        "title": "Blog Post",
        "type": "blog",
        "image_url": "https://example.com/images/blog.jpg",
        "created_at": datetime(2024, 1, 14, 10, 0, 0),
        "monthly_clicks": 892,
    },
    {
        "id": 3,
        "url": "https://example.com/landing",
        "domain": "example.com",
        "title": "Landing Page",
        "type": "landing",
        "image_url": "https://example.com/images/landing.jpg",
        "created_at": datetime(2024, 1, 13, 10, 0, 0),
        "monthly_clicks": 654,
    },
    {
        "id": 4,
        "url": "https://example.com/feature",
        "domain": "example.com",
        "title": "Product Feature",
        "type": "product",
        "image_url": "https://example.com/images/feature.jpg",
        "created_at": datetime(2024, 1, 12, 10, 0, 0),
        "monthly_clicks": 456,
    },
    {
        "id": 5,
        "url": "https://mysite.io/article",
        "domain": "mysite.io",
        "title": "Article",
        "type": "blog",
        "image_url": "https://mysite.io/images/article.jpg",
        "created_at": datetime(2024, 1, 11, 10, 0, 0),
        "monthly_clicks": 321,
    },
    {
        "id": 6,
        "url": "https://example.com",
        "domain": "example.com",
        "title": "Homepage",
        "type": "landing",
        "image_url": "https://example.com/images/homepage.jpg",
        "created_at": datetime(2024, 1, 10, 10, 0, 0),
        "monthly_clicks": 2100,
    },
]


# Domain operations
def list_domains() -> List[Domain]:
    """List all domains."""
    return [Domain(**domain) for domain in DOMAINS]


def get_domain_by_id(domain_id: int) -> Optional[Domain]:
    """Get a domain by ID."""
    for domain in DOMAINS:
        if domain["id"] == domain_id:
            return Domain(**domain)
    return None


def add_domain(domain_create: DomainCreate) -> Domain:
    """Add a new domain."""
    new_id = max([d["id"] for d in DOMAINS], default=0) + 1
    new_domain = {
        "id": new_id,
        "name": domain_create.name,
        "environment": domain_create.environment,
        "status": domain_create.status,
        "created_at": datetime.now(),
        "monthly_clicks": 0,
    }
    DOMAINS.append(new_domain)
    return Domain(**new_domain)


def delete_domain(domain_id: int) -> bool:
    """Delete a domain by ID."""
    global DOMAINS
    initial_length = len(DOMAINS)
    DOMAINS = [d for d in DOMAINS if d["id"] != domain_id]
    return len(DOMAINS) < initial_length


# Brand settings operations
def get_brand_settings() -> BrandSettings:
    """Get current brand settings."""
    return BrandSettings(**BRAND_SETTINGS)


def update_brand_settings(update: BrandSettingsUpdate) -> BrandSettings:
    """Update brand settings."""
    global BRAND_SETTINGS
    update_dict = update.model_dump(exclude_unset=True)
    BRAND_SETTINGS.update(update_dict)
    return BrandSettings(**BRAND_SETTINGS)


# Preview operations
def list_previews(preview_type: Optional[str] = None) -> List[Preview]:
    """List all previews, optionally filtered by type."""
    previews = PREVIEWS
    if preview_type:
        previews = [p for p in PREVIEWS if p["type"].lower() == preview_type.lower()]
    return [Preview(**preview) for preview in previews]


def list_previews_by_type(preview_type: str) -> List[Preview]:
    """List previews filtered by type."""
    return list_previews(preview_type)


# Analytics operations
def get_analytics_summary(period: str) -> AnalyticsSummary:
    """Get analytics summary for a given period."""
    # Calculate totals from current data
    total_clicks = sum(d["monthly_clicks"] for d in DOMAINS)
    total_previews = len(PREVIEWS)
    total_domains = len([d for d in DOMAINS if d["status"] == "active"])
    
    # Calculate brand score (mock calculation)
    brand_score = min(100, 85 + (total_domains * 2) + (total_previews // 2))
    
    # Get top domains
    active_domains = [d for d in DOMAINS if d["status"] == "active"]
    top_domains_list = []
    for domain in sorted(active_domains, key=lambda x: x["monthly_clicks"], reverse=True)[:4]:
        clicks = domain["monthly_clicks"]
        # Mock CTR calculation
        ctr = (clicks / (clicks * 10)) * 100 if clicks > 0 else 0.0
        top_domains_list.append(
            TopDomain(
                domain=domain["name"],
                clicks=clicks,
                ctr=round(ctr, 1)
            )
        )
    
    return AnalyticsSummary(
        period=period,
        total_clicks=total_clicks,
        total_previews=total_previews,
        total_domains=total_domains,
        brand_score=int(brand_score),
        top_domains=top_domains_list,
    )

