"""
AI Image Quality Fixer - Uses OpenAI Vision API to detect and fix rendering issues.

Features:
- Detects gradient banding using AI vision analysis
- Detects blurry/3D text effects
- Applies targeted fixes based on AI analysis
- Post-processes images to eliminate artifacts
"""

import logging
import base64
import json
from io import BytesIO
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image, ImageFilter, ImageEnhance

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Check if OpenAI is available (conditional import)
try:
    from openai import OpenAI
    try:
        OpenAI(api_key=settings.OPENAI_API_KEY)
        AI_AVAILABLE = True
    except Exception:
        AI_AVAILABLE = False
        logger.warning("OpenAI not available - AI image quality fixes disabled")
except ImportError:
    AI_AVAILABLE = False
    OpenAI = None
    logger.warning("OpenAI package not installed - AI image quality fixes disabled")


BANDING_DETECTION_PROMPT = """Analyze this preview image for visual quality issues, specifically:

1. GRADIENT BANDING: Look for visible horizontal or vertical bands/stripes in gradient backgrounds. These appear as distinct color steps instead of smooth transitions.

2. TEXT BLURRINESS: Check if text appears blurry, has unwanted 3D/shadow effects, or lacks crispness.

3. COLOR ARTIFACTS: Look for any color quantization issues, posterization, or unnatural color transitions.

OUTPUT JSON:
{
    "has_banding": true/false,
    "banding_severity": "none|mild|moderate|severe",
    "banding_location": "background|gradient|all",
    "has_blurry_text": true/false,
    "text_blur_severity": "none|mild|moderate|severe",
    "has_color_artifacts": true/false,
    "overall_quality": "excellent|good|fair|poor",
    "recommended_fixes": ["blur_gradient", "reduce_text_shadow", "smooth_colors", etc.],
    "confidence": 0.0-1.0
}

Be precise and only flag issues that are clearly visible. Confidence should reflect how certain you are about the issues detected."""


def prepare_image_for_vision(image: Image.Image) -> str:
    """Prepare PIL Image for OpenAI Vision API."""
    original_size = image.size
    original_mode = image.mode
    
    logger.info(f"🤖 [OPENAI_VISION] Preparing image: original_size={original_size}, mode={original_mode}")
    
    # Convert to RGB if needed
    if image.mode in ('RGBA', 'P', 'LA'):
        logger.info(f"🤖 [OPENAI_VISION] Converting {image.mode} to RGB...")
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode in ('RGBA', 'LA'):
            background.paste(image, mask=image.split()[-1])
        image = background
    
    # Resize if too large (max 2048px)
    max_dim = 2048
    if image.width > max_dim or image.height > max_dim:
        ratio = min(max_dim / image.width, max_dim / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        logger.info(f"🤖 [OPENAI_VISION] Resizing {image.size} -> {new_size} (ratio={ratio:.3f})")
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Encode to base64 JPEG
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    image_size_bytes = len(buffer.getvalue())
    base64_size_chars = len(image_base64)
    
    logger.info(f"🤖 [OPENAI_VISION] Image encoded: JPEG size={image_size_bytes} bytes, base64={base64_size_chars} chars, final_size={image.size}")
    
    return image_base64


def detect_quality_issues_with_ai(image: Image.Image) -> Optional[Dict[str, Any]]:
    """
    Use OpenAI Vision API to detect gradient banding and other quality issues.
    
    Args:
        image: PIL Image to analyze
        
    Returns:
        Dict with detected issues and recommendations, or None if analysis fails
    """
    if not AI_AVAILABLE or OpenAI is None:
        logger.debug("AI not available, skipping quality detection")
        return None
    
    try:
        logger.info(f"🤖 [OPENAI_VISION] Starting AI Vision API call for quality detection...")
        logger.info(f"🤖 [OPENAI_VISION] Input image: {image.size}, mode={image.mode}")
        
        # Prepare image
        image_base64 = prepare_image_for_vision(image)
        
        # Call OpenAI Vision API
        logger.info(f"🤖 [OPENAI_VISION] Calling OpenAI API: model=gpt-4o, max_tokens=500, temperature=0.3")
        logger.info(f"🤖 [OPENAI_VISION] Request: image_detail=high, prompt_length={len(BANDING_DETECTION_PROMPT)} chars")
        
        import time
        start_time = time.time()
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert image quality analyst specializing in detecting rendering artifacts, gradient banding, and text clarity issues."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": BANDING_DETECTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        elapsed_time = time.time() - start_time
        
        # Log API response details
        usage = response.usage
        logger.info(f"🤖 [OPENAI_VISION] API response received in {elapsed_time:.2f}s")
        logger.info(f"🤖 [OPENAI_VISION] Token usage: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        
        content = response.choices[0].message.content.strip()
        logger.info(f"🤖 [OPENAI_VISION] Raw response length: {len(content)} chars")
        
        # Parse JSON response
        logger.info(f"🤖 [OPENAI_VISION] Parsing JSON response...")
        original_content = content  # Store for error logging
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
            logger.info(f"🤖 [OPENAI_VISION] Extracted JSON from ```json``` block")
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            logger.info(f"🤖 [OPENAI_VISION] Extracted JSON from ``` block")
        
        analysis = json.loads(content)
        
        # Log full analysis results
        logger.info(f"🤖 [OPENAI_VISION] ✅ Analysis complete:")
        logger.info(f"🤖 [OPENAI_VISION]   - has_banding: {analysis.get('has_banding')}")
        logger.info(f"🤖 [OPENAI_VISION]   - banding_severity: {analysis.get('banding_severity')}")
        logger.info(f"🤖 [OPENAI_VISION]   - banding_location: {analysis.get('banding_location')}")
        logger.info(f"🤖 [OPENAI_VISION]   - has_blurry_text: {analysis.get('has_blurry_text')}")
        logger.info(f"🤖 [OPENAI_VISION]   - text_blur_severity: {analysis.get('text_blur_severity')}")
        logger.info(f"🤖 [OPENAI_VISION]   - has_color_artifacts: {analysis.get('has_color_artifacts')}")
        logger.info(f"🤖 [OPENAI_VISION]   - overall_quality: {analysis.get('overall_quality')}")
        logger.info(f"🤖 [OPENAI_VISION]   - confidence: {analysis.get('confidence')}")
        logger.info(f"🤖 [OPENAI_VISION]   - recommended_fixes: {analysis.get('recommended_fixes', [])}")
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"🤖 [OPENAI_VISION] ❌ Failed to parse JSON response: {e}")
        try:
            logger.error(f"🤖 [OPENAI_VISION] Response content (first 500 chars): {original_content[:500]}...")
        except NameError:
            logger.error(f"🤖 [OPENAI_VISION] Could not log response content")
        return None
    except Exception as e:
        logger.error(f"🤖 [OPENAI_VISION] ❌ API call failed: {type(e).__name__}: {e}")
        import traceback
        logger.debug(f"🤖 [OPENAI_VISION] Traceback: {traceback.format_exc()}")
        return None


def apply_ai_recommended_fixes(
    image: Image.Image,
    analysis: Dict[str, Any]
) -> Tuple[Image.Image, List[str]]:
    """
    Apply fixes based on AI analysis recommendations.
    
    Args:
        image: PIL Image to fix
        analysis: AI analysis results
        
    Returns:
        Tuple of (fixed_image, list_of_applied_fixes)
    """
    applied_fixes = []
    fixed_image = image.copy()
    
    # Check for banding issues
    has_banding = analysis.get("has_banding", False)
    banding_severity = analysis.get("banding_severity", "none")
    
    if has_banding and banding_severity != "none":
        # Apply dithering instead of blur - blur masks the problem, dithering fixes it
        import numpy as np
        from backend.services.gradient_generator import apply_fast_dithering
        
        logger.info(f"🔧 Applying fast dithering to fix banding (severity: {banding_severity})")
        img_array = np.array(fixed_image)
        # Increase dithering strength - mild banding needs stronger dithering
        dithered_array = apply_fast_dithering(img_array, strength={
            "mild": 5.0,      # Increased from 4.0 for better coverage
            "moderate": 7.0,  # Increased from 5.0 - moderate needs stronger dithering
            "severe": 9.0     # Increased from 6.0 - severe needs very strong dithering
        }.get(banding_severity, 4.0))
        
        fixed_image = Image.fromarray(dithered_array, mode='RGB')
        applied_fixes.append(f"Applied fast dithering (strength={banding_severity}) to fix gradient banding")
        logger.info(f"🔧 Fixed banding with dithering (strength: {banding_severity})")
    
    # Check for blurry text (we can't fix this post-render, but we log it)
    has_blurry_text = analysis.get("has_blurry_text", False)
    if has_blurry_text:
        applied_fixes.append("Blurry text detected - consider reducing shadow offset in next generation")
        logger.warning("⚠️ Blurry text detected - this should be fixed in rendering phase")
    
    # Check for color artifacts
    has_color_artifacts = analysis.get("has_color_artifacts", False)
    if has_color_artifacts:
        # Apply subtle color smoothing
        fixed_image = fixed_image.filter(ImageFilter.SMOOTH_MORE)
        applied_fixes.append("Applied color smoothing to reduce artifacts")
        logger.info("🔧 Applied color smoothing")
    
    # Apply recommended fixes from AI
    recommended_fixes = analysis.get("recommended_fixes", [])
    for fix in recommended_fixes:
        if fix == "smooth_colors" and "smooth_colors" not in applied_fixes:
            fixed_image = fixed_image.filter(ImageFilter.SMOOTH_MORE)
            applied_fixes.append("Applied color smoothing")
        elif fix == "enhance_contrast":
            enhancer = ImageEnhance.Contrast(fixed_image)
            fixed_image = enhancer.enhance(1.1)  # Slight contrast boost
            applied_fixes.append("Enhanced contrast slightly")
    
    return fixed_image, applied_fixes


def improve_image_quality_with_ai(image: Image.Image) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Main function: Detect quality issues with AI and apply fixes.
    
    Args:
        image: PIL Image to improve
        
    Returns:
        Tuple of (improved_image, analysis_results)
    """
    if not AI_AVAILABLE:
        logger.debug("AI not available, returning original image")
        return image, {"ai_available": False}
    
    # Detect issues with AI
    analysis = detect_quality_issues_with_ai(image)
    
    if not analysis:
        logger.debug("AI analysis failed or no issues detected")
        return image, {"ai_available": True, "analysis": None}
    
    # Check if fixes are needed
    has_banding = analysis.get("has_banding", False)
    has_blurry_text = analysis.get("has_blurry_text", False)
    has_color_artifacts = analysis.get("has_color_artifacts", False)
    
    if not (has_banding or has_blurry_text or has_color_artifacts):
        logger.info("✅ AI detected no quality issues")
        return image, {"ai_available": True, "analysis": analysis, "fixes_applied": []}
    
    # Apply fixes
    fixed_image, applied_fixes = apply_ai_recommended_fixes(image, analysis)
    
    logger.info(f"✅ Applied {len(applied_fixes)} AI-recommended fixes: {applied_fixes}")
    
    return fixed_image, {
        "ai_available": True,
        "analysis": analysis,
        "fixes_applied": applied_fixes
    }

