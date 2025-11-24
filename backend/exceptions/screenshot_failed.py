"""Custom exception for screenshot capture failures."""


class ScreenshotFailedException(Exception):
    """Raised when screenshot capture fails after retries."""
    pass

