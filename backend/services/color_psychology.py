"""
Color Psychology Engine.

Provides intelligent color handling based on Design DNA analysis.
Understands the emotional impact of colors and generates palettes
that honor the original design's psychological intent.

Key Features:
- Emotion-to-color mapping
- Intelligent gradient generation
- Color harmony calculations
- Contrast optimization for accessibility
- Background treatment recommendations
- Accent color strategies
"""

import colorsys
import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# COLOR EMOTION MAPPINGS
# =============================================================================

# Primary emotions and their associated color ranges (HSL)
EMOTION_COLORS = {
    "trust": {
        "primary_hues": [(200, 220)],  # Blues
        "saturation_range": (0.4, 0.7),
        "lightness_range": (0.4, 0.6),
        "mood": "stable, reliable, calm"
    },
    "energy": {
        "primary_hues": [(0, 30), (330, 360)],  # Reds, oranges
        "saturation_range": (0.7, 1.0),
        "lightness_range": (0.45, 0.55),
        "mood": "exciting, passionate, urgent"
    },
    "calm": {
        "primary_hues": [(180, 220), (100, 140)],  # Teals, greens
        "saturation_range": (0.2, 0.5),
        "lightness_range": (0.5, 0.7),
        "mood": "peaceful, serene, balanced"
    },
    "sophistication": {
        "primary_hues": [(0, 360)],  # Any hue works, depends on saturation
        "saturation_range": (0.1, 0.4),
        "lightness_range": (0.2, 0.4),
        "mood": "refined, premium, elegant"
    },
    "warmth": {
        "primary_hues": [(20, 50)],  # Oranges, warm yellows
        "saturation_range": (0.5, 0.8),
        "lightness_range": (0.5, 0.65),
        "mood": "friendly, inviting, comfortable"
    },
    "innovation": {
        "primary_hues": [(260, 290)],  # Purples, violets
        "saturation_range": (0.5, 0.8),
        "lightness_range": (0.4, 0.6),
        "mood": "creative, forward-thinking, unique"
    },
    "nature": {
        "primary_hues": [(80, 140)],  # Greens
        "saturation_range": (0.3, 0.6),
        "lightness_range": (0.4, 0.6),
        "mood": "organic, fresh, healthy"
    },
    "luxury": {
        "primary_hues": [(40, 50), (270, 290)],  # Golds, deep purples
        "saturation_range": (0.3, 0.6),
        "lightness_range": (0.25, 0.45),
        "mood": "premium, exclusive, rich"
    },
    "playfulness": {
        "primary_hues": [(280, 320), (40, 60)],  # Magentas, bright yellows
        "saturation_range": (0.7, 1.0),
        "lightness_range": (0.5, 0.7),
        "mood": "fun, creative, youthful"
    }
}


# =============================================================================
# COLOR CONFIGURATION
# =============================================================================

@dataclass
class ColorConfig:
    """Complete color configuration for rendering."""
    
    # Primary palette
    primary: Tuple[int, int, int]
    secondary: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    background: Tuple[int, int, int]
    text: Tuple[int, int, int]
    
    # Derived colors
    primary_light: Tuple[int, int, int]
    primary_dark: Tuple[int, int, int]
    accent_light: Tuple[int, int, int]
    
    # Gradient settings
    gradient_type: str  # linear, radial, none
    gradient_angle: int  # degrees for linear
    gradient_colors: List[Tuple[int, int, int]]
    
    # Background treatment
    background_style: str  # solid, gradient, subtle-pattern
    overlay_opacity: float  # for image backgrounds
    
    # Text colors
    text_on_primary: Tuple[int, int, int]
    text_on_accent: Tuple[int, int, int]
    text_muted: Tuple[int, int, int]
    
    # Shadow colors
    shadow_color: Tuple[int, int, int]
    shadow_opacity: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
            "primary_light": self.primary_light,
            "primary_dark": self.primary_dark,
            "accent_light": self.accent_light,
            "gradient_type": self.gradient_type,
            "gradient_angle": self.gradient_angle,
            "gradient_colors": self.gradient_colors,
            "background_style": self.background_style,
            "overlay_opacity": self.overlay_opacity,
            "text_on_primary": self.text_on_primary,
            "text_on_accent": self.text_on_accent,
            "text_muted": self.text_muted,
            "shadow_color": self.shadow_color,
            "shadow_opacity": self.shadow_opacity
        }
    
    def primary_hex(self) -> str:
        return rgb_to_hex(self.primary)
    
    def secondary_hex(self) -> str:
        return rgb_to_hex(self.secondary)
    
    def accent_hex(self) -> str:
        return rgb_to_hex(self.accent)


# =============================================================================
# COLOR UTILITIES
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (59, 130, 246)  # Default blue


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, rgb[0])),
        max(0, min(255, rgb[1])),
        max(0, min(255, rgb[2]))
    )


def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB to HSL."""
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s, l)


def hsl_to_rgb(hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert HSL to RGB."""
    h, s, l = hsl[0] / 360, hsl[1], hsl[2]
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def get_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance (WCAG)."""
    def adjust(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = adjust(rgb[0]), adjust(rgb[1]), adjust(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def get_contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """Calculate contrast ratio between two colors (WCAG)."""
    l1 = get_luminance(color1)
    l2 = get_luminance(color2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def lighten_color(rgb: Tuple[int, int, int], amount: float = 0.2) -> Tuple[int, int, int]:
    """Lighten a color by a percentage."""
    h, s, l = rgb_to_hsl(rgb)
    l = min(1.0, l + amount)
    return hsl_to_rgb((h, s, l))


def darken_color(rgb: Tuple[int, int, int], amount: float = 0.2) -> Tuple[int, int, int]:
    """Darken a color by a percentage."""
    h, s, l = rgb_to_hsl(rgb)
    l = max(0.0, l - amount)
    return hsl_to_rgb((h, s, l))


def desaturate_color(rgb: Tuple[int, int, int], amount: float = 0.3) -> Tuple[int, int, int]:
    """Desaturate a color."""
    h, s, l = rgb_to_hsl(rgb)
    s = max(0.0, s - amount)
    return hsl_to_rgb((h, s, l))


def get_complementary(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Get complementary color."""
    h, s, l = rgb_to_hsl(rgb)
    h = (h + 180) % 360
    return hsl_to_rgb((h, s, l))


def get_analogous(rgb: Tuple[int, int, int], angle: int = 30) -> List[Tuple[int, int, int]]:
    """Get analogous colors."""
    h, s, l = rgb_to_hsl(rgb)
    return [
        hsl_to_rgb(((h - angle) % 360, s, l)),
        rgb,
        hsl_to_rgb(((h + angle) % 360, s, l))
    ]


def get_triadic(rgb: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
    """Get triadic colors."""
    h, s, l = rgb_to_hsl(rgb)
    return [
        rgb,
        hsl_to_rgb(((h + 120) % 360, s, l)),
        hsl_to_rgb(((h + 240) % 360, s, l))
    ]


# =============================================================================
# CONTRAST OPTIMIZATION
# =============================================================================

def get_optimal_text_color(
    background: Tuple[int, int, int],
    prefer_white: bool = True
) -> Tuple[int, int, int]:
    """
    Get optimal text color for readability on a background.
    
    Ensures WCAG AA compliance (4.5:1 for normal text).
    """
    white = (255, 255, 255)
    black = (17, 24, 39)  # Near-black for softer appearance
    
    white_contrast = get_contrast_ratio(white, background)
    black_contrast = get_contrast_ratio(black, background)
    
    # Prefer white if specified and has sufficient contrast
    if prefer_white and white_contrast >= 4.5:
        return white
    
    # Otherwise, pick highest contrast
    return white if white_contrast > black_contrast else black


def ensure_contrast(
    foreground: Tuple[int, int, int],
    background: Tuple[int, int, int],
    min_ratio: float = 4.5
) -> Tuple[int, int, int]:
    """
    Adjust foreground color to ensure minimum contrast ratio.
    
    WCAG AA requires 4.5:1 for normal text, 3:1 for large text.
    For professional marketing, aim for 7:1 (AAA) when possible.
    """
    current_ratio = get_contrast_ratio(foreground, background)
    
    if current_ratio >= min_ratio:
        return foreground
    
    # Determine if we should lighten or darken
    bg_luminance = get_luminance(background)
    
    h, s, l = rgb_to_hsl(foreground)
    step = 0.03  # Smaller steps for more precise adjustment
    max_iterations = 50
    iterations = 0
    
    if bg_luminance > 0.5:
        # Light background needs darker foreground
        while l > 0 and iterations < max_iterations:
            new_color = hsl_to_rgb((h, s, l))
            if get_contrast_ratio(new_color, background) >= min_ratio:
                return new_color
            l -= step
            iterations += 1
    else:
        # Dark background needs lighter foreground
        while l < 1 and iterations < max_iterations:
            new_color = hsl_to_rgb((h, s, l))
            if get_contrast_ratio(new_color, background) >= min_ratio:
                return new_color
            l += step
            iterations += 1
    
    # If we couldn't achieve contrast, return pure white or black
    return (255, 255, 255) if bg_luminance < 0.5 else (17, 24, 39)


def get_high_impact_colors(
    primary: Tuple[int, int, int],
    background: Tuple[int, int, int]
) -> Dict[str, Tuple[int, int, int]]:
    """
    Generate high-impact color variations for professional marketing.
    
    Creates vibrant, attention-grabbing colors while maintaining
    professional appearance and contrast requirements.
    """
    h, s, l = rgb_to_hsl(primary)
    
    # Boost saturation for vibrancy (but not too much)
    vibrant_s = min(1.0, s * 1.3) if s < 0.7 else s
    
    # Create variations
    vibrant = hsl_to_rgb((h, vibrant_s, l))
    
    # Ensure text colors have excellent contrast
    text_on_bg = ensure_contrast((255, 255, 255), background, min_ratio=7.0)
    text_muted = ensure_contrast(
        hsl_to_rgb((h, s * 0.5, l * 0.8 if l > 0.5 else l * 1.2)),
        background,
        min_ratio=4.5
    )
    
    # Create accent that pops
    accent_h = (h + 30) % 360  # Analogous but different
    accent = hsl_to_rgb((accent_h, min(1.0, vibrant_s * 1.2), 0.55))
    accent = ensure_contrast(accent, background, min_ratio=4.5)
    
    # Create CTA color (high visibility)
    cta_h = (h + 180) % 360 if abs(h - 30) > 60 else 30  # Complementary or orange
    cta = hsl_to_rgb((cta_h, 0.9, 0.5))
    cta = ensure_contrast(cta, (255, 255, 255), min_ratio=4.5)
    
    return {
        "vibrant_primary": vibrant,
        "text": text_on_bg,
        "text_muted": text_muted,
        "accent": accent,
        "cta": cta,
        "cta_text": get_optimal_text_color(cta)
    }


def enhance_color_vibrancy(
    color: Tuple[int, int, int],
    boost: float = 0.15
) -> Tuple[int, int, int]:
    """
    Enhance color vibrancy while maintaining professional appearance.
    
    Args:
        color: RGB color tuple
        boost: Amount to boost saturation (0.0-0.5)
    
    Returns:
        Enhanced RGB color
    """
    h, s, l = rgb_to_hsl(color)
    
    # Boost saturation
    new_s = min(1.0, s + boost)
    
    # Slightly adjust lightness for optimal vibrancy
    if l > 0.6:
        new_l = l - 0.05  # Darken overly light colors
    elif l < 0.3:
        new_l = l + 0.05  # Lighten overly dark colors
    else:
        new_l = l
    
    return hsl_to_rgb((h, new_s, new_l))


# =============================================================================
# GRADIENT GENERATION
# =============================================================================

def generate_gradient_colors(
    primary: Tuple[int, int, int],
    secondary: Tuple[int, int, int],
    style: str = "smooth",
    steps: int = 3
) -> List[Tuple[int, int, int]]:
    """
    Generate gradient color stops.
    
    Args:
        primary: Starting color
        secondary: Ending color
        style: smooth, vibrant, or subtle
        steps: Number of color stops
        
    Returns:
        List of RGB tuples for gradient
    """
    if steps < 2:
        return [primary, secondary]
    
    colors = []
    
    for i in range(steps):
        t = i / (steps - 1)
        
        # Interpolate in HSL for smoother gradients
        h1, s1, l1 = rgb_to_hsl(primary)
        h2, s2, l2 = rgb_to_hsl(secondary)
        
        # Handle hue wraparound
        if abs(h2 - h1) > 180:
            if h1 > h2:
                h2 += 360
            else:
                h1 += 360
        
        h = (h1 + t * (h2 - h1)) % 360
        s = s1 + t * (s2 - s1)
        l = l1 + t * (l2 - l1)
        
        # Adjust based on style
        if style == "vibrant":
            s = min(1.0, s * 1.2)
        elif style == "subtle":
            s = s * 0.8
        
        colors.append(hsl_to_rgb((h, s, l)))
    
    return colors


def get_gradient_for_emotion(
    emotion: str,
    base_color: Optional[Tuple[int, int, int]] = None
) -> List[Tuple[int, int, int]]:
    """
    Generate a gradient that conveys a specific emotion.
    """
    emotion_gradients = {
        "trust": [(37, 99, 235), (59, 130, 246), (96, 165, 250)],
        "energy": [(220, 38, 38), (239, 68, 68), (248, 113, 113)],
        "calm": [(20, 184, 166), (45, 212, 191), (94, 234, 212)],
        "sophistication": [(30, 41, 59), (51, 65, 85), (71, 85, 105)],
        "warmth": [(234, 88, 12), (249, 115, 22), (251, 146, 60)],
        "innovation": [(124, 58, 237), (139, 92, 246), (167, 139, 250)],
        "nature": [(22, 163, 74), (34, 197, 94), (74, 222, 128)],
        "luxury": [(120, 53, 15), (146, 64, 14), (180, 83, 9)],
        "playfulness": [(192, 38, 211), (217, 70, 239), (232, 121, 249)]
    }
    
    if emotion.lower() in emotion_gradients:
        colors = emotion_gradients[emotion.lower()]
        
        # If base color provided, tint the gradient
        if base_color:
            h_base, s_base, l_base = rgb_to_hsl(base_color)
            tinted = []
            for color in colors:
                h, s, l = rgb_to_hsl(color)
                # Blend hue towards base
                h = (h + h_base) / 2
                tinted.append(hsl_to_rgb((h, s, l)))
            return tinted
        
        return colors
    
    # Default gradient
    return [(59, 130, 246), (37, 99, 235), (29, 78, 216)]


# =============================================================================
# BACKGROUND TREATMENTS
# =============================================================================

def get_background_treatment(
    design_style: str,
    color_strategy: str,
    light_dark_balance: float,
    primary_color: Tuple[int, int, int]
) -> Dict[str, Any]:
    """
    Determine background treatment based on design parameters.
    """
    style_lower = design_style.lower()
    
    # Determine if dark or light theme
    is_dark = light_dark_balance < 0.4
    
    treatments = {
        "minimalist": {
            "style": "solid" if is_dark else "gradient",
            "gradient_angle": 180,
            "overlay_opacity": 0.0,
            "background": darken_color(primary_color, 0.6) if is_dark else (255, 255, 255)
        },
        "luxurious": {
            "style": "gradient",
            "gradient_angle": 135,
            "overlay_opacity": 0.1,
            "background": darken_color(primary_color, 0.7)
        },
        "playful": {
            "style": "gradient",
            "gradient_angle": 45,
            "overlay_opacity": 0.0,
            "background": primary_color
        },
        "technical": {
            "style": "solid",
            "gradient_angle": 0,
            "overlay_opacity": 0.0,
            "background": (15, 23, 42) if is_dark else (248, 250, 252)
        },
        "corporate": {
            "style": "gradient",
            "gradient_angle": 180,
            "overlay_opacity": 0.05,
            "background": (255, 255, 255) if not is_dark else (30, 41, 59)
        },
        "bold": {
            "style": "gradient",
            "gradient_angle": 135,
            "overlay_opacity": 0.0,
            "background": primary_color
        }
    }
    
    return treatments.get(style_lower, treatments["corporate"])


# =============================================================================
# CORE CONFIGURATION GENERATOR
# =============================================================================

def get_color_config(
    primary_hex: str,
    secondary_hex: str,
    accent_hex: str,
    background_hex: str = "#FFFFFF",
    text_hex: str = "#111827",
    dominant_emotion: str = "trust",
    color_strategy: str = "complementary",
    design_style: str = "corporate",
    light_dark_balance: float = 0.7
) -> ColorConfig:
    """
    Generate complete color configuration based on Design DNA.
    
    Args:
        primary_hex: Primary brand color
        secondary_hex: Secondary color
        accent_hex: Accent/CTA color
        background_hex: Background color
        text_hex: Main text color
        dominant_emotion: Emotional intent
        color_strategy: Color harmony strategy
        design_style: Overall design style
        light_dark_balance: 0=dark theme, 1=light theme
        
    Returns:
        ColorConfig with all color settings
    """
    # Convert to RGB
    primary = hex_to_rgb(primary_hex)
    secondary = hex_to_rgb(secondary_hex)
    accent = hex_to_rgb(accent_hex)
    background = hex_to_rgb(background_hex)
    text = hex_to_rgb(text_hex)
    
    # Generate derived colors
    primary_light = lighten_color(primary, 0.2)
    primary_dark = darken_color(primary, 0.2)
    accent_light = lighten_color(accent, 0.15)
    
    # Determine gradient settings
    gradient_type = "linear" if design_style.lower() in ["bold", "playful", "luxurious"] else "none"
    gradient_angle = 135 if design_style.lower() in ["luxurious", "corporate"] else 45
    
    gradient_colors = generate_gradient_colors(
        primary_dark,
        secondary,
        style="vibrant" if design_style.lower() in ["playful", "bold"] else "smooth"
    )
    
    # Background treatment
    bg_treatment = get_background_treatment(
        design_style, color_strategy, light_dark_balance, primary
    )
    
    # Text colors
    text_on_primary = get_optimal_text_color(primary)
    text_on_accent = get_optimal_text_color(accent)
    text_muted = lighten_color(text, 0.3) if light_dark_balance > 0.5 else darken_color(text, 0.3)
    
    # Shadow color
    shadow_color = (0, 0, 0) if light_dark_balance > 0.5 else (255, 255, 255)
    shadow_opacity = 0.15 if design_style.lower() in ["bold", "playful"] else 0.1
    
    return ColorConfig(
        primary=primary,
        secondary=secondary,
        accent=accent,
        background=background,
        text=text,
        primary_light=primary_light,
        primary_dark=primary_dark,
        accent_light=accent_light,
        gradient_type=gradient_type,
        gradient_angle=gradient_angle,
        gradient_colors=gradient_colors,
        background_style=bg_treatment["style"],
        overlay_opacity=bg_treatment["overlay_opacity"],
        text_on_primary=text_on_primary,
        text_on_accent=text_on_accent,
        text_muted=text_muted,
        shadow_color=shadow_color,
        shadow_opacity=shadow_opacity
    )


# =============================================================================
# INTEGRATION WITH DESIGN DNA
# =============================================================================

def color_config_from_design_dna(dna_dict: Dict[str, Any]) -> ColorConfig:
    """
    Create ColorConfig from Design DNA dictionary.
    
    Convenience function for integration with design_dna_extractor.
    """
    color_psych = dna_dict.get("color_psychology", {})
    philosophy = dna_dict.get("philosophy", {})
    
    return get_color_config(
        primary_hex=color_psych.get("primary_hex", "#2563EB"),
        secondary_hex=color_psych.get("secondary_hex", "#1E40AF"),
        accent_hex=color_psych.get("accent_hex", "#F59E0B"),
        background_hex=color_psych.get("background_hex", "#FFFFFF"),
        text_hex=color_psych.get("text_hex", "#111827"),
        dominant_emotion=color_psych.get("dominant_emotion", "trust"),
        color_strategy=color_psych.get("color_strategy", "complementary"),
        design_style=philosophy.get("primary_style", "corporate"),
        light_dark_balance=color_psych.get("light_dark_balance", 0.7)
    )


def get_emotion_palette(emotion: str) -> Dict[str, str]:
    """
    Get a complete palette for a specific emotion.
    
    Useful for generating previews when original colors aren't available.
    """
    emotion_palettes = {
        "trust": {
            "primary": "#2563EB",
            "secondary": "#1E40AF",
            "accent": "#F59E0B",
            "background": "#FFFFFF",
            "text": "#1F2937"
        },
        "energy": {
            "primary": "#DC2626",
            "secondary": "#991B1B",
            "accent": "#FBBF24",
            "background": "#FFFFFF",
            "text": "#1F2937"
        },
        "calm": {
            "primary": "#14B8A6",
            "secondary": "#0D9488",
            "accent": "#6366F1",
            "background": "#F0FDFA",
            "text": "#134E4A"
        },
        "sophistication": {
            "primary": "#1E293B",
            "secondary": "#334155",
            "accent": "#C9A227",
            "background": "#0F172A",
            "text": "#E2E8F0"
        },
        "warmth": {
            "primary": "#EA580C",
            "secondary": "#C2410C",
            "accent": "#0EA5E9",
            "background": "#FFFBEB",
            "text": "#78350F"
        },
        "innovation": {
            "primary": "#7C3AED",
            "secondary": "#6D28D9",
            "accent": "#06B6D4",
            "background": "#FFFFFF",
            "text": "#1F2937"
        },
        "nature": {
            "primary": "#16A34A",
            "secondary": "#15803D",
            "accent": "#EAB308",
            "background": "#F0FDF4",
            "text": "#14532D"
        },
        "luxury": {
            "primary": "#78350F",
            "secondary": "#451A03",
            "accent": "#D4AF37",
            "background": "#1C1917",
            "text": "#FAFAF9"
        },
        "playfulness": {
            "primary": "#C026D3",
            "secondary": "#A21CAF",
            "accent": "#FACC15",
            "background": "#FDF4FF",
            "text": "#701A75"
        }
    }
    
    return emotion_palettes.get(emotion.lower(), emotion_palettes["trust"])

