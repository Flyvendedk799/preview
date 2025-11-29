"""
Brand extraction service for preview generation.

Extracts brand elements from websites:
- Logo (favicon or header logo)
- Primary brand colors
- Hero/featured images
- Brand name and tagline
"""
import base64
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


def extract_brand_logo(html_content: str, url: str, screenshot_bytes: bytes) -> Optional[str]:
    """
    Extract brand logo from website.

    Priority order:
    1. High-res logo from header/nav
    2. Favicon (if high quality)
    3. First image in header/nav area

    Args:
        html_content: HTML content of the page
        url: URL of the website
        screenshot_bytes: Screenshot for fallback logo extraction

    Returns:
        Base64-encoded logo image or None
    """
    try:
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
        ]

        for selector in logo_selectors:
            logo_img = soup.select_one(selector)
            if logo_img and logo_img.get('src'):
                logo_url = urljoin(base_url, logo_img['src'])

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
                            logger.info(f"Extracted logo from: {selector}")
                            return logo_base64
                except Exception as e:
                    logger.warning(f"Failed to download logo from {logo_url}: {e}")
                    continue

        # Fallback: Try favicon
        favicon_selectors = [
            'link[rel="icon"]',
            'link[rel="shortcut icon"]',
            'link[rel="apple-touch-icon"]',
        ]

        for selector in favicon_selectors:
            favicon = soup.select_one(selector)
            if favicon and favicon.get('href'):
                favicon_url = urljoin(base_url, favicon['href'])
                try:
                    response = requests.get(favicon_url, timeout=5)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        if img.width >= 64:  # Only use if reasonable quality
                            buffered = BytesIO()
                            img.save(buffered, format="PNG")
                            logo_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            logger.info(f"Extracted logo from favicon: {selector}")
                            return logo_base64
                except Exception as e:
                    logger.warning(f"Failed to download favicon from {favicon_url}: {e}")
                    continue

        logger.info("No suitable logo found")
        return None

    except Exception as e:
        logger.error(f"Logo extraction failed: {e}", exc_info=True)
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


def _extract_colors_from_image(image_bytes: bytes) -> Dict[str, str]:
    """
    Extract dominant colors from an image using PIL.
    
    Args:
        image_bytes: Image bytes
        
    Returns:
        Dict with primary, secondary, accent colors
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        # Resize for faster processing
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get colors (sample every 10th pixel for speed)
        pixels = []
        width, height = img.size
        for y in range(0, height, 5):
            for x in range(0, width, 5):
                pixels.append(img.getpixel((x, y)))
        
        # Get most common colors
        color_counts = Counter(pixels)
        top_colors = color_counts.most_common(3)
        
        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}".upper()
        
        colors = {
            "primary_color": rgb_to_hex(top_colors[0][0]) if top_colors else "#2563EB",
            "secondary_color": rgb_to_hex(top_colors[1][0]) if len(top_colors) > 1 else "#1E40AF",
            "accent_color": rgb_to_hex(top_colors[2][0]) if len(top_colors) > 2 else "#F59E0B"
        }
        
        return colors
    except Exception as e:
        logger.warning(f"Failed to extract colors from image: {e}")
        return {
            "primary_color": "#2563EB",
            "secondary_color": "#1E40AF",
            "accent_color": "#F59E0B"
        }


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
