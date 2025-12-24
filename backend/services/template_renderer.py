"""Template rendering service for public sites using Jinja2."""
import os
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown as md_convert
from backend.models.published_site import (
    PublishedSite, SiteBranding, SiteSettings, SiteMenu, SiteMenuItem,
    SitePost, SiteCategory, SitePage
)
from backend.db.session import SessionLocal


# Initialize Jinja2 environment
_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'default', 'templates')
_env = Environment(
    loader=FileSystemLoader(_template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

# Custom filters
def markdown_filter(text: str) -> str:
    """Convert Markdown to HTML."""
    if not text:
        return ""
    return md_convert(text, extensions=['fenced_code', 'tables', 'codehilite'])

def date_filter(date_value, format_str: str = "%B %d, %Y") -> str:
    """Format date string or datetime object."""
    if not date_value:
        return ""
    try:
        if isinstance(date_value, datetime):
            dt = date_value
        elif isinstance(date_value, str):
            # Try ISO format first
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        break
                    except:
                        continue
                else:
                    return str(date_value)
        else:
            return str(date_value)
        return dt.strftime(format_str)
    except Exception:
        return str(date_value)

_env.filters['markdown'] = markdown_filter
_env.filters['date'] = date_filter


def render_template(site: PublishedSite, template_name: str, context: Dict[str, Any]) -> str:
    """
    Render a template for a site using Jinja2.
    
    Args:
        site: PublishedSite instance (with relationships loaded)
        template_name: Template name (e.g., 'home', 'post', 'page', 'category', '404')
        context: Template context variables
        
    Returns:
        Rendered HTML string
    """
    db = SessionLocal()
    try:
        # Load site relationships if not already loaded
        if not hasattr(site, 'branding') or site.branding is None:
            site.branding = db.query(SiteBranding).filter(SiteBranding.site_id == site.id).first()
        
        if not hasattr(site, 'settings') or site.settings is None:
            site.settings = db.query(SiteSettings).filter(SiteSettings.site_id == site.id).first()
        
        if not hasattr(site, 'menus') or site.menus is None:
            site.menus = db.query(SiteMenu).filter(
                SiteMenu.site_id == site.id,
                SiteMenu.is_active == True
            ).all()
            # Load menu items
            for menu in site.menus:
                if not hasattr(menu, 'items') or menu.items is None:
                    menu.items = db.query(SiteMenuItem).filter(
                        SiteMenuItem.menu_id == menu.id,
                        SiteMenuItem.is_active == True
                    ).order_by(SiteMenuItem.sort_order).all()
        
        # Load domain if not loaded
        if not hasattr(site, 'domain') or site.domain is None:
            from backend.models.domain import Domain
            site.domain = db.query(Domain).filter(Domain.id == site.domain_id).first()
        
        # Prepare template context
        template_context = {
            'site': site,
            'request': context.get('request'),  # For URL generation if needed
            **context
        }
        
        # Map template names to files
        template_map = {
            'home': 'home.html',
            'post': 'post.html',
            'page': 'page.html',
            'category': 'category.html',
            '404': '404.html',
        }
        
        template_file = template_map.get(template_name, '404.html')
        
        # Render template
        template = _env.get_template(template_file)
        html = template.render(**template_context)
        
        return html
        
    except Exception as e:
        # Fallback to error page
        try:
            error_template = _env.get_template('404.html')
            return error_template.render({
                'site': site,
                'error': str(e)
            })
        except:
            # Ultimate fallback
            return f"""<!DOCTYPE html>
<html>
<head>
    <title>Error - {site.name}</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Template Error</h1>
    <p>An error occurred while rendering the template: {str(e)}</p>
</body>
</html>"""
    finally:
        db.close()


def render_markdown(content: str) -> str:
    """Convert Markdown content to HTML."""
    return md_convert(content, extensions=['fenced_code', 'tables', 'codehilite'])
