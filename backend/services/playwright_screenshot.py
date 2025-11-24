"""Playwright-based screenshot service for capturing website screenshots."""
from playwright.sync_api import sync_playwright


def capture_screenshot(url: str) -> bytes:
    """
    Uses Playwright Chromium to generate an accurate screenshot of a webpage.
    Returns raw PNG bytes.
    
    Args:
        url: URL to capture screenshot of
        
    Returns:
        Raw image bytes (PNG format)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        
        page = browser.new_page(
            viewport={"width": 1200, "height": 630},  # Ideal OG size
            device_scale_factor=2
        )
        
        page.goto(url, wait_until="networkidle", timeout=25000)
        
        # Ensure full-page screenshot because highlight detection uses it
        screenshot = page.screenshot(type="png", full_page=True)
        
        browser.close()
        return screenshot

