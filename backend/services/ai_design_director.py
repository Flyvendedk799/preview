"""
AI Design Director - Creative AI-Powered Design Decisions

This module uses GPT-4 Vision to analyze screenshots and make intelligent
creative decisions about:
- Background style (gradient direction, colors, intensity)
- Color scheme (which colors to emphasize, contrast levels)
- Visual style (modern, bold, elegant, playful)
- Composition approach
- Typography recommendations

The AI acts as a creative director, making professional design decisions
instead of using hardcoded rules.
"""

import logging
import json
import base64
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image
from io import BytesIO
from openai import OpenAI

from backend.core.config import settings

logger = logging.getLogger(__name__)


DESIGN_DIRECTOR_PROMPT = """You are a world-class creative director at a top design agency. Analyze this website screenshot and make intelligent design decisions for creating a stunning OG preview image.

The preview will be 1200x630 pixels. Based on the website's visual identity, recommend:

## BACKGROUND DESIGN
Decide on the perfect background that would make this preview stand out on social media while honoring the brand:

1. **background_type**: "gradient" | "solid_with_depth" | "dark_dramatic" | "light_elegant"
2. **gradient_style**: "diagonal" | "radial" | "horizontal" | "vertical"
3. **gradient_angle**: 0-360 (degrees, where 0=right, 90=down, 135=diagonal)
4. **primary_bg_color**: Best background color (hex, e.g., "#1E293B")
5. **secondary_bg_color**: Second gradient color (hex)
6. **background_intensity**: "subtle" | "medium" | "bold" - how prominent the gradient should be

## COLOR STRATEGY
Based on the brand colors you see:

1. **text_color**: Best color for headlines (hex) - must contrast well with background
2. **accent_color**: Color for highlights/CTAs (hex)
3. **should_use_dark_bg**: true/false - would a dark background work better?
4. **contrast_level**: "high" | "medium" - how much contrast to use
5. **color_mood**: "professional" | "energetic" | "calm" | "bold" | "elegant"

## VISUAL STYLE
1. **design_style**: "modern-minimal" | "bold-dynamic" | "corporate-clean" | "startup-fresh" | "luxury-elegant"
2. **vignette_strength**: 0.0-0.5 - how much edge darkening
3. **use_accent_bar**: true/false - should we add a colored accent bar?
4. **accent_bar_color**: If using accent bar, what color (hex)

## TYPOGRAPHY
1. **headline_style**: "bold-impact" | "elegant-refined" | "friendly-rounded" | "tech-modern"
2. **headline_weight**: "black" | "bold" | "semibold"
3. **text_shadow**: "none" | "subtle" | "medium" - shadow behind text for contrast

## REASONING
Provide brief reasoning for your choices - why these decisions suit this brand.

OUTPUT JSON:
{
    "background": {
        "type": "gradient",
        "style": "diagonal",
        "angle": 135,
        "primary_color": "#1E293B",
        "secondary_color": "#334155",
        "intensity": "medium"
    },
    "colors": {
        "text_color": "#FFFFFF",
        "text_secondary": "#E2E8F0",
        "accent_color": "#F97316",
        "use_dark_bg": true,
        "contrast_level": "high",
        "mood": "professional"
    },
    "visual_style": {
        "design_style": "modern-minimal",
        "vignette_strength": 0.15,
        "use_accent_bar": true,
        "accent_bar_color": "#F97316"
    },
    "typography": {
        "headline_style": "bold-impact",
        "headline_weight": "black",
        "text_shadow": "subtle"
    },
    "reasoning": "Brief explanation of creative decisions"
}

Make BOLD creative decisions that will make this preview STAND OUT on social media feeds."""


def prepare_screenshot_for_vision(screenshot_bytes: bytes, max_size: int = 1024) -> str:
    """Prepare screenshot for Vision API, optimizing for speed and cost."""
    image = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
    
    # Resize for efficiency
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def get_ai_design_decisions(
    screenshot_bytes: bytes,
    brand_name: str = "",
    extracted_colors: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Use AI Vision to analyze screenshot and make creative design decisions.
    
    This is the core AI-powered design system that makes intelligent choices
    about how to design the preview based on the actual website.
    
    Args:
        screenshot_bytes: Website screenshot as bytes
        brand_name: Name of the brand (for context)
        extracted_colors: Already extracted colors (for reference)
        
    Returns:
        Dict with AI design decisions, or None if analysis fails
    """
    try:
        logger.info(f"🎨 [AI_DIRECTOR] Starting AI design direction for: {brand_name}")
        
        # Prepare image
        image_base64 = prepare_screenshot_for_vision(screenshot_bytes)
        logger.info(f"🎨 [AI_DIRECTOR] Screenshot prepared: {len(base64.b64decode(image_base64))} bytes")
        
        # Add color context to prompt if available
        context = ""
        if extracted_colors:
            context = f"\n\nExtracted brand colors for reference:\n- Primary: {extracted_colors.get('primary_color', 'unknown')}\n- Secondary: {extracted_colors.get('secondary_color', 'unknown')}\n- Accent: {extracted_colors.get('accent_color', 'unknown')}"
        if brand_name:
            context += f"\n\nBrand: {brand_name}"
        
        full_prompt = DESIGN_DIRECTOR_PROMPT + context
        
        import time
        start_time = time.time()
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an elite creative director making bold, professional design decisions. Output valid JSON only."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_prompt
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
            max_tokens=800,
            temperature=0.7  # Higher temperature for creative decisions
        )
        
        elapsed_time = time.time() - start_time
        usage = response.usage
        
        logger.info(f"🎨 [AI_DIRECTOR] AI response in {elapsed_time:.2f}s (tokens: {usage.total_tokens})")
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        decisions = json.loads(content)
        
        logger.info(f"🎨 [AI_DIRECTOR] ✅ Design decisions received:")
        logger.info(f"🎨 [AI_DIRECTOR]   - Background: {decisions.get('background', {}).get('type')} / {decisions.get('background', {}).get('style')}")
        logger.info(f"🎨 [AI_DIRECTOR]   - Text color: {decisions.get('colors', {}).get('text_color')}")
        logger.info(f"🎨 [AI_DIRECTOR]   - Dark BG: {decisions.get('colors', {}).get('use_dark_bg')}")
        logger.info(f"🎨 [AI_DIRECTOR]   - Style: {decisions.get('visual_style', {}).get('design_style')}")
        logger.info(f"🎨 [AI_DIRECTOR]   - Reasoning: {decisions.get('reasoning', '')[:100]}...")
        
        return decisions
        
    except json.JSONDecodeError as e:
        logger.warning(f"🎨 [AI_DIRECTOR] Failed to parse AI response: {e}")
        return None
    except Exception as e:
        logger.error(f"🎨 [AI_DIRECTOR] AI design direction failed: {e}", exc_info=True)
        return None


def apply_ai_design_decisions(
    design_decisions: Dict[str, Any],
    current_colors: Any,  # ColorConfig
    current_typography: Any  # TypographyConfig
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Apply AI design decisions to override current color and typography configs.
    
    Returns:
        Tuple of (color_overrides, typography_overrides)
    """
    color_overrides = {}
    typography_overrides = {}
    
    # Apply background decisions
    bg = design_decisions.get('background', {})
    if bg:
        # Convert hex colors to RGB tuples
        primary_hex = bg.get('primary_color', '')
        secondary_hex = bg.get('secondary_color', '')
        
        if primary_hex:
            color_overrides['background'] = hex_to_rgb(primary_hex)
            color_overrides['gradient_colors'] = [
                hex_to_rgb(primary_hex),
                hex_to_rgb(secondary_hex) if secondary_hex else darken_rgb(hex_to_rgb(primary_hex), 0.2)
            ]
        
        color_overrides['gradient_type'] = bg.get('style', 'diagonal')
        color_overrides['gradient_angle'] = bg.get('angle', 135)
        color_overrides['gradient_intensity'] = bg.get('intensity', 'medium')
    
    # Apply color decisions
    colors = design_decisions.get('colors', {})
    if colors:
        text_hex = colors.get('text_color', '')
        accent_hex = colors.get('accent_color', '')
        
        if text_hex:
            color_overrides['text'] = hex_to_rgb(text_hex)
        if accent_hex:
            color_overrides['accent'] = hex_to_rgb(accent_hex)
        
        color_overrides['use_dark_bg'] = colors.get('use_dark_bg', False)
        color_overrides['contrast_level'] = colors.get('contrast_level', 'high')
    
    # Apply visual style decisions
    visual = design_decisions.get('visual_style', {})
    if visual:
        color_overrides['vignette_strength'] = visual.get('vignette_strength', 0.15)
        color_overrides['use_accent_bar'] = visual.get('use_accent_bar', True)
        if visual.get('accent_bar_color'):
            color_overrides['accent_bar_color'] = hex_to_rgb(visual.get('accent_bar_color'))
    
    # Apply typography decisions
    typo = design_decisions.get('typography', {})
    if typo:
        typography_overrides['headline_style'] = typo.get('headline_style', 'bold-impact')
        typography_overrides['headline_weight'] = typo.get('headline_weight', 'bold')
        typography_overrides['text_shadow'] = typo.get('text_shadow', 'subtle')
    
    return color_overrides, typography_overrides


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (59, 130, 246)  # Default blue


def darken_rgb(rgb: Tuple[int, int, int], amount: float = 0.2) -> Tuple[int, int, int]:
    """Darken an RGB color."""
    return tuple(max(0, int(c * (1 - amount))) for c in rgb)


def get_default_design_decisions() -> Dict[str, Any]:
    """Get sensible default design decisions if AI fails."""
    return {
        "background": {
            "type": "gradient",
            "style": "diagonal",
            "angle": 135,
            "primary_color": "#1E293B",
            "secondary_color": "#334155",
            "intensity": "medium"
        },
        "colors": {
            "text_color": "#FFFFFF",
            "text_secondary": "#E2E8F0",
            "accent_color": "#3B82F6",
            "use_dark_bg": True,
            "contrast_level": "high",
            "mood": "professional"
        },
        "visual_style": {
            "design_style": "modern-minimal",
            "vignette_strength": 0.15,
            "use_accent_bar": True,
            "accent_bar_color": "#3B82F6"
        },
        "typography": {
            "headline_style": "bold-impact",
            "headline_weight": "black",
            "text_shadow": "subtle"
        },
        "reasoning": "Default professional design for reliable output"
    }

