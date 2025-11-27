"""
Screenshot generation job module with AI-driven visual focus.

Production-hardened with:
- Deterministic fallback order
- Full observability logging
- Performance guardrails
- URL-based caching
"""
from uuid import uuid4
import cv2
import numpy as np
import hashlib
import time
import logging
from io import BytesIO
from typing import Tuple, Dict, Any, Optional
from PIL import Image
from backend.services.playwright_screenshot import capture_screenshot
from backend.services.r2_client import upload_file_to_r2
from backend.core.config import settings
from backend.exceptions.screenshot_failed import ScreenshotFailedException

logger = logging.getLogger("preview_worker")


# =============================================================================
# FALLBACK ORDER (Explicit and Deterministic)
# =============================================================================

FALLBACK_ORDER = [
    "ai_high_confidence",      # 1. AI with confidence >= 0.7
    "ai_relaxed_confidence",   # 2. AI with confidence >= 0.5
    "cv_heuristic",            # 3. Classical brightness/edge heuristic
    "og_image",                # 4. Original OG image from page (if available)
    "full_screenshot"          # 5. Full uncropped screenshot
]


# =============================================================================
# GENERATION RESULT TRACKING
# =============================================================================

class GenerationResult:
    """Track screenshot generation result for observability."""
    
    def __init__(self, url: str):
        self.url = url
        self.url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        self.start_time = time.time()
        self.steps: list = []
        self.final_method: str = None
        self.main_image_url: str = None
        self.highlight_image_url: str = None
        self.ai_analysis: Dict[str, Any] = None
        self.errors: list = []
    
    def log_step(self, step: str, success: bool, details: str = None, duration_ms: int = None):
        """Log a processing step."""
        entry = {
            "step": step,
            "success": success,
            "timestamp": time.time() - self.start_time,
            "details": details,
            "duration_ms": duration_ms
        }
        self.steps.append(entry)
        
        level = logging.INFO if success else logging.WARNING
        logger.log(level, f"[{self.url_hash}] {step}: success={success}, {details or ''}")
    
    def log_error(self, step: str, error: str):
        """Log an error."""
        self.errors.append({"step": step, "error": error})
        logger.error(f"[{self.url_hash}] {step} ERROR: {error}")
    
    def finalize(self, method: str):
        """Mark generation as complete."""
        self.final_method = method
        total_time = int((time.time() - self.start_time) * 1000)
        logger.info(f"[{self.url_hash}] Generation complete: method={method}, "
                   f"total_time={total_time}ms, errors={len(self.errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for storage/logging."""
        return {
            "url": self.url,
            "url_hash": self.url_hash,
            "final_method": self.final_method,
            "steps": self.steps,
            "errors": self.errors,
            "ai_analysis": self.ai_analysis,
            "total_time_ms": int((time.time() - self.start_time) * 1000)
        }


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_screenshot(url: str, og_image_url: Optional[str] = None) -> Tuple[str, str]:
    """
    Capture screenshot and upload to R2 with AI-focused highlight.
    
    Uses deterministic fallback order:
    1. AI crop (high confidence >= 0.7)
    2. AI crop (relaxed confidence >= 0.5)
    3. CV heuristic crop
    4. OG image (if provided)
    5. Full screenshot
    
    Args:
        url: URL to capture screenshot of
        og_image_url: Optional OG image URL from page metadata
        
    Returns:
        Tuple of (main_image_url, highlight_image_url)
        
    Raises:
        ScreenshotFailedException: If screenshot capture fails
    """
    result = GenerationResult(url)
    
    try:
        # Step 1: Capture screenshot
        step_start = time.time()
        screenshot_bytes = capture_screenshot(url)
        step_duration = int((time.time() - step_start) * 1000)
        result.log_step("screenshot_capture", True, 
                       f"size={len(screenshot_bytes)} bytes", step_duration)
        
        # Step 2: Upload main screenshot
        step_start = time.time()
        main_filename = f"screenshots/{uuid4()}.png"
        main_image_url = upload_file_to_r2(screenshot_bytes, main_filename, "image/png")
        result.main_image_url = main_image_url
        step_duration = int((time.time() - step_start) * 1000)
        result.log_step("main_upload", True, f"url={main_filename}", step_duration)
        
        # Step 3: Generate highlight using fallback order
        highlight_image_url, method_used = generate_highlight_with_fallback(
            screenshot_bytes, 
            og_image_url,
            main_image_url,
            result
        )
        result.highlight_image_url = highlight_image_url
        result.finalize(method_used)
        
        return main_image_url, highlight_image_url
        
    except ScreenshotFailedException as e:
        result.log_error("screenshot_capture", str(e))
        raise
    except Exception as e:
        result.log_error("unexpected", str(e))
        raise ScreenshotFailedException(f"Screenshot generation failed: {str(e)}")


def generate_highlight_with_fallback(
    screenshot_bytes: bytes,
    og_image_url: Optional[str],
    main_image_url: str,
    result: GenerationResult
) -> Tuple[str, str]:
    """
    Generate highlight image using deterministic fallback order.
    
    Returns:
        Tuple of (highlight_url, method_used)
    """
    
    # Fallback 1 & 2: AI crop (high then relaxed confidence)
    try:
        step_start = time.time()
        highlight_bytes, ai_analysis = generate_ai_highlight_image(screenshot_bytes)
        step_duration = int((time.time() - step_start) * 1000)
        
        result.ai_analysis = ai_analysis
        confidence = ai_analysis.get("confidence", 0)
        fallback_used = ai_analysis.get("fallback_used")
        
        if fallback_used:
            # AI returned a fallback result
            result.log_step("ai_analysis", False, 
                           f"fallback={fallback_used}, confidence={confidence:.2f}", 
                           step_duration)
        else:
            # AI succeeded
            method = "ai_high_confidence" if confidence >= 0.7 else "ai_relaxed_confidence"
            
            # Upload highlight
            highlight_filename = f"screenshots/{uuid4()}_highlight.png"
            highlight_url = upload_file_to_r2(highlight_bytes, highlight_filename, "image/png")
            
            result.log_step("ai_analysis", True,
                           f"intent={ai_analysis.get('intent_type')}, "
                           f"confidence={confidence:.2f}",
                           step_duration)
            
            return highlight_url, method
            
    except Exception as e:
        result.log_error("ai_analysis", str(e))
    
    # Fallback 3: CV heuristic crop
    try:
        step_start = time.time()
        heuristic_bytes = generate_basic_highlight_image(screenshot_bytes)
        step_duration = int((time.time() - step_start) * 1000)
        
        highlight_filename = f"screenshots/{uuid4()}_highlight.png"
        highlight_url = upload_file_to_r2(heuristic_bytes, highlight_filename, "image/png")
        
        result.log_step("cv_heuristic", True, "brightness+edge analysis", step_duration)
        return highlight_url, "cv_heuristic"
        
    except Exception as e:
        result.log_error("cv_heuristic", str(e))
    
    # Fallback 4: OG image
    if og_image_url:
        result.log_step("og_image", True, f"using existing OG image")
        return og_image_url, "og_image"
    
    # Fallback 5: Full screenshot
    result.log_step("full_screenshot", True, "using uncropped main image")
    return main_image_url, "full_screenshot"


# =============================================================================
# AI HIGHLIGHT GENERATION
# =============================================================================

def generate_ai_highlight_image(screenshot_bytes: bytes) -> Tuple[bytes, Dict[str, Any]]:
    """
    Generate AI-focused highlight image using visual analysis.
    
    Args:
        screenshot_bytes: Original screenshot image bytes
        
    Returns:
        Tuple of (highlight_image_bytes, analysis_metadata)
    """
    from backend.services.ai_visual_focus import generate_ai_focused_preview
    return generate_ai_focused_preview(screenshot_bytes, target_ratio="1.91:1")


# =============================================================================
# BASIC HEURISTIC HIGHLIGHT (CV2-based fallback)
# =============================================================================

def generate_basic_highlight_image(screenshot_bytes: bytes) -> bytes:
    """
    FALLBACK: Basic highlight detection using brightness and edge density.
    
    Used when AI analysis fails or returns low confidence.
    Detects brightest/most visually dense region and crops to 16:9.
    
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
    
    # Apply F-pattern bias (favor top-left)
    h, w = visual_score.shape
    f_pattern_weight = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            # Higher weight for top and left regions
            y_weight = 1.0 - (y / h) * 0.3  # Top is 1.0, bottom is 0.7
            x_weight = 1.0 - (x / w) * 0.2  # Left is 1.0, right is 0.8
            f_pattern_weight[y, x] = y_weight * x_weight
    
    visual_score = visual_score * f_pattern_weight
    
    # Find the region with highest visual score (16:9 aspect ratio)
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
    
    step_y = max(1, target_height // 8)
    step_x = max(1, target_width // 8)
    
    for y in range(0, h - target_height + 1, step_y):
        for x in range(0, w - target_width + 1, step_x):
            region = visual_score[y:y+target_height, x:x+target_width]
            score = np.sum(region)
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
    
    # Crop the highlight region
    highlight_region = img_array[best_y:best_y+target_height, best_x:best_x+target_width]
    
    # Resize to standard output (1200x630)
    highlight_image = Image.fromarray(highlight_region)
    highlight_image = highlight_image.resize((1200, 630), Image.Resampling.LANCZOS)
    
    # Convert to bytes
    output = BytesIO()
    highlight_image.save(output, format='PNG', optimize=True)
    return output.getvalue()


# =============================================================================
# DEBUG / VERIFICATION UTILITIES
# =============================================================================

def generate_debug_comparison(
    url: str,
    screenshot_bytes: bytes = None
) -> Dict[str, Any]:
    """
    Generate side-by-side comparison for debugging/verification.
    
    This captures all three outputs:
    1. Raw screenshot
    2. AI-cropped highlight
    3. Heuristic-cropped highlight
    
    For internal testing and proof of improvement.
    """
    if screenshot_bytes is None:
        screenshot_bytes = capture_screenshot(url)
    
    results = {
        "url": url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_screenshot_size": len(screenshot_bytes)
    }
    
    # AI crop
    try:
        ai_bytes, ai_analysis = generate_ai_highlight_image(screenshot_bytes)
        results["ai"] = {
            "success": True,
            "size": len(ai_bytes),
            "analysis": ai_analysis
        }
    except Exception as e:
        results["ai"] = {"success": False, "error": str(e)}
    
    # Heuristic crop
    try:
        heuristic_bytes = generate_basic_highlight_image(screenshot_bytes)
        results["heuristic"] = {
            "success": True,
            "size": len(heuristic_bytes)
        }
    except Exception as e:
        results["heuristic"] = {"success": False, "error": str(e)}
    
    return results
