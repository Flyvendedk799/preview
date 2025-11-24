"""Temporary testing endpoints for validation (DEV ONLY)."""
import os
from fastapi import APIRouter, HTTPException, Query
from backend.core.config import settings

router = APIRouter(prefix="/test", tags=["testing"])

# Only enable in development
if os.getenv("ENV", "development").lower() != "production":
    @router.get("/screenshot")
    def test_screenshot(url: str = Query(..., description="URL to capture screenshot of")):
        """
        Debug endpoint: captures a screenshot with Playwright and returns base64.
        Remove after validation.
        """
        from backend.services.playwright_screenshot import capture_screenshot
        import base64
        
        try:
            data = capture_screenshot(url)
            return {"base64": base64.b64encode(data).decode()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Screenshot failed: {str(e)}")

