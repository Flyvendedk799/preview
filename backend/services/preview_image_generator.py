"""
Generate PREMIUM preview images for og:image.

DESIGN PHILOSOPHY:
Create social preview images that:
1. Look like they were designed by a professional
2. Use bold typography that pops at small sizes
3. Have modern, sophisticated color usage
4. Create visual interest that stops the scroll
5. Feel premium and trustworthy
"""

import base64
import logging
import math
from io import BytesIO
from uuid import uuid4
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from backend.services.r2_client import upload_file_to_r2

logger = logging.getLogger(__name__)

# Standard OG image dimensions (1.91:1 ratio)
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (59, 130, 246)  # Default blue


def _darken_color(color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
    """Darken a color by a factor."""
    return tuple(int(c * factor) for c in color)


def _lighten_color(color: Tuple[int, int, int], factor: float = 0.3) -> Tuple[int, int, int]:
    """Lighten a color by mixing with white."""
    return tuple(int(c + (255 - c) * factor) for c in color)


def _get_contrast_color(bg_color: tuple) -> tuple:
    """Get white or dark text based on background luminance."""
    luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
    return (255, 255, 255) if luminance < 0.5 else (20, 20, 30)


def _get_text_shadow_color(text_color: tuple) -> tuple:
    """Get shadow color for text."""
    if text_color[0] > 200:  # White text
        return (0, 0, 0, 80)  # Dark shadow
    return (255, 255, 255, 40)  # Light shadow


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


def _draw_gradient_background(
    image: Image.Image,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    direction: str = "diagonal"
) -> Image.Image:
    """Draw a smooth gradient background."""
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    if direction == "diagonal":
        for y in range(height):
            # Diagonal gradient (135 degrees)
            progress = y / height
            r = int(color1[0] * (1 - progress) + color2[0] * progress)
            g = int(color1[1] * (1 - progress) + color2[1] * progress)
            b = int(color1[2] * (1 - progress) + color2[2] * progress)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    elif direction == "radial":
        # Radial gradient from center
        cx, cy = width // 2, height // 2
        max_dist = math.sqrt(cx**2 + cy**2)
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                progress = min(dist / max_dist, 1.0)
                r = int(color1[0] * (1 - progress) + color2[0] * progress)
                g = int(color1[1] * (1 - progress) + color2[1] * progress)
                b = int(color1[2] * (1 - progress) + color2[2] * progress)
                draw.point((x, y), fill=(r, g, b))
    else:  # horizontal
        for x in range(width):
            progress = x / width
            r = int(color1[0] * (1 - progress) + color2[0] * progress)
            g = int(color1[1] * (1 - progress) + color2[1] * progress)
            b = int(color1[2] * (1 - progress) + color2[2] * progress)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    return image


def _draw_text_with_shadow(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    shadow_offset: int = 2,
    shadow_color: Tuple[int, int, int, int] = None
) -> None:
    """Draw text with a subtle shadow for depth."""
    x, y = position
    if shadow_color is None:
        shadow_color = (0, 0, 0, 60)
    
    # Draw shadow (slightly offset)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color[:3])
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill)


def _create_rounded_rectangle_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    """Create a mask for rounded rectangles."""
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle
    draw.rounded_rectangle([(0, 0), (size[0]-1, size[1]-1)], radius=radius, fill=255)
    
    return mask


def generate_designed_preview(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    domain: str,
    blueprint: Dict[str, Any],
    template_type: str = "default",
    tags: List[str] = None,
    context_items: List[Dict[str, str]] = None,
    credibility_items: List[Dict[str, str]] = None,
    primary_image_base64: Optional[str] = None
) -> bytes:
    """
    Generate a PREMIUM og:image that stops the scroll.
    
    Design principles:
    1. Bold, readable typography (hero headline that pops)
    2. Sophisticated color usage (gradients, depth)
    3. Visual hierarchy that guides the eye
    4. Trust signals prominently displayed
    5. Clean, modern aesthetic
    """
    if tags is None:
        tags = []
    if context_items is None:
        context_items = []
    if credibility_items is None:
        credibility_items = []
    
    try:
        # Get brand colors
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
        accent_color = _hex_to_rgb(blueprint.get("accent_color", "#F59E0B"))
        
        # Determine design style based on template type and content
        has_proof = bool(credibility_items) or bool(subtitle and any(c in subtitle for c in ['★', '⭐', '+', 'users', 'review']))
        has_image = bool(primary_image_base64)
        
        # Choose the best template based on content
        if template_type in ["landing", "saas", "startup"]:
            return _generate_hero_template(
                screenshot_bytes, title, subtitle, description, 
                primary_color, secondary_color, accent_color,
                credibility_items, tags, primary_image_base64
            )
        elif template_type in ["product", "ecommerce"]:
            return _generate_product_template(
                screenshot_bytes, title, subtitle, description,
                primary_color, secondary_color, accent_color,
                credibility_items, tags, primary_image_base64
            )
        else:
            # Default: Modern card with gradient
            return _generate_modern_card_template(
                screenshot_bytes, title, subtitle, description,
                primary_color, secondary_color, accent_color,
                credibility_items, tags, primary_image_base64, domain
            )
        
    except Exception as e:
        logger.error(f"Designed preview generation failed: {e}", exc_info=True)
        return _generate_fallback_preview(title, domain, blueprint)


def _generate_hero_template(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int],
    credibility_items: List[Dict],
    tags: List[str],
    primary_image_base64: Optional[str]
) -> bytes:
    """
    Hero template: Bold headline with gradient background.
    Best for: Landing pages, SaaS, startups.
    """
    # Create gradient background
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
    img = _draw_gradient_background(img, primary_color, _darken_color(secondary_color, 0.6), "diagonal")
    
    # Add screenshot as subtle background texture (20% opacity)
    try:
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
        screenshot = _prepare_screenshot_background(screenshot, OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT)
        
        # Blend screenshot with gradient (very subtle)
        screenshot_alpha = Image.new('L', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), 40)  # 15% opacity
        screenshot_rgba = screenshot.convert('RGBA')
        screenshot_rgba.putalpha(screenshot_alpha)
        img = Image.alpha_composite(img.convert('RGBA'), screenshot_rgba).convert('RGB')
    except:
        pass
    
    draw = ImageDraw.Draw(img)
    
    # Content area with padding
    padding = 80
    content_width = OG_IMAGE_WIDTH - (padding * 2)
    content_y = padding
    
    # === LOGO/IMAGE (top-left) ===
    logo_size = 80
    if primary_image_base64:
        try:
            logo_data = base64.b64decode(primary_image_base64)
            logo_img = Image.open(BytesIO(logo_data)).convert('RGBA')
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Add white background for contrast
            logo_bg = Image.new('RGBA', (logo_size + 8, logo_size + 8), (255, 255, 255, 230))
            img.paste(logo_bg.convert('RGB'), (padding - 4, content_y - 4))
            img.paste(logo_img, (padding, content_y), logo_img)
            content_y += logo_size + 40
        except Exception as e:
            logger.warning(f"Failed to load logo: {e}")
    
    # === PROOF BADGE (if available) ===
    if credibility_items:
        proof_text = credibility_items[0].get("value", "")
        if proof_text:
            proof_font = _load_font(24, bold=True)
            
            # Draw proof badge with accent background
            try:
                bbox = draw.textbbox((0, 0), proof_text, font=proof_font)
                badge_width = bbox[2] - bbox[0] + 32
                badge_height = 44
            except:
                badge_width = len(proof_text) * 12 + 32
                badge_height = 44
            
            # Badge background (accent color with transparency)
            badge_img = Image.new('RGBA', (int(badge_width), badge_height), (*accent_color, 220))
            img.paste(badge_img.convert('RGB'), (padding, content_y))
            draw = ImageDraw.Draw(img)  # Refresh draw object
            
            draw.text((padding + 16, content_y + 10), proof_text, font=proof_font, fill=(255, 255, 255))
            content_y += badge_height + 30
    
    # === MAIN HEADLINE ===
    title_font = _load_font(56, bold=True)
    if title and title != "Untitled":
        title_lines = _wrap_text(title, title_font, content_width, draw)
        for i, line in enumerate(title_lines[:2]):  # Max 2 lines
            y_pos = content_y + (i * 68)
            _draw_text_with_shadow(draw, (padding, y_pos), line, title_font, (255, 255, 255), 3)
        content_y += min(len(title_lines), 2) * 68 + 24
    
    # === SUBTITLE/DESCRIPTION ===
    if subtitle or description:
        text = subtitle or description
        desc_font = _load_font(28, bold=False)
        desc_lines = _wrap_text(text, desc_font, content_width, draw)
        for i, line in enumerate(desc_lines[:2]):
            y_pos = content_y + (i * 36)
            draw.text((padding, y_pos), line, font=desc_font, fill=(255, 255, 255, 200))
        content_y += min(len(desc_lines), 2) * 36 + 30
    
    # === TAGS (as pills at bottom) ===
    if tags:
        tag_font = _load_font(20, bold=True)
        tag_x = padding
        tag_y = OG_IMAGE_HEIGHT - padding - 36
        
        for tag in tags[:3]:
            try:
                bbox = draw.textbbox((0, 0), tag, font=tag_font)
                tag_width = bbox[2] - bbox[0] + 24
            except:
                tag_width = len(tag) * 10 + 24
            
            # Tag pill background
            tag_bg = Image.new('RGBA', (int(tag_width), 36), (255, 255, 255, 50))
            img.paste(tag_bg.convert('RGB'), (tag_x, tag_y), tag_bg)
            draw = ImageDraw.Draw(img)
            
            draw.text((tag_x + 12, tag_y + 8), tag, font=tag_font, fill=(255, 255, 255))
            tag_x += int(tag_width) + 12
    
    # Save
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def _generate_product_template(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int],
    credibility_items: List[Dict],
    tags: List[str],
    primary_image_base64: Optional[str]
) -> bytes:
    """
    Product template: Split layout with image on right.
    Best for: E-commerce, products.
    """
    # Clean white background
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (250, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Left side content
    left_width = OG_IMAGE_WIDTH // 2 - 40
    padding = 60
    content_y = padding
    
    # Accent line on left
    draw.rectangle([(0, 0), (6, OG_IMAGE_HEIGHT)], fill=primary_color)
    
    # === PROOF/RATING ===
    if credibility_items:
        proof_text = credibility_items[0].get("value", "")
        if proof_text:
            proof_font = _load_font(22, bold=True)
            draw.text((padding, content_y), proof_text, font=proof_font, fill=accent_color)
            content_y += 40
    
    # === TITLE ===
    title_font = _load_font(44, bold=True)
    if title and title != "Untitled":
        title_lines = _wrap_text(title, title_font, left_width - padding, draw)
        for i, line in enumerate(title_lines[:2]):
            y_pos = content_y + (i * 54)
            draw.text((padding, y_pos), line, font=title_font, fill=(20, 20, 30))
        content_y += min(len(title_lines), 2) * 54 + 20
    
    # === DESCRIPTION ===
    if description:
        desc_font = _load_font(24, bold=False)
        desc_lines = _wrap_text(description, desc_font, left_width - padding, draw)
        for i, line in enumerate(desc_lines[:3]):
            y_pos = content_y + (i * 32)
            draw.text((padding, y_pos), line, font=desc_font, fill=(80, 80, 100))
        content_y += min(len(desc_lines), 3) * 32 + 30
    
    # === TAGS ===
    if tags:
        tag_font = _load_font(18, bold=False)
        for i, tag in enumerate(tags[:3]):
            tag_y = content_y + (i * 28)
            # Checkmark
            draw.text((padding, tag_y), "✓", font=tag_font, fill=primary_color)
            draw.text((padding + 24, tag_y), tag, font=tag_font, fill=(60, 60, 80))
        content_y += len(tags[:3]) * 28 + 30
    
    # === RIGHT SIDE: PRODUCT IMAGE ===
    right_x = OG_IMAGE_WIDTH // 2 + 20
    right_width = OG_IMAGE_WIDTH // 2 - 60
    
    if primary_image_base64:
        try:
            product_data = base64.b64decode(primary_image_base64)
            product_img = Image.open(BytesIO(product_data)).convert('RGBA')
            
            # Scale to fit right side
            img_ratio = product_img.width / product_img.height
            target_height = OG_IMAGE_HEIGHT - 80
            target_width = int(target_height * img_ratio)
            
            if target_width > right_width:
                target_width = right_width
                target_height = int(target_width / img_ratio)
            
            product_img = product_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Center on right side
            img_x = right_x + (right_width - target_width) // 2
            img_y = (OG_IMAGE_HEIGHT - target_height) // 2
            
            img.paste(product_img, (img_x, img_y), product_img)
        except Exception as e:
            logger.warning(f"Failed to load product image: {e}")
    else:
        # Use screenshot as product preview
        try:
            screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
            screenshot = screenshot.resize((right_width, OG_IMAGE_HEIGHT - 80), Image.Resampling.LANCZOS)
            img.paste(screenshot, (right_x, 40))
        except:
            pass
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def _generate_modern_card_template(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int],
    credibility_items: List[Dict],
    tags: List[str],
    primary_image_base64: Optional[str],
    domain: str
) -> bytes:
    """
    Modern card template: Elegant card with subtle gradient.
    Best for: General purpose, professional.
    """
    # Subtle gradient background
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (248, 249, 252))
    
    # Draw very subtle diagonal lines pattern for texture
    draw = ImageDraw.Draw(img)
    for i in range(0, OG_IMAGE_WIDTH + OG_IMAGE_HEIGHT, 40):
        draw.line([(i, 0), (0, i)], fill=(240, 241, 245), width=1)
    
    # Card dimensions
    card_margin = 40
    card_width = OG_IMAGE_WIDTH - (card_margin * 2)
    card_height = OG_IMAGE_HEIGHT - (card_margin * 2)
    card_x, card_y = card_margin, card_margin
    
    # Card shadow
    shadow_offset = 8
    draw.rectangle(
        [(card_x + shadow_offset, card_y + shadow_offset),
         (card_x + card_width + shadow_offset, card_y + card_height + shadow_offset)],
        fill=(200, 200, 210)
    )
    
    # White card
    draw.rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + card_height)],
        fill=(255, 255, 255)
    )
    
    # Top accent bar (gradient)
    bar_height = 6
    for x in range(card_width):
        progress = x / card_width
        r = int(primary_color[0] * (1 - progress) + accent_color[0] * progress)
        g = int(primary_color[1] * (1 - progress) + accent_color[1] * progress)
        b = int(primary_color[2] * (1 - progress) + accent_color[2] * progress)
        draw.line([(card_x + x, card_y), (card_x + x, card_y + bar_height)], fill=(r, g, b))
    
    # Content area
    padding = 48
    content_x = card_x + padding
    content_y = card_y + bar_height + padding
    content_width = card_width - (padding * 2)
    
    # === LOGO ===
    logo_size = 64
    if primary_image_base64:
        try:
            logo_data = base64.b64decode(primary_image_base64)
            logo_img = Image.open(BytesIO(logo_data)).convert('RGBA')
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Create rounded mask
            mask = _create_rounded_rectangle_mask((logo_size, logo_size), 12)
            
            # Paste logo
            img.paste(logo_img, (content_x, content_y), mask)
            content_y += logo_size + 24
        except:
            pass
    
    # === PROOF BADGE ===
    if credibility_items:
        proof_text = credibility_items[0].get("value", "")
        if proof_text:
            proof_font = _load_font(20, bold=True)
            draw.text((content_x, content_y), proof_text, font=proof_font, fill=accent_color)
            content_y += 36
    
    # === TITLE ===
    title_font = _load_font(40, bold=True)
    if title and title != "Untitled":
        title_lines = _wrap_text(title, title_font, content_width, draw)
        for i, line in enumerate(title_lines[:2]):
            y_pos = content_y + (i * 50)
            draw.text((content_x, y_pos), line, font=title_font, fill=(20, 25, 35))
        content_y += min(len(title_lines), 2) * 50 + 16
    
    # === SUBTITLE ===
    if subtitle:
        sub_font = _load_font(24, bold=False)
        sub_lines = _wrap_text(subtitle, sub_font, content_width, draw)
        for i, line in enumerate(sub_lines[:2]):
            y_pos = content_y + (i * 32)
            draw.text((content_x, y_pos), line, font=sub_font, fill=(80, 85, 100))
        content_y += min(len(sub_lines), 2) * 32 + 16
    
    # === DESCRIPTION ===
    if description:
        desc_font = _load_font(22, bold=False)
        desc_lines = _wrap_text(description, desc_font, content_width, draw)
        for i, line in enumerate(desc_lines[:2]):
            y_pos = content_y + (i * 30)
            draw.text((content_x, y_pos), line, font=desc_font, fill=(100, 105, 120))
        content_y += min(len(desc_lines), 2) * 30 + 24
    
    # === TAGS ===
    if tags:
        tag_font = _load_font(18, bold=False)
        tag_x = content_x
        for tag in tags[:4]:
            try:
                bbox = draw.textbbox((0, 0), tag, font=tag_font)
                tag_width = bbox[2] - bbox[0] + 20
            except:
                tag_width = len(tag) * 10 + 20
            
            # Tag pill
            draw.rounded_rectangle(
                [(tag_x, content_y), (tag_x + tag_width, content_y + 28)],
                radius=14,
                fill=_lighten_color(primary_color, 0.85)
            )
            draw.text((tag_x + 10, content_y + 5), tag, font=tag_font, fill=primary_color)
            tag_x += int(tag_width) + 10
    
    # === DOMAIN (bottom-right) ===
    domain_font = _load_font(16, bold=False)
    domain_clean = domain.replace('www.', '').upper()
    draw.text(
        (card_x + card_width - padding - len(domain_clean) * 8, card_y + card_height - padding - 20),
        domain_clean,
        font=domain_font,
        fill=(160, 165, 180)
    )
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def _generate_landing_template_image(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    cta_text: Optional[str],
    tags: List[str],
    blueprint: Dict[str, Any]
) -> bytes:
    """
    Legacy landing template - redirects to hero template for consistency.
    """
    primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
    secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
    accent_color = _hex_to_rgb(blueprint.get("accent_color", "#F59E0B"))
    
    return _generate_hero_template(
        screenshot_bytes=screenshot_bytes,
        title=title,
        subtitle=subtitle,
        description=description,
        primary_color=primary_color,
        secondary_color=secondary_color,
        accent_color=accent_color,
        credibility_items=[],
        tags=tags if tags else [],
        primary_image_base64=None
    )


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
    """Generate a clean fallback preview if main generation fails."""
    try:
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#3B82F6"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E293B"))
        
        # Create gradient background
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
        img = _draw_gradient_background(img, primary_color, _darken_color(secondary_color, 0.7), "diagonal")
        draw = ImageDraw.Draw(img)
        
        # Add subtle pattern overlay
        for i in range(0, OG_IMAGE_WIDTH + OG_IMAGE_HEIGHT, 60):
            draw.line([(i, 0), (0, i)], fill=(*_lighten_color(primary_color, 0.1)[:3],), width=1)
        
        # Center content vertically
        padding = 80
        content_width = OG_IMAGE_WIDTH - (padding * 2)
        
        # Title - large and bold
        title_font = _load_font(52, bold=True)
        if title and title != "Untitled":
            title_lines = _wrap_text(title, title_font, content_width, draw)
            
            # Calculate vertical centering
            total_height = len(title_lines) * 64
            start_y = (OG_IMAGE_HEIGHT - total_height) // 2 - 30
            
            for i, line in enumerate(title_lines[:2]):
                y_pos = start_y + (i * 64)
                _draw_text_with_shadow(draw, (padding, y_pos), line, title_font, (255, 255, 255), 3)
        
        # Domain at bottom
        domain_font = _load_font(18, bold=True)
        domain_clean = domain.replace('www.', '').upper()
        draw.text(
            (padding, OG_IMAGE_HEIGHT - padding - 24),
            domain_clean,
            fill=(255, 255, 255, 180),
            font=domain_font
        )
        
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Fallback generation failed: {e}", exc_info=True)
        # Ultimate fallback - simple colored rectangle
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
    template_type: str = "default",
    tags: List[str] = None,
    context_items: List[Dict[str, str]] = None,
    credibility_items: List[Dict[str, str]] = None,
    primary_image_base64: Optional[str] = None
) -> Optional[str]:
    """
    Generate designed og:image matching React component and upload to R2.
    
    Creates a beautiful, designed preview image that:
    - Matches the React component card design (white card with accent bar)
    - Has proper typography hierarchy
    - Shows all elements (icon, title, subtitle, description, tags, CTA)
    - Is optimized for mobile social feeds
    
    Args:
        screenshot_bytes: Raw PNG bytes of page screenshot (used for fallback)
        url: Full URL (for domain extraction)
        title: Main headline for the image
        subtitle: Optional subtitle/tagline
        description: Optional description
        cta_text: Optional CTA button text
        blueprint: Color palette
        template_type: Page type
        tags: List of tag strings
        context_items: List of context items with icon and text
        credibility_items: List of credibility items with type and value
        primary_image_base64: Base64 encoded primary image/icon
    
    Returns:
        Public URL of uploaded image, or None if failed
    """
    if blueprint is None:
        blueprint = {}
    if tags is None:
        tags = []
    if context_items is None:
        context_items = []
    if credibility_items is None:
        credibility_items = []
    
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
            template_type=template_type,
            tags=tags,
            context_items=context_items,
            credibility_items=credibility_items,
            primary_image_base64=primary_image_base64
        )
        
        # Upload to R2
        filename = f"previews/demo/{uuid4()}.png"
        image_url = upload_file_to_r2(image_bytes, filename, "image/png")
        
        logger.info(f"Designed preview uploaded: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Failed to generate/upload preview image: {e}", exc_info=True)
        return None
