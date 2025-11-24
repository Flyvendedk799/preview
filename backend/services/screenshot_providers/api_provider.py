"""Screenshot API provider implementation."""
import time
import requests
from backend.core.config import settings
from backend.services.screenshot_providers.base import ScreenshotProvider
from backend.exceptions.screenshot_failed import ScreenshotFailedException


class ApiScreenshotProvider(ScreenshotProvider):
    """Screenshot provider using external screenshot API."""
    
    def capture(self, url: str) -> bytes:
        """
        Capture a screenshot using screenshot API with retry logic.
        
        Args:
            url: URL to capture screenshot of
            
        Returns:
            Raw image bytes (PNG format)
            
        Raises:
            ScreenshotFailedException: If capture fails after retries
        """
        api_key = settings.SCREENSHOT_API_KEY
        
        if not api_key:
            raise ScreenshotFailedException("SCREENSHOT_API_KEY not configured")
        
        # Using screenshotapi.net as example
        api_url = "https://shot.screenshotapi.net/screenshot"
        
        params = {
            "token": api_key,
            "url": url,
            "output": "image",
            "file_type": "png",
            "wait_for_event": "load",
            "full_page": True,
        }
        
        # Retry logic: up to 3 attempts (initial + 2 retries)
        max_retries = 2
        backoff_delays = [0.5, 1.5]  # Exponential backoff
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(api_url, params=params, timeout=20)
                
                # Retry on 5xx errors
                if 500 <= response.status_code < 600:
                    if attempt < max_retries:
                        delay = backoff_delays[attempt]
                        time.sleep(delay)
                        continue
                    else:
                        response.raise_for_status()
                
                response.raise_for_status()
                return response.content
                
            except requests.Timeout as e:
                last_exception = e
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    time.sleep(delay)
                    continue
            except requests.RequestException as e:
                last_exception = e
                # Retry on network errors
                if attempt < max_retries:
                    delay = backoff_delays[attempt]
                    time.sleep(delay)
                    continue
                else:
                    break
        
        # All retries exhausted
        error_msg = f"Screenshot capture failed after {max_retries + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        raise ScreenshotFailedException(error_msg)

