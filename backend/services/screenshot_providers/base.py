"""Base interface for screenshot providers."""
from abc import ABC, abstractmethod


class ScreenshotProvider(ABC):
    """Base class for screenshot capture providers."""
    
    @abstractmethod
    def capture(self, url: str) -> bytes:
        """
        Capture a screenshot of a website.
        
        Args:
            url: URL to capture screenshot of
            
        Returns:
            Raw image bytes (PNG format)
            
        Raises:
            ScreenshotFailedException: If capture fails after retries
        """
        raise NotImplementedError

