"""
Generate final composited preview image for og:image.

This service takes the reconstructed preview data and generates a final
PNG/JPG image that includes all elements (title, description, CTA, etc.)
composited together. This image becomes the og:image for link previews.
"""

import base64
import logging
from io import BytesIO
from uuid import uuid4
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
from backend.services.r2_client import upload_file_to_r2
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Standard OG image dimensions (1.91:1 ratio)
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def generate_preview_image_html(
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    primary_image_base64: Optional[str],
    blueprint: Dict[str, Any],
    template_type: str
) -> str:
    """
    Generate HTML for the preview image.
    
    This HTML will be rendered by Playwright to create the final image.
    """
    primary_color = blueprint.get("primary_color", "#3B82F6")
    secondary_color = blueprint.get("secondary_color", "#1E293B")
    accent_color = blueprint.get("accent_color", "#F59E0B")
    
    # Background image if available
    bg_image_style = ""
    if primary_image_base64:
        bg_image_style = f'background-image: url(data:image/png;base64,{primary_image_base64}); background-size: cover; background-position: center;'
    
    # Template-specific styling
    if template_type == "landing":
        # Landing page: gradient background with overlay
        background = f'linear-gradient(135deg, {primary_color}, {secondary_color})'
        text_color = "#FFFFFF"
        overlay = "rgba(0, 0, 0, 0.5)"
    elif template_type == "profile":
        # Profile: gradient header, white content
        background = f'linear-gradient(135deg, {primary_color}, {secondary_color})'
        text_color = "#FFFFFF"
        overlay = "rgba(0, 0, 0, 0.3)"
    else:
        # Default: white background
        background = "#FFFFFF"
        text_color = "#1F2937"
        overlay = "transparent"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                width: {OG_IMAGE_WIDTH}px;
                height: {OG_IMAGE_HEIGHT}px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                overflow: hidden;
                position: relative;
            }}
            
            .container {{
                width: 100%;
                height: 100%;
                position: relative;
                background: {background};
                {bg_image_style}
            }}
            
            .overlay {{
                position: absolute;
                inset: 0;
                background: {overlay};
            }}
            
            .content {{
                position: relative;
                z-index: 10;
                padding: 60px 80px;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                color: {text_color};
            }}
            
            .title {{
                font-size: 56px;
                font-weight: 900;
                line-height: 1.1;
                margin-bottom: 20px;
                max-width: 900px;
            }}
            
            .subtitle {{
                font-size: 32px;
                font-weight: 600;
                line-height: 1.3;
                margin-bottom: 16px;
                opacity: 0.95;
                max-width: 800px;
            }}
            
            .description {{
                font-size: 24px;
                font-weight: 400;
                line-height: 1.5;
                margin-bottom: 32px;
                opacity: 0.9;
                max-width: 700px;
            }}
            
            .cta-button {{
                display: inline-block;
                padding: 18px 36px;
                background: {accent_color};
                color: #FFFFFF;
                font-size: 24px;
                font-weight: 700;
                border-radius: 12px;
                text-decoration: none;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                max-width: fit-content;
            }}
            
            /* Profile template specific */
            .profile-header {{
                height: 200px;
                background: linear-gradient(135deg, {primary_color}, {secondary_color});
                position: relative;
            }}
            
            .profile-content {{
                background: #FFFFFF;
                padding: 40px 60px;
                margin-top: -100px;
                border-radius: 20px 20px 0 0;
                position: relative;
                z-index: 10;
            }}
            
            .profile-image {{
                width: 120px;
                height: 120px;
                border-radius: 50%;
                border: 6px solid #FFFFFF;
                margin: -60px auto 24px;
                display: block;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            }}
            
            .profile-title {{
                font-size: 42px;
                font-weight: 800;
                color: #1F2937;
                text-align: center;
                margin-bottom: 12px;
            }}
            
            .profile-subtitle {{
                font-size: 22px;
                color: #6B7280;
                text-align: center;
                margin-bottom: 24px;
            }}
            
            .profile-description {{
                font-size: 20px;
                color: #374151;
                text-align: center;
                line-height: 1.6;
                max-width: 600px;
                margin: 0 auto 32px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="overlay"></div>
            <div class="content">
    """
    
    if template_type == "profile":
        # Profile template layout
        html += f"""
                <div class="profile-header"></div>
                <div class="profile-content">
        """
        if primary_image_base64:
            html += f'<img src="data:image/png;base64,{primary_image_base64}" class="profile-image" alt="Profile" />'
        html += f"""
                    <h1 class="profile-title">{title}</h1>
        """
        if subtitle:
            html += f'<p class="profile-subtitle">{subtitle}</p>'
        if description:
            html += f'<p class="profile-description">{description}</p>'
        if cta_text:
            html += f'<a href="#" class="cta-button">{cta_text}</a>'
        html += """
                </div>
        """
    else:
        # Landing/product template layout
        html += f'<h1 class="title">{title}</h1>'
        if subtitle:
            html += f'<p class="subtitle">{subtitle}</p>'
        if description:
            html += f'<p class="description">{description}</p>'
        if cta_text:
            html += f'<a href="#" class="cta-button">{cta_text}</a>'
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_composited_preview_image(
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    primary_image_base64: Optional[str],
    blueprint: Dict[str, Any],
    template_type: str
) -> bytes:
    """
    Generate final composited preview image.
    
    Uses Playwright to render HTML and capture as PNG.
    
    Returns:
        PNG image bytes
    """
    try:
        html = generate_preview_image_html(
            title=title,
            subtitle=subtitle,
            description=description,
            cta_text=cta_text,
            primary_image_base64=primary_image_base64,
            blueprint=blueprint,
            template_type=template_type
        )
        
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(
                viewport={"width": OG_IMAGE_WIDTH, "height": OG_IMAGE_HEIGHT},
                device_scale_factor=2  # High DPI for quality
            )
            
            page.set_content(html, wait_until="networkidle")
            
            # Wait a bit for fonts to load
            page.wait_for_timeout(1000)
            
            # Capture screenshot
            screenshot_bytes = page.screenshot(
                type="png",
                full_page=False,
                clip={"x": 0, "y": 0, "width": OG_IMAGE_WIDTH, "height": OG_IMAGE_HEIGHT}
            )
            
            browser.close()
            
            return screenshot_bytes
            
    except Exception as e:
        logger.error(f"Error generating composited preview image: {e}", exc_info=True)
        # Fallback: create a simple image with PIL
        return _generate_fallback_image(title, subtitle, description, cta_text, blueprint)


def _generate_fallback_image(
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    blueprint: Dict[str, Any]
) -> bytes:
    """Fallback image generation using PIL if Playwright fails."""
    try:
        primary_color = hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        accent_color = hex_to_rgb(blueprint.get("accent_color", "#F59E0B"))
        
        # Create image
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load a font (fallback to default if not available)
        try:
            # Try to use a system font
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # Draw title
        y = 100
        draw.text((80, y), title, fill=(255, 255, 255), font=font_large)
        
        # Draw description if available
        if description:
            y += 100
            draw.text((80, y), description[:100] + "...", fill=(255, 255, 255), font=font_medium)
        
        # Draw CTA button
        if cta_text:
            y += 100
            button_width = 300
            button_height = 60
            draw.rectangle(
                [(80, y), (80 + button_width, y + button_height)],
                fill=accent_color
            )
            draw.text((100, y + 15), cta_text[:30], fill=(255, 255, 255), font=font_medium)
        
        # Save to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Fallback image generation failed: {e}", exc_info=True)
        # Ultimate fallback: solid color image
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (59, 130, 246))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


def generate_and_upload_preview_image(
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    primary_image_base64: Optional[str],
    blueprint: Dict[str, Any],
    template_type: str
) -> Optional[str]:
    """
    Generate composited preview image and upload to R2.
    
    Returns:
        Public URL of uploaded image, or None if upload fails
    """
    try:
        logger.info("Generating composited preview image")
        image_bytes = generate_composited_preview_image(
            title=title,
            subtitle=subtitle,
            description=description,
            cta_text=cta_text,
            primary_image_base64=primary_image_base64,
            blueprint=blueprint,
            template_type=template_type
        )
        
        # Upload to R2
        filename = f"previews/demo/{uuid4()}.png"
        image_url = upload_file_to_r2(image_bytes, filename, "image/png")
        
        logger.info(f"Preview image uploaded: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Failed to generate/upload preview image: {e}", exc_info=True)
        return None

