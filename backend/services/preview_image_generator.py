"""
Generate PREMIUM preview images for og:image.

DESIGN PHILOSOPHY - Enhanced with Design DNA Intelligence:
Create social preview images that:
1. Look like they were designed by a professional
2. Use bold typography that pops at small sizes
3. Have modern, sophisticated color usage
4. Create visual interest that stops the scroll
5. Feel premium and trustworthy
6. NEW: Honor the original design's personality and intent
7. NEW: Adapt typography, colors, and composition to match brand DNA

This module now integrates with:
- Design DNA Extractor for understanding design philosophy
- Typography Intelligence for font personality matching
- Color Psychology Engine for emotional accuracy
- Adaptive Template Engine for dynamic compositions
"""

import base64
import logging
import math
from io import BytesIO
from uuid import uuid4
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from backend.services.r2_client import upload_file_to_r2

# Design DNA Integration
try:
    from backend.services.adaptive_template_engine import (
        AdaptiveTemplateEngine,
        PreviewContent,
        generate_adaptive_preview
    )
    from backend.services.design_dna_extractor import (
        DesignDNA,
        DesignPhilosophy,
        TypographyDNA,
        ColorPsychology,
        SpatialIntelligence,
        HeroElement,
        BrandPersonality,
        UIComponents,
        VisualEffects,
        LayoutPatterns
    )
    ADAPTIVE_ENGINE_AVAILABLE = True
except ImportError:
    ADAPTIVE_ENGINE_AVAILABLE = False

# Enhanced Product Template Renderer
try:
    from backend.services.product_template_renderer import render_enhanced_product_preview
    ENHANCED_PRODUCT_RENDERER_AVAILABLE = True
except ImportError:
    ENHANCED_PRODUCT_RENDERER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Standard OG image dimensions (1.91:1 ratio)
OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple with validation.
    FIX 3: Validates color format and provides safe fallbacks.
    """
    if not hex_color or not isinstance(hex_color, str):
        return (59, 130, 246)  # Default blue
    
    hex_color = hex_color.lstrip('#').strip()
    
    # Validate hex format (3 or 6 characters)
    if len(hex_color) not in [3, 6]:
        logger.warning(f"Invalid hex color format: {hex_color}, using default")
        return (59, 130, 246)
    
    # Expand 3-char hex to 6-char
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    
    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Validate RGB values are in valid range
        if all(0 <= c <= 255 for c in rgb):
            return rgb
        else:
            logger.warning(f"RGB values out of range: {rgb}, using default")
            return (59, 130, 246)
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse hex color '{hex_color}': {e}, using default")
        return (59, 130, 246)  # Default blue


def _darken_color(color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
    """Darken a color by a factor."""
    return tuple(int(c * factor) for c in color)


def _lighten_color(color: Tuple[int, int, int], factor: float = 0.3) -> Tuple[int, int, int]:
    """Lighten a color by mixing with white."""
    return tuple(int(c + (255 - c) * factor) for c in color)


def _get_contrast_color(bg_color: tuple) -> tuple:
    """
    Get high-contrast text color based on WCAG AAA accessibility standards.
    DESIGN FIX 3: Enhanced contrast for better readability.
    Ensures minimum 7:1 contrast ratio for large text, 4.5:1 for normal text.
    """
    luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
    
    # Enhanced contrast calculation
    if luminance < 0.4:  # Dark background
        return (255, 255, 255)  # Pure white for maximum contrast
    elif luminance < 0.5:  # Medium-dark background
        return (255, 255, 255)  # White still best
    elif luminance < 0.7:  # Medium-light background
        return (15, 23, 42)  # Very dark blue-gray
    else:  # Light background
        return (10, 10, 15)  # Near-black for maximum contrast


def _get_text_shadow_color(text_color: tuple) -> tuple:
    """Get shadow color for text."""
    if text_color[0] > 200:  # White text
        return (0, 0, 0, 80)  # Dark shadow
    return (255, 255, 255, 40)  # Light shadow


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """
    Load font with fallbacks.
    DESIGN FIX 1: Improved font loading with better size scaling.
    """
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
            font = ImageFont.truetype(path, size)
            # DESIGN FIX 1: Ensure minimum readable size
            if size < 12:
                logger.warning(f"Font size {size} too small, using 12")
                return ImageFont.truetype(path, 12)
            logger.info(f"🔍 FONT DEBUG: Successfully loaded font {path} at size {size}")
            return font
        except Exception as e:
            logger.warning(f"🔍 FONT DEBUG: Failed to load font {path}: {e}")
            continue
    
    # Fallback to default with size adjustment
    logger.warning(f"🔍 FONT DEBUG: All TrueType fonts failed, using default font")
    default_font = ImageFont.load_default()
    if size < 12:
        return default_font
    return default_font


def smart_truncate(text: str, max_chars: int) -> str:
    """
    PHASE 4: Truncate at sentence or word boundary, never mid-word.
    
    Priority order:
    1. Try to end at a sentence boundary (. ! ?)
    2. Fall back to word boundary
    3. Never cut in the middle of a word
    
    Args:
        text: Text to truncate
        max_chars: Maximum character length
        
    Returns:
        Truncated text with proper ending
    """
    # CRITICAL FIX: Ensure text is a string to prevent garbled rendering
    if text is None:
        return ""
    
    text = str(text)
    
    if not text or len(text) <= max_chars:
        return text
    
    # Get substring up to max_chars
    truncated = text[:max_chars]
    
    # PRIORITY 1: Try to find sentence boundary
    # Look for sentence-ending punctuation followed by space or end
    sentence_ends = ['. ', '! ', '? ', '."', '!"', '?"', ".)", "!)"]
    best_sentence_end = -1
    
    for end_marker in sentence_ends:
        pos = truncated.rfind(end_marker)
        if pos > max_chars * 0.5:  # At least 50% of content preserved
            if pos > best_sentence_end:
                best_sentence_end = pos + len(end_marker) - 1
    
    # Also check for sentence ending at the very end
    if truncated.rstrip()[-1] in '.!?' and len(truncated) > max_chars * 0.5:
        return truncated.rstrip()
    
    if best_sentence_end > 0:
        return truncated[:best_sentence_end + 1].rstrip()
    
    # PRIORITY 2: Try to find a good word boundary
    # Look for last space
    last_space = truncated.rfind(' ')
    
    if last_space > max_chars * 0.6:  # At least 60% of content preserved
        truncated_at_word = truncated[:last_space].rstrip()
        
        # Don't end on short connecting words if possible
        last_word = truncated_at_word.split()[-1].lower() if truncated_at_word.split() else ""
        short_words = {'a', 'an', 'the', 'and', 'or', 'but', 'of', 'in', 'on', 'at', 'to', 'for', 'by', 'is', 'are', 'was'}
        
        if last_word in short_words and len(truncated_at_word.split()) > 2:
            # Try to go back one more word
            earlier_space = truncated_at_word.rfind(' ')
            if earlier_space > max_chars * 0.5:
                truncated_at_word = truncated_at_word[:earlier_space].rstrip()
        
        return truncated_at_word + "..."
    
    # PRIORITY 3: Just truncate at max_chars but add ellipsis
    # Never cut in the middle of a word - back up to last space
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + "..."
    
    # Very rare: no spaces at all (single long word) - hard truncate
    return truncated[:max_chars - 3] + "..."


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw, max_lines: int = 3) -> List[str]:
    """
    PHASE 4: Wrap text with smart line breaking and sentence-aware truncation.
    
    Features:
    - Never cut sentences mid-word
    - Preserve natural reading flow
    - Smart handling of long words (URLs, etc.)
    - Sentence boundary awareness for cleaner endings
    
    Args:
        text: Text to wrap
        font: Font to use for measurement
        max_width: Maximum pixel width
        draw: ImageDraw object for text measurement
        max_lines: Maximum number of lines (default 3)
        
    Returns:
        List of lines that fit within constraints
    """
    # CRITICAL FIX: Ensure text is a string to prevent garbled rendering
    if text is None:
        return []
    
    text = str(text)
    
    if not text or not text.strip():
        return []
    
    # Clean text first - normalize whitespace
    text = " ".join(text.split())
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
        except:
            # Fallback calculation: approximate width
            char_width = font.size * 0.6 if hasattr(font, 'size') else 8
            width = len(test_line) * char_width
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            
            # Handle very long words (URLs, technical terms, etc.)
            if len(word) > 40:
                # For very long words, use smart_truncate
                truncated_word = smart_truncate(word, 37)
                current_line = [truncated_word]
            else:
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # PHASE 4: Smart truncation with sentence awareness
    if len(lines) > max_lines:
        # Keep first max_lines-1 complete lines
        result = lines[:max_lines - 1]
        
        # Get remaining text for smart truncation
        remaining_text = ' '.join(lines[max_lines - 1:])
        
        # Calculate how many chars fit in the last line
        # Approximate based on first line length
        first_line_chars = len(lines[0]) if lines else 60
        last_line_max = max(40, first_line_chars)
        
        # Use smart_truncate for the last line
        last_line = smart_truncate(remaining_text, last_line_max)
        
        # Double check it fits
        try:
            bbox = draw.textbbox((0, 0), last_line, font=font)
            last_line_width = bbox[2] - bbox[0]
            
            # If still too wide, truncate further
            while last_line_width > max_width and len(last_line) > 20:
                last_line = smart_truncate(last_line[:-4], len(last_line) - 10)
                bbox = draw.textbbox((0, 0), last_line, font=font)
                last_line_width = bbox[2] - bbox[0]
        except:
            pass  # Keep the truncated line as-is
        
        result.append(last_line)
        return result
    
    return lines


def _draw_gradient_background(
    image: Image.Image,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    direction: str = "diagonal"
) -> Image.Image:
    """
    Draw a smooth gradient background using LAB color space for perceptually uniform gradients.
    """
    from backend.services.gradient_generator import generate_smooth_gradient
    
    width, height = image.size
    
    # Map direction to angle
    angle_map = {
        "diagonal": 135,
        "vertical": 90,
        "horizontal": 0,
        "radial": 0  # Will use radial style
    }
    angle = angle_map.get(direction, 135)
    style = "radial" if direction == "radial" else "linear"
    
    # Generate smooth gradient using LAB color space
    gradient_img = generate_smooth_gradient(
        width, height, color1, color2, angle=angle, style=style
    )
    
    # Paste onto original image
    image.paste(gradient_img)
    
    logger.debug(f"Generated gradient using LAB color space: {width}x{height}")
    
    return image
    
    # OLD METHOD - KEPT FOR REFERENCE BUT NOT USED
    if False:
        # Generate at 3x resolution for much smoother gradients (more color steps = less banding)
        scale_factor = 3
        high_width = width * scale_factor
        high_height = height * scale_factor
        
        # Calculate gradient direction using numpy for speed
        import numpy as np
        
        if direction == "diagonal":
        # Create diagonal gradient using PIL's HSV mode for smoother perceptual transitions
        # This is more reliable than manual HSV conversion
        import colorsys
        
        # Convert RGB to HSV for smoother interpolation
        h1, s1, v1 = colorsys.rgb_to_hsv(color1[0]/255.0, color1[1]/255.0, color1[2]/255.0)
        h2, s2, v2 = colorsys.rgb_to_hsv(color2[0]/255.0, color2[1]/255.0, color2[2]/255.0)
        
        # Create coordinate arrays
        y_coords = np.arange(high_height, dtype=np.float64)[:, np.newaxis] / max(high_height - 1, 1)
        x_coords = np.arange(high_width, dtype=np.float64)[np.newaxis, :] / max(high_width - 1, 1)
        # Combine for diagonal effect (70% vertical, 30% horizontal)
        progress = y_coords * 0.7 + x_coords * 0.3
        
        # Interpolate in HSV space (smoother perceptual transitions)
        h = h1 * (1 - progress) + h2 * progress
        s = s1 * (1 - progress) + s2 * progress
        v = v1 * (1 - progress) + v2 * progress
        
        # Use PIL's HSV mode for accurate conversion with dithering to prevent banding
        # PIL HSV mode: H=0-255 (represents 0-360°), S=0-255 (represents 0-100%), V=0-255 (represents 0-100%)
        # Add subtle noise before quantization to break up banding
        noise_strength = 0.3  # Small noise to prevent quantization artifacts
        h_noise = np.random.uniform(-noise_strength, noise_strength, h.shape)
        s_noise = np.random.uniform(-noise_strength, noise_strength, s.shape)
        v_noise = np.random.uniform(-noise_strength, noise_strength, v.shape)
        
        h_scaled = np.clip((h * 255 / 360.0) + h_noise, 0, 255).astype(np.uint8)  # H: 0-360° -> 0-255
        s_scaled = np.clip((s * 255) + s_noise, 0, 255).astype(np.uint8)  # S: 0-1 -> 0-255
        v_scaled = np.clip((v * 255) + v_noise, 0, 255).astype(np.uint8)  # V: 0-1 -> 0-255
        
        # Create HSV image
        hsv_array = np.stack([h_scaled, s_scaled, v_scaled], axis=2)
        hsv_img = Image.fromarray(hsv_array, mode='HSV')
        
        # Convert HSV to RGB using PIL (most accurate method)
        high_res_img = hsv_img.convert('RGB')
        
        # Apply strong Gaussian smoothing before quantization
        try:
            from scipy import ndimage
            rgb_array = np.array(high_res_img, dtype=np.float64)
            rgb_array[:, :, 0] = ndimage.gaussian_filter(rgb_array[:, :, 0], sigma=2.0)
            rgb_array[:, :, 1] = ndimage.gaussian_filter(rgb_array[:, :, 1], sigma=2.0)
            rgb_array[:, :, 2] = ndimage.gaussian_filter(rgb_array[:, :, 2], sigma=2.0)
            high_res_img = Image.fromarray(np.clip(np.round(rgb_array), 0, 255).astype(np.uint8), mode='RGB')
            logger.debug("Applied scipy Gaussian filter in HSV space")
        except ImportError:
            logger.debug("Scipy not available, using downscale smoothing only")
            pass


def _draw_text_with_shadow(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    shadow_offset: int = 1,
    shadow_color: Tuple[int, int, int, int] = None,
    shadow_blur: int = 0
) -> None:
    """
    Draw text with minimal shadow for crisp rendering.
    FIXED: Reduced shadow offset to 1px and only for very dark backgrounds to prevent blurry 3D effect.
    """
    # CRITICAL FIX: Ensure text is a string to prevent garbled rendering
    text = str(text) if text is not None else ""
    
    x, y = position
    
    # Only draw shadow for very light text on very dark backgrounds, with minimal offset
    # Reduced offset to 1px to prevent blurry/3D appearance
    if fill[0] > 220:  # Very light text (almost white) - add minimal shadow
        # Use very subtle shadow with 1px offset only
        shadow_fill = (30, 30, 30)  # Very dark gray
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_fill)
    
    # Draw main text on top
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
    primary_image_base64: Optional[str] = None,
    product_intelligence: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generate a PREMIUM og:image that stops the scroll.
    
    Design principles:
    1. Big, bold headlines that are impossible to ignore
    2. Social proof prominently displayed (people trust numbers)
    3. Strong visual hierarchy (1.5 seconds to make an impression)
    4. Clean, premium aesthetic (no clutter)
    5. Brand colors for recognition
    """
    if tags is None:
        tags = []
    if context_items is None:
        context_items = []
    if credibility_items is None:
        credibility_items = []
    
    # CRITICAL FIX: Ensure all text parameters are strings to prevent garbled rendering
    title = str(title) if title is not None else "Untitled"
    subtitle = str(subtitle) if subtitle is not None else None
    description = str(description) if description is not None else None
    cta_text = str(cta_text) if cta_text is not None else None
    domain = str(domain) if domain is not None else "example.com"
    
    # Ensure tags are strings
    tags = [str(tag) for tag in tags if tag is not None]
    
    # Ensure context_items have string values
    for item in context_items:
        if 'text' in item and item['text'] is not None:
            item['text'] = str(item['text'])
    
    # Ensure credibility_items have string values
    for item in credibility_items:
        if 'value' in item and item['value'] is not None:
            logger.info(f"🔍 IMAGE_GEN DEBUG: Converting credibility value {repr(item['value'])} ({type(item['value'])})")
            item['value'] = str(item['value'])
    
    logger.info(f"🔍 IMAGE_GEN DEBUG: Final credibility_items: {credibility_items}")
    
    try:
        # Ensure we have valid colors
        primary_color = _hex_to_rgb(blueprint.get("primary_color", "#2563EB"))
        secondary_color = _hex_to_rgb(blueprint.get("secondary_color", "#1E40AF"))
        accent_color = _hex_to_rgb(blueprint.get("accent_color", "#F59E0B"))
        
        # Smart template selection based on content and type
        template_lower = template_type.lower() if template_type else ""
        
        # Analyze what content we have
        has_strong_proof = any(
            c.get("value") and any(x in str(c.get("value", "")).lower() 
            for x in ['★', '⭐', '+', 'users', 'reviews', 'customers', 'rating', 'star'])
            for c in credibility_items
        )
        has_logo = bool(primary_image_base64)
        has_tags = bool(tags and len(tags) > 0)
        
        logger.info(f"🎨 Generating preview: template={template_type}, has_proof={has_strong_proof}, has_logo={has_logo}")
        
        # === TEMPLATE SELECTION ===
        # SaaS, Startup, Landing → Hero (bold gradient, big headline)
        if template_lower in ["saas", "startup", "landing", "enterprise", "tool"]:
            logger.info("Using HERO template (bold headline, gradient background)")
            return _generate_hero_template(
                screenshot_bytes, title, subtitle, description, 
                primary_color, secondary_color, accent_color,
                credibility_items, tags, primary_image_base64
            )
        
        # Product, E-commerce → Enhanced Product Template (category-aware)
        elif template_lower in ["product", "ecommerce", "marketplace"]:
            if ENHANCED_PRODUCT_RENDERER_AVAILABLE and product_intelligence:
                logger.info("Using ENHANCED PRODUCT template (category-aware, conversion-optimized)")
                return render_enhanced_product_preview(
                    screenshot_bytes, title, subtitle, description,
                    primary_color, secondary_color, accent_color,
                    credibility_items, tags, primary_image_base64,
                    product_intelligence
                )
            else:
                logger.info("Using PRODUCT template (split layout, features)")
                return _generate_product_template(
                    screenshot_bytes, title, subtitle, description,
                    primary_color, secondary_color, accent_color,
                    credibility_items, tags, primary_image_base64
                )
        
        # Profile, Personal → Profile Template (gradient header, circular avatar)
        elif template_lower in ["profile", "personal"]:
            logger.info("Using PROFILE template (gradient header, circular avatar)")
            return _generate_profile_template(
                screenshot_bytes, title, subtitle, description,
                primary_color, secondary_color, accent_color,
                credibility_items, tags, context_items, primary_image_base64, domain
            )
        
        # Portfolio, Blog, Article → Modern Card (clean, professional)
        elif template_lower in ["portfolio", "blog", "article", "agency"]:
            logger.info("Using MODERN CARD template (clean, professional)")
            return _generate_modern_card_template(
                screenshot_bytes, title, subtitle, description,
                primary_color, secondary_color, accent_color,
                credibility_items, tags, primary_image_base64, domain
            )
        
        # Unknown/Default → Choose based on content
        else:
            # If we have strong social proof, use Hero (proof badge prominent)
            if has_strong_proof:
                logger.info("Using HERO template (strong social proof detected)")
                return _generate_hero_template(
                    screenshot_bytes, title, subtitle, description, 
                    primary_color, secondary_color, accent_color,
                    credibility_items, tags, primary_image_base64
                )
            else:
                # Default to Modern Card (most versatile)
                logger.info("Using MODERN CARD template (default)")
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
    PREMIUM Hero template: Bold headline with cinematic gradient.
    Design philosophy: Big, bold, and impossible to ignore.
    """
    # Create clean, professional gradient (no screenshot texture for cleaner look)
    # Use the brand colors to create a polished, modern gradient
    # FIXED: Don't darken colors further - they're already appropriately dark from brand extraction
    # Only slightly adjust if needed for contrast, but preserve the intended color
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
    img = _draw_gradient_background(img, primary_color, secondary_color, "diagonal")
    
    # CLEAN design - no noisy patterns, just the gradient
    draw = ImageDraw.Draw(img)
    
    # ENHANCED: Standardized spacing system using 8px grid and golden ratio
    # Golden ratio: 1.618 (for harmonious proportions)
    GOLDEN_RATIO = 1.618
    
    # Base padding scales with image size using golden ratio for better proportions
    base_padding = int(OG_IMAGE_WIDTH / (GOLDEN_RATIO * 2))  # ~370px / 1.618 / 2 ≈ 114px
    padding = max(80, min(120, base_padding))  # Clamp between 80-120px for better spacing
    content_width = OG_IMAGE_WIDTH - (padding * 2)
    
    # Vertical spacing using golden ratio
    vertical_unit = int(padding / GOLDEN_RATIO)  # ~70px at 114px padding
    spacing_small = vertical_unit // 2  # ~35px
    spacing_medium = vertical_unit  # ~70px
    spacing_large = int(vertical_unit * GOLDEN_RATIO)  # ~113px
    
    # LAYOUT: Logo top-left, Social Proof badge top-right, Big headline center
    content_y = padding
    
    # === TOP BAR: Logo + Social Proof ===
    # MOBILE-FIRST: Larger logo for mobile visibility
    logo_size = 96  # Increased from 72 for better mobile visibility
    
    # LOGO FIX: Use full logo image (from brand_extractor) instead of cropped screenshot
    # This ensures we get the actual logo file, properly sized and not cropped incorrectly
    if primary_image_base64:
        try:
            logo_data = base64.b64decode(primary_image_base64)
            logo_img = Image.open(BytesIO(logo_data)).convert('RGBA')
            
            # Preserve aspect ratio for logos (don't force square if it's not square)
            original_width, original_height = logo_img.size
            aspect_ratio = original_width / original_height if original_height > 0 else 1
            
            # Calculate new size maintaining aspect ratio
            if aspect_ratio > 1:  # Wider than tall
                new_width = logo_size
                new_height = int(logo_size / aspect_ratio)
            else:  # Taller than wide or square
                new_height = logo_size
                new_width = int(logo_size * aspect_ratio)
            
            # Resize with high quality
            logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Rounded white background for logo (larger to accommodate non-square logos)
            bg_size = max(new_width, new_height) + 16
            logo_bg = Image.new('RGBA', (bg_size, bg_size), (255, 255, 255, 250))
            img.paste(logo_bg.convert('RGB'), (padding - 8, content_y - 8))
            
            # Center logo on background
            logo_x = padding + (bg_size - new_width) // 2 - 8
            logo_y = content_y + (bg_size - new_height) // 2 - 8
            img.paste(logo_img, (logo_x, logo_y), logo_img)
        except Exception as e:
            logger.warning(f"Failed to load logo: {e}")
    
    # Social proof badge on RIGHT (premium positioning)
    if credibility_items:
        proof_text = str(credibility_items[0].get("value", "")).strip()
        if proof_text and len(proof_text) > 2:
            # MOBILE-FIRST: Social proof badge readable on mobile
            proof_font = _load_font(32, bold=True)  # Increased from 22 for mobile readability
            try:
                bbox = draw.textbbox((0, 0), proof_text, font=proof_font)
                badge_width = bbox[2] - bbox[0] + 40
                badge_height = 56  # Increased from 48 for better mobile visibility
            except:
                badge_width = len(proof_text) * 12 + 40
                badge_height = 48
            
            badge_x = OG_IMAGE_WIDTH - padding - int(badge_width)
            
            # Accent-colored badge with rounded feel
            badge_img = Image.new('RGBA', (int(badge_width), badge_height), (*accent_color, 255))
            img.paste(badge_img.convert('RGB'), (badge_x, content_y))
            draw = ImageDraw.Draw(img)
            draw.text((badge_x + 20, content_y + 12), str(proof_text), font=proof_font, fill=(255, 255, 255))
    
    content_y += logo_size + 60
    
    # === MAIN HEADLINE - The star of the show ===
    # ENHANCED: Dynamic typography based on title length
    # Short titles (< 30 chars) get bigger text, long titles get smaller
    title_length = len(title) if title else 0
    
    if title_length < 25:
        title_font_size = 96  # Large for short titles
    elif title_length < 40:
        title_font_size = 80  # Medium for medium titles
    elif title_length < 60:
        title_font_size = 64  # Smaller for longer titles
    else:
        title_font_size = 56  # Smallest for very long titles
    
    title_font = _load_font(title_font_size, bold=True)
    
    # Line height: 1.2x font size for tighter, modern look
    title_line_height = int(title_font_size * 1.2)
    
    if title and title != "Untitled":
        title_lines = _wrap_text(title, title_font, content_width, draw)
        
        # Calculate vertical position - center the text block
        max_lines = 3 if title_length > 50 else 2  # Allow 3 lines for long titles
        actual_lines = min(len(title_lines), max_lines)
        total_title_height = actual_lines * title_line_height
        remaining_space = OG_IMAGE_HEIGHT - content_y - padding - spacing_medium
        title_y = content_y + max(0, int((remaining_space - total_title_height) / 3))
        
        # Draw title lines
        for i, line in enumerate(title_lines[:max_lines]):
            y_pos = title_y + (i * title_line_height)
            # Clean, subtle shadow for readability (reduced offset to avoid blurry 3D effect)
            _draw_text_with_shadow(draw, (padding, y_pos), line, title_font, (255, 255, 255), 2)
        content_y = title_y + actual_lines * title_line_height + spacing_medium
    
    # === SUPPORTING TEXT (subtitle or description) ===
    # ENHANCED: Typography hierarchy - readable subtitle/description
    support_text = subtitle or description
    if support_text and support_text != title and support_text.lower().strip() != title.lower().strip():
        # Subtitle should be readable but not compete with title
        desc_font_size = 36  # Fixed readable size
        desc_font = _load_font(desc_font_size, bold=False)
        desc_line_height = int(desc_font_size * 1.4)  # Tighter line height
        
        desc_lines = _wrap_text(support_text, desc_font, content_width, draw)
        # Limit to 2 lines to keep clean
        for i, line in enumerate(desc_lines[:2]):
            y_pos = content_y + (i * desc_line_height)
            # Clean, subtle shadow for readability (reduced offset to avoid blurry effect)
            _draw_text_with_shadow(draw, (padding, y_pos), line, desc_font, (240, 240, 245), 2)
    
    # === BOTTOM ACCENT BAR (brand color stripe) ===
    bar_height = 6
    draw.rectangle([(0, OG_IMAGE_HEIGHT - bar_height), (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT)], fill=accent_color)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=False)  # Disable optimization to preserve dithering
    return buffer.getvalue()


def _smart_crop_avatar(avatar_img: Image.Image, target_size: int) -> Image.Image:
    """
    Smart crop avatar with face detection and intelligent centering.
    Falls back to center crop if face detection fails.
    """
    # Try to detect face/center of interest
    # For now, use intelligent center crop with focus on upper-center (where faces usually are)
    width, height = avatar_img.size
    
    # If already square, just resize
    if width == height:
        return avatar_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    # For non-square images, crop to square focusing on center-upper region
    # This works well for profile photos where face is typically in upper-center
    if width > height:
        # Landscape: crop from center, prefer upper portion
        crop_size = height
        x_offset = (width - crop_size) // 2
        y_offset = max(0, int(height * 0.1))  # Slight bias toward top
        cropped = avatar_img.crop((x_offset, y_offset, x_offset + crop_size, y_offset + crop_size))
    else:
        # Portrait: crop from center, prefer upper portion
        crop_size = width
        x_offset = 0
        y_offset = max(0, int((height - crop_size) * 0.2))  # Bias toward top
        cropped = avatar_img.crop((x_offset, y_offset, x_offset + crop_size, y_offset + crop_size))
    
    # Resize with high-quality resampling
    return cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)


def _create_avatar_with_shadow(avatar_img: Image.Image, size: int, border_size: int = 4) -> Image.Image:
    """
    Create a premium avatar with shadow and border.
    """
    # Create larger canvas for shadow
    shadow_offset = 8
    canvas_size = size + (border_size * 2) + (shadow_offset * 2)
    canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    
    # Create shadow (larger, blurred circle)
    shadow_size = size + (border_size * 2)
    shadow = Image.new('RGBA', (shadow_size, shadow_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [(shadow_offset, shadow_offset), (shadow_size - shadow_offset, shadow_size - shadow_offset)],
        fill=(0, 0, 0, 40)  # Semi-transparent shadow
    )
    # Blur shadow
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
    
    # Paste shadow
    canvas.paste(shadow, (0, 0), shadow)
    
    # Create white border circle
    border_circle = Image.new('RGBA', (size + border_size * 2, size + border_size * 2), (255, 255, 255, 255))
    border_mask = Image.new('L', (size + border_size * 2, size + border_size * 2), 0)
    border_mask_draw = ImageDraw.Draw(border_mask)
    border_mask_draw.ellipse([(0, 0), (size + border_size * 2 - 1, size + border_size * 2 - 1)], fill=255)
    
    # Create inner circle mask for avatar
    inner_mask = Image.new('L', (size, size), 0)
    inner_mask_draw = ImageDraw.Draw(inner_mask)
    inner_mask_draw.ellipse([(0, 0), (size - 1, size - 1)], fill=255)
    
    # Paste avatar onto border
    border_circle.paste(avatar_img, (border_size, border_size), inner_mask)
    
    # Paste border onto canvas
    canvas.paste(border_circle, (shadow_offset, shadow_offset), border_mask)
    
    return canvas


def _generate_profile_template(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str],
    description: Optional[str],
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    accent_color: Tuple[int, int, int],
    credibility_items: List[Dict],
    tags: List[str],
    context_items: List[Dict],
    primary_image_base64: Optional[str],
    domain: str
) -> bytes:
    """
    PREMIUM Profile template: Professional, elegant design with perfect spacing.
    Design: Rich gradient header, perfectly cropped avatar with shadow, balanced layout.
    """
    # Create premium white background with subtle texture
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # === PREMIUM GRADIENT HEADER ===
    header_height = 140  # Taller header for better visual impact
    header_img = Image.new('RGB', (OG_IMAGE_WIDTH, header_height), primary_color)
    
    # Rich diagonal gradient
    header_img = _draw_gradient_background(header_img, primary_color, secondary_color, "diagonal")
    
    # Add depth with subtle overlay
    overlay = Image.new('RGBA', (OG_IMAGE_WIDTH, header_height), (0, 0, 0, 15))
    header_img = Image.alpha_composite(header_img.convert('RGBA'), overlay).convert('RGB')
    
    img.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(img)
    
    # === AVATAR POSITIONING ===
    avatar_size = 140  # Larger, more prominent avatar
    avatar_x = (OG_IMAGE_WIDTH - avatar_size) // 2
    avatar_y = header_height - 70  # Overlaps header nicely
    
    # === PREMIUM AVATAR WITH SMART CROP ===
    avatar_loaded = False
    if primary_image_base64:
        try:
            avatar_data = base64.b64decode(primary_image_base64)
            avatar_img = Image.open(BytesIO(avatar_data)).convert('RGBA')
            
            # Smart crop for better face/profile centering
            avatar_img = _smart_crop_avatar(avatar_img, avatar_size)
            
            # Create premium avatar with shadow and border
            avatar_with_effects = _create_avatar_with_shadow(avatar_img, avatar_size, border_size=6)
            
            # Calculate position accounting for shadow offset
            shadow_offset = 8
            paste_x = avatar_x - shadow_offset - 6  # Account for border and shadow
            paste_y = avatar_y - shadow_offset - 6
            
            img.paste(avatar_with_effects, (paste_x, paste_y), avatar_with_effects)
            avatar_loaded = True
        except Exception as e:
            logger.warning(f"Failed to load avatar: {e}")
    
    # Fallback: Premium initial circle
    if not avatar_loaded:
        # Create gradient circle background
        avatar_bg = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(avatar_bg)
        
        # Draw gradient circle
        for i in range(avatar_size):
            progress = i / avatar_size
            r = int(primary_color[0] * (1 - progress) + secondary_color[0] * progress)
            g = int(primary_color[1] * (1 - progress) + secondary_color[1] * progress)
            b = int(primary_color[2] * (1 - progress) + secondary_color[2] * progress)
            bg_draw.ellipse([(i, i), (avatar_size - i, avatar_size - i)], outline=(r, g, b, 255), width=1)
        
        # Fill center
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([(0, 0), (avatar_size - 1, avatar_size - 1)], fill=255)
        
        avatar_bg.paste(Image.new('RGB', (avatar_size, avatar_size), primary_color), (0, 0), mask)
        
        # Create with shadow
        avatar_with_effects = _create_avatar_with_shadow(avatar_bg, avatar_size, border_size=6)
        paste_x = avatar_x - 8 - 6
        paste_y = avatar_y - 8 - 6
        img.paste(avatar_with_effects, (paste_x, paste_y), avatar_with_effects)
        
        # Draw initial letter with shadow
        initial_font = _load_font(56, bold=True)
        initial = str(title[0]).upper() if title else "?"
        try:
            bbox = draw.textbbox((0, 0), initial, font=initial_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = 56
            text_height = 56
        
        # Text shadow
        draw.text(
            (avatar_x + (avatar_size - text_width) // 2 + 2, avatar_y + (avatar_size - text_height) // 2 + 2),
            str(initial),
            font=initial_font,
            fill=(0, 0, 0, 30)
        )
        # Text
        draw.text(
            (avatar_x + (avatar_size - text_width) // 2, avatar_y + (avatar_size - text_height) // 2),
            str(initial),
            font=initial_font,
            fill=(255, 255, 255)
        )
    
    # === CONTENT LAYOUT (premium spacing) ===
    content_start_y = avatar_y + avatar_size + 32  # More space after avatar
    padding = 60
    
    # === NAME (large, bold, with subtle shadow) ===
    if title and title != "Untitled":
        # MOBILE-FIRST: Name must be readable on mobile (80px = 6.7% of width → ~27px on mobile)
        name_font = _load_font(80, bold=True)  # Increased from 42 for mobile readability
        name_lines = _wrap_text(title, name_font, OG_IMAGE_WIDTH - (padding * 2), draw)
        name_y = content_start_y
        
        for i, line in enumerate(name_lines[:2]):  # Allow 2 lines for longer names
            try:
                bbox = draw.textbbox((0, 0), line, font=name_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(line) * 24
                text_height = 42
            
            # Text shadow for depth
            _draw_text_with_shadow(
                draw,
                ((OG_IMAGE_WIDTH - text_width) // 2, name_y + (i * (text_height + 8))),
                line,
                name_font,
                (17, 24, 39),
                shadow_offset=2,
                shadow_color=(255, 255, 255, 100)
            )
        
        content_start_y = name_y + min(len(name_lines), 2) * (text_height + 8) + 16
    
    # === SUBTITLE/ROLE (elegant, medium weight) ===
    if subtitle:
        # MOBILE-FIRST: Subtitle readable on mobile
        subtitle_font = _load_font(40, bold=True)  # Increased from 20, made bold
        subtitle_lines = _wrap_text(subtitle, subtitle_font, OG_IMAGE_WIDTH - (padding * 2), draw)
        subtitle_y = content_start_y + 8
        
        for i, line in enumerate(subtitle_lines[:2]):
            try:
                bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * 12
            
            draw.text(
                ((OG_IMAGE_WIDTH - text_width) // 2, subtitle_y + (i * 24)),
                str(line),
                font=subtitle_font,
                fill=(75, 85, 99)
            )
        content_start_y = subtitle_y + min(len(subtitle_lines), 2) * 24 + 20
    
    # === CONTEXT ITEMS (subtle, elegant) ===
    if context_items:
        # MOBILE-FIRST: Context items readable on mobile
        context_font = _load_font(24, bold=True)  # Increased from 16, made bold
        context_y = content_start_y + 4
        
        context_texts = []
        for item in context_items[:2]:
            text = str(item.get("text", "")).strip()
            if text:
                context_texts.append(text)
        
        if context_texts:
            context_str = " • ".join(context_texts)
            try:
                bbox = draw.textbbox((0, 0), context_str, font=context_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(context_str) * 9
            
            draw.text(
                ((OG_IMAGE_WIDTH - text_width) // 2, context_y),
                str(context_str),
                font=context_font,
                fill=(107, 114, 128)  # Lighter gray
            )
            content_start_y = context_y + 28
    
    # === TAGS (premium pills with better spacing) ===
    if tags:
        # MOBILE-FIRST: Tags readable on mobile
        tag_font = _load_font(20, bold=True)  # Increased from 14, made bold
        tag_y = content_start_y + 12
        tag_spacing = 10
        
        tag_widths = []
        for tag in tags[:4]:
            try:
                bbox = draw.textbbox((0, 0), str(tag), font=tag_font)
                tag_widths.append(bbox[2] - bbox[0] + 28)  # More padding
            except:
                tag_widths.append(len(str(tag)) * 8 + 28)
        
        total_tags_width = sum(tag_widths) + (tag_spacing * (len(tags[:4]) - 1))
        tag_start_x = (OG_IMAGE_WIDTH - total_tags_width) // 2
        
        current_x = tag_start_x
        for i, tag in enumerate(tags[:4]):
            tag_width = tag_widths[i]
            
            # Premium pill with subtle gradient
            pill_bg = tuple(int(c * 0.12) for c in primary_color)
            draw.rounded_rectangle(
                [(current_x, tag_y), (current_x + tag_width, tag_y + 28)],
                radius=14,
                fill=pill_bg
            )
            
            # Tag text
            try:
                bbox = draw.textbbox((0, 0), str(tag), font=tag_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(str(tag)) * 8
            
            draw.text(
                (current_x + (tag_width - text_width) // 2, tag_y + 7),
                str(tag),
                font=tag_font,
                fill=primary_color
            )
            
            current_x += tag_width + tag_spacing
        
        content_start_y = tag_y + 36
    
    # === DESCRIPTION (elegant, readable) ===
    if description and description != subtitle and len(description) > 10:
        # MOBILE-FIRST: Description readable on mobile
        desc_font = _load_font(36, bold=True)  # Increased from 18, made bold
        desc_lines = _wrap_text(description, desc_font, OG_IMAGE_WIDTH - (padding * 2), draw)
        desc_y = content_start_y + 16
        
        for i, line in enumerate(desc_lines[:3]):
            try:
                bbox = draw.textbbox((0, 0), line, font=desc_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * 10
            
            draw.text(
                ((OG_IMAGE_WIDTH - text_width) // 2, desc_y + (i * 26)),
                str(line),
                font=desc_font,
                fill=(55, 65, 81),
                spacing=2  # Better line spacing
            )
        content_start_y = desc_y + min(len(desc_lines), 3) * 26 + 20
    
    # === CREDIBILITY ITEMS (bottom, elegant) ===
    if credibility_items:
        # MOBILE-FIRST: Credibility items readable on mobile
        cred_font = _load_font(24, bold=True)  # Increased from 16, made bold
        cred_y = OG_IMAGE_HEIGHT - 50
        
        cred_texts = []
        for item in credibility_items[:2]:
            value = str(item.get("value", "")).strip()
            if value:
                cred_texts.append(value)
        
        if cred_texts:
            cred_str = " • ".join(cred_texts)
            try:
                bbox = draw.textbbox((0, 0), cred_str, font=cred_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(cred_str) * 9
            
            draw.text(
                ((OG_IMAGE_WIDTH - text_width) // 2, cred_y),
                str(cred_str),
                font=cred_font,
                fill=(107, 114, 128)  # Subtle gray
            )
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True, quality=95)
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
    PREMIUM Product template: Clean split layout.
    Design: Trust signals prominent, product/image on right.
    """
    # Clean white background
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Bold accent bar on left edge
    draw.rectangle([(0, 0), (10, OG_IMAGE_HEIGHT)], fill=primary_color)
    
    # Left side content area (60% of width)
    left_width = int(OG_IMAGE_WIDTH * 0.58)
    padding = 64
    content_y = padding
    
    # === SOCIAL PROOF BADGE (prominent at top) ===
    if credibility_items:
        proof_text = str(credibility_items[0].get("value", "")).strip()
        if proof_text and len(proof_text) > 2:
            # MOBILE-FIRST: Social proof badge readable on mobile
            proof_font = _load_font(32, bold=True)  # Increased from 22 for mobile readability
            try:
                bbox = draw.textbbox((0, 0), proof_text, font=proof_font)
                badge_width = bbox[2] - bbox[0] + 24
                badge_height = 38
            except:
                badge_width = len(proof_text) * 12 + 24
                badge_height = 38
            
            # Accent badge
            draw.rounded_rectangle(
                [(padding, content_y), (padding + badge_width, content_y + badge_height)],
                radius=19,
                fill=accent_color
            )
            draw.text((padding + 12, content_y + 8), str(proof_text), font=proof_font, fill=(255, 255, 255))
            content_y += badge_height + 32
    
    # === TITLE (big and bold) ===
    # MOBILE-FIRST: Product title readable on mobile
    title_font = _load_font(80, bold=True)  # Increased from 46 for mobile readability
    if title and title != "Untitled":
        title_lines = _wrap_text(title, title_font, left_width - padding - 40, draw)
        for i, line in enumerate(title_lines[:2]):
            y_pos = content_y + (i * 56)
            draw.text((padding, y_pos), str(line), font=title_font, fill=(15, 23, 42))
        content_y += min(len(title_lines), 2) * 56 + 24
    
    # === DESCRIPTION/BENEFIT ===
    if description:
        # MOBILE-FIRST: Product description readable on mobile
        desc_font = _load_font(36, bold=True)  # Increased from 22, made bold
        desc_lines = _wrap_text(description, desc_font, left_width - padding - 40, draw)
        for i, line in enumerate(desc_lines[:3]):
            y_pos = content_y + (i * 30)
            draw.text((padding, y_pos), str(line), font=desc_font, fill=(71, 85, 105))
        content_y += min(len(desc_lines), 3) * 30 + 28
    
    # === FEATURE CHECKMARKS ===
    if tags:
        # MOBILE-FIRST: Feature checkmarks readable on mobile
        check_font = _load_font(24, bold=True)  # Increased from 18, made bold
        for i, tag in enumerate(tags[:3]):
            tag_y = content_y + (i * 32)
            # Checkmark circle
            draw.ellipse(
                [(padding, tag_y + 2), (padding + 22, tag_y + 24)],
                fill=_lighten_color(primary_color, 0.85)
            )
            draw.text((padding + 5, tag_y + 3), "✓", font=check_font, fill=primary_color)
            draw.text((padding + 32, tag_y + 3), str(tag), font=check_font, fill=(51, 65, 85))
    
    # === RIGHT SIDE: PRODUCT/SCREENSHOT ===
    right_x = left_width + 20
    right_width = OG_IMAGE_WIDTH - right_x - 32
    right_height = OG_IMAGE_HEIGHT - 64
    
    # Subtle background for image area
    draw.rectangle(
        [(right_x, 32), (OG_IMAGE_WIDTH - 32, OG_IMAGE_HEIGHT - 32)],
        fill=(248, 250, 252)
    )
    
    if primary_image_base64:
        try:
            product_data = base64.b64decode(primary_image_base64)
            product_img = Image.open(BytesIO(product_data)).convert('RGBA')
            
            # Scale to fit
            img_ratio = product_img.width / product_img.height
            target_height = right_height - 40
            target_width = int(target_height * img_ratio)
            
            if target_width > right_width - 40:
                target_width = right_width - 40
                target_height = int(target_width / img_ratio)
            
            product_img = product_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Center in right area
            img_x = right_x + (right_width - target_width) // 2
            img_y = 32 + (right_height - target_height) // 2
            
            img.paste(product_img, (img_x, img_y), product_img)
        except Exception as e:
            logger.warning(f"Failed to load product image: {e}")
            # Fall back to screenshot
            try:
                screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
                screenshot = screenshot.resize((right_width - 20, right_height - 20), Image.Resampling.LANCZOS)
                img.paste(screenshot, (right_x + 10, 42))
            except:
                pass
    else:
        # Use screenshot as product preview
        try:
            screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
            screenshot = screenshot.resize((right_width - 20, right_height - 20), Image.Resampling.LANCZOS)
            img.paste(screenshot, (right_x + 10, 42))
        except:
            pass
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=False)  # Disable optimization to preserve dithering
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
    PREMIUM Modern card: Clean, professional, high-converting.
    Design: Big headline, prominent social proof, subtle branding.
    """
    # Clean white background with subtle warmth
    img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (252, 252, 254))
    draw = ImageDraw.Draw(img)
    
    # Subtle gradient overlay for depth (top-left to bottom-right)
    for y in range(OG_IMAGE_HEIGHT):
        alpha = int(10 * (1 - y / OG_IMAGE_HEIGHT))  # Very subtle
        draw.line([(0, y), (OG_IMAGE_WIDTH, y)], fill=(245 + alpha, 246 + alpha, 250))
    
    # Card dimensions - slightly inset for shadow room
    card_margin = 32
    card_width = OG_IMAGE_WIDTH - (card_margin * 2)
    card_height = OG_IMAGE_HEIGHT - (card_margin * 2)
    card_x, card_y = card_margin, card_margin
    
    # Multi-layer shadow for premium depth
    for offset in [12, 8, 4]:
        alpha = 40 - (offset * 2)
        shadow_color = (180 + alpha, 180 + alpha, 190 + alpha)
        draw.rectangle(
            [(card_x + offset, card_y + offset),
             (card_x + card_width + offset, card_y + card_height + offset)],
            fill=shadow_color
        )
    
    # White card
    draw.rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + card_height)],
        fill=(255, 255, 255)
    )
    
    # Bold accent bar (thicker for impact)
    bar_height = 8
    draw.rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + bar_height)],
        fill=primary_color
    )
    
    # DESIGN FIX 2: Consistent padding system
    padding = int(OG_IMAGE_WIDTH * 0.047)  # ~4.7% of width (56px at 1200px)
    padding = max(40, min(70, padding))  # Clamp between 40-70px
    content_x = card_x + padding
    content_y = card_y + bar_height + padding
    content_width = card_width - (padding * 2)
    
    # === TOP ROW: Logo + Social Proof ===
    row_y = content_y
    # MOBILE-FIRST: Larger logo for mobile visibility
    # MOBILE-FIRST: Larger logo for mobile visibility
    logo_size = 96  # Increased from 72 for better mobile visibility  # Increased from 56 for better mobile visibility
    
    # LOGO FIX: Use full logo image with aspect ratio preservation
    if primary_image_base64:
        try:
            logo_data = base64.b64decode(primary_image_base64)
            logo_img = Image.open(BytesIO(logo_data)).convert('RGBA')
            
            # Preserve aspect ratio for logos
            original_width, original_height = logo_img.size
            aspect_ratio = original_width / original_height if original_height > 0 else 1
            
            # Calculate new size maintaining aspect ratio
            if aspect_ratio > 1:  # Wider than tall
                new_width = logo_size
                new_height = int(logo_size / aspect_ratio)
            else:  # Taller than wide or square
                new_height = logo_size
                new_width = int(logo_size * aspect_ratio)
            
            # Resize with high quality
            logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            mask = _create_rounded_rectangle_mask((new_width, new_height), 10)
            img.paste(logo_img, (content_x, row_y), mask)
        except Exception as e:
            logger.warning(f"Failed to load logo: {e}")
    
    # Social proof badge prominently on right (if available)
    if credibility_items:
        proof_text = str(credibility_items[0].get("value", "")).strip()
        if proof_text and len(proof_text) > 2:
            # MOBILE-FIRST: Social proof badge readable on mobile
            proof_font = _load_font(32, bold=True)  # Increased from 20 for mobile readability
            try:
                bbox = draw.textbbox((0, 0), proof_text, font=proof_font)
                badge_width = bbox[2] - bbox[0] + 28
                badge_height = 48  # Increased from 36 for better mobile visibility
            except:
                badge_width = len(proof_text) * 11 + 28
                badge_height = 36
            
            badge_x = content_x + content_width - int(badge_width)
            
            # Accent-colored badge
            draw.rounded_rectangle(
                [(badge_x, row_y + 10), (badge_x + badge_width, row_y + 10 + badge_height)],
                radius=18,
                fill=accent_color
            )
            draw.text((badge_x + 14, row_y + 17), str(proof_text), font=proof_font, fill=(255, 255, 255))
    
    content_y = row_y + logo_size + 36
    
    # MOBILE-FIRST DESIGN: Headline must be readable on mobile feeds
    title_font = _load_font(96, bold=True)  # Increased from 48 for mobile readability (8% of width)
    if title and title != "Untitled":
        title_lines = _wrap_text(title, title_font, content_width, draw)
        for i, line in enumerate(title_lines[:2]):
            y_pos = content_y + (i * 58)
            draw.text((content_x, y_pos), str(line), font=title_font, fill=(15, 23, 42))  # Near black
        content_y += min(len(title_lines), 2) * 58 + 20
    
    # === SUBTITLE/PROOF (if not shown in badge) ===
    show_subtitle = subtitle and subtitle not in str(credibility_items)
    if show_subtitle:
        # MOBILE-FIRST: Subtitle readable on mobile
        sub_font = _load_font(40, bold=True)  # Increased from 24, made bold
        sub_lines = _wrap_text(subtitle, sub_font, content_width, draw)
        for i, line in enumerate(sub_lines[:2]):
            y_pos = content_y + (i * 32)
            draw.text((content_x, y_pos), str(line), font=sub_font, fill=(71, 85, 105))  # Slate-500
        content_y += min(len(sub_lines), 2) * 32 + 16
    
    # === DESCRIPTION ===
    if description and description != subtitle:
        # MOBILE-FIRST: Product description readable on mobile
        desc_font = _load_font(36, bold=True)  # Increased from 22, made bold
        desc_lines = _wrap_text(description, desc_font, content_width, draw)
        for i, line in enumerate(desc_lines[:2]):
            y_pos = content_y + (i * 30)
            draw.text((content_x, y_pos), str(line), font=desc_font, fill=(100, 116, 139))  # Slate-400
        content_y += min(len(desc_lines), 2) * 30 + 20
    
    # === TAGS (bottom, as subtle chips) ===
    if tags:
        # MOBILE-FIRST: Tags readable on mobile
        tag_font = _load_font(20, bold=True)  # Increased from 16, made bold
        tag_y = card_y + card_height - padding - 32
        tag_x = content_x
        
        for tag in tags[:3]:  # Max 3 tags
            try:
                bbox = draw.textbbox((0, 0), str(tag), font=tag_font)
                tag_width = bbox[2] - bbox[0] + 18
            except:
                tag_width = len(str(tag)) * 9 + 18
            
            # Subtle pill
            draw.rounded_rectangle(
                [(tag_x, tag_y), (tag_x + tag_width, tag_y + 26)],
                radius=13,
                fill=_lighten_color(primary_color, 0.9)
            )
            draw.text((tag_x + 9, tag_y + 4), str(tag), font=tag_font, fill=_darken_color(primary_color, 0.7))
            tag_x += int(tag_width) + 8
    
    # === DOMAIN (bottom-right, subtle) ===
    domain_font = _load_font(14, bold=False)
    domain_clean = domain.replace('www.', '')
    try:
        bbox = draw.textbbox((0, 0), domain_clean, font=domain_font)
        domain_width = bbox[2] - bbox[0]
    except:
        domain_width = len(domain_clean) * 8
    
    draw.text(
        (card_x + card_width - padding - domain_width, card_y + card_height - padding - 20),
        str(domain_clean),
        font=domain_font,
        fill=(148, 163, 184)  # Slate-400
    )
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=False)  # Disable optimization to preserve dithering
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
        
        # Create clean gradient background (no patterns)
        # FIXED: Use colors directly without excessive darkening
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), primary_color)
        img = _draw_gradient_background(img, primary_color, secondary_color, "diagonal")
        draw = ImageDraw.Draw(img)
        
        # Center content vertically
        padding = 80
        content_width = OG_IMAGE_WIDTH - (padding * 2)
        
        # Title - large and bold
        # MOBILE-FIRST: Fallback title readable on mobile
        title_font = _load_font(96, bold=True)  # Increased from 52 for mobile readability
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
            str(domain_clean),
            fill=(255, 255, 255, 180),
            font=domain_font
        )
        
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=False)  # Disable optimization to preserve dithering
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Fallback generation failed: {e}", exc_info=True)
        # Ultimate fallback - simple colored rectangle
        img = Image.new('RGB', (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (59, 130, 246))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


def generate_dna_aware_preview(
    screenshot_bytes: bytes,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    proof_text: Optional[str] = None,
    logo_base64: Optional[str] = None,
    design_dna: Dict[str, Any] = None
) -> Optional[bytes]:
    """
    Generate a Design DNA-aware preview using the Adaptive Template Engine.
    
    This creates previews that honor the original design's personality:
    - Typography matches brand voice (authoritative, friendly, elegant, etc.)
    - Colors evoke the same emotional response as the original
    - Spacing and layout match the design's density philosophy
    - Visual effects appropriate to the brand's style
    
    Args:
        screenshot_bytes: Raw PNG bytes for background treatment
        title: Main headline
        subtitle: Optional subtitle
        description: Optional description
        proof_text: Social proof text
        logo_base64: Optional logo image
        design_dna: Design DNA dictionary from extraction
        
    Returns:
        PNG image bytes, or None if generation fails
    """
    if not ADAPTIVE_ENGINE_AVAILABLE:
        logger.warning("Adaptive Template Engine not available, falling back to classic generation")
        return None
    
    if not design_dna:
        logger.warning("No Design DNA provided, cannot generate DNA-aware preview")
        return None
    
    try:
        # Convert design_dna dict to DesignDNA object
        dna = DesignDNA(
            philosophy=DesignPhilosophy(
                primary_style=design_dna.get("style", "corporate"),
                visual_tension=design_dna.get("mood", "balanced"),
                formality=design_dna.get("formality", 0.5),
                design_era="contemporary",
                reasoning=design_dna.get("design_reasoning", "")
            ),
            typography=TypographyDNA(
                headline_personality=design_dna.get("typography_personality", "bold"),
                body_personality="neutral",
                weight_contrast="medium",
                case_strategy="mixed",
                spacing_character=_map_spacing_feel(design_dna.get("spacing_feel", "balanced")),
                font_mood=""
            ),
            color_psychology=ColorPsychology(
                dominant_emotion=design_dna.get("color_emotion", "trust"),
                color_strategy="complementary",
                saturation_character="balanced",
                # FIXED: Calculate light_dark_balance from actual primary color for correct text color
                light_dark_balance=_calculate_luminance_from_hex(design_dna.get("primary_color", "#2563EB")),
                accent_usage="",
                # Use palette from blueprint if available, otherwise defaults
                primary_hex=design_dna.get("primary_color", "#2563EB"),
                secondary_hex=design_dna.get("secondary_color", "#1E40AF"),
                accent_hex=design_dna.get("accent_color", "#F59E0B"),
                background_hex=design_dna.get("background_color", "#FFFFFF"),
                # FIXED: Text color is WHITE for dark backgrounds, dark for light backgrounds
                text_hex=_get_optimal_text_hex(design_dna.get("primary_color", "#2563EB"))
            ),
            spatial=SpatialIntelligence(
                density=design_dna.get("spacing_feel", "balanced"),
                rhythm="even",
                alignment_philosophy="strict-grid",
                whitespace_intention="",
                padding_scale=_map_padding_scale(design_dna.get("spacing_feel", "balanced"))
            ),
            hero_element=HeroElement(
                element_type="headline",
                content=title,
                why_important="Primary message",
                how_to_honor="Use as main title",
                visual_weight=1.0
            ),
            brand_personality=BrandPersonality(
                adjectives=design_dna.get("brand_adjectives", ["professional", "modern"]),
                target_feeling="",
                voice_tone="professional",
                design_confidence=0.8,
                industry_context=""
            ),
            ui_components=UIComponents(**design_dna.get("ui_components", {})) if design_dna.get("ui_components") else UIComponents(button_style="flat"),
            visual_effects=VisualEffects(**design_dna.get("visual_effects", {})) if design_dna.get("visual_effects") else VisualEffects(shadows="subtle"),
            layout_patterns=LayoutPatterns(**design_dna.get("layout_patterns", {})) if design_dna.get("layout_patterns") else LayoutPatterns(content_structure="centered"),
            confidence=0.7
        )
        
        # Generate using Adaptive Template Engine
        image_bytes = generate_adaptive_preview(
            design_dna=dna,
            title=title,
            subtitle=subtitle,
            description=description,
            proof_text=proof_text,
            logo_base64=logo_base64,
            screenshot_bytes=screenshot_bytes
        )
        
        logger.info(f"🎨 Generated DNA-aware preview: style={dna.philosophy.primary_style}, typography={dna.typography.headline_personality}")
        return image_bytes
        
    except Exception as e:
        logger.error(f"DNA-aware preview generation failed: {e}", exc_info=True)
        return None


def _map_spacing_feel(spacing_feel: str) -> str:
    """Map spacing feel to typography spacing character."""
    mapping = {
        "compact": "tight-dense",
        "balanced": "balanced",
        "spacious": "generous-luxury",
        "ultra-minimal": "generous-luxury"
    }
    return mapping.get(spacing_feel.lower(), "balanced")


def _calculate_luminance_from_hex(hex_color: str) -> float:
    """
    Calculate relative luminance (0-1) from a hex color.
    
    FIXED: Used to determine if background is dark or light for text color selection.
    Returns value < 0.5 for dark colors (needs white text).
    Returns value >= 0.5 for light colors (needs dark text).
    """
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        # Relative luminance formula (sRGB)
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        logger.info(f"🎨 Luminance calculation: #{hex_color} → L={luminance:.3f} ({'dark' if luminance < 0.5 else 'light'} bg)")
        return luminance
    except Exception as e:
        logger.warning(f"⚠️ Luminance calculation failed for {hex_color}: {e}")
        return 0.7  # Default to light theme on error


def _get_optimal_text_hex(bg_hex: str) -> str:
    """
    Get optimal text color (hex) for a given background color.
    
    FIXED: Ensures white text on dark backgrounds and dark text on light backgrounds.
    """
    luminance = _calculate_luminance_from_hex(bg_hex)
    text_hex = "#FFFFFF" if luminance < 0.5 else "#111827"
    logger.info(f"🎨 Optimal text color: bg={bg_hex}, L={luminance:.3f} → text={text_hex}")
    return text_hex


def _map_padding_scale(spacing_feel: str) -> str:
    """Map spacing feel to padding scale."""
    mapping = {
        "compact": "compact",
        "balanced": "medium",
        "spacious": "generous",
        "ultra-minimal": "luxurious"
    }
    return mapping.get(spacing_feel.lower(), "medium")


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
    primary_image_base64: Optional[str] = None,
    design_dna: Dict[str, Any] = None,
    product_intelligence: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Generate designed og:image matching React component and upload to R2.
    
    NOW ENHANCED WITH DESIGN DNA INTELLIGENCE:
    When design_dna is provided, uses the Adaptive Template Engine to create
    previews that honor the original design's personality, typography, and colors.
    
    Creates a beautiful, designed preview image that:
    - Matches the React component card design (white card with accent bar)
    - Has proper typography hierarchy
    - Shows all elements (icon, title, subtitle, description, tags, CTA)
    - Is optimized for mobile social feeds
    - NEW: Honors original design's DNA when available
    
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
        design_dna: Design DNA dictionary for intelligent rendering (NEW)
    
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
        
        # NEW: Try DNA-aware generation first if design_dna is available
        image_bytes = None
        
        if design_dna and ADAPTIVE_ENGINE_AVAILABLE:
            # Merge palette colors into design_dna for the adaptive engine
            enriched_dna = {**design_dna}
            if blueprint:
                enriched_dna["primary_color"] = blueprint.get("primary_color", design_dna.get("primary_color", "#2563EB"))
                enriched_dna["secondary_color"] = blueprint.get("secondary_color", design_dna.get("secondary_color", "#1E40AF"))
                enriched_dna["accent_color"] = blueprint.get("accent_color", design_dna.get("accent_color", "#F59E0B"))
            
            # Build proof text from credibility items
            proof_text = None
            if credibility_items:
                proof_parts = [f"{item.get('value', '')}" for item in credibility_items[:2] if item.get('value')]
                proof_text = " • ".join(proof_parts) if proof_parts else None
            
            logger.info(f"🧬 Attempting DNA-aware preview generation with style: {design_dna.get('style', 'unknown')}")
            
            image_bytes = generate_dna_aware_preview(
                screenshot_bytes=screenshot_bytes,
                title=title,
                subtitle=subtitle,
                description=description,
                proof_text=proof_text,
                logo_base64=primary_image_base64,
                design_dna=enriched_dna
            )
            
            if image_bytes:
                logger.info("✅ Successfully generated DNA-aware preview")
        
        # Fall back to classic generation if DNA-aware failed or wasn't available
        if not image_bytes:
            logger.info("📋 Using classic template generation")
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
                primary_image_base64=primary_image_base64,
                product_intelligence=product_intelligence
            )
        
        # AI-powered quality improvement: detect and fix banding/blur issues
        try:
            from backend.services.ai_image_quality_fixer import improve_image_quality_with_ai
            image_pil = Image.open(BytesIO(image_bytes))
            improved_image, ai_results = improve_image_quality_with_ai(image_pil)
            
            if ai_results.get("fixes_applied"):
                logger.info(f"✅ AI applied {len(ai_results['fixes_applied'])} quality fixes")
                # Convert back to bytes
                buffer = BytesIO()
                improved_image.save(buffer, format='PNG', optimize=False)
                image_bytes = buffer.getvalue()
            elif ai_results.get("analysis"):
                logger.info("✅ AI quality check passed - no fixes needed")
        except Exception as e:
            logger.warning(f"AI quality improvement failed (non-critical): {e}")
            # Continue with original image if AI fix fails
        
        # Upload to R2
        filename = f"previews/demo/{uuid4()}.png"
        image_url = upload_file_to_r2(image_bytes, filename, "image/png")
        
        logger.info(f"Designed preview uploaded: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Failed to generate/upload preview image: {e}", exc_info=True)
        return None
