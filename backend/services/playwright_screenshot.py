"""Playwright-based screenshot service for capturing website screenshots."""
from typing import Tuple
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
        # Chromium args for containerized environments (Railway, Docker)
        # These flags prevent GPU crashes and resource issues
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

        page = browser.new_page(
            viewport={"width": 1200, "height": 630},  # Ideal OG size
            device_scale_factor=2
        )

        page.goto(url, wait_until="networkidle", timeout=25000)

        # Ensure full-page screenshot because highlight detection uses it
        screenshot = page.screenshot(type="png", full_page=True)

        browser.close()
        return screenshot


def capture_screenshot_and_html(url: str) -> Tuple[bytes, str]:
    """
    Capture both screenshot and HTML content from a webpage.

    This is more efficient than calling capture_screenshot and fetching HTML separately,
    as it reuses the same browser session.

    Args:
        url: URL to capture

    Returns:
        Tuple of (screenshot_bytes, html_content)
    """
    with sync_playwright() as p:
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

        page = browser.new_page(
            viewport={"width": 1200, "height": 630},
            device_scale_factor=2
        )

        page.goto(url, wait_until="networkidle", timeout=25000)

        # Capture both screenshot and HTML
        screenshot = page.screenshot(type="png", full_page=True)
        html_content = page.content()

        browser.close()
        return screenshot, html_content

