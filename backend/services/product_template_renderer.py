"""
Enhanced Product Template Renderer

Category-aware, conversion-optimized rendering for product previews.
Integrates:
- Product Intelligence (pricing, urgency, ratings)
- Product Visual System (visual specs)
- Product Design System (category profiles)

Renders different layouts based on product category:
- Electronics: Clean, spec-focused split layout
- Fashion: Hero image with lifestyle context
- Food: Appetizing close-up with vibrant colors
- Beauty: Elegant card with soft imagery
- And more...
"""

import base64
import logging
from io import BytesIO
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Import product systems
try:
    from backend.services.product_intelligence import ProductCategory
    from backend.services.product_design_system import get_design_profile, LayoutStyle, ImageTreatment
    from backend.services.product_visual_system import (
        generate_product_visual_spec,
        UrgencyLevel,
        PriceDisplayStyle
    )
    PRODUCT_SYSTEMS_AVAILABLE = True
except ImportError:
    PRODUCT_SYSTEMS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Standard OG image dimensions
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630


# =============================================================================
# Helper Functions
# =============================================================================

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load font with fallback."""
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    """Wrap text to fit within max width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
        except:
            width = len(test_line) * (font.size * 0.6)
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def _lighten_color(color: Tuple[int, int, int], factor: float = 0.3) -> Tuple[int, int, int]:
    """Lighten a color by mixing with white."""
    return tuple(int(c + (255 - c) * factor) for c in color)


def _darken_color(color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
    """Darken a color by a factor."""
    return tuple(int(c * factor) for c in color)


# =============================================================================
# Urgency Banner Renderer
# =============================================================================

def _render_urgency_banner(
    img: Image.Image,
    draw: ImageDraw.Draw,
    message: str,
    bg_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int],
    font_size: int = 28
) -> int:
    """
    Render urgency banner at top of image.
    
    Returns: Height of banner (to offset subsequent content)
    """
    banner_height = 60
    
    # Draw banner background
    draw.rectangle(
        [(0, 0), (OG_IMAGE_WIDTH, banner_height)],
        fill=bg_color
    )
    
    # Draw text centered
    font = _load_font(font_size, bold=True)
    try:
        bbox = draw.textbbox((0, 0), message, font=font)
        text_width = bbox[2] - bbox[0]
    except:
        text_width = len(message) * (font_size * 0.6)
    
    text_x = (OG_IMAGE_WIDTH - text_width) // 2
    text_y = (banner_height - font_size) // 2 - 5
    
    draw.text((text_x, text_y), message, font=font, fill=text_color)
    
    return banner_height


# =============================================================================
# Discount Badge Renderer
# =============================================================================

def _render_discount_badge(
    img: Image.Image,
    draw: ImageDraw.Draw,
    text: str,
    bg_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int],
    size: str = "large",
    position: str = "top-right-corner"
):
    """Render discount badge in corner."""
    # Size mapping
    size_map = {
        "small": 60,
        "medium": 80,
        "large": 100,
        "extra-large": 120
    }
    badge_size = size_map.get(size, 80)
    font_size = badge_size // 3
    
    # Position mapping
    if position == "top-right-corner":
        badge_x = OG_IMAGE_WIDTH - badge_size - 30
        badge_y = 30
    elif position == "top-left-corner":
        badge_x = 30
        badge_y = 30
    else:
        badge_x = OG_IMAGE_WIDTH - badge_size - 30
        badge_y = 30
    
    # Draw circular badge
    draw.ellipse(
        [(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)],
        fill=bg_color
    )
    
    # Draw text centered in badge
    font = _load_font(font_size, bold=True)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = len(text) * (font_size * 0.6)
        text_height = font_size
    
    text_x = badge_x + (badge_size - text_width) // 2
    text_y = badge_y + (badge_size - text_height) // 2 - 5
    
    draw.text((text_x, text_y), text, font=font, fill=text_color)


# =============================================================================
# Rating Renderer
# =============================================================================

def _render_rating(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    rating: float,
    review_count: Optional[int],
    star_size: int = 24,
    star_color: Tuple[int, int, int] = (245, 158, 11),  # Gold
    show_count: bool = True
) -> int:
    """
    Render star rating.
    
    Returns: Width of rendered rating
    """
    # Draw stars
    star_spacing = star_size + 4
    for i in range(5):
        star_x = x + (i * star_spacing)
        filled = i < int(rating)
        
        # Simple star representation (filled circle for simplicity)
        if filled:
            draw.ellipse(
                [(star_x, y), (star_x + star_size, y + star_size)],
                fill=star_color
            )
        else:
            draw.ellipse(
                [(star_x, y), (star_x + star_size, y + star_size)],
                outline=star_color,
                width=2
            )
    
    total_width = 5 * star_spacing
    
    # Draw rating number and count
    if show_count and review_count:
        font = _load_font(star_size, bold=True)
        text = f"  {rating:.1f} ({review_count:,})"
        draw.text((x + total_width, y), text, font=font, fill=(31, 41, 55))
        
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(text) * (star_size * 0.6)
        
        total_width += text_width
    
    return total_width


# =============================================================================
# Category-Specific Layout Renderers
# =============================================================================

def _render_electronics_layout(
    img: Image.Image,
    draw: ImageDraw.Draw,
    title: str,
    description: Optional[str],
    features: List[str],
    price_text: str,
    price_color: Tuple[int, int, int],
    price_size: int,
    original_price: Optional[str],
    rating: Optional[float],
    review_count: Optional[int],
    product_image: Optional[Image.Image],
    primary_color: Tuple[int, int, int],
    y_offset: int = 0
):
    """Render electronics layout: Clean split with specs."""
    # Left side: Content (55%)
    left_width = int(OG_IMAGE_WIDTH * 0.55)
    padding = 64
    content_y = padding + y_offset
    
    # Accent bar
    draw.rectangle([(0, y_offset), (8, OG_IMAGE_HEIGHT)], fill=primary_color)
    
    # Title
    title_font = _load_font(72, bold=True)
    title_lines = _wrap_text(title, title_font, left_width - padding - 40, draw)
    for i, line in enumerate(title_lines[:2]):
        draw.text((padding, content_y + (i * 50)), line, font=title_font, fill=(15, 23, 42))
    content_y += min(len(title_lines), 2) * 50 + 32
    
    # Rating (prominent for electronics)
    if rating:
        _render_rating(draw, padding, content_y, rating, review_count, star_size=28, show_count=True)
        content_y += 45
    
    # Price
    price_font = _load_font(price_size, bold=True)
    draw.text((padding, content_y), price_text, font=price_font, fill=price_color)
    content_y += price_size + 20
    
    # Original price (strikethrough)
    if original_price:
        orig_font = _load_font(28)
        draw.text((padding, content_y), original_price, font=orig_font, fill=(156, 163, 175))
        # Strikethrough line
        try:
            bbox = draw.textbbox((padding, content_y), original_price, font=orig_font)
            line_y = content_y + 14
            draw.line([(bbox[0], line_y), (bbox[2], line_y)], fill=(156, 163, 175), width=2)
        except:
            pass
        content_y += 40
    
    # Specs/Features (grid-style for electronics)
    if features:
        spec_font = _load_font(22, bold=True)
        for i, feature in enumerate(features[:4]):
            # Checkmark
            check_y = content_y + (i * 32)
            draw.ellipse(
                [(padding, check_y), (padding + 20, check_y + 20)],
                fill=_lighten_color(primary_color, 0.85)
            )
            draw.text((padding + 4, check_y + 2), "✓", font=_load_font(16, bold=True), fill=primary_color)
            # Feature text
            draw.text((padding + 28, check_y), feature, font=spec_font, fill=(51, 65, 85))
    
    # Right side: Product image (clean background)
    if product_image:
        right_x = left_width + 30
        right_width = OG_IMAGE_WIDTH - right_x - 50
        right_height = OG_IMAGE_HEIGHT - y_offset - 100
        
        # Light gray background
        draw.rectangle(
            [(right_x, y_offset + 50), (OG_IMAGE_WIDTH - 50, OG_IMAGE_HEIGHT - 50)],
            fill=(248, 250, 252)
        )
        
        # Center product image
        img_ratio = product_image.width / product_image.height
        target_height = right_height - 40
        target_width = int(target_height * img_ratio)
        
        if target_width > right_width - 40:
            target_width = right_width - 40
            target_height = int(target_width / img_ratio)
        
        product_image = product_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        img_x = right_x + (right_width - target_width) // 2
        img_y = y_offset + 50 + (right_height - target_height) // 2
        
        img.paste(product_image, (img_x, img_y), product_image if product_image.mode == 'RGBA' else None)


def _render_fashion_layout(
    img: Image.Image,
    draw: ImageDraw.Draw,
    title: str,
    price_text: str,
    price_color: Tuple[int, int, int],
    price_size: int,
    original_price: Optional[str],
    product_image: Optional[Image.Image],
    colors: List[str],
    sizes: List[str],
    primary_color: Tuple[int, int, int],
    y_offset: int = 0
):
    """Render fashion layout: Hero image with lifestyle context."""
    # Large background image
    if product_image:
        # Resize to fill width
        aspect = product_image.width / product_image.height
        target_width = OG_IMAGE_WIDTH
        target_height = int(target_width / aspect)
        
        if target_height < OG_IMAGE_HEIGHT:
            target_height = OG_IMAGE_HEIGHT
            target_width = int(target_height * aspect)
        
        product_image = product_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Center and crop
        x_offset = (target_width - OG_IMAGE_WIDTH) // 2
        y_offset_img = (target_height - OG_IMAGE_HEIGHT) // 2
        product_image = product_image.crop((x_offset, y_offset_img, x_offset + OG_IMAGE_WIDTH, y_offset_img + OG_IMAGE_HEIGHT))
        
        # Paste as background
        img.paste(product_image, (0, 0))
        
        # Darken overlay for text readability
        overlay = Image.new('RGBA', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (0, 0, 0, 120))
        img.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(img)
    
    # Content at bottom with semi-transparent background
    content_height = 250
    content_y = OG_IMAGE_HEIGHT - content_height
    
    # Semi-transparent white background
    overlay = Image.new('RGBA', (OG_IMAGE_WIDTH, content_height), (255, 255, 255, 235))
    img.paste(overlay, (0, content_y), overlay)
    draw = ImageDraw.Draw(img)
    
    padding = 50
    text_y = content_y + 40
    
    # Title (large, centered)
    title_font = _load_font(64, bold=True)
    try:
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
    except:
        title_width = len(title) * (64 * 0.6)
    
    title_x = (OG_IMAGE_WIDTH - title_width) // 2
    draw.text((title_x, text_y), title, font=title_font, fill=(15, 23, 42))
    text_y += 80
    
    # Price (HERO prominence for fashion)
    price_font = _load_font(price_size, bold=True)
    try:
        bbox = draw.textbbox((0, 0), price_text, font=price_font)
        price_width = bbox[2] - bbox[0]
    except:
        price_width = len(price_text) * (price_size * 0.6)
    
    price_x = (OG_IMAGE_WIDTH - price_width) // 2
    draw.text((price_x, text_y), price_text, font=price_font, fill=price_color)
    
    # Original price next to current (if on sale)
    if original_price:
        orig_font = _load_font(32)
        orig_text_x = price_x + price_width + 20
        draw.text((orig_text_x, text_y + 10), original_price, font=orig_font, fill=(107, 114, 128))
        # Strikethrough
        try:
            bbox = draw.textbbox((orig_text_x, text_y + 10), original_price, font=orig_font)
            line_y = text_y + 26
            draw.line([(bbox[0], line_y), (bbox[2], line_y)], fill=(107, 114, 128), width=2)
        except:
            pass
    
    text_y += 70
    
    # Colors and sizes (centered, badge style)
    if colors or sizes:
        badge_font = _load_font(18, bold=True)
        variants_text = []
        if colors:
            variants_text.append(f"Colors: {', '.join(colors[:4])}")
        if sizes:
            variants_text.append(f"Sizes: {', '.join(sizes[:6])}")
        
        full_text = "  •  ".join(variants_text)
        try:
            bbox = draw.textbbox((0, 0), full_text, font=badge_font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(full_text) * (18 * 0.6)
        
        text_x = (OG_IMAGE_WIDTH - text_width) // 2
        draw.text((text_x, text_y), full_text, font=badge_font, fill=(71, 85, 105))


def _render_food_layout(
    img: Image.Image,
    draw: ImageDraw.Draw,
    title: str,
    price_text: str,
    price_color: Tuple[int, int, int],
    price_size: int,
    rating: Optional[float],
    review_count: Optional[int],
    badges: List[str],
    product_image: Optional[Image.Image],
    primary_color: Tuple[int, int, int],
    y_offset: int = 0
):
    """Render food layout: Appetizing close-up with vibrant colors."""
    # Large product image (close-up zoom)
    if product_image:
        # Enhance colors for food
        enhancer = ImageEnhance.Color(product_image)
        product_image = enhancer.enhance(1.25)  # +25% saturation
        
        # Increase contrast
        contrast = ImageEnhance.Contrast(product_image)
        product_image = contrast.enhance(1.1)
        
        # Resize to fill most of image
        aspect = product_image.width / product_image.height
        target_width = int(OG_IMAGE_WIDTH * 0.95)
        target_height = int(target_width / aspect)
        
        if target_height < OG_IMAGE_HEIGHT * 0.7:
            target_height = int(OG_IMAGE_HEIGHT * 0.7)
            target_width = int(target_height * aspect)
        
        product_image = product_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Center
        img_x = (OG_IMAGE_WIDTH - target_width) // 2
        img_y = 30
        
        img.paste(product_image, (img_x, img_y), product_image if product_image.mode == 'RGBA' else None)
    
    # Content overlay at bottom
    overlay_height = 180
    overlay_y = OG_IMAGE_HEIGHT - overlay_height
    
    # Semi-transparent white
    overlay = Image.new('RGBA', (OG_IMAGE_WIDTH, overlay_height), (255, 255, 255, 240))
    img.paste(overlay, (0, overlay_y), overlay)
    draw = ImageDraw.Draw(img)
    
    padding = 40
    content_y = overlay_y + 30
    
    # Title (extra-bold for food)
    title_font = _load_font(56, bold=True)
    draw.text((padding, content_y), title, font=title_font, fill=(15, 23, 42))
    content_y += 70
    
    # Rating + Price + Badges in a row
    row_y = content_y
    row_x = padding
    
    # Rating
    if rating:
        _render_rating(draw, row_x, row_y, rating, review_count, star_size=24, show_count=True)
        row_x += 300
    
    # Price
    price_font = _load_font(price_size, bold=True)
    draw.text((row_x, row_y - 5), price_text, font=price_font, fill=price_color)
    row_x += 200
    
    # Badges (Organic, Non-GMO, etc.)
    if badges:
        badge_font = _load_font(18, bold=True)
        for badge in badges[:3]:
            # Badge background
            try:
                bbox = draw.textbbox((0, 0), badge, font=badge_font)
                badge_width = bbox[2] - bbox[0] + 16
            except:
                badge_width = len(badge) * 11 + 16
            
            draw.rounded_rectangle(
                [(row_x, row_y), (row_x + badge_width, row_y + 30)],
                radius=15,
                fill=_lighten_color(primary_color, 0.9)
            )
            draw.text((row_x + 8, row_y + 5), badge, font=badge_font, fill=primary_color)
            row_x += badge_width + 10


def _render_beauty_layout(
    img: Image.Image,
    draw: ImageDraw.Draw,
    title: str,
    price_text: str,
    price_color: Tuple[int, int, int],
    price_size: int,
    features: List[str],
    rating: Optional[float],
    review_count: Optional[int],
    product_image: Optional[Image.Image],
    primary_color: Tuple[int, int, int],
    y_offset: int = 0
):
    """Render beauty layout: Elegant card with soft imagery."""
    # Elegant gradient background
    for y in range(OG_IMAGE_HEIGHT):
        progress = y / OG_IMAGE_HEIGHT
        r = int(255 - (255 - 248) * progress)
        g = int(255 - (255 - 250) * progress)
        b = int(255 - (255 - 255) * progress)
        draw.line([(0, y), (OG_IMAGE_WIDTH, y)], fill=(r, g, b))
    
    # Card dimensions
    card_width = int(OG_IMAGE_WIDTH * 0.85)
    card_height = int(OG_IMAGE_HEIGHT * 0.85)
    card_x = (OG_IMAGE_WIDTH - card_width) // 2
    card_y = (OG_IMAGE_HEIGHT - card_height) // 2 + y_offset
    
    # White card with shadow
    shadow_offset = 8
    draw.rectangle(
        [(card_x + shadow_offset, card_y + shadow_offset), 
         (card_x + card_width + shadow_offset, card_y + card_height + shadow_offset)],
        fill=(220, 220, 230)
    )
    draw.rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + card_height)],
        fill=(255, 255, 255)
    )
    
    padding = 50
    content_y = card_y + padding
    
    # Product image at top (soft, elegant)
    if product_image:
        # Soft enhancement for beauty
        enhancer = ImageEnhance.Brightness(product_image)
        product_image = enhancer.enhance(1.05)
        
        img_height = int(card_height * 0.45)
        aspect = product_image.width / product_image.height
        img_width = int(img_height * aspect)
        
        if img_width > card_width - (padding * 2):
            img_width = card_width - (padding * 2)
            img_height = int(img_width / aspect)
        
        product_image = product_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
        
        img_x = card_x + (card_width - img_width) // 2
        img.paste(product_image, (img_x, content_y), product_image if product_image.mode == 'RGBA' else None)
        content_y += img_height + 30
    
    # Title (elegant, centered)
    title_font = _load_font(44)  # Not bold, elegant
    try:
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
    except:
        title_width = len(title) * (44 * 0.6)
    
    title_x = card_x + (card_width - title_width) // 2
    draw.text((title_x, content_y), title, font=title_font, fill=(15, 23, 42))
    content_y += 60
    
    # Features (key ingredients)
    if features:
        feat_font = _load_font(20)
        for i, feature in enumerate(features[:3]):
            draw.text((card_x + padding, content_y + (i * 28)), f"• {feature}", font=feat_font, fill=(71, 85, 105))
        content_y += len(features[:3]) * 28 + 30
    
    # Bottom row: Rating + Price
    bottom_y = card_y + card_height - padding - 40
    
    # Rating (left)
    if rating:
        _render_rating(draw, card_x + padding, bottom_y, rating, review_count, star_size=22, show_count=True)
    
    # Price (right)
    price_font = _load_font(price_size, bold=True)
    try:
        bbox = draw.textbbox((0, 0), price_text, font=price_font)
        price_width = bbox[2] - bbox[0]
    except:
        price_width = len(price_text) * (price_size * 0.6)
    
    price_x = card_x + card_width - padding - price_width
    draw.text((price_x, bottom_y - 5), price_text, font=price_font, fill=price_color)


# =============================================================================
# Main Enhanced Product Renderer
# =============================================================================

def render_enhanced_product_preview(
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
    product_intelligence: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Render enhanced product preview with category-aware layout.
    
    Args:
        screenshot_bytes: Original screenshot
        title: Product title
        subtitle: Product subtitle
        description: Product description
        primary_color: Brand primary color
        secondary_color: Brand secondary color
        accent_color: Brand accent color
        credibility_items: Credibility/social proof items
        tags: Feature tags
        primary_image_base64: Product image (base64)
        product_intelligence: Product intelligence data (from _product_intelligence)
    
    Returns:
        bytes: PNG image data
    """
    if not PRODUCT_SYSTEMS_AVAILABLE or not product_intelligence:
        # Fallback to basic template if systems not available
        logger.warning("Product systems not available, using basic template")
        return _render_basic_product_template(
            screenshot_bytes, title, subtitle, description,
            primary_color, secondary_color, accent_color,
            credibility_items, tags, primary_image_base64
        )
    
    # Create base image
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Get category and profile
    category_name = product_intelligence.get("category", "general")
    try:
        category = ProductCategory(category_name)
    except:
        category = ProductCategory.GENERAL
    
    design_profile = get_design_profile(category)
    
    # Generate visual specs
    visual_spec = generate_product_visual_spec(product_intelligence)
    
    y_offset = 0
    
    # Render urgency banner if present
    if visual_spec.urgency_banner and visual_spec.urgency_banner.show:
        banner = visual_spec.urgency_banner
        y_offset = _render_urgency_banner(
            img, draw,
            banner.message,
            banner.bg_color.rgb,
            banner.text_color.rgb,
            banner.font_size
        )
        draw = ImageDraw.Draw(img)  # Recreate after banner
    
    # Render discount badge if present
    if visual_spec.discount_badge and visual_spec.discount_badge.show:
        badge = visual_spec.discount_badge
        _render_discount_badge(
            img, draw,
            badge.text,
            badge.bg_color.rgb,
            badge.text_color.rgb,
            badge.size,
            badge.position
        )
    
    # Prepare product image
    product_image = None
    if primary_image_base64:
        try:
            product_data = base64.b64decode(primary_image_base64)
            product_image = Image.open(BytesIO(product_data)).convert('RGBA')
        except Exception as e:
            logger.warning(f"Failed to load product image: {e}")
    
    # Get pricing info
    pricing = product_intelligence.get("pricing", {})
    price_text = pricing.get("current_price", "$0.00")
    original_price = pricing.get("original_price")
    
    # Get price visual specs
    price_color = primary_color
    price_size = 40
    if visual_spec.price:
        price_color = visual_spec.price.current_price_color.rgb
        price_size = visual_spec.price.current_price_font_size
    
    # Get rating info
    rating_info = product_intelligence.get("rating", {})
    rating = rating_info.get("rating")
    review_count = rating_info.get("review_count")
    
    # Get trust signals
    trust_signals = product_intelligence.get("trust_signals", {})
    badges = trust_signals.get("badges", [])
    
    # Get product details
    features = tags  # Use tags as features for now
    colors = []
    sizes = []
    
    # Render based on category layout
    if design_profile.layout_style == LayoutStyle.SPLIT:
        # Electronics, Home, Books
        _render_electronics_layout(
            img, draw, title, description, features,
            price_text, price_color, price_size, original_price,
            rating, review_count, product_image, primary_color, y_offset
        )
    
    elif design_profile.layout_style == LayoutStyle.HERO:
        if category in [ProductCategory.FASHION, ProductCategory.SPORTS]:
            # Fashion, Sports
            _render_fashion_layout(
                img, draw, title, price_text, price_color, price_size,
                original_price, product_image, colors, sizes, primary_color, y_offset
            )
        elif category == ProductCategory.FOOD:
            # Food
            _render_food_layout(
                img, draw, title, price_text, price_color, price_size,
                rating, review_count, badges, product_image, primary_color, y_offset
            )
        else:
            # Default hero
            _render_fashion_layout(
                img, draw, title, price_text, price_color, price_size,
                original_price, product_image, colors, sizes, primary_color, y_offset
            )
    
    elif design_profile.layout_style == LayoutStyle.CARD:
        # Beauty, Jewelry
        _render_beauty_layout(
            img, draw, title, price_text, price_color, price_size,
            features, rating, review_count, product_image, primary_color, y_offset
        )
    
    else:
        # Fallback to electronics layout
        _render_electronics_layout(
            img, draw, title, description, features,
            price_text, price_color, price_size, original_price,
            rating, review_count, product_image, primary_color, y_offset
        )
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True, quality=95)
    return buffer.getvalue()


def _render_basic_product_template(
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
    """Basic fallback product template."""
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Simple split layout
    draw.rectangle([(0, 0), (8, OG_IMAGE_HEIGHT)], fill=primary_color)
    
    padding = 64
    content_y = padding
    
    # Title
    title_font = _load_font(72, bold=True)
    draw.text((padding, content_y), title[:50], font=title_font, fill=(15, 23, 42))
    content_y += 100
    
    # Description
    if description:
        desc_font = _load_font(28)
        draw.text((padding, content_y), description[:100], font=desc_font, fill=(71, 85, 105))
        content_y += 50
    
    # Tags
    if tags:
        tag_font = _load_font(22)
        for i, tag in enumerate(tags[:3]):
            draw.text((padding, content_y + (i * 30)), f"• {tag}", font=tag_font, fill=(51, 65, 85))
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()
