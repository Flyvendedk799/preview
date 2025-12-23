"""
Brand extraction service for preview generation.

Extracts brand elements from websites:
- Logo (favicon or header logo) with AI-powered detection
- Primary brand colors
- Hero/featured images
- Brand name and tagline

ENHANCED with AI Logo Detection:
- Uses GPT-4o vision to locate logos in screenshots
- Falls back to HTML-based extraction
- Validates logo quality and prominence
"""
import base64
import json
import logging
import re
from collections import Counter
from io import BytesIO
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse, urljoin
import requests
from PIL import Image
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# AI Logo Detection Integration
try:
    from openai import OpenAI
    from backend.core.config import settings
    AI_LOGO_DETECTION_AVAILABLE = True
except ImportError:
    AI_LOGO_DETECTION_AVAILABLE = False
    logger.warning("OpenAI not available for AI logo detection")

# PHASE 2: Error Recovery Integration
try:
    from backend.services.error_recovery import (
        classify_error,
        get_recovery_action,
        ErrorType,
        RecoveryAction,
        graceful_extract
    )
    ERROR_RECOVERY_AVAILABLE = True
except ImportError:
    ERROR_RECOVERY_AVAILABLE = False


# =============================================================================
# AI-POWERED LOGO DETECTION
# =============================================================================

LOGO_DETECTION_PROMPT = """Analyze this webpage screenshot and locate the brand/company logo.

MISSION: Find the PRIMARY brand logo that identifies the company/website.

LOOK FOR LOGOS IN THESE LOCATIONS (priority order):
1. Header/Navigation bar (top-left or top-center is most common)
2. Hero section (large logo in the main content area)
3. Footer (bottom of page, usually smaller)
4. Sidebar or floating elements

LOGO CHARACTERISTICS TO IDENTIFY:
- Company name in stylized text
- Icon/symbol representing the brand
- Combination of icon + text (logomark + logotype)
- Usually appears in prominent position with good contrast
- Often has consistent styling (not mixed with other content)

DO NOT IDENTIFY AS LOGOS:
- Navigation menu items
- Social media icons (Facebook, Twitter, etc.)
- Generic icons (hamburger menu, search, user)
- Partner/client logos in "trusted by" sections
- Product images or screenshots

OUTPUT JSON:
{
    "logos_found": [
        {
            "bbox": {
                "x": <0.0-1.0 normalized left position>,
                "y": <0.0-1.0 normalized top position>,
                "width": <0.0-1.0 normalized width>,
                "height": <0.0-1.0 normalized height>
            },
            "confidence": <0.0-1.0>,
            "location": "header|hero|footer|sidebar",
            "type": "text|icon|combined",
            "description": "<brief description of what the logo looks like>"
        }
    ],
    "best_logo_index": <index of the best logo to use, or -1 if no good logo found>,
    "extraction_notes": "<any notes about the extraction>"
}

CRITICAL RULES:
1. Bounding box must TIGHTLY wrap the logo (no extra padding)
2. Only include logos with confidence >= 0.6
3. If multiple logos found, best_logo_index should point to the primary brand logo
4. If no suitable logo found, set best_logo_index to -1
5. Coordinates are normalized (0.0-1.0) relative to image dimensions"""


def extract_logo_with_ai(screenshot_bytes: bytes, url: str = "") -> Optional[Dict[str, Any]]:
    """
    Use GPT-4o vision to detect and locate logos in a screenshot.
    
    This is the primary logo detection method, providing accurate bounding boxes
    for logo extraction from screenshots.
    
    Args:
        screenshot_bytes: Screenshot bytes
        url: URL for context
        
    Returns:
        Dict with logo info including bbox, or None if detection fails
    """
    if not AI_LOGO_DETECTION_AVAILABLE:
        logger.debug("AI logo detection not available")
        return None
    
    logger.info(f"🤖 Running AI logo detection for: {url[:50] if url else 'unknown'}...")
    
    try:
        # Prepare image for API
        image = Image.open(BytesIO(screenshot_bytes))
        original_width, original_height = image.size
        
        # Resize if too large (max 2048px)
        max_dim = 2048
        if image.width > max_dim or image.height > max_dim:
            ratio = min(max_dim / image.width, max_dim / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode in ('RGBA', 'P', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                background.paste(image, mask=image.split()[-1])
            image = background
        
        # Encode to base64
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=90)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Call GPT-4o vision
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at detecting brand logos in webpage screenshots. Output valid JSON only."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": LOGO_DETECTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1  # Low temperature for consistent detection
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        # Validate result
        logos_found = result.get("logos_found", [])
        best_index = result.get("best_logo_index", -1)
        
        if not logos_found or best_index < 0 or best_index >= len(logos_found):
            logger.info("🤖 AI logo detection: No suitable logo found")
            return None
        
        best_logo = logos_found[best_index]
        
        # Validate confidence
        if best_logo.get("confidence", 0) < 0.6:
            logger.info(f"🤖 AI logo detection: Logo confidence too low ({best_logo.get('confidence', 0):.2f})")
            return None
        
        logger.info(
            f"✅ AI logo detected: {best_logo.get('location', 'unknown')} "
            f"({best_logo.get('type', 'unknown')}) "
            f"confidence={best_logo.get('confidence', 0):.2f}"
        )
        
        return {
            "bbox": best_logo.get("bbox"),
            "confidence": best_logo.get("confidence"),
            "location": best_logo.get("location"),
            "type": best_logo.get("type"),
            "description": best_logo.get("description"),
            "original_width": original_width,
            "original_height": original_height
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"🤖 AI logo detection: JSON parse error: {e}")
        return None
    except Exception as e:
        logger.warning(f"🤖 AI logo detection failed: {e}")
        return None


def crop_logo_from_screenshot(screenshot_bytes: bytes, logo_info: Dict[str, Any]) -> Optional[str]:
    """
    Crop the logo from screenshot using AI-detected bounding box.
    
    Args:
        screenshot_bytes: Screenshot bytes
        logo_info: Logo info dict with bbox from AI detection
        
    Returns:
        Base64-encoded logo image or None
    """
    try:
        bbox = logo_info.get("bbox")
        if not bbox:
            return None
        
        image = Image.open(BytesIO(screenshot_bytes))
        width, height = image.size
        
        # Convert normalized coordinates to pixels
        x = int(bbox.get("x", 0) * width)
        y = int(bbox.get("y", 0) * height)
        w = int(bbox.get("width", 0.1) * width)
        h = int(bbox.get("height", 0.1) * height)
        
        # Add small padding (5% of dimensions)
        padding_x = int(w * 0.05)
        padding_y = int(h * 0.05)
        
        # Calculate crop box with padding
        left = max(0, x - padding_x)
        top = max(0, y - padding_y)
        right = min(width, x + w + padding_x)
        bottom = min(height, y + h + padding_y)
        
        # Validate crop dimensions
        if right <= left or bottom <= top:
            logger.warning("Invalid crop dimensions for logo")
            return None
        
        crop_width = right - left
        crop_height = bottom - top
        
        # Minimum size validation
        if crop_width < 30 or crop_height < 30:
            logger.warning(f"Logo crop too small: {crop_width}x{crop_height}")
            return None
        
        # Crop the logo
        logo_image = image.crop((left, top, right, bottom))
        
        # Convert to RGBA to handle transparency
        if logo_image.mode != 'RGBA':
            logo_image = logo_image.convert('RGBA')
        
        # Save as PNG to preserve quality
        buffer = BytesIO()
        logo_image.save(buffer, format='PNG', optimize=True)
        logo_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        logger.info(f"✅ Logo cropped successfully: {crop_width}x{crop_height}px")
        return logo_base64
        
    except Exception as e:
        logger.warning(f"Failed to crop logo from screenshot: {e}")
        return None


def extract_brand_logo(html_content: str, url: str, screenshot_bytes: bytes) -> Optional[str]:
    """
    Extract brand logo from website with AI-powered detection.

    Priority order:
    1. 🤖 AI-powered logo detection from screenshot (most accurate)
    2. High-res logo from header/nav HTML elements
    3. Favicon (if high quality)
    4. Fallback: Simple screenshot crop (top-left region)

    Args:
        html_content: HTML content of the page
        url: URL of the website
        screenshot_bytes: Screenshot for AI logo detection

    Returns:
        Base64-encoded logo image or None
    """
    logger.info(f"🔍 Starting logo extraction for: {url}")
    
    try:
        # =================================================================
        # PRIORITY 1: AI-Powered Logo Detection (most accurate)
        # =================================================================
        if screenshot_bytes and AI_LOGO_DETECTION_AVAILABLE:
            logo_info = extract_logo_with_ai(screenshot_bytes, url)
            if logo_info:
                logo_base64 = crop_logo_from_screenshot(screenshot_bytes, logo_info)
                if logo_base64:
                    logger.info(
                        f"✅ Logo extracted via AI detection: "
                        f"{logo_info.get('location', 'unknown')} "
                        f"({logo_info.get('description', 'no description')[:50]})"
                    )
                    return logo_base64
        
        # =================================================================
        # PRIORITY 2: HTML-based logo extraction
        # =================================================================
        logger.debug("  AI detection not available or failed, trying HTML-based extraction...")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        # Try to find logo in common locations
        logo_selectors = [
            'img[class*="logo" i]',
            'img[id*="logo" i]',
            'img[alt*="logo" i]',
            'a[class*="logo" i] img',
            'header img',
            'nav img',
            '.navbar img',
            '.header img',
            # Additional selectors for better coverage
            '[class*="brand"] img',
            'a[href="/"] img',
            '.site-logo img',
            '#logo img',
        ]

        for selector in logo_selectors:
            logo_img = soup.select_one(selector)
            if logo_img and logo_img.get('src'):
                logo_url = urljoin(base_url, logo_img['src'])
                logger.debug(f"  Trying logo selector: {selector} -> {logo_url}")

                # Download logo
                try:
                    response = requests.get(logo_url, timeout=5)
                    if response.status_code == 200:
                        # Check if image is reasonable size (not too small)
                        img = Image.open(BytesIO(response.content))
                        if img.width >= 50 and img.height >= 50:  # Minimum dimensions
                            # Convert to base64
                            buffered = BytesIO()
                            img.save(buffered, format="PNG")
                            logo_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            logger.info(f"✅ Logo extracted from HTML: {selector} ({img.width}x{img.height})")
                            return logo_base64
                        else:
                            logger.debug(f"  Logo too small: {img.width}x{img.height}, skipping")
                except Exception as e:
                    logger.debug(f"  Failed to download logo from {logo_url}: {e}")
                    continue

        # =================================================================
        # PRIORITY 3: Favicon fallback
        # =================================================================
        logger.debug("  HTML logo extraction failed, trying favicon...")
        favicon_selectors = [
            'link[rel="apple-touch-icon"]',  # Usually highest quality
            'link[rel="icon"][sizes]',  # Sized icons
            'link[rel="icon"]',
            'link[rel="shortcut icon"]',
        ]

        for selector in favicon_selectors:
            favicon = soup.select_one(selector)
            if favicon and favicon.get('href'):
                favicon_url = urljoin(base_url, favicon['href'])
                logger.debug(f"  Trying favicon: {selector} -> {favicon_url}")
                try:
                    response = requests.get(favicon_url, timeout=5)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        if img.width >= 64:  # Only use if reasonable quality
                            buffered = BytesIO()
                            img.save(buffered, format="PNG")
                            logo_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            logger.info(f"✅ Logo extracted from favicon: {selector} ({img.width}x{img.height})")
                            return logo_base64
                except Exception as e:
                    logger.debug(f"  Failed to download favicon from {favicon_url}: {e}")
                    continue

        # =================================================================
        # PRIORITY 4: Simple screenshot crop fallback
        # =================================================================
        logger.debug("  HTML/favicon extraction failed, trying screenshot-based extraction...")
        logo_base64 = _extract_logo_from_screenshot(screenshot_bytes)
        if logo_base64:
            logger.info("✅ Logo extracted from screenshot (fallback crop method)")
            return logo_base64

        logger.warning(f"❌ No suitable logo found for: {url}")
        return None

    except Exception as e:
        logger.error(f"❌ Logo extraction failed for {url}: {e}", exc_info=True)
        return None


def _extract_logo_from_screenshot(screenshot_bytes: bytes) -> Optional[str]:
    """
    Fallback method: Extract logo from screenshot by analyzing top-left region.
    
    This is a simple heuristic that crops the top-left region where logos typically appear.
    
    Args:
        screenshot_bytes: Screenshot bytes
        
    Returns:
        Base64-encoded logo image or None
    """
    try:
        screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
        width, height = screenshot.size
        
        # Crop top-left region (typically where logos appear)
        # Use 20% of width and 15% of height
        crop_width = int(width * 0.2)
        crop_height = int(height * 0.15)
        
        logo_region = screenshot.crop((0, 0, crop_width, crop_height))
        
        # Check if region has meaningful content (not just background)
        # Simple heuristic: check if there's sufficient color variation
        pixels = list(logo_region.getdata())
        if len(pixels) < 100:  # Too small
            return None
        
        # Convert to base64
        buffered = BytesIO()
        logo_region.save(buffered, format="PNG")
        logo_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        logger.debug(f"  Screenshot logo extraction: cropped {crop_width}x{crop_height} from top-left")
        return logo_base64
        
    except Exception as e:
        logger.debug(f"  Screenshot logo extraction failed: {e}")
        return None


def extract_hero_image(html_content: str, url: str) -> Optional[str]:
    """
    Extract hero/featured image from website.

    Priority order:
    1. og:image meta tag
    2. Large images in header/hero section
    3. First significant image on page

    Args:
        html_content: HTML content of the page
        url: URL of the website

    Returns:
        Base64-encoded hero image or None
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        # Try og:image first
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = urljoin(base_url, og_image['content'])
            try:
                response = requests.get(image_url, timeout=5)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    # Resize if too large
                    if img.width > 1200:
                        ratio = 1200 / img.width
                        new_size = (1200, int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)

                    buffered = BytesIO()
                    img.save(buffered, format="JPEG", quality=85)
                    hero_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    logger.info("Extracted hero image from og:image")
                    return hero_base64
            except Exception as e:
                logger.warning(f"Failed to download og:image: {e}")

        # Try hero section images
        hero_selectors = [
            '.hero img',
            '.banner img',
            'header img[class*="hero" i]',
            'section[class*="hero" i] img',
            '.jumbotron img',
        ]

        for selector in hero_selectors:
            hero_img = soup.select_one(selector)
            if hero_img and hero_img.get('src'):
                image_url = urljoin(base_url, hero_img['src'])
                try:
                    response = requests.get(image_url, timeout=5)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        if img.width >= 400 and img.height >= 300:  # Reasonable size
                            # Resize if needed
                            if img.width > 1200:
                                ratio = 1200 / img.width
                                new_size = (1200, int(img.height * ratio))
                                img = img.resize(new_size, Image.Resampling.LANCZOS)

                            buffered = BytesIO()
                            img.save(buffered, format="JPEG", quality=85)
                            hero_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            logger.info(f"Extracted hero image from: {selector}")
                            return hero_base64
                except Exception as e:
                    logger.warning(f"Failed to download hero image: {e}")
                    continue

        logger.info("No suitable hero image found")
        return None

    except Exception as e:
        logger.error(f"Hero image extraction failed: {e}", exc_info=True)
        return None


def _calculate_luminance(rgb: tuple) -> float:
    """Calculate relative luminance of an RGB color (0-1 scale)."""
    def adjust(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [adjust(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _get_contrast_ratio(color1: tuple, color2: tuple) -> float:
    """Calculate WCAG contrast ratio between two RGB colors."""
    l1 = _calculate_luminance(color1)
    l2 = _calculate_luminance(color2)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def _colors_are_too_similar(colors: list, min_contrast: float = 2.0) -> bool:
    """Check if all extracted colors are too similar (low contrast potential)."""
    if len(colors) < 2:
        return True
    
    # Check all pairs for sufficient contrast
    for i, c1 in enumerate(colors):
        for c2 in colors[i+1:]:
            if _get_contrast_ratio(c1, c2) >= min_contrast:
                return False  # Found at least one good contrast pair
    return True  # All colors are too similar


def _darken_tuple(rgb: tuple, factor: float = 0.2) -> tuple:
    """Darken an RGB color tuple by a factor."""
    return tuple(max(0, int(c * (1 - factor))) for c in rgb)


def _extract_colors_from_image(image_bytes: bytes) -> Dict[str, str]:
    """
    Extract dominant colors from an image using PIL.
    
    ENHANCED: Now validates color contrast and uses fallbacks
    when all extracted colors are too similar (e.g., all white).
    
    Args:
        image_bytes: Image bytes
        
    Returns:
        Dict with primary, secondary, accent colors with guaranteed contrast
    """
    # Fallback colors with good contrast
    FALLBACK_COLORS = {
        "primary_color": "#1E293B",  # Dark slate (good for text)
        "secondary_color": "#FFFFFF",  # White (good for backgrounds)
        "accent_color": "#F97316"  # Orange (brand accent)
    }
    
    try:
        img = Image.open(BytesIO(image_bytes))
        # Resize for faster processing
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get colors (sample every 5th pixel for speed)
        pixels = []
        width, height = img.size
        for y in range(0, height, 5):
            for x in range(0, width, 5):
                pixels.append(img.getpixel((x, y)))
        
        # Get most common colors - get more to find contrasting ones
        color_counts = Counter(pixels)
        top_colors = color_counts.most_common(10)  # Get more colors to find contrast
        
        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}".upper()
        
        # Get the raw top 3 colors
        raw_colors = [c[0] for c in top_colors[:3]] if len(top_colors) >= 3 else []
        
        # Check if extracted colors have sufficient contrast
        if len(raw_colors) < 2 or _colors_are_too_similar(raw_colors):
            logger.warning(f"Extracted colors lack contrast: {[rgb_to_hex(c) for c in raw_colors]}, using enhanced extraction")
            
            # Try to find contrasting colors from the extended palette
            all_colors = [c[0] for c in top_colors]
            
            # Separate into light and dark colors
            light_colors = [c for c in all_colors if _calculate_luminance(c) > 0.5]
            dark_colors = [c for c in all_colors if _calculate_luminance(c) <= 0.5]
            
            if dark_colors and light_colors:
                # IMPORTANT: In the preview system, primary_color is used for BACKGROUNDS
                # We need to determine if this is a light or dark themed site
                
                # Calculate if the site is predominantly light or dark
                light_pixel_count = sum(1 for c in all_colors if _calculate_luminance(c) > 0.5)
                total_colors = len(all_colors)
                is_light_themed = light_pixel_count > total_colors * 0.6  # 60%+ light = light theme
                
                dark_colors.sort(key=lambda c: _calculate_luminance(c))
                light_colors.sort(key=lambda c: _calculate_luminance(c), reverse=True)
                
                if is_light_themed:
                    # LIGHT THEMED SITE: Use vibrant gradient for visual interest
                    # Primary should be a rich gradient-friendly color, not pure white
                    
                    # Find the most saturated/colorful color from the palette
                    def get_saturation(rgb):
                        max_c = max(rgb)
                        min_c = min(rgb)
                        if max_c == 0:
                            return 0
                        return (max_c - min_c) / max_c
                    
                    colorful_colors = sorted(all_colors, key=get_saturation, reverse=True)
                    
                    # Use a softer dark gradient for light-themed sites (not pitch black)
                    # This creates a visually appealing preview even for white sites
                    # FIXED: Use even lighter slate colors to avoid "too black" look
                    primary = (71, 85, 105)  # Slate-600 - much softer, professional
                    secondary = (51, 65, 85)  # Slate-700 - softer than before
                    
                    # Try to find a brand color for accent (must be colorful, not dark)
                    accent = None
                    for c in colorful_colors:
                        sat = get_saturation(c)
                        lum = _calculate_luminance(c)
                        # Must have color AND not be too dark (luminance > 0.3)
                        if sat > 0.3 and lum > 0.3:
                            accent = c
                            break
                    
                    # Fallback to vibrant orange if no colorful accent found
                    if not accent:
                        accent = (249, 115, 22)  # Orange-500 - vibrant and visible
                    
                    colors = {
                        "primary_color": rgb_to_hex(primary),
                        "secondary_color": rgb_to_hex(secondary),
                        "accent_color": rgb_to_hex(accent)
                    }
                    logger.info(f"Light-themed site: using dark gradient for visual appeal: {colors}")
                    return colors
                else:
                    # DARK THEMED SITE: Use the actual dark colors from the site
                    primary = dark_colors[0]
                    secondary = dark_colors[1] if len(dark_colors) > 1 else _darken_tuple(primary, 0.2)
                    
                    # Find an accent color
                    accent = None
                    for c in all_colors:
                        if c != primary and c != secondary:
                            if _get_contrast_ratio(c, primary) >= 3.0:
                                accent = c
                                break
                    
                    if not accent:
                        accent = (251, 191, 36)  # Amber fallback for dark themes
                    
                    colors = {
                        "primary_color": rgb_to_hex(primary),
                        "secondary_color": rgb_to_hex(secondary),
                        "accent_color": rgb_to_hex(accent)
                    }
                    logger.info(f"Dark-themed site: using extracted dark colors: {colors}")
                    return colors
            else:
                # No dark/light separation possible - all colors are same luminance
                # Use professional gradient fallback
                if light_colors:
                    # All light colors - use softer dark gradient (not pitch black)
                    return {
                        "primary_color": "#475569",  # Slate-600 - much softer, professional
                        "secondary_color": "#334155",  # Slate-700 - softer than before
                        "accent_color": "#F97316"  # Orange accent - vibrant
                    }
                elif dark_colors:
                    # All dark colors - use extracted dark with amber accent
                    return {
                        "primary_color": rgb_to_hex(dark_colors[0]),
                        "secondary_color": "#0F172A",  # Slate-900
                        "accent_color": "#FBBF24"  # Amber accent
                    }
                else:
                    return FALLBACK_COLORS
        
        # Original colors have sufficient contrast - use them
        colors = {
            "primary_color": rgb_to_hex(top_colors[0][0]) if top_colors else "#2563EB",
            "secondary_color": rgb_to_hex(top_colors[1][0]) if len(top_colors) > 1 else "#1E40AF",
            "accent_color": rgb_to_hex(top_colors[2][0]) if len(top_colors) > 2 else "#F59E0B"
        }
        
        return colors
    except Exception as e:
        logger.warning(f"Failed to extract colors from image: {e}")
        return FALLBACK_COLORS


def extract_brand_colors(html_content: str, screenshot_bytes: Optional[bytes] = None) -> Dict[str, str]:
    """
    Extract brand colors from website with intelligent fallbacks.

    Priority:
    1. Screenshot color analysis (most accurate)
    2. CSS custom properties/variables
    3. Meta theme-color tag
    4. Branded MetaView fallback (not generic)

    Args:
        html_content: HTML content of the page
        screenshot_bytes: Optional screenshot for color extraction

    Returns:
        Dict with primary, secondary, accent colors
    """
    # Use branded MetaView fallback instead of generic blue
    colors = {
        "primary_color": "#F97316",  # MetaView orange (branded fallback)
        "secondary_color": "#1E293B",  # Dark gray
        "accent_color": "#FBBF24"  # MetaView amber
    }

    try:
        # Priority 1: Extract from screenshot if available (most accurate)
        if screenshot_bytes:
            palette = _extract_colors_from_image(screenshot_bytes)
            if palette:
                colors["primary_color"] = palette.get("primary_color", colors["primary_color"])
                colors["secondary_color"] = palette.get("secondary_color", colors["secondary_color"])
                colors["accent_color"] = palette.get("accent_color", colors["accent_color"])
                logger.info(f"Extracted colors from screenshot: {colors}")
                return colors

        # Priority 2: Parse CSS for common brand color patterns
        soup = BeautifulSoup(html_content, 'html.parser')

        # Check for CSS variables (modern approach)
        style_tags = soup.find_all('style')
        for style in style_tags:
            if style.string:
                # Look for CSS custom properties (primary, brand, main colors)
                var_matches = re.findall(r'--(?:primary|brand|main)[-\w]*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb\([^)]+\))', style.string)
                if var_matches:
                    colors["primary_color"] = var_matches[0]
                    logger.info(f"Extracted primary color from CSS variables: {colors['primary_color']}")
                    # Try to find secondary/accent in same style block
                    secondary_matches = re.findall(r'--(?:secondary|accent)[-\w]*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb\([^)]+\))', style.string)
                    if len(secondary_matches) > 0:
                        colors["secondary_color"] = secondary_matches[0]
                    if len(secondary_matches) > 1:
                        colors["accent_color"] = secondary_matches[1]
                    break

        # Priority 3: Check meta theme-color tag
        theme_color = soup.find('meta', attrs={'name': 'theme-color'})
        if theme_color and theme_color.get('content'):
            theme_hex = theme_color['content'].strip()
            if re.match(r'^#[0-9a-fA-F]{6}$', theme_hex, re.IGNORECASE):
                colors["primary_color"] = theme_hex
                logger.info(f"Extracted primary color from theme-color meta: {colors['primary_color']}")

        return colors

    except Exception as e:
        logger.error(f"Color extraction failed: {e}", exc_info=True)
        # Return branded MetaView fallback, not generic blue
        return colors


def extract_brand_name(html_content: str, url: str) -> Optional[str]:
    """
    Extract brand name from website.

    Priority order:
    1. og:site_name meta tag
    2. <title> tag (cleaned)
    3. Domain name

    Args:
        html_content: HTML content of the page
        url: URL of the website

    Returns:
        Brand name or None
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Try og:site_name
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name and og_site_name.get('content'):
            return og_site_name['content']

        # Try title tag (remove common suffixes)
        title = soup.find('title')
        if title and title.string:
            title_text = title.string.strip()
            # Remove common separators and everything after them
            for sep in [' | ', ' - ', ' – ', ' :: ']:
                if sep in title_text:
                    title_text = title_text.split(sep)[0]
                    break
            return title_text

        # Fallback: Use domain name
        domain = urlparse(url).netloc
        # Remove www. and TLD
        domain = re.sub(r'^www\.', '', domain)
        domain = re.sub(r'\.[a-z]{2,}$', '', domain)
        return domain.capitalize()

    except Exception as e:
        logger.error(f"Brand name extraction failed: {e}", exc_info=True)
        return None


def extract_all_brand_elements(
    html_content: str,
    url: str,
    screenshot_bytes: bytes
) -> Dict[str, Any]:
    """
    Extract all brand elements from a website.

    Args:
        html_content: HTML content of the page
        url: URL of the website
        screenshot_bytes: Screenshot bytes

    Returns:
        Dict containing all brand elements
    """
    logger.info(f"Extracting brand elements for: {url}")

    brand_elements = {
        "brand_name": extract_brand_name(html_content, url),
        "logo_base64": extract_brand_logo(html_content, url, screenshot_bytes),
        "hero_image_base64": extract_hero_image(html_content, url),
        "colors": extract_brand_colors(html_content, screenshot_bytes),
    }

    logger.info(f"Brand extraction complete: name={brand_elements['brand_name']}, "
                f"has_logo={bool(brand_elements['logo_base64'])}, "
                f"has_hero={bool(brand_elements['hero_image_base64'])}")

    return brand_elements
