"""Sitemap generation endpoint for SEO."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.models.blog_post import BlogPost
from backend.core.config import settings
import os

router = APIRouter(tags=["seo"])


def format_datetime_for_sitemap(dt: Optional[datetime]) -> str:
    """Format datetime for sitemap XML (W3C format)."""
    if not dt:
        return datetime.utcnow().strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


@router.get("/sitemap.xml")
def generate_sitemap(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate XML sitemap for search engines.
    Includes all public pages and published blog posts.
    """
    # Get base URL from request or environment
    base_url = os.getenv("FRONTEND_URL", "https://mymetaview.com")
    if not base_url.startswith("http"):
        # If FRONTEND_URL doesn't have protocol, construct from request
        scheme = request.url.scheme
        host = request.headers.get("host", "mymetaview.com")
        base_url = f"{scheme}://{host}"
    
    # Remove trailing slash
    base_url = base_url.rstrip("/")
    
    # Get all published blog posts
    blog_posts = db.query(BlogPost).filter(
        BlogPost.status == "published",
        BlogPost.published_at <= datetime.utcnow(),
        BlogPost.no_index == False  # Only include posts that should be indexed
    ).order_by(BlogPost.published_at.desc()).all()
    
    # Start building XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    
    # Static pages with priorities
    static_pages = [
        {
            "loc": f"{base_url}/",
            "priority": "1.0",
            "changefreq": "daily",
            "lastmod": datetime.utcnow()
        },
        {
            "loc": f"{base_url}/blog",
            "priority": "0.9",
            "changefreq": "daily",
            "lastmod": datetime.utcnow()
        },
        {
            "loc": f"{base_url}/demo",
            "priority": "0.8",
            "changefreq": "weekly",
            "lastmod": datetime.utcnow()
        },
    ]
    
    # Add static pages
    for page in static_pages:
        xml_lines.extend([
            "  <url>",
            f"    <loc>{page['loc']}</loc>",
            f"    <lastmod>{format_datetime_for_sitemap(page['lastmod'])}</lastmod>",
            f"    <changefreq>{page['changefreq']}</changefreq>",
            f"    <priority>{page['priority']}</priority>",
            "  </url>",
        ])
    
    # Add blog posts
    for post in blog_posts:
        post_url = f"{base_url}/blog/{post.slug}"
        lastmod = post.updated_at or post.published_at or post.created_at
        
        xml_lines.extend([
            "  <url>",
            f"    <loc>{post_url}</loc>",
            f"    <lastmod>{format_datetime_for_sitemap(lastmod)}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.7</priority>",
        ])
        
        # Add featured image if available
        if post.featured_image:
            xml_lines.extend([
                "    <image:image>",
                f"      <image:loc>{post.featured_image}</image:loc>",
                f"      <image:title>{post.title}</image:title>",
            ])
            if post.featured_image_alt:
                xml_lines.append(f"      <image:caption>{post.featured_image_alt}</image:caption>")
            xml_lines.append("    </image:image>")
        
        xml_lines.append("  </url>")
    
    # Close urlset
    xml_lines.append("</urlset>")
    
    # Join and return XML
    xml_content = "\n".join(xml_lines)
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        }
    )
