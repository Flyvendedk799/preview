"""Playwright-based screenshot service for capturing website screenshots."""
import logging
from typing import Tuple, List
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError, Page

logger = logging.getLogger(__name__)


# =============================================================================
# COOKIE POPUP HANDLING
# =============================================================================

# Common cookie consent button selectors (ordered by specificity)
COOKIE_ACCEPT_SELECTORS = [
    # Generic accept buttons
    'button[id*="accept"]',
    'button[class*="accept"]',
    'a[id*="accept"]',
    'a[class*="accept"]',
    '[data-testid*="accept"]',
    '[data-action*="accept"]',
    
    # Common cookie consent platforms
    # OneTrust
    '#onetrust-accept-btn-handler',
    '.onetrust-accept-btn-handler',
    '#accept-recommended-btn-handler',
    
    # Cookiebot
    '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
    '#CybotCookiebotDialogBodyButtonAccept',
    'a#CybotCookiebotDialogBodyLevelButtonAccept',
    
    # Cookie Consent (Osano)
    '.cc-btn.cc-allow',
    '.cc-accept-all',
    '.cc-dismiss',
    
    # Quantcast
    '.qc-cmp2-summary-buttons button[mode="primary"]',
    '.qc-cmp-button',
    
    # Didomi
    '#didomi-notice-agree-button',
    '.didomi-continue-without-agreeing',
    
    # TrustArc / TRUSTe
    '.trustarc-agree-btn',
    '.truste-consent-button',
    '#truste-consent-button',
    
    # Termly
    '[data-tid="banner-accept"]',
    '.t-acceptAllButton',
    
    # CookieYes
    '[data-cky-tag="accept-button"]',
    '.cky-btn-accept',
    
    # GDPR Cookie Compliance
    '.moove-gdpr-infobar-allow-all',
    
    # Cookie Notice
    '#cookie-notice .cn-set-cookie',
    '#cookie-notice .cn-accept-cookie',
    
    # Borlabs Cookie
    '.borlabs-cookie button[data-cookie-accept]',
    
    # Complianz
    '.cmplz-accept',
    '.cmplz-btn.cmplz-accept',
    
    # Generic patterns (try these last)
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("Accept all")',
    'button:has-text("Accept Cookies")',
    'button:has-text("Accept cookies")',
    'button:has-text("Allow")',
    'button:has-text("Allow All")',
    'button:has-text("Allow all")',
    'button:has-text("I Accept")',
    'button:has-text("I agree")',
    'button:has-text("I Agree")',
    'button:has-text("Got it")',
    'button:has-text("OK")',
    'button:has-text("Agree")',
    'button:has-text("Agree & Continue")',
    'button:has-text("Continue")',
    'button:has-text("Close")',
    'a:has-text("Accept")',
    'a:has-text("Accept All")',
    'a:has-text("I Agree")',
    
    # European language variants
    'button:has-text("Akzeptieren")',  # German
    'button:has-text("Accepter")',  # French
    'button:has-text("Aceptar")',  # Spanish
    'button:has-text("Accetta")',  # Italian
    'button:has-text("Godkänn")',  # Swedish
    'button:has-text("Aceitar")',  # Portuguese
    'button:has-text("Akkoord")',  # Dutch
]

# CSS selectors for cookie banners to hide
COOKIE_BANNER_HIDE_SELECTORS = [
    # OneTrust
    '#onetrust-banner-sdk',
    '#onetrust-consent-sdk',
    '.onetrust-pc-dark-filter',
    
    # Cookiebot
    '#CybotCookiebotDialog',
    '#CybotCookiebotDialogBodyUnderlay',
    
    # Cookie Consent
    '.cc-window',
    '.cc-banner',
    '.cc-overlay',
    
    # Quantcast
    '.qc-cmp2-container',
    '#qc-cmp2-ui',
    
    # Didomi
    '#didomi-host',
    '#didomi-notice',
    
    # TrustArc
    '.truste-banner',
    '#truste-consent-track',
    
    # Termly
    '[data-tid="banner"]',
    '#termly-code-snippet-support',
    
    # CookieYes
    '.cky-consent-container',
    '.cky-modal',
    
    # Generic patterns
    '[class*="cookie-banner"]',
    '[class*="cookie-consent"]',
    '[class*="cookie-notice"]',
    '[class*="cookie-popup"]',
    '[class*="cookie-modal"]',
    '[class*="gdpr-banner"]',
    '[class*="gdpr-consent"]',
    '[class*="gdpr-notice"]',
    '[class*="consent-banner"]',
    '[class*="consent-modal"]',
    '[class*="privacy-banner"]',
    '[class*="privacy-notice"]',
    '[id*="cookie-banner"]',
    '[id*="cookie-consent"]',
    '[id*="cookie-notice"]',
    '[id*="cookie-popup"]',
    '[id*="gdpr-banner"]',
    '[id*="gdpr-consent"]',
    '[id*="consent-banner"]',
    '[id*="privacy-banner"]',
    
    # Overlay/backdrop
    '[class*="cookie-overlay"]',
    '[class*="consent-overlay"]',
    '[class*="modal-backdrop"]',
]


def dismiss_cookie_popups(page: Page, timeout: int = 3000) -> bool:
    """
    Attempt to dismiss cookie consent popups by clicking accept buttons.
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait for each button (ms)
        
    Returns:
        True if a cookie popup was dismissed, False otherwise
    """
    dismissed = False
    
    for selector in COOKIE_ACCEPT_SELECTORS:
        try:
            # Check if element exists and is visible
            element = page.query_selector(selector)
            if element and element.is_visible():
                # Try to click it
                element.click(timeout=timeout)
                logger.info(f"🍪 Dismissed cookie popup using selector: {selector}")
                dismissed = True
                # Wait for popup to disappear
                page.wait_for_timeout(500)
                break
        except Exception as e:
            # Element might not be clickable or selector didn't match
            continue
    
    return dismissed


def hide_cookie_banners(page: Page) -> int:
    """
    Hide cookie banners using CSS injection (fallback method).
    
    Args:
        page: Playwright page object
        
    Returns:
        Number of elements hidden
    """
    hidden_count = 0
    
    # Build CSS to hide all cookie banners
    css_rules = []
    for selector in COOKIE_BANNER_HIDE_SELECTORS:
        css_rules.append(f'{selector} {{ display: none !important; visibility: hidden !important; opacity: 0 !important; }}')
    
    # Add rule to remove any fixed overlays that might be blocking content
    css_rules.append('''
        body.cookie-banner-open { overflow: auto !important; }
        html.cookie-banner-open { overflow: auto !important; }
        .modal-open { overflow: auto !important; }
    ''')
    
    css_content = '\n'.join(css_rules)
    
    try:
        # Inject CSS to hide banners
        page.add_style_tag(content=css_content)
        
        # Also try to remove elements directly for more aggressive hiding
        script = '''
        () => {
            const selectors = ''' + str(COOKIE_BANNER_HIDE_SELECTORS[:20]) + ''';
            let count = 0;
            selectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.remove();
                        count++;
                    });
                } catch (e) {}
            });
            
            // Also remove any elements with cookie-related attributes
            document.querySelectorAll('[aria-label*="cookie" i], [aria-label*="consent" i], [aria-label*="gdpr" i]').forEach(el => {
                el.style.display = 'none';
                count++;
            });
            
            // Remove body scroll lock
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            
            return count;
        }
        '''
        
        hidden_count = page.evaluate(script)
        
        if hidden_count > 0:
            logger.info(f"🍪 Hidden {hidden_count} cookie-related elements via CSS/JS")
            
    except Exception as e:
        logger.warning(f"Failed to hide cookie banners: {e}")
    
    return hidden_count


def handle_cookie_popups(page: Page) -> bool:
    """
    Main function to handle cookie popups on a page.
    
    First tries to dismiss popups by clicking accept buttons,
    then falls back to hiding them with CSS.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if any cookie handling was performed
    """
    handled = False
    
    # Wait a moment for any lazy-loaded popups to appear
    page.wait_for_timeout(1000)
    
    # First, try to click accept buttons (preferred method)
    if dismiss_cookie_popups(page):
        handled = True
    
    # Then, hide any remaining banners with CSS
    if hide_cookie_banners(page) > 0:
        handled = True
    
    # Small delay to let any animations finish
    if handled:
        page.wait_for_timeout(500)
    
    return handled


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
                        logger.warning(f"Networkidle timeout for {url}, trying 'load' strategy")
                        page.goto(url, wait_until="load", timeout=30000)
                        page.wait_for_timeout(2000)
                except PlaywrightTimeoutError as e:
                    logger.error(f"Page navigation timeout for {url} (both strategies failed): {e}")
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

                # HANDLE COOKIE POPUPS before screenshot
                try:
                    cookie_handled = handle_cookie_popups(page)
                    if cookie_handled:
                        logger.info(f"🍪 Cookie popup handled for {url}")
                except Exception as e:
                    logger.warning(f"Cookie popup handling failed (non-critical): {e}")

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

                # HANDLE COOKIE POPUPS before screenshot
                try:
                    cookie_handled = handle_cookie_popups(page)
                    if cookie_handled:
                        logger.info(f"🍪 Cookie popup handled for {url}")
                except Exception as e:
                    logger.warning(f"Cookie popup handling failed (non-critical): {e}")

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

