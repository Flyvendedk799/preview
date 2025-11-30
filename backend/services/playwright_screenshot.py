"""Playwright-based screenshot service for capturing website screenshots."""
import logging
from typing import Tuple
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

logger = logging.getLogger(__name__)


def capture_screenshot(url: str) -> bytes:
    """
    Uses Playwright Chromium to generate an accurate screenshot of a webpage.
    Returns raw PNG bytes.

    Args:
        url: URL to capture screenshot of

    Returns:
        Raw image bytes (PNG format)
        
    Raises:
        Exception: If screenshot capture fails with descriptive error message
    """
    try:
        with sync_playwright() as p:
            # Chromium args for containerized environments (Railway, Docker)
            # These flags prevent GPU crashes and resource issues
            try:
                browser = p.chromium.launch(
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--single-process",
                        "--no-zygote"
                    ],
                    headless=True
                )
            except Exception as e:
                logger.error(f"Failed to launch browser for {url}: {e}")
                raise Exception(f"Failed to start browser: {str(e)}")

            try:
                page = browser.new_page(
                    viewport={"width": 1200, "height": 630},  # Ideal OG size
                    device_scale_factor=2
                )

                try:
                    # Try networkidle first (best for most sites)
                    try:
                        page.goto(url, wait_until="networkidle", timeout=45000)
                    except PlaywrightTimeoutError:
                        # Fallback to 'load' for heavy JavaScript sites
                        page.goto(url, wait_until="load", timeout=30000)
                        page.wait_for_timeout(2000)
                except PlaywrightTimeoutError as e:
                    logger.error(f"Page navigation timeout for {url}: {e}")
                    browser.close()
                    raise Exception(f"Page load timeout: The website took too long to load. Please try again or check if the URL is accessible.")
                except PlaywrightError as e:
                    logger.error(f"Playwright error navigating to {url}: {e}")
                    browser.close()
                    error_msg = str(e)
                    if "net::ERR_CERT_AUTHORITY_INVALID" in error_msg or "SSL" in error_msg:
                        raise Exception(f"SSL certificate error: The website's certificate is invalid or self-signed. Cannot capture screenshot.")
                    elif "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                        raise Exception(f"DNS error: Could not resolve the domain name. Please check the URL.")
                    elif "net::ERR_CONNECTION_REFUSED" in error_msg:
                        raise Exception(f"Connection refused: The website is not accessible. Please check if the URL is correct.")
                    else:
                        raise Exception(f"Failed to load page: {error_msg}")

                # Ensure full-page screenshot because highlight detection uses it
                try:
                    screenshot = page.screenshot(type="png", full_page=True)
                except Exception as e:
                    logger.error(f"Screenshot capture failed for {url}: {e}")
                    browser.close()
                    raise Exception(f"Failed to capture screenshot: {str(e)}")

                browser.close()
                return screenshot
                
            except Exception as e:
                # Ensure browser is closed even if page operations fail
                try:
                    browser.close()
                except:
                    pass
                raise
                
    except Exception as e:
        # Re-raise with more context if it's not already a descriptive error
        if "Failed to" not in str(e) and "error" not in str(e).lower():
            logger.error(f"Unexpected error capturing screenshot for {url}: {e}")
            raise Exception(f"Failed to capture screenshot: {str(e)}")
        raise


def capture_screenshot_and_html(url: str) -> Tuple[bytes, str]:
    """
    Capture both screenshot and HTML content from a webpage.

    This is more efficient than calling capture_screenshot and fetching HTML separately,
    as it reuses the same browser session.

    Args:
        url: URL to capture

    Returns:
        Tuple of (screenshot_bytes, html_content)
        
    Raises:
        Exception: If capture fails with descriptive error message
    """
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--single-process",
                        "--no-zygote"
                    ],
                    headless=True
                )
            except Exception as e:
                logger.error(f"Failed to launch browser for {url}: {e}")
                raise Exception(f"Failed to start browser: {str(e)}")

            try:
                page = browser.new_page(
                    viewport={"width": 1200, "height": 630},
                    device_scale_factor=2
                )

                try:
                    # Try networkidle first (best for most sites)
                    page.goto(url, wait_until="networkidle", timeout=45000)
                except PlaywrightTimeoutError as e:
                    logger.warning(f"Networkidle timeout for {url}, trying 'load' strategy: {e}")
                    try:
                        # Fallback to 'load' for heavy JavaScript sites (like OpenAI.com)
                        # This waits for the load event, which is more lenient than networkidle
                        page.goto(url, wait_until="load", timeout=30000)
                        # Give a small delay for any remaining JS to execute
                        page.wait_for_timeout(2000)
                    except PlaywrightTimeoutError as e2:
                        logger.error(f"Page navigation timeout for {url} (both strategies failed): {e2}")
                        browser.close()
                        raise Exception(f"Page load timeout: The website took too long to load.")
                except PlaywrightError as e:
                    logger.error(f"Playwright error navigating to {url}: {e}")
                    browser.close()
                    error_msg = str(e)
                    if "net::ERR_CERT_AUTHORITY_INVALID" in error_msg or "SSL" in error_msg:
                        raise Exception(f"SSL certificate error: The website's certificate is invalid.")
                    elif "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                        raise Exception(f"DNS error: Could not resolve the domain name.")
                    else:
                        raise Exception(f"Failed to load page: {error_msg}")

                # Capture both screenshot and HTML
                try:
                    screenshot = page.screenshot(type="png", full_page=True)
                    html_content = page.content()
                except Exception as e:
                    logger.error(f"Failed to capture screenshot/HTML for {url}: {e}")
                    browser.close()
                    raise Exception(f"Failed to capture screenshot: {str(e)}")

                browser.close()
                return screenshot, html_content
                
            except Exception as e:
                # Ensure browser is closed even if page operations fail
                try:
                    browser.close()
                except:
                    pass
                raise
                
    except Exception as e:
        # Re-raise with more context if it's not already a descriptive error
        if "Failed to" not in str(e) and "error" not in str(e).lower():
            logger.error(f"Unexpected error capturing screenshot/HTML for {url}: {e}")
            raise Exception(f"Failed to capture screenshot: {str(e)}")
        raise

