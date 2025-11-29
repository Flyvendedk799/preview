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
    template_type: str = "default",
    tags: List[str] = None,
    context_items: List[Dict[str, str]] = None,
    credibility_items: List[Dict[str, str]] = None,
    primary_image_base64: Optional[str] = None
) -> bytes:
    """
    Generate a beautifully designed og:image matching the React component card design.
    
    Design approach:
    - White card background (matching React component)
    - Top accent bar (2px, using primary_color)
    - Icon/image in top-left (if available)
    - Title, subtitle, description
    - Tags as features with checkmarks
    - Context items (if available)
    - CTA button at bottom
    - Rounded corners and shadow effect
    
    This creates an image that matches the AI Reconstructed Preview component.
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
        
        # Create white card background - make it prominent and centered
        card_width = OG_IMAGE_WIDTH - 120  # Card width with margins (60px each side)
        card_height = OG_IMAGE_HEIGHT - 60  # Card height with margins (30px top/bottom)
        card_x = 60  # Left margin
        card_y = 30  # Top margin
        
        # Create base image with light gray background (for shadow effect)
        final_image = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (245, 245, 247))
        draw = ImageDraw.Draw(final_image)
        
        # Draw shadow (dark border around card for depth)
        shadow_padding = 6
        draw.rectangle(
            [(card_x - shadow_padding, card_y - shadow_padding),
             (card_x + card_width + shadow_padding, card_y + card_height + shadow_padding)],
            fill=(220, 220, 220)
        )
        
        # Draw white card background
        draw.rectangle(
            [(card_x, card_y), (card_x + card_width, card_y + card_height)],
            fill=(255, 255, 255)
        )
        
        # Draw top accent bar (2px height)
        accent_bar_height = 2
        draw.rectangle(
            [(card_x, card_y), (card_x + card_width, card_y + accent_bar_height)],
            fill=primary_color
        )
        
        # Content padding (matching React component p-6 = 24px)
        padding = 48  # 24px * 2 (scaled for 1200px width)
        content_x = card_x + padding
        content_y = card_y + accent_bar_height + padding
        
        # Typography settings
        title_font = _load_font(32, bold=True)  # text-xl = 20px, scaled
        subtitle_font = _load_font(22, bold=False)  # text-sm = 14px, scaled
        description_font = _load_font(22, bold=False)  # text-sm = 14px, scaled
        tag_font = _load_font(22, bold=False)  # text-sm = 14px, scaled
        context_font = _load_font(18, bold=False)  # text-xs = 12px, scaled
        cta_font = _load_font(22, bold=True)  # text-sm = 14px, scaled
        
        max_text_width = card_width - (padding * 2)
        
        # Draw icon/image (64px = 16 * 4, scaled)
        icon_size = 128  # w-16 h-16 scaled for 1200px
        if primary_image_base64:
            try:
                icon_data = base64.b64decode(primary_image_base64)
                icon_img = Image.open(BytesIO(icon_data)).convert('RGBA')
                icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                
                # Create rounded rectangle mask for icon using ellipse approximation
                mask = Image.new('L', (icon_size, icon_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                radius = 16  # rounded-xl
                # Draw rounded rectangle by drawing filled rectangle with rounded corners
                # Approximate with filled rectangle and corner circles
                mask_draw.rectangle([(radius, 0), (icon_size - radius, icon_size)], fill=255)
                mask_draw.rectangle([(0, radius), (icon_size, icon_size - radius)], fill=255)
                mask_draw.ellipse([(0, 0), (radius * 2, radius * 2)], fill=255)
                mask_draw.ellipse([(icon_size - radius * 2, 0), (icon_size, radius * 2)], fill=255)
                mask_draw.ellipse([(0, icon_size - radius * 2), (radius * 2, icon_size)], fill=255)
                mask_draw.ellipse([(icon_size - radius * 2, icon_size - radius * 2), (icon_size, icon_size)], fill=255)
                
                # Paste icon with rounded corners
                icon_with_alpha = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
                icon_with_alpha.paste(icon_img, (0, 0))
                final_image.paste(icon_with_alpha, (content_x, content_y), mask)
            except Exception as e:
                logger.warning(f"Failed to load icon image: {e}")
                # Draw placeholder icon (colored box)
                icon_bg = Image.new('RGB', (icon_size, icon_size), 
                                   tuple(int(c * 0.08) for c in primary_color))
                final_image.paste(icon_bg, (content_x, content_y))
        else:
            # Draw placeholder icon (colored box)
            icon_bg = Image.new('RGB', (icon_size, icon_size), 
                               tuple(int(c * 0.08) for c in primary_color))
            final_image.paste(icon_bg, (content_x, content_y))
        
        content_y += icon_size + 32  # mb-4 = 16px * 2, scaled
        
        # Draw title
        if title and title != "Untitled":
            title_lines = _wrap_text(title, title_font, max_text_width, draw)
            for i, line in enumerate(title_lines):
                y_pos = content_y + (i * 40)
                draw.text((content_x, y_pos), line, fill=(17, 24, 39), font=title_font)  # text-gray-900
            content_y += len(title_lines) * 40 + 16  # mb-2 = 8px * 2, scaled
        
        # Draw subtitle
        if subtitle:
            subtitle_lines = _wrap_text(subtitle, subtitle_font, max_text_width, draw)
            for i, line in enumerate(subtitle_lines[:2]):  # Max 2 lines
                y_pos = content_y + (i * 28)
                draw.text((content_x, y_pos), line, fill=(75, 85, 99), font=subtitle_font)  # text-gray-600
            content_y += min(len(subtitle_lines), 2) * 28 + 24  # mb-3 = 12px * 2, scaled
        
        # Draw description
        if description:
            desc_lines = _wrap_text(description, description_font, max_text_width, draw)
            for i, line in enumerate(desc_lines[:3]):  # Max 3 lines (line-clamp-3)
                y_pos = content_y + (i * 28)
                draw.text((content_x, y_pos), line, fill=(75, 85, 99), font=description_font)  # text-gray-600
            content_y += min(len(desc_lines), 3) * 28 + 32  # mb-4 = 16px * 2, scaled
        
        # Draw tags as features with checkmarks
        if tags:
            checkmark_size = 16  # w-4 h-4 scaled
            for i, tag in enumerate(tags[:3]):  # Max 3 tags
                tag_y = content_y + (i * 32)  # space-y-2 = 8px * 4, scaled
                
                # Draw checkmark (simplified as checkmark path using polygon)
                check_x = content_x
                check_y = tag_y + 8
                # Draw checkmark as two lines forming a check
                # Vertical part
                draw.line([(check_x + 2, check_y + 4), (check_x + 6, check_y + 8)], 
                         fill=primary_color, width=2)
                # Horizontal part
                draw.line([(check_x + 6, check_y + 8), (check_x + 12, check_y + 2)], 
                         fill=primary_color, width=2)
                
                # Draw tag text
                tag_text_x = check_x + checkmark_size + 16  # gap-2 = 8px * 2, scaled
                draw.text((tag_text_x, tag_y), tag, fill=(55, 65, 81), font=tag_font)  # text-gray-700
            
            content_y += min(len(tags), 3) * 32 + 32  # mb-4 = 16px * 2, scaled
        
        # Draw context items (if available)
        if context_items:
            # Draw border line (border-t)
            border_y = content_y
            draw.line([(content_x, border_y), (content_x + max_text_width, border_y)], 
                     fill=(243, 244, 246), width=2)  # border-gray-100
            content_y += 32  # pt-4 = 16px * 2, scaled
            
            context_x = content_x
            for i, item in enumerate(context_items[:2]):  # Max 2 items
                if i > 0:
                    context_x += 80  # gap-4 = 16px * 5, scaled
                
                # Draw context icon (simplified as small circle)
                icon_x = context_x
                icon_y = content_y
                draw.ellipse([(icon_x, icon_y), (icon_x + 16, icon_y + 16)], 
                           fill=(156, 163, 175), outline=(156, 163, 175))  # text-gray-500
                
                # Draw context text
                text_x = icon_x + 24  # gap-1 = 4px * 6, scaled
                draw.text((text_x, content_y), item.get("text", ""), 
                         fill=(107, 114, 128), font=context_font)  # text-gray-500
            
            content_y += 32  # mb-4 = 16px * 2, scaled
        
        # Draw CTA button at bottom (position after all content)
        if cta_text:
            # Position button after all content with some spacing
            button_y = content_y + 20  # Add spacing after last element
            button_height = 50  # py-2.5 scaled
            button_width = max_text_width
            
            # Draw button background (rounded rectangle approximated)
            button_radius = 8  # rounded-lg
            # Draw rounded rectangle (approximate)
            draw.rectangle(
                [(content_x, button_y), (content_x + button_width, button_y + button_height)],
                fill=primary_color
            )
            
            # Draw button text (centered)
            try:
                bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
                text_width = bbox[2] - bbox[0]
                text_x = content_x + (button_width - text_width) // 2
                text_y = button_y + (button_height - (bbox[3] - bbox[1])) // 2
                draw.text((text_x, text_y), cta_text, fill=(255, 255, 255), font=cta_font)
            except:
                draw.text((content_x + 16, button_y + 12), cta_text, fill=(255, 255, 255), font=cta_font)
        
        # Save to bytes
        buffer = BytesIO()
        final_image.save(buffer, format='PNG', optimize=True)
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
