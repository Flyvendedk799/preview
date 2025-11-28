"""
Generate final composited preview image for og:image.

DESIGN PHILOSOPHY:
The og:image should be a well-designed visual asset that:
1. Has intentional, readable typography (optimized for small sizes)
2. Shows the key message in a beautiful way
3. Uses the screenshot as context/background
4. Complements (not duplicates) og:title

The AI decides what content goes in the image vs og:title.
"""

import base64
import logging
from io import BytesIO
from uuid import uuid4
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from backend.services.r2_client import upload_file_to_r2

logger = logging.getLogger(__name__)

# Standard OG image dimensions (1.91:1 ratio)
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (59, 130, 246)  # Default blue


def _get_contrast_color(bg_color: tuple) -> tuple:
    """Get white or dark text based on background luminance."""
    luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
    return (255, 255, 255) if luminance < 0.5 else (30, 30, 30)


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load font with fallbacks."""
    font_paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font_paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    
    paths = font_paths_bold if bold else font_paths_regular
    
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
        except:
            width = len(test_line) * (font.size // 2)
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines[:3]  # Max 3 lines


def generate_designed_preview(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    domain: str,
    blueprint: Dict[str, Any],
    template_type: str = "default"
) -> bytes:
    """
    Generate a beautifully designed og:image.
    
    Design approach:
    - Screenshot as dimmed background for context
    - Large, readable headline overlay
    - Optional CTA button
    - Brand colors for visual identity
    - Optimized typography for mobile viewing
    
    This creates an image that looks designed and intentional,
    not just a raw screenshot.
    """
    try:
        # Load and process screenshot
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGBA')
        
        # Get brand colors
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
        accent_color = _hex_to_rgb(blueprint.get("accent_color", "#F59E0B"))
        
        # Create base image
        final_image = Image.new('RGBA', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (255, 255, 255, 255))
        
        # Resize and position screenshot as background
        screenshot_bg = _prepare_screenshot_background(screenshot, OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT)
        final_image.paste(screenshot_bg, (0, 0))
        
        # Apply dark overlay for text readability
        overlay = Image.new('RGBA', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Gradient overlay - darker on left where text will be
        for x in range(OG_IMAGE_WIDTH):
            # Stronger on left, fading to right
            alpha = int(180 * (1 - (x / OG_IMAGE_WIDTH) * 0.6))
            overlay_draw.line([(x, 0), (x, OG_IMAGE_HEIGHT)], fill=(0, 0, 0, alpha))
        
        final_image = Image.alpha_composite(final_image, overlay)
        
        # Add brand accent bar at top
        accent_bar = Image.new('RGBA', (OG_IMAGE_WIDTH, 6), (*primary_color, 255))
        final_image.paste(accent_bar, (0, 0))
        
        # Convert to RGB for drawing
        draw_image = final_image.convert('RGB')
        draw = ImageDraw.Draw(draw_image)
        
        # Typography settings - LARGE for mobile readability
        title_font = _load_font(52, bold=True)
        subtitle_font = _load_font(28, bold=False)
        cta_font = _load_font(22, bold=True)
        domain_font = _load_font(18, bold=True)
        
        # Content area (left side with padding)
        content_x = 60
        content_y = 80
        max_text_width = OG_IMAGE_WIDTH - 200  # Leave space on right
        
        # Draw title (wrapped, large, white)
        if title and title != "Untitled":
            title_lines = _wrap_text(title, title_font, max_text_width, draw)
            for i, line in enumerate(title_lines):
                y_pos = content_y + (i * 60)
                # Shadow for depth
                draw.text((content_x + 2, y_pos + 2), line, fill=(0, 0, 0), font=title_font)
                draw.text((content_x, y_pos), line, fill=(255, 255, 255), font=title_font)
            content_y += len(title_lines) * 60 + 20
        
        # Draw subtitle or description (smaller, slightly transparent)
        display_text = subtitle or description
        if display_text and content_y < 400:
            # Truncate if too long
            if len(display_text) > 120:
                display_text = display_text[:117] + "..."
            
            sub_lines = _wrap_text(display_text, subtitle_font, max_text_width, draw)
            for i, line in enumerate(sub_lines[:2]):  # Max 2 lines
                y_pos = content_y + (i * 36)
                draw.text((content_x, y_pos), line, fill=(220, 220, 220), font=subtitle_font)
            content_y += min(len(sub_lines), 2) * 36 + 30
        
        # Draw CTA button (if available and space permits)
        if cta_text and content_y < 480:
            cta_text_clean = cta_text[:30]  # Limit length
            
            try:
                bbox = draw.textbbox((0, 0), cta_text_clean, font=cta_font)
                cta_width = bbox[2] - bbox[0] + 48
                cta_height = 50
            except:
                cta_width = len(cta_text_clean) * 14 + 48
                cta_height = 50
            
            # Button background
            button_x = content_x
            button_y = content_y
            
            # Rounded rectangle (approximated)
            draw.rectangle(
                [(button_x, button_y), (button_x + cta_width, button_y + cta_height)],
                fill=accent_color
            )
            
            # Button text
            text_color = _get_contrast_color(accent_color)
            draw.text(
                (button_x + 24, button_y + 12),
                cta_text_clean,
                fill=text_color,
                font=cta_font
            )
        
        # Domain badge (bottom left)
        domain_clean = domain.replace('www.', '').upper()
        domain_y = OG_IMAGE_HEIGHT - 50
        
        # Semi-transparent background for domain
        try:
            bbox = draw.textbbox((0, 0), domain_clean, font=domain_font)
            domain_width = bbox[2] - bbox[0] + 24
        except:
            domain_width = len(domain_clean) * 12 + 24
        
        # Draw domain with background
        draw.rectangle(
            [(content_x - 8, domain_y - 4), (content_x + domain_width, domain_y + 28)],
            fill=(0, 0, 0, 128)
        )
        draw.text((content_x, domain_y), domain_clean, fill=(255, 255, 255), font=domain_font)
        
        # Save to bytes
        buffer = BytesIO()
        draw_image.save(buffer, format='PNG', optimize=True)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Designed preview generation failed: {e}", exc_info=True)
        return _generate_fallback_preview(title, domain, blueprint)


def _prepare_screenshot_background(
    screenshot: Image.Image,
    target_width: int,
    target_height: int
) -> Image.Image:
    """
    Prepare screenshot as a background image.
    
    - Resize to cover the full area
    - Apply slight blur for depth
    - Darken slightly for text overlay
    """
    src_width, src_height = screenshot.size
    target_ratio = target_width / target_height
    src_ratio = src_width / src_height
    
    # Resize to cover (may crop)
    if src_ratio > target_ratio:
        # Source is wider - scale by height
        new_height = target_height
        new_width = int(src_width * (target_height / src_height))
    else:
        # Source is taller - scale by width
        new_width = target_width
        new_height = int(src_height * (target_width / src_width))
    
    resized = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center crop to target size
    left = (new_width - target_width) // 2
    top = 0  # Keep top of page visible
    cropped = resized.crop((left, top, left + target_width, top + target_height))
    
    # Apply subtle blur for depth (makes text more readable)
    blurred = cropped.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Slightly darken
    enhancer = ImageEnhance.Brightness(blurred)
    darkened = enhancer.enhance(0.85)
    
    return darkened.convert('RGBA')


def _generate_fallback_preview(
    title: str,
    domain: str,
    blueprint: Dict[str, Any]
) -> bytes:
    """Generate fallback preview if main generation fails."""
    try:
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
        
        # Gradient background
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
        draw = ImageDraw.Draw(img)
        
        # Diagonal gradient
        for y in range(OG_IMAGE_HEIGHT):
            ratio = y / OG_IMAGE_HEIGHT
            r = int(primary_color[0] * (1 - ratio * 0.3) + secondary_color[0] * ratio * 0.3)
            g = int(primary_color[1] * (1 - ratio * 0.3) + secondary_color[1] * ratio * 0.3)
            b = int(primary_color[2] * (1 - ratio * 0.3) + secondary_color[2] * ratio * 0.3)
            draw.line([(0, y), (OG_IMAGE_WIDTH, y)], fill=(r, g, b))
        
        # Title
        title_font = _load_font(48, bold=True)
        if title and title != "Untitled":
            title_lines = _wrap_text(title, title_font, OG_IMAGE_WIDTH - 120, draw)
            y = OG_IMAGE_HEIGHT // 2 - len(title_lines) * 30
            for line in title_lines:
                draw.text((60, y), line, fill=(255, 255, 255), font=title_font)
                y += 60
        
        # Domain
        domain_font = _load_font(20, bold=True)
        domain_clean = domain.replace('www.', '').upper()
        draw.text((60, OG_IMAGE_HEIGHT - 60), domain_clean, fill=(255, 255, 255, 180), font=domain_font)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Fallback generation failed: {e}", exc_info=True)
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (59, 130, 246))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


def generate_and_upload_preview_image(
    screenshot_bytes: bytes,
    url: str,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    cta_text: Optional[str] = None,
    blueprint: Dict[str, Any] = None,
    template_type: str = "default"
) -> Optional[str]:
    """
    Generate designed og:image and upload to R2.
    
    Creates a beautiful, designed preview image that:
    - Uses screenshot as contextual background
    - Has large, readable typography
    - Shows key messaging (title, CTA)
    - Is optimized for mobile social feeds
    
    Args:
        screenshot_bytes: Raw PNG bytes of page screenshot
        url: Full URL (for domain extraction)
        title: Main headline for the image
        subtitle: Optional subtitle/tagline
        description: Optional description
        cta_text: Optional CTA button text
        blueprint: Color palette
        template_type: Page type
    
    Returns:
        Public URL of uploaded image, or None if failed
    """
    if blueprint is None:
        blueprint = {}
    
    try:
        # Extract domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        logger.info(f"Generating designed preview for: {domain}")
        
        # Generate the image
        image_bytes = generate_designed_preview(
            screenshot_bytes=screenshot_bytes,
            title=title,
            subtitle=subtitle,
            description=description,
            cta_text=cta_text,
            domain=domain,
            blueprint=blueprint,
            template_type=template_type
        )
        
        # Upload to R2
        filename = f"previews/demo/{uuid4()}.png"
        image_url = upload_file_to_r2(image_bytes, filename, "image/png")
        
        logger.info(f"Designed preview uploaded: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Failed to generate/upload preview image: {e}", exc_info=True)
        return None
