"""Playwright screenshot provider (placeholder for future implementation)."""
from backend.services.screenshot_providers.base import ScreenshotProvider
from backend.exceptions.screenshot_failed import ScreenshotFailedException


class PlaywrightScreenshotProvider(ScreenshotProvider):
    """Screenshot provider using Playwright (not yet implemented)."""
    
    def capture(self, url: str) -> bytes:
        """
        Capture a screenshot using Playwright.
        
        This is a placeholder for future implementation.
        
        Args:
            url: URL to capture screenshot of
            
        Returns:
            Raw image bytes (PNG format)
            
        Raises:
            ScreenshotFailedException: Always (not implemented yet)
        """
        raise ScreenshotFailedException("Playwright provider not yet implemented. Use ApiScreenshotProvider instead.")

