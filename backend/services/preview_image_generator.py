"""
Generate final composited preview image for og:image.

This service takes the reconstructed preview data and generates a final
PNG/JPG image that matches the ReconstructedPreview component design exactly.
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


def generate_preview_image_html(
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    primary_image_base64: Optional[str],
    screenshot_url: Optional[str],
    blueprint: Dict[str, Any],
    template_type: str,
    tags: list = None,
    context_items: list = None
) -> str:
    """
    Generate HTML that exactly matches the ReconstructedPreview component design.
    """
    if tags is None:
        tags = []
    if context_items is None:
        context_items = []
        
    primary_color = blueprint.get("primary_color", "#3B82F6")
    secondary_color = blueprint.get("secondary_color", "#1E293B")
    accent_color = blueprint.get("accent_color", "#F59E0B")
    
    imageUrl = f'data:image/png;base64,{primary_image_base64}' if primary_image_base64 else (screenshot_url or '')
    
    # Match the exact design from ReconstructedPreview component
    if template_type == "landing":
        # LandingTemplate design
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
                    background: linear-gradient(135deg, {primary_color}, {secondary_color});
                }}
                
                .container {{
                    width: 100%;
                    height: 100%;
                    position: relative;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                }}
                
                .bg-image {{
                    position: absolute;
                    inset: 0;
                }}
                
                .bg-image img {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    opacity: 0.2;
                }}
                
                .bg-overlay {{
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(to right, rgba(0, 0, 0, 0.6), transparent);
                }}
                
                .content {{
                    position: relative;
                    z-index: 10;
                    padding: 60px 80px;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    color: white;
                }}
                
                .tags {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-bottom: 16px;
                }}
                
                .tag {{
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    background: rgba(255, 255, 255, 0.2);
                    color: rgba(255, 255, 255, 0.9);
                }}
                
                .title {{
                    font-size: 48px;
                    font-weight: 700;
                    line-height: 1.2;
                    margin-bottom: 12px;
                    max-width: 900px;
                    color: white;
                }}
                
                .subtitle {{
                    font-size: 24px;
                    font-weight: 600;
                    line-height: 1.3;
                    margin-bottom: 8px;
                    max-width: 800px;
                    color: rgba(255, 255, 255, 0.9);
                }}
                
                .description {{
                    font-size: 18px;
                    font-weight: 400;
                    line-height: 1.5;
                    margin-bottom: 24px;
                    max-width: 700px;
                    color: rgba(255, 255, 255, 0.7);
                }}
                
                .cta-button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: {accent_color};
                    color: {primary_color};
                    font-size: 14px;
                    font-weight: 700;
                    border-radius: 8px;
                    text-decoration: none;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    transition: opacity 0.2s;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {f'<div class="bg-image"><img src="{imageUrl}" alt="" /></div>' if imageUrl else ''}
                <div class="bg-overlay"></div>
                <div class="content">
                    {f'<div class="tags">' + ''.join([f'<span class="tag">{tag}</span>' for tag in tags[:2]]) + '</div>' if tags else ''}
                    <h1 class="title">{title}</h1>
                    {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
                    {f'<p class="description">{description}</p>' if description else ''}
                    {f'<a href="#" class="cta-button">{cta_text}</a>' if cta_text else ''}
                </div>
            </div>
        </body>
        </html>
        """
    elif template_type == "profile":
        # ProfileTemplate design
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
                    background: #F9FAFB;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .card {{
                    width: 90%;
                    max-width: 500px;
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                }}
                
                .header {{
                    height: 112px;
                    background: linear-gradient(135deg, {primary_color}, {secondary_color});
                    position: relative;
                }}
                
                .header-overlay {{
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.1));
                }}
                
                .header-pattern {{
                    position: absolute;
                    inset: 0;
                    opacity: 0.1;
                    background-image: radial-gradient(circle at 25px 25px, white 2%, transparent 0%);
                    background-size: 50px 50px;
                }}
                
                .content {{
                    position: relative;
                    padding: 24px;
                    padding-top: 0;
                }}
                
                .profile-image-container {{
                    display: flex;
                    justify-content: center;
                    margin-top: -64px;
                    margin-bottom: 16px;
                }}
                
                .profile-image {{
                    width: 112px;
                    height: 112px;
                    border-radius: 50%;
                    border: 4px solid white;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    object-fit: cover;
                }}
                
                .name {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #111827;
                    text-align: center;
                    margin-bottom: 4px;
                }}
                
                .subtitle {{
                    font-size: 14px;
                    color: #4B5563;
                    text-align: center;
                    margin-bottom: 12px;
                }}
                
                .context {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 16px;
                    font-size: 14px;
                    color: #374151;
                    font-weight: 500;
                    margin-bottom: 16px;
                }}
                
                .tags {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 8px;
                    margin-bottom: 16px;
                }}
                
                .tag {{
                    padding: 4px 12px;
                    border-radius: 9999px;
                    font-size: 12px;
                    font-weight: 500;
                    background: {primary_color}15;
                    color: {primary_color};
                }}
                
                .description {{
                    border-top: 1px solid #F3F4F6;
                    padding-top: 16px;
                    margin-top: 8px;
                    font-size: 14px;
                    color: #374151;
                    text-align: center;
                    line-height: 1.5;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <div class="header-overlay"></div>
                    <div class="header-pattern"></div>
                </div>
                <div class="content">
                    <div class="profile-image-container">
                        {f'<img src="data:image/png;base64,{primary_image_base64}" class="profile-image" alt="" />' if primary_image_base64 else f'<div class="profile-image" style="background: {primary_color}; display: flex; align-items: center; justify-content: center; color: white; font-size: 36px; font-weight: 700;">{title[0].upper() if title else "P"}</div>'}
                    </div>
                    <h2 class="name">{title}</h2>
                    {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
                    {f'<div class="context">{context_items[0]["text"] if context_items else ""}</div>' if context_items else ''}
                    {f'<div class="tags">' + ''.join([f'<span class="tag">{tag}</span>' for tag in tags[:4]]) + '</div>' if tags else ''}
                    {f'<p class="description">{description}</p>' if description else ''}
                </div>
            </div>
        </body>
        </html>
        """
    else:
        # Product/Service template - white card with icon
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
                    background: #F9FAFB;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .card {{
                    width: 90%;
                    max-width: 600px;
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                }}
                
                .accent-bar {{
                    height: 8px;
                    background: {primary_color};
                }}
                
                .content {{
                    padding: 24px;
                }}
                
                .icon-container {{
                    margin-bottom: 16px;
                }}
                
                .icon {{
                    width: 64px;
                    height: 64px;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    background: {primary_color}15;
                    color: {primary_color};
                }}
                
                .icon img {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    border-radius: 12px;
                }}
                
                .title {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 8px;
                }}
                
                .subtitle {{
                    font-size: 14px;
                    color: #4B5563;
                    margin-bottom: 12px;
                }}
                
                .description {{
                    font-size: 14px;
                    color: #4B5563;
                    line-height: 1.5;
                    margin-bottom: 16px;
                }}
                
                .cta-button {{
                    width: 100%;
                    padding: 10px 16px;
                    background: {primary_color};
                    color: white;
                    font-size: 14px;
                    font-weight: 500;
                    border-radius: 8px;
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="accent-bar"></div>
                <div class="content">
                    <div class="icon-container">
                        {f'<img src="data:image/png;base64,{primary_image_base64}" class="icon" alt="" />' if primary_image_base64 else '<div class="icon">✨</div>'}
                    </div>
                    <h2 class="title">{title}</h2>
                    {f'<p class="subtitle">{subtitle}</p>' if subtitle else ''}
                    {f'<p class="description">{description}</p>' if description else ''}
                    {f'<button class="cta-button">{cta_text}</button>' if cta_text else ''}
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
    screenshot_url: Optional[str],
    blueprint: Dict[str, Any],
    template_type: str,
    tags: list = None,
    context_items: list = None
) -> bytes:
    """
    Generate final composited preview image.
    
    Uses Playwright to render HTML and capture as PNG.
    """
    try:
        html = generate_preview_image_html(
            title=title,
            subtitle=subtitle,
            description=description,
            cta_text=cta_text,
            primary_image_base64=primary_image_base64,
            screenshot_url=screenshot_url,
            blueprint=blueprint,
            template_type=template_type,
            tags=tags or [],
            context_items=context_items or []
        )
        
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(
                viewport={"width": OG_IMAGE_WIDTH, "height": OG_IMAGE_HEIGHT},
                device_scale_factor=2  # High DPI for quality
            )
            
            page.set_content(html, wait_until="networkidle")
            
            # Wait for fonts and images to load
            page.wait_for_timeout(1500)
            
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
        primary_color = tuple(int(blueprint.get("primary_color", "#3B82F6").lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        accent_color = tuple(int(blueprint.get("accent_color", "#F59E0B").lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # Create image
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load a font (fallback to default if not available)
        try:
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
    screenshot_url: Optional[str],
    blueprint: Dict[str, Any],
    template_type: str,
    tags: list = None,
    context_items: list = None
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
            screenshot_url=screenshot_url,
            blueprint=blueprint,
            template_type=template_type,
            tags=tags or [],
            context_items=context_items or []
        )
        
        # Upload to R2
        filename = f"previews/demo/{uuid4()}.png"
        image_url = upload_file_to_r2(image_bytes, filename, "image/png")
        
        logger.info(f"Preview image uploaded: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Failed to generate/upload preview image: {e}", exc_info=True)
        return None
