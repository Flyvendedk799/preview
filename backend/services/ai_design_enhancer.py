"""
AI Design Enhancer - Applies Graphic Design Principles for Visual Appeal

Uses AI Vision to analyze composition and apply professional design principles:
- Rule of thirds
- Visual hierarchy
- Color harmony
- Spacing and rhythm
- Balance and contrast
- Typography refinement
"""

import logging
import json
import base64
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
from openai import OpenAI

from backend.core.config import settings

logger = logging.getLogger(__name__)


DESIGN_COMPOSITION_PROMPT = """You are a world-class creative director at a top design agency. Your job is to ensure this preview image meets the highest professional standards.

CRITICAL: Be STRICT. Most designs have room for improvement. Score honestly - a score of 0.9+ should only be given to exceptional designs.

EVALUATE THESE DESIGN PRINCIPLES (score 0.0-1.0 for each):

1. **VISUAL HIERARCHY** (0.0-1.0): 
   - Is there ONE clear focal point that immediately grabs attention?
   - Does the eye flow naturally from headline → subheadline → CTA?
   - Is the most important element the most prominent?

2. **TYPOGRAPHY QUALITY** (0.0-1.0):
   - Is the headline large, bold, and impactful enough?
   - Are font sizes well-proportioned (headline 2-3x larger than body)?
   - Is text crisp and readable? Any blur or shadow issues?
   - Is letter-spacing and line-height optimal?

3. **COLOR & CONTRAST** (0.0-1.0):
   - Is text-to-background contrast ratio high enough for easy reading?
   - Are colors vibrant and appealing (not washed out or muddy)?
   - Does the color palette feel cohesive and professional?
   - Is there visual "pop" that would catch attention on social media?

4. **SPACING & BREATHING ROOM** (0.0-1.0):
   - Is there adequate whitespace around elements?
   - Are elements properly aligned on a clear grid?
   - Is the layout balanced (not cramped or too sparse)?

5. **PROFESSIONAL POLISH** (0.0-1.0):
   - Does this look like it was designed by a professional?
   - Would this perform well on social media?
   - Are there any amateur-looking elements?
   - Does it feel modern and current?

6. **BRAND IMPACT** (0.0-1.0):
   - Does the design convey professionalism and trust?
   - Is the brand/product clearly communicated?
   - Would you click on this preview?

OUTPUT JSON:
{
    "composition_score": 0.0-1.0,
    "visual_hierarchy_score": 0.0-1.0,
    "color_harmony_score": 0.0-1.0,
    "typography_score": 0.0-1.0,
    "spacing_score": 0.0-1.0,
    "balance_score": 0.0-1.0,
    "contrast_score": 0.0-1.0,
    "professional_polish_score": 0.0-1.0,
    "brand_impact_score": 0.0-1.0,
    "overall_appeal": "excellent|good|fair|poor",
    
    "critical_issues": [
        {
            "type": "hierarchy|typography|color|contrast|spacing|polish|brand",
            "severity": "critical|major|minor",
            "description": "What's wrong",
            "fix": "How to fix it (be specific)"
        }
    ],
    
    "enhancement_actions": [
        {
            "action": "increase_contrast|boost_saturation|sharpen_text|increase_headline_weight|add_shadow|brighten|darken|increase_spacing",
            "intensity": "light|medium|strong",
            "reason": "Why this improves the design"
        }
    ],
    
    "color_analysis": {
        "needs_more_contrast": true/false,
        "needs_more_saturation": true/false,
        "needs_brightening": true/false,
        "needs_darkening": true/false,
        "contrast_issue": "none|low|very_low",
        "saturation_issue": "none|washed_out|muddy"
    },
    
    "typography_analysis": {
        "headline_impact": "excellent|good|weak|very_weak",
        "needs_sharpening": true/false,
        "needs_bolder_weight": true/false,
        "readability": "excellent|good|fair|poor"
    },
    
    "final_verdict": {
        "ready_for_production": true/false,
        "minimum_improvements_needed": ["list of must-fix items"],
        "would_perform_well_on_social": true/false
    },
    
    "confidence": 0.0-1.0
}

BE CRITICAL. Professional marketing previews must be EXCELLENT. Flag anything that reduces quality."""


def prepare_image_for_vision(image: Image.Image) -> str:
    """Prepare PIL Image for OpenAI Vision API."""
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize if too large (max 2048px on longest side for API efficiency)
    max_size = 2048
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to JPEG
    from io import BytesIO
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def analyze_design_composition(image: Image.Image) -> Optional[Dict[str, Any]]:
    """
    Use AI Vision to analyze design composition and provide recommendations.
    
    Args:
        image: PIL Image to analyze
        
    Returns:
        Dict with design analysis and recommendations, or None if analysis fails
    """
    try:
        logger.info(f"🎨 [AI_DESIGN] Starting design composition analysis...")
        logger.info(f"🎨 [AI_DESIGN] Input image: {image.size}, mode={image.mode}")
        
        # Prepare image
        image_base64 = prepare_image_for_vision(image)
        logger.info(f"🎨 [AI_DESIGN] Image encoded: JPEG size={len(base64.b64decode(image_base64))} bytes")
        
        # Call OpenAI Vision API
        logger.info(f"🎨 [AI_DESIGN] Calling OpenAI API: model=gpt-4o, max_tokens=1000")
        
        import time
        start_time = time.time()
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior graphic designer specializing in visual composition, typography, and design principles. Provide detailed, actionable design analysis."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": DESIGN_COMPOSITION_PROMPT
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
            max_tokens=1000,
            temperature=0.3
        )
        
        elapsed_time = time.time() - start_time
        
        # Log API response details
        usage = response.usage
        logger.info(f"🎨 [AI_DESIGN] API response received in {elapsed_time:.2f}s")
        logger.info(f"🎨 [AI_DESIGN] Token usage: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
        
        content = response.choices[0].message.content.strip()
        logger.info(f"🎨 [AI_DESIGN] Raw response length: {len(content)} chars")
        
        # Parse JSON response
        logger.info(f"🎨 [AI_DESIGN] Parsing JSON response...")
        original_content = content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
            logger.info(f"🎨 [AI_DESIGN] Extracted JSON from ```json``` block")
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            logger.info(f"🎨 [AI_DESIGN] Extracted JSON from ``` block")
        
        analysis = json.loads(content)
        
        # Log key analysis results
        logger.info(f"🎨 [AI_DESIGN] ✅ Design analysis complete:")
        logger.info(f"🎨 [AI_DESIGN]   - Composition score: {analysis.get('composition_score', 0):.2f}")
        logger.info(f"🎨 [AI_DESIGN]   - Visual hierarchy: {analysis.get('visual_hierarchy_score', 0):.2f}")
        logger.info(f"🎨 [AI_DESIGN]   - Color harmony: {analysis.get('color_harmony_score', 0):.2f}")
        logger.info(f"🎨 [AI_DESIGN]   - Typography: {analysis.get('typography_score', 0):.2f}")
        logger.info(f"🎨 [AI_DESIGN]   - Overall appeal: {analysis.get('overall_appeal', 'unknown')}")
        logger.info(f"🎨 [AI_DESIGN]   - Issues found: {len(analysis.get('issues', []))}")
        logger.info(f"🎨 [AI_DESIGN]   - Recommendations: {len(analysis.get('recommendations', []))}")
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.warning(f"🎨 [AI_DESIGN] Failed to parse AI response: {e}. Raw content: {original_content[:500]}...")
        return None
    except Exception as e:
        logger.warning(f"🎨 [AI_DESIGN] AI design analysis failed: {e}", exc_info=True)
        return None


def apply_design_improvements(
    image: Image.Image,
    analysis: Dict[str, Any],
    zones: Dict[str, Tuple[int, int, int, int]]
) -> Tuple[Image.Image, List[str]]:
    """
    Apply comprehensive design improvements based on AI analysis.
    
    Uses the AI's detailed analysis to apply professional-grade enhancements
    for contrast, saturation, sharpness, and overall visual quality.
    """
    enhanced_image = image.copy()
    applied_improvements = []
    
    # Get all scores and analysis
    contrast_score = analysis.get('contrast_score', 1.0)
    color_harmony_score = analysis.get('color_harmony_score', 1.0)
    typography_score = analysis.get('typography_score', 1.0)
    visual_hierarchy = analysis.get('visual_hierarchy_score', 1.0)
    professional_polish = analysis.get('professional_polish_score', 1.0)
    brand_impact = analysis.get('brand_impact_score', 1.0)
    overall_appeal = analysis.get('overall_appeal', 'good')
    
    color_analysis = analysis.get('color_analysis', {})
    typography_analysis = analysis.get('typography_analysis', {})
    enhancement_actions = analysis.get('enhancement_actions', [])
    final_verdict = analysis.get('final_verdict', {})
    
    logger.info(f"🎨 [AI_DESIGN] Starting comprehensive design enhancement...")
    logger.info(f"🎨 [AI_DESIGN] Scores: contrast={contrast_score:.2f}, color={color_harmony_score:.2f}, "
                f"typo={typography_score:.2f}, hierarchy={visual_hierarchy:.2f}, polish={professional_polish:.2f}")
    logger.info(f"🎨 [AI_DESIGN] Overall appeal: {overall_appeal}")
    
    # ==================== CONTRAST ENHANCEMENT ====================
    # This is THE most critical factor for professional-looking designs
    needs_contrast = color_analysis.get('needs_more_contrast', False)
    contrast_issue = color_analysis.get('contrast_issue', 'none')
    
    # Calculate contrast enhancement factor based on multiple signals
    contrast_factor = 1.0
    if contrast_score < 0.4 or contrast_issue == 'very_low':
        contrast_factor = 1.35  # Maximum boost for very low contrast
    elif contrast_score < 0.5 or needs_contrast:
        contrast_factor = 1.28
    elif contrast_score < 0.6 or contrast_issue == 'low':
        contrast_factor = 1.22
    elif contrast_score < 0.7 or visual_hierarchy < 0.6:
        contrast_factor = 1.18
    elif contrast_score < 0.8 or overall_appeal in ['poor', 'fair']:
        contrast_factor = 1.12
    elif contrast_score < 0.9:
        contrast_factor = 1.08
    
    if contrast_factor > 1.0:
        logger.info(f"🎨 [AI_DESIGN] Applying contrast enhancement: {contrast_factor:.2f}x")
        enhancer = ImageEnhance.Contrast(enhanced_image)
        enhanced_image = enhancer.enhance(contrast_factor)
        applied_improvements.append(f"Enhanced contrast ({contrast_factor:.2f}x)")
    
    # ==================== COLOR SATURATION ====================
    needs_saturation = color_analysis.get('needs_more_saturation', False)
    saturation_issue = color_analysis.get('saturation_issue', 'none')
    
    saturation_factor = 1.0
    if saturation_issue == 'washed_out' or color_harmony_score < 0.4:
        saturation_factor = 1.25  # Strong boost for washed out colors
    elif saturation_issue == 'muddy' or color_harmony_score < 0.5:
        saturation_factor = 1.20
    elif needs_saturation or color_harmony_score < 0.6:
        saturation_factor = 1.15
    elif color_harmony_score < 0.7:
        saturation_factor = 1.12
    elif color_harmony_score < 0.85:
        saturation_factor = 1.08
    
    if saturation_factor > 1.0:
        logger.info(f"🎨 [AI_DESIGN] Applying saturation boost: {saturation_factor:.2f}x")
        enhancer = ImageEnhance.Color(enhanced_image)
        enhanced_image = enhancer.enhance(saturation_factor)
        applied_improvements.append(f"Boosted color vibrancy ({saturation_factor:.2f}x)")
    
    # ==================== BRIGHTNESS OPTIMIZATION ====================
    needs_brightening = color_analysis.get('needs_brightening', False)
    needs_darkening = color_analysis.get('needs_darkening', False)
    
    if needs_brightening or overall_appeal == 'poor':
        logger.info(f"🎨 [AI_DESIGN] Brightening image for visibility")
        enhancer = ImageEnhance.Brightness(enhanced_image)
        enhanced_image = enhancer.enhance(1.08)
        applied_improvements.append("Brightened for visibility")
    elif needs_darkening:
        logger.info(f"🎨 [AI_DESIGN] Darkening for richer colors")
        enhancer = ImageEnhance.Brightness(enhanced_image)
        enhanced_image = enhancer.enhance(0.95)
        applied_improvements.append("Darkened for richer colors")
    
    # ==================== TEXT SHARPENING ====================
    headline_impact = typography_analysis.get('headline_impact', 'good')
    needs_sharpening = typography_analysis.get('needs_sharpening', False)
    readability = typography_analysis.get('readability', 'good')
    
    # Determine sharpening intensity
    if headline_impact == 'very_weak' or readability == 'poor' or typography_score < 0.4:
        logger.info(f"🎨 [AI_DESIGN] Applying STRONG text sharpening")
        enhanced_image = enhanced_image.filter(ImageFilter.UnsharpMask(radius=2.5, percent=200, threshold=2))
        applied_improvements.append("Applied strong text sharpening")
    elif headline_impact == 'weak' or readability == 'fair' or needs_sharpening or typography_score < 0.6:
        logger.info(f"🎨 [AI_DESIGN] Applying medium text sharpening")
        enhanced_image = enhanced_image.filter(ImageFilter.UnsharpMask(radius=2.0, percent=160, threshold=2))
        applied_improvements.append("Applied text sharpening")
    elif typography_score < 0.8:
        logger.info(f"🎨 [AI_DESIGN] Applying light text sharpening")
        enhanced_image = enhanced_image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
        applied_improvements.append("Applied light sharpening")
    
    # ==================== PROCESS AI ENHANCEMENT ACTIONS ====================
    for action in enhancement_actions:
        action_type = action.get('action', '')
        intensity = action.get('intensity', 'medium')
        reason = action.get('reason', '')
        
        logger.info(f"🎨 [AI_DESIGN] AI action: {action_type} ({intensity}) - {reason}")
        
        # Map intensity to factor
        intensity_map = {'light': 1.05, 'medium': 1.12, 'strong': 1.20}
        factor = intensity_map.get(intensity, 1.10)
        
        if action_type == 'increase_contrast' and 'contrast' not in str(applied_improvements).lower():
            enhancer = ImageEnhance.Contrast(enhanced_image)
            enhanced_image = enhancer.enhance(factor)
            applied_improvements.append(f"AI: {action_type} ({intensity})")
        elif action_type == 'boost_saturation' and 'saturation' not in str(applied_improvements).lower():
            enhancer = ImageEnhance.Color(enhanced_image)
            enhanced_image = enhancer.enhance(factor)
            applied_improvements.append(f"AI: {action_type} ({intensity})")
        elif action_type == 'brighten':
            enhancer = ImageEnhance.Brightness(enhanced_image)
            enhanced_image = enhancer.enhance(factor)
            applied_improvements.append(f"AI: {action_type}")
        elif action_type == 'darken':
            enhancer = ImageEnhance.Brightness(enhanced_image)
            enhanced_image = enhancer.enhance(2.0 - factor)  # Invert for darkening
            applied_improvements.append(f"AI: {action_type}")
    
    # ==================== LOG CRITICAL ISSUES ====================
    critical_issues = analysis.get('critical_issues', [])
    for issue in critical_issues:
        logger.warning(f"🎨 [AI_DESIGN] CRITICAL ISSUE: {issue.get('type')} - {issue.get('description')} (Fix: {issue.get('fix')})")
    
    # ==================== LOG FINAL VERDICT ====================
    if final_verdict:
        ready = final_verdict.get('ready_for_production', False)
        social_ready = final_verdict.get('would_perform_well_on_social', False)
        min_fixes = final_verdict.get('minimum_improvements_needed', [])
        logger.info(f"🎨 [AI_DESIGN] Final verdict: production_ready={ready}, social_ready={social_ready}")
        if min_fixes:
            logger.info(f"🎨 [AI_DESIGN] Minimum improvements needed: {min_fixes}")
    
    logger.info(f"🎨 [AI_DESIGN] ✅ Applied {len(applied_improvements)} design improvements")
    
    return enhanced_image, applied_improvements


def enhance_with_design_principles(image: Image.Image, zones: Dict[str, Tuple[int, int, int, int]]) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Main function to enhance image using AI design analysis.
    
    Args:
        image: PIL Image to enhance
        zones: Dict mapping element names to (x, y, width, height) zones
        
    Returns:
        Tuple of (enhanced_image, analysis_dict)
    """
    logger.info(f"🎨 [AI_DESIGN] Starting design enhancement with AI analysis...")
    
    # Analyze design composition
    analysis = analyze_design_composition(image)
    
    if not analysis:
        logger.warning(f"🎨 [AI_DESIGN] Design analysis failed, returning original image")
        return image, {}
    
    # Apply improvements
    enhanced_image, improvements = apply_design_improvements(image, analysis, zones)
    
    # Add improvements to analysis
    analysis['applied_improvements'] = improvements
    
    return enhanced_image, analysis

