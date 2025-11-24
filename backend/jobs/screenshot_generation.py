"""Screenshot generation job module."""
from uuid import uuid4
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from backend.services.playwright_screenshot import capture_screenshot
from backend.services.r2_client import upload_file_to_r2
from backend.core.config import settings
from backend.exceptions.screenshot_failed import ScreenshotFailedException
import logging

logger = logging.getLogger("preview_worker")


def generate_screenshot(url: str) -> tuple[str, str]:
    """
    Capture screenshot and upload to R2, also generate highlight image.
    
    Args:
        url: URL to capture screenshot of
        
    Returns:
        Tuple of (main_image_url, highlight_image_url)
        
    Raises:
        ScreenshotFailedException: If screenshot capture fails
    """
    try:
        screenshot_bytes = capture_screenshot(url)
        
        # Upload main screenshot
        main_filename = f"screenshots/{uuid4()}.png"
        main_image_url = upload_file_to_r2(screenshot_bytes, main_filename, "image/png")
        
        # Generate highlight image
        try:
            highlight_bytes = generate_highlight_image(screenshot_bytes)
            highlight_filename = f"screenshots/{uuid4()}_highlight.png"
            highlight_image_url = upload_file_to_r2(highlight_bytes, highlight_filename, "image/png")
        except Exception as e:
            logger.warning(f"Highlight generation failed, using main image: {e}")
            highlight_image_url = main_image_url  # Fallback to main image
        
        return main_image_url, highlight_image_url
    except ScreenshotFailedException as e:
        logger.error("Screenshot generation failed", exc_info=True)
        raise
    except Exception as e:
        logger.error("Unexpected error during screenshot generation", exc_info=True)
        raise ScreenshotFailedException(f"Screenshot generation failed: {str(e)}")


def generate_highlight_image(screenshot_bytes: bytes) -> bytes:
    """
    Detect brightest/most visually dense region and crop 16:9 highlight image.
    
    Args:
        screenshot_bytes: Original screenshot image bytes
        
    Returns:
        Highlight image bytes (16:9 cropped)
    """
    # Load image from bytes
    image = Image.open(BytesIO(screenshot_bytes))
    img_array = np.array(image)
    
    # Convert to RGB if needed
    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
    
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
    
    # Calculate brightness map
    brightness = gray.astype(np.float32)
    
    # Calculate visual density (brightness + edge density)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = cv2.GaussianBlur(edges.astype(np.float32), (21, 21), 0)
    
    # Combine brightness and edge density
    visual_score = brightness * 0.7 + edge_density * 0.3
    
    # Find the region with highest visual score
    h, w = visual_score.shape
    target_aspect = 16 / 9
    target_height = min(h, int(w / target_aspect))
    target_width = int(target_height * target_aspect)
    
    # Ensure dimensions fit
    if target_width > w:
        target_width = w
        target_height = int(w / target_aspect)
    
    # Slide window to find best region
    best_score = 0
    best_x, best_y = 0, 0
    
    for y in range(0, h - target_height + 1, max(1, target_height // 4)):
        for x in range(0, w - target_width + 1, max(1, target_width // 4)):
            region = visual_score[y:y+target_height, x:x+target_width]
            score = np.sum(region)
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
    
    # Crop the highlight region
    highlight_region = img_array[best_y:best_y+target_height, best_x:best_x+target_width]
    
    # Convert back to PIL Image and then to bytes
    highlight_image = Image.fromarray(highlight_region)
    output = BytesIO()
    highlight_image.save(output, format='PNG')
    return output.getvalue()

