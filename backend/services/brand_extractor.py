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


def extract_brand_colors(html_content: str, screenshot_bytes: Optional[bytes] = None) -> Dict[str, str]:
    """
    Extract brand colors from website.

    Uses both HTML analysis and screenshot color analysis.

    Args:
        html_content: HTML content of the page
        screenshot_bytes: Optional screenshot for color extraction

    Returns:
        Dict with primary, secondary, accent colors
    """
    from backend.services.preview_reasoning import extract_color_palette

    colors = {
        "primary_color": "#2563EB",  # Default blue
        "secondary_color": "#1E40AF",
        "accent_color": "#F59E0B"
    }

    try:
        # Extract from screenshot if available
        if screenshot_bytes:
            palette = extract_color_palette(screenshot_bytes)
            if palette:
                colors["primary_color"] = palette.get("primary", colors["primary_color"])
                colors["secondary_color"] = palette.get("secondary", colors["secondary_color"])
                colors["accent_color"] = palette.get("accent", colors["accent_color"])
                logger.info(f"Extracted colors from screenshot: {colors}")
                return colors

        # Fallback: Parse CSS for common brand color patterns
        soup = BeautifulSoup(html_content, 'html.parser')

        # Check for CSS variables (modern approach)
        style_tags = soup.find_all('style')
        for style in style_tags:
            if style.string:
                # Look for CSS custom properties
                var_matches = re.findall(r'--(?:primary|brand|main)[-\w]*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb\([^)]+\))', style.string)
                if var_matches:
                    # Use first match as primary color
                    colors["primary_color"] = var_matches[0]
                    logger.info(f"Extracted primary color from CSS variables: {colors['primary_color']}")
                    break

        return colors

    except Exception as e:
        logger.error(f"Color extraction failed: {e}", exc_info=True)
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
