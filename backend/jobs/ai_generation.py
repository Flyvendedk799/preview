"""AI generation job module."""
from typing import Dict, Optional
from backend.services.preview_generator import generate_ai_preview
from backend.schemas.brand import BrandSettings as BrandSettingsSchema


def generate_ai_metadata(url: str, brand_settings: BrandSettingsSchema, html_content: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Generate AI-powered metadata for a URL.
    
    Args:
        url: URL to generate metadata for
        brand_settings: User's brand settings
        html_content: Optional pre-fetched HTML content
        
    Returns:
        Dictionary with title, description, keywords, tone, type, reasoning, image_url (fallback)
    """
    return generate_ai_preview(url, brand_settings, html_content)

