"""
AI-driven visual focus detection for link preview images.

Uses OpenAI Vision API to analyze screenshots and determine the optimal
focal region based on UI/UX attention principles.
"""
import json
import base64
import logging
from io import BytesIO
from typing import Tuple, Optional, Dict, Any
from PIL import Image
import numpy as np
from openai import OpenAI
from backend.core.config import settings

logger = logging.getLogger("preview_worker")


def analyze_visual_focus(screenshot_bytes: bytes) -> Dict[str, Any]:
    """
    Use OpenAI Vision API to analyze a screenshot and determine the primary focal region.
    
    Applies UI/UX attention principles:
    - Visual hierarchy (size, color, contrast)
    - CTA prominence (buttons, forms, key actions)
    - Typography weight (headlines, hero text)
    - F-pattern / Z-pattern scanning behavior
    - Color dominance and contrast
    - Spacing and whitespace patterns
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        
    Returns:
        Dictionary with:
        - focal_region: {x, y, width, height} as percentages (0-100)
        - reasoning: Explanation of why this region was chosen
        - confidence: 0-1 confidence score
        - primary_element: What the AI identified as the main focus
    """
    try:
        # Encode image to base64
        image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a UI/UX visual analysis expert. Analyze screenshots to identify the PRIMARY FOCAL REGION that communicates the page's core intent within 1-2 seconds.

Apply these proven attention principles:
1. VISUAL HIERARCHY: Larger elements, bolder text, higher contrast areas naturally draw attention
2. CTA PROMINENCE: Buttons, forms, and action elements are intentional focus points
3. TYPOGRAPHY WEIGHT: Headlines, hero text, and bold statements guide the eye
4. F-PATTERN SCANNING: Users scan left-to-right, top-to-bottom, focusing on top-left quadrant first
5. Z-PATTERN SCANNING: For image-heavy pages, users scan in a Z pattern
6. COLOR CONTRAST: High-contrast elements against backgrounds capture attention
7. WHITESPACE: Elements with breathing room stand out more

Your goal: Find the region that best represents what the page WANTS users to see and understand immediately.

IMPORTANT: Return coordinates as PERCENTAGES (0-100) relative to the full image dimensions."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this webpage screenshot and identify the optimal focal region for a link preview.

The preview will be cropped to this region, so it must:
1. Capture the page's PRIMARY message or value proposition
2. Include the most visually compelling element (hero image, headline, CTA)
3. Work well at small sizes (social media preview cards)
4. Be visually clean without clutter

Return JSON with this exact structure:
{
    "focal_region": {
        "x": <left edge percentage 0-100>,
        "y": <top edge percentage 0-100>,
        "width": <width as percentage 0-100>,
        "height": <height as percentage 0-100>
    },
    "primary_element": "<what is the main focus: headline/hero_image/cta/product/form/etc>",
    "reasoning": "<brief explanation of why this region best represents the page>",
    "confidence": <0.0-1.0>
}

The region should be roughly 16:9 or 1.91:1 aspect ratio for optimal preview display."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        # Validate and normalize the response
        focal = result.get("focal_region", {})
        return {
            "focal_region": {
                "x": max(0, min(100, float(focal.get("x", 0)))),
                "y": max(0, min(100, float(focal.get("y", 0)))),
                "width": max(10, min(100, float(focal.get("width", 100)))),
                "height": max(10, min(100, float(focal.get("height", 100))))
            },
            "primary_element": result.get("primary_element", "unknown"),
            "reasoning": result.get("reasoning", ""),
            "confidence": max(0, min(1, float(result.get("confidence", 0.5))))
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"AI visual focus JSON parse error: {e}")
        return _get_default_focal_region()
    except Exception as e:
        logger.warning(f"AI visual focus analysis failed: {e}")
        return _get_default_focal_region()


def _get_default_focal_region() -> Dict[str, Any]:
    """Return default focal region (top-center, following F-pattern principle)."""
    return {
        "focal_region": {
            "x": 5,
            "y": 0,
            "width": 90,
            "height": 55
        },
        "primary_element": "fallback_top_region",
        "reasoning": "Using default top-center region based on F-pattern scanning behavior",
        "confidence": 0.3
    }


def generate_ai_focused_preview(
    screenshot_bytes: bytes,
    target_ratio: str = "1.91:1"
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Generate an AI-focused preview image from a screenshot.
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        target_ratio: Target aspect ratio ("1.91:1" for OG, "1:1" for square)
        
    Returns:
        Tuple of (cropped_image_bytes, analysis_metadata)
    """
    # Step 1: Load image
    image = Image.open(BytesIO(screenshot_bytes))
    img_width, img_height = image.size
    
    # Step 2: Get AI analysis
    analysis = analyze_visual_focus(screenshot_bytes)
    focal = analysis["focal_region"]
    
    # Step 3: Convert percentage coordinates to pixels
    focal_x = int(img_width * focal["x"] / 100)
    focal_y = int(img_height * focal["y"] / 100)
    focal_w = int(img_width * focal["width"] / 100)
    focal_h = int(img_height * focal["height"] / 100)
    
    # Step 4: Calculate target dimensions based on ratio
    if target_ratio == "1:1":
        target_aspect = 1.0
    else:  # Default to 1.91:1 (OG image standard)
        target_aspect = 1.91
    
    # Step 5: Adjust crop to match target aspect ratio while keeping focal point centered
    crop_box = _calculate_optimal_crop(
        img_width, img_height,
        focal_x, focal_y, focal_w, focal_h,
        target_aspect
    )
    
    # Step 6: Crop the image
    cropped = image.crop(crop_box)
    
    # Step 7: Resize to standard preview dimensions
    if target_ratio == "1:1":
        output_size = (600, 600)
    else:
        output_size = (1200, 630)
    
    # Use high-quality resampling
    final_image = cropped.resize(output_size, Image.Resampling.LANCZOS)
    
    # Step 8: Convert to bytes
    output = BytesIO()
    final_image.save(output, format='PNG', optimize=True)
    
    return output.getvalue(), analysis


def _calculate_optimal_crop(
    img_width: int, img_height: int,
    focal_x: int, focal_y: int,
    focal_w: int, focal_h: int,
    target_aspect: float
) -> Tuple[int, int, int, int]:
    """
    Calculate optimal crop box that includes the focal region and matches target aspect ratio.
    
    Args:
        img_width, img_height: Original image dimensions
        focal_x, focal_y: Top-left of focal region
        focal_w, focal_h: Dimensions of focal region
        target_aspect: Target width/height ratio
        
    Returns:
        Tuple of (left, top, right, bottom) crop coordinates
    """
    # Calculate focal center
    focal_center_x = focal_x + focal_w // 2
    focal_center_y = focal_y + focal_h // 2
    
    # Start with focal region size, expand to fit aspect ratio
    if focal_w / focal_h > target_aspect:
        # Focal region is wider than target - expand height
        crop_w = focal_w
        crop_h = int(crop_w / target_aspect)
    else:
        # Focal region is taller than target - expand width
        crop_h = focal_h
        crop_w = int(crop_h * target_aspect)
    
    # Ensure minimum size (at least 50% of image)
    min_crop_w = int(img_width * 0.5)
    min_crop_h = int(min_crop_w / target_aspect)
    
    crop_w = max(crop_w, min_crop_w)
    crop_h = max(crop_h, min_crop_h)
    
    # Ensure we don't exceed image bounds
    crop_w = min(crop_w, img_width)
    crop_h = min(crop_h, img_height)
    
    # Recalculate to maintain aspect ratio after bounds check
    if crop_w / crop_h > target_aspect:
        crop_w = int(crop_h * target_aspect)
    else:
        crop_h = int(crop_w / target_aspect)
    
    # Center crop on focal point
    left = focal_center_x - crop_w // 2
    top = focal_center_y - crop_h // 2
    
    # Adjust if out of bounds
    if left < 0:
        left = 0
    if top < 0:
        top = 0
    if left + crop_w > img_width:
        left = img_width - crop_w
    if top + crop_h > img_height:
        top = img_height - crop_h
    
    # Final bounds check
    left = max(0, left)
    top = max(0, top)
    right = min(img_width, left + crop_w)
    bottom = min(img_height, top + crop_h)
    
    return (left, top, right, bottom)


def generate_multiple_ratios(
    screenshot_bytes: bytes
) -> Dict[str, Tuple[bytes, Dict[str, Any]]]:
    """
    Generate preview images in multiple standard ratios.
    
    Args:
        screenshot_bytes: Raw PNG screenshot bytes
        
    Returns:
        Dictionary with ratio keys and (image_bytes, analysis) tuples
    """
    # Analyze once, crop multiple times
    analysis = analyze_visual_focus(screenshot_bytes)
    
    results = {}
    
    for ratio in ["1.91:1", "1:1"]:
        image = Image.open(BytesIO(screenshot_bytes))
        img_width, img_height = image.size
        
        focal = analysis["focal_region"]
        focal_x = int(img_width * focal["x"] / 100)
        focal_y = int(img_height * focal["y"] / 100)
        focal_w = int(img_width * focal["width"] / 100)
        focal_h = int(img_height * focal["height"] / 100)
        
        target_aspect = 1.0 if ratio == "1:1" else 1.91
        crop_box = _calculate_optimal_crop(
            img_width, img_height,
            focal_x, focal_y, focal_w, focal_h,
            target_aspect
        )
        
        cropped = image.crop(crop_box)
        output_size = (600, 600) if ratio == "1:1" else (1200, 630)
        final_image = cropped.resize(output_size, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        final_image.save(output, format='PNG', optimize=True)
        
        results[ratio] = (output.getvalue(), analysis)
    
    return results

