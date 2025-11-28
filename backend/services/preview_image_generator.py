"""
Generate final composited preview image for og:image.

DESIGN PHILOSOPHY:
The og:image should be a VISUAL HOOK, not a text document.
- Screenshot-first: Use the actual page as the primary visual
- Minimal text: Only domain/logo for brand recognition
- Mobile-optimized: Must be legible at ~300px width
- Let og:title and og:description handle the text content

This approach follows professional social media marketing best practices.
"""

import base64
import logging
from io import BytesIO
from uuid import uuid4
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from backend.services.r2_client import upload_file_to_r2

logger = logging.getLogger(__name__)

# Standard OG image dimensions (1.91:1 ratio)
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630

# Brand bar configuration
BRAND_BAR_HEIGHT = 60
BRAND_BAR_PADDING = 24


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _get_contrast_color(bg_color: tuple) -> tuple:
    """Get white or dark text based on background luminance."""
    luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
    return (255, 255, 255) if luminance < 0.5 else (30, 30, 30)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load font with fallbacks."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    
    return ImageFont.load_default()


def generate_screenshot_based_preview(
    screenshot_bytes: bytes,
    domain: str,
    blueprint: Dict[str, Any],
    template_type: str = "default"
) -> bytes:
    """
    Generate og:image using screenshot as the primary visual.
    
    Strategy:
    - Screenshot fills most of the frame
    - Subtle brand bar at bottom with domain
    - Light gradient overlay for visual cohesion
    - NO text overlays (titles, descriptions, CTAs)
    
    Args:
        screenshot_bytes: Raw PNG bytes of the page screenshot
        domain: Domain name for brand bar (e.g., "example.com")
        blueprint: Color palette with primary_color, secondary_color, accent_color
        template_type: Page type (profile, product, landing, etc.) - for optional tweaks
    
    Returns:
        PNG image bytes
    """
    try:
        # Load screenshot
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGBA')
        
        # Get brand colors
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
        
        # Calculate dimensions
        content_height = OG_IMAGE_HEIGHT - BRAND_BAR_HEIGHT
        
        # Smart crop/resize screenshot to fit content area
        screenshot_resized = _smart_crop_screenshot(
            screenshot, 
            OG_IMAGE_WIDTH, 
            content_height,
            template_type
        )
        
        # Create final image
        final_image = Image.new('RGBA', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (255, 255, 255, 255))
        
        # Paste screenshot at top
        final_image.paste(screenshot_resized, (0, 0))
        
        # Add subtle gradient overlay at bottom of screenshot (for visual transition)
        gradient_overlay = _create_bottom_gradient(OG_IMAGE_WIDTH, content_height, primary_color)
        final_image = Image.alpha_composite(final_image, gradient_overlay)
        
        # Add brand bar at bottom
        brand_bar = _create_brand_bar(
            OG_IMAGE_WIDTH, 
            BRAND_BAR_HEIGHT, 
            domain, 
            primary_color,
            secondary_color
        )
        final_image.paste(brand_bar, (0, content_height))
        
        # Convert to RGB for PNG export
        final_rgb = Image.new('RGB', final_image.size, (255, 255, 255))
        final_rgb.paste(final_image, mask=final_image.split()[-1] if final_image.mode == 'RGBA' else None)
        
        # Save to bytes
        buffer = BytesIO()
        final_rgb.save(buffer, format='PNG', optimize=True)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Screenshot-based preview generation failed: {e}", exc_info=True)
        # Fallback to simple branded image
        return _generate_fallback_preview(domain, blueprint)


def _smart_crop_screenshot(
    screenshot: Image.Image, 
    target_width: int, 
    target_height: int,
    template_type: str
) -> Image.Image:
    """
    Intelligently crop and resize screenshot to fit target dimensions.
    
    Strategy varies by template type:
    - Landing/Service: Focus on top hero section
    - Profile: Try to center on main content
    - Default: Crop from top
    """
    src_width, src_height = screenshot.size
    target_ratio = target_width / target_height
    src_ratio = src_width / src_height
    
    if src_ratio > target_ratio:
        # Source is wider - crop sides
        new_width = int(src_height * target_ratio)
        left = (src_width - new_width) // 2
        cropped = screenshot.crop((left, 0, left + new_width, src_height))
    else:
        # Source is taller - crop from top (keep hero section)
        new_height = int(src_width / target_ratio)
        
        # For most pages, the important content is at the top
        # Only take from the top portion of the page
        cropped = screenshot.crop((0, 0, src_width, min(new_height, src_height)))
        
        # If we couldn't get enough height, pad with white
        if cropped.size[1] < new_height:
            padded = Image.new('RGBA', (src_width, new_height), (255, 255, 255, 255))
            padded.paste(cropped, (0, 0))
            cropped = padded
    
    # Resize to exact target dimensions
    return cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)


def _create_bottom_gradient(width: int, height: int, color: tuple) -> Image.Image:
    """Create a subtle gradient overlay at the bottom for visual transition to brand bar."""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Gradient starts at 80% of height
    gradient_start = int(height * 0.8)
    gradient_height = height - gradient_start
    
    for y in range(gradient_height):
        # Gradually increase opacity
        alpha = int(30 * (y / gradient_height))  # Max 30 alpha for subtlety
        draw.line(
            [(0, gradient_start + y), (width, gradient_start + y)],
            fill=(color[0], color[1], color[2], alpha)
        )
    
    return overlay


def _create_brand_bar(
    width: int, 
    height: int, 
    domain: str, 
    primary_color: tuple,
    secondary_color: tuple
) -> Image.Image:
    """
    Create a clean brand bar with domain.
    
    Design:
    - Solid background using secondary color (usually dark)
    - Domain text on the left
    - Optional: small accent line at top
    """
    bar = Image.new('RGB', (width, height), secondary_color)
    draw = ImageDraw.Draw(bar)
    
    # Accent line at top (2px, primary color)
    draw.rectangle([(0, 0), (width, 2)], fill=primary_color)
    
    # Domain text
    font = _load_font(24, bold=True)
    text_color = _get_contrast_color(secondary_color)
    
    # Clean up domain
    clean_domain = domain.replace('www.', '').upper()
    
    # Calculate text position (vertically centered, left padded)
    try:
        bbox = draw.textbbox((0, 0), clean_domain, font=font)
        text_height = bbox[3] - bbox[1]
    except:
        text_height = 24
    
    text_y = (height - text_height) // 2
    
    # Draw domain
    draw.text((BRAND_BAR_PADDING, text_y), clean_domain, fill=text_color, font=font)
    
    # Optional: Add a subtle icon/indicator on the right
    indicator_size = 8
    indicator_x = width - BRAND_BAR_PADDING - indicator_size
    indicator_y = (height - indicator_size) // 2
    draw.ellipse(
        [(indicator_x, indicator_y), (indicator_x + indicator_size, indicator_y + indicator_size)],
        fill=primary_color
    )
    
    return bar


def _generate_fallback_preview(domain: str, blueprint: Dict[str, Any]) -> bytes:
    """Generate a simple branded fallback image if screenshot processing fails."""
    try:
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
        
        # Create gradient background
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
        draw = ImageDraw.Draw(img)
        
        # Diagonal gradient effect
        for y in range(OG_IMAGE_HEIGHT):
            ratio = y / OG_IMAGE_HEIGHT
            r = int(primary_color[0] * (1 - ratio) + secondary_color[0] * ratio)
            g = int(primary_color[1] * (1 - ratio) + secondary_color[1] * ratio)
            b = int(primary_color[2] * (1 - ratio) + secondary_color[2] * ratio)
            draw.line([(0, y), (OG_IMAGE_WIDTH, y)], fill=(r, g, b))
        
        # Domain in center
        font = _load_font(48, bold=True)
        clean_domain = domain.replace('www.', '').upper()
        
        try:
            bbox = draw.textbbox((0, 0), clean_domain, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(clean_domain) * 30
            text_height = 48
        
        text_x = (OG_IMAGE_WIDTH - text_width) // 2
        text_y = (OG_IMAGE_HEIGHT - text_height) // 2
        
        draw.text((text_x, text_y), clean_domain, fill=(255, 255, 255), font=font)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Fallback preview generation failed: {e}", exc_info=True)
        # Ultimate fallback: solid color
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (59, 130, 246))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


def generate_and_upload_preview_image(
    screenshot_bytes: bytes,
    url: str,
    blueprint: Dict[str, Any],
    template_type: str = "default"
) -> Optional[str]:
    """
    Generate screenshot-based og:image and upload to R2.
    
    This is the main entry point for og:image generation.
    
    Args:
        screenshot_bytes: Raw PNG bytes of the page screenshot
        url: Full URL (used to extract domain)
        blueprint: Color palette
        template_type: Page type for optional conditional enhancements
    
    Returns:
        Public URL of uploaded image, or None if upload fails
    """
    try:
        # Extract domain from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        logger.info(f"Generating screenshot-based preview for: {domain}")
        
        # Generate the image
        image_bytes = generate_screenshot_based_preview(
            screenshot_bytes=screenshot_bytes,
            domain=domain,
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


# =============================================================================
# LEGACY SUPPORT - Keep old function signature for backwards compatibility
# =============================================================================

def generate_composited_preview_image(*args, **kwargs) -> bytes:
    """
    Legacy function - redirects to new screenshot-based approach.
    
    Note: This function signature is deprecated. Use generate_screenshot_based_preview instead.
    """
    logger.warning("generate_composited_preview_image is deprecated, use generate_screenshot_based_preview")
    
    # Try to extract screenshot_bytes from kwargs
    screenshot_url = kwargs.get('screenshot_url')
    if screenshot_url:
        try:
            import requests
            response = requests.get(screenshot_url, timeout=10)
            if response.status_code == 200:
                return generate_screenshot_based_preview(
                    screenshot_bytes=response.content,
                    domain="preview",
                    blueprint=kwargs.get('blueprint', {}),
                    template_type=kwargs.get('template_type', 'default')
                )
        except:
            pass
    
    # Fallback
    return _generate_fallback_preview("preview", kwargs.get('blueprint', {}))
