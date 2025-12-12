"""
Typography Intelligence System.

Provides intelligent typography styling based on Design DNA analysis.
Handles font selection, sizing, weight, spacing, and text effects
to honor the original design's typographic personality.

Key Features:
- Font personality mapping (authoritative, friendly, elegant, etc.)
- Adaptive font sizing based on content and importance
- Weight contrast calculations
- Letter-spacing and line-height optimization
- Text effect recommendations (shadows, gradients)
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# FONT PERSONALITY MAPPING
# =============================================================================

class FontPersonality(str, Enum):
    """Font personality categories."""
    AUTHORITATIVE = "authoritative"
    FRIENDLY = "friendly"
    ELEGANT = "elegant"
    TECHNICAL = "technical"
    BOLD = "bold"
    SUBTLE = "subtle"
    EXPRESSIVE = "expressive"
    REFINED = "refined"
    PLAYFUL = "playful"
    MINIMAL = "minimal"


# Font stack recommendations by personality
# These use system fonts and common web fonts available on most systems
FONT_STACKS = {
    "authoritative": {
        "headline": "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "body": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "accent": "'Inter', sans-serif",
        "fallback_pillow": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
    },
    "friendly": {
        "headline": "'Nunito', 'Quicksand', 'Poppins', -apple-system, sans-serif",
        "body": "'Nunito', -apple-system, sans-serif",
        "accent": "'Nunito', sans-serif",
        "fallback_pillow": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    },
    "elegant": {
        "headline": "'Playfair Display', 'Georgia', 'Times New Roman', serif",
        "body": "'Source Sans Pro', 'Helvetica Neue', sans-serif",
        "accent": "'Playfair Display', serif",
        "fallback_pillow": ["DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"]
    },
    "technical": {
        "headline": "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Monaco', monospace",
        "body": "'Inter', 'SF Pro Text', sans-serif",
        "accent": "'JetBrains Mono', monospace",
        "fallback_pillow": ["DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"]
    },
    "bold": {
        "headline": "'Inter', 'SF Pro Display', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "accent": "'Inter', sans-serif",
        "fallback_pillow": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
    },
    "subtle": {
        "headline": "'Source Sans Pro', 'Helvetica Neue', -apple-system, sans-serif",
        "body": "'Source Sans Pro', 'Helvetica Neue', sans-serif",
        "accent": "'Source Sans Pro', sans-serif",
        "fallback_pillow": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    },
    "expressive": {
        "headline": "'Archivo Black', 'Oswald', 'Impact', sans-serif",
        "body": "'Work Sans', 'Open Sans', sans-serif",
        "accent": "'Archivo Black', sans-serif",
        "fallback_pillow": ["DejaVuSans-Bold.ttf", "FreeSansBold.ttf"]
    },
    "refined": {
        "headline": "'Cormorant Garamond', 'Libre Baskerville', 'Georgia', serif",
        "body": "'Lato', 'Source Sans Pro', sans-serif",
        "accent": "'Cormorant Garamond', serif",
        "fallback_pillow": ["DejaVuSerif.ttf", "LiberationSerif-Regular.ttf"]
    },
    "playful": {
        "headline": "'Fredoka One', 'Baloo 2', 'Comic Sans MS', sans-serif",
        "body": "'Nunito', 'Quicksand', sans-serif",
        "accent": "'Fredoka One', sans-serif",
        "fallback_pillow": ["DejaVuSans-Bold.ttf", "FreeSansBold.ttf"]
    },
    "minimal": {
        "headline": "'Helvetica Neue', 'Arial', -apple-system, sans-serif",
        "body": "'Helvetica Neue', 'Arial', sans-serif",
        "accent": "'Helvetica Neue', sans-serif",
        "fallback_pillow": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    }
}


# =============================================================================
# TYPOGRAPHY CONFIGURATION
# =============================================================================

@dataclass
class TypographyConfig:
    """Complete typography configuration for rendering."""
    
    # Font families
    headline_font: str
    body_font: str
    accent_font: str
    pillow_fonts: List[str]
    
    # Sizes (in pixels for 1200x630 OG image)
    headline_size: int
    subheadline_size: int
    body_size: int
    caption_size: int
    tag_size: int
    
    # Weights
    headline_weight: str
    body_weight: str
    accent_weight: str
    
    # Spacing
    headline_letter_spacing: float  # em units
    body_letter_spacing: float
    headline_line_height: float
    body_line_height: float
    
    # Effects
    use_text_shadow: bool
    shadow_intensity: float  # 0-1
    use_gradient_text: bool
    
    # Case
    headline_case: str  # normal, uppercase, lowercase, capitalize
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline_font": self.headline_font,
            "body_font": self.body_font,
            "accent_font": self.accent_font,
            "pillow_fonts": self.pillow_fonts,
            "headline_size": self.headline_size,
            "subheadline_size": self.subheadline_size,
            "body_size": self.body_size,
            "caption_size": self.caption_size,
            "tag_size": self.tag_size,
            "headline_weight": self.headline_weight,
            "body_weight": self.body_weight,
            "accent_weight": self.accent_weight,
            "headline_letter_spacing": self.headline_letter_spacing,
            "body_letter_spacing": self.body_letter_spacing,
            "headline_line_height": self.headline_line_height,
            "body_line_height": self.body_line_height,
            "use_text_shadow": self.use_text_shadow,
            "shadow_intensity": self.shadow_intensity,
            "use_gradient_text": self.use_gradient_text,
            "headline_case": self.headline_case
        }


# =============================================================================
# SIZE CALCULATIONS
# =============================================================================

# Base sizes for different design densities (1200x630 image)
SIZE_SCALES = {
    "compact": {
        "headline": 72,
        "subheadline": 32,
        "body": 24,
        "caption": 18,
        "tag": 16
    },
    "balanced": {
        "headline": 96,
        "subheadline": 40,
        "body": 28,
        "caption": 20,
        "tag": 18
    },
    "spacious": {
        "headline": 120,
        "subheadline": 48,
        "body": 32,
        "caption": 22,
        "tag": 20
    },
    "ultra-minimal": {
        "headline": 144,
        "subheadline": 56,
        "body": 36,
        "caption": 24,
        "tag": 22
    }
}

# Weight mappings
WEIGHT_MAPPINGS = {
    "high": {
        "headline": "black",  # 900
        "body": "regular",    # 400
        "accent": "bold"      # 700
    },
    "medium": {
        "headline": "bold",   # 700
        "body": "regular",    # 400
        "accent": "semibold"  # 600
    },
    "subtle": {
        "headline": "semibold",  # 600
        "body": "regular",       # 400
        "accent": "medium"       # 500
    }
}

# Spacing by character
SPACING_MAPPINGS = {
    "tight-dense": {
        "headline_letter": -0.02,
        "body_letter": 0,
        "headline_line": 1.1,
        "body_line": 1.4
    },
    "balanced": {
        "headline_letter": -0.01,
        "body_letter": 0.01,
        "headline_line": 1.2,
        "body_line": 1.5
    },
    "generous-luxury": {
        "headline_letter": 0.02,
        "body_letter": 0.02,
        "headline_line": 1.3,
        "body_line": 1.6
    }
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def get_typography_config(
    headline_personality: str,
    weight_contrast: str = "medium",
    spacing_character: str = "balanced",
    density: str = "balanced",
    design_style: str = "corporate",
    formality: float = 0.5
) -> TypographyConfig:
    """
    Generate complete typography configuration based on design parameters.
    
    Args:
        headline_personality: Typography personality (authoritative, friendly, etc.)
        weight_contrast: high, medium, or subtle
        spacing_character: tight-dense, balanced, or generous-luxury
        density: compact, balanced, spacious, or ultra-minimal
        design_style: Overall design style for effect decisions
        formality: 0-1 formality scale
        
    Returns:
        TypographyConfig with all typography settings
    """
    # Get font stack
    personality_key = headline_personality.lower()
    if personality_key not in FONT_STACKS:
        personality_key = "bold"  # Default
    
    fonts = FONT_STACKS[personality_key]
    
    # Get sizes
    density_key = density.lower() if density.lower() in SIZE_SCALES else "balanced"
    sizes = SIZE_SCALES[density_key]
    
    # Adjust sizes based on content (will be refined per-render)
    # For now, use base sizes
    
    # Get weights
    weight_key = weight_contrast.lower() if weight_contrast.lower() in WEIGHT_MAPPINGS else "medium"
    weights = WEIGHT_MAPPINGS[weight_key]
    
    # Get spacing
    spacing_key = spacing_character.lower() if spacing_character.lower() in SPACING_MAPPINGS else "balanced"
    spacing = SPACING_MAPPINGS[spacing_key]
    
    # Determine effects based on design style and formality
    use_shadow = design_style.lower() in ["bold", "expressive", "maximalist", "playful"]
    shadow_intensity = 0.3 if use_shadow else 0.0
    
    # Gradient text for certain styles
    use_gradient = design_style.lower() in ["luxurious", "futuristic", "playful"] and formality < 0.7
    
    # Case strategy based on personality
    case_map = {
        "authoritative": "normal",
        "technical": "normal",
        "bold": "normal",
        "expressive": "uppercase",
        "elegant": "normal",
        "minimal": "lowercase",
        "refined": "normal"
    }
    headline_case = case_map.get(personality_key, "normal")
    
    return TypographyConfig(
        headline_font=fonts["headline"],
        body_font=fonts["body"],
        accent_font=fonts["accent"],
        pillow_fonts=fonts["fallback_pillow"],
        headline_size=sizes["headline"],
        subheadline_size=sizes["subheadline"],
        body_size=sizes["body"],
        caption_size=sizes["caption"],
        tag_size=sizes["tag"],
        headline_weight=weights["headline"],
        body_weight=weights["body"],
        accent_weight=weights["accent"],
        headline_letter_spacing=spacing["headline_letter"],
        body_letter_spacing=spacing["body_letter"],
        headline_line_height=spacing["headline_line"],
        body_line_height=spacing["body_line"],
        use_text_shadow=use_shadow,
        shadow_intensity=shadow_intensity,
        use_gradient_text=use_gradient,
        headline_case=headline_case
    )


def calculate_adaptive_font_size(
    text: str,
    base_size: int,
    max_width: int,
    min_size: int = 24,
    max_size: int = 160
) -> int:
    """
    Calculate adaptive font size based on text length and container.
    
    Ensures text fits while maintaining readability.
    """
    # Approximate character width ratio (varies by font)
    char_width_ratio = 0.55
    
    # Calculate how many characters fit at base size
    estimated_width = len(text) * base_size * char_width_ratio
    
    if estimated_width <= max_width:
        return min(base_size, max_size)
    
    # Scale down to fit
    scale = max_width / estimated_width
    new_size = int(base_size * scale)
    
    return max(min_size, min(new_size, max_size))


def get_optimal_line_breaks(
    text: str,
    font_size: int,
    max_width: int,
    max_lines: int = 2
) -> List[str]:
    """
    Calculate optimal line breaks for balanced typography.
    
    Returns list of lines that fit within constraints.
    """
    if not text:
        return []
    
    # Approximate character width
    char_width = font_size * 0.55
    chars_per_line = int(max_width / char_width)
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        
        if current_length + word_length <= chars_per_line:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
            
            if len(lines) >= max_lines:
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(" ".join(current_line))
    
    # Smart truncation: break at word boundaries, not mid-word
    if len(lines) == max_lines and len(words) > sum(len(l.split()) for l in lines):
        last_line = lines[-1]
        if len(last_line) > chars_per_line - 3:
            # Find the last space before the truncation point
            truncate_at = chars_per_line - 3
            last_space = last_line.rfind(' ', 0, truncate_at)
            
            if last_space > 0:
                # Break at word boundary gracefully
                last_line = last_line[:last_space].rstrip() + "..."
            else:
                # No space found (single very long word), truncate but preserve start
                last_line = last_line[:truncate_at].rstrip() + "..."
        
        lines[-1] = last_line
    
    return lines


def get_text_shadow_params(
    text_color: Tuple[int, int, int],
    shadow_intensity: float,
    design_style: str
) -> Dict[str, Any]:
    """
    Calculate text shadow parameters based on design style.
    
    Returns shadow configuration for rendering.
    """
    if shadow_intensity <= 0:
        return {"enabled": False}
    
    # Determine shadow color based on text color brightness
    brightness = (text_color[0] * 299 + text_color[1] * 587 + text_color[2] * 114) / 1000
    
    if brightness > 128:  # Light text
        shadow_color = (0, 0, 0)
        shadow_alpha = int(100 * shadow_intensity)
    else:  # Dark text
        shadow_color = (255, 255, 255)
        shadow_alpha = int(60 * shadow_intensity)
    
    # Shadow offset and blur based on style
    style_lower = design_style.lower()
    
    if style_lower in ["bold", "expressive", "maximalist"]:
        offset = (4, 4)
        blur = 8
    elif style_lower in ["technical", "minimal"]:
        offset = (1, 1)
        blur = 2
    else:
        offset = (2, 2)
        blur = 4
    
    return {
        "enabled": True,
        "color": shadow_color,
        "alpha": shadow_alpha,
        "offset": offset,
        "blur": blur
    }


# =============================================================================
# PILLOW FONT HELPERS
# =============================================================================

def get_pillow_font_path(
    font_list: List[str],
    prefer_bold: bool = True
) -> str:
    """
    Get the best available Pillow font path from a list of preferences.
    
    Args:
        font_list: List of font filenames to try
        prefer_bold: Whether to prefer bold variants
        
    Returns:
        Path to the best available font
    """
    import os
    
    # Common font directories
    font_dirs = [
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/truetype/liberation/",
        "/usr/share/fonts/truetype/freefont/",
        "/usr/share/fonts/TTF/",
        "/System/Library/Fonts/",
        "C:\\Windows\\Fonts\\"
    ]
    
    # Try each font in the list
    for font_name in font_list:
        for font_dir in font_dirs:
            font_path = os.path.join(font_dir, font_name)
            if os.path.exists(font_path):
                return font_path
    
    # Fallback to common fonts
    fallbacks = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    
    if not prefer_bold:
        fallbacks = [f.replace("-Bold", "") for f in fallbacks]
    
    for path in fallbacks:
        if os.path.exists(path):
            return path
    
    # Return None to trigger default font
    return None


def get_typography_for_density(
    personality: str,
    density: str = "balanced"
) -> Dict[str, int]:
    """
    Get typography sizes for a given density level.
    
    Quick helper for image generation.
    """
    density_key = density.lower() if density.lower() in SIZE_SCALES else "balanced"
    sizes = SIZE_SCALES[density_key]
    
    # Adjust based on personality
    personality_lower = personality.lower()
    
    # Bold/expressive personalities get larger headlines
    if personality_lower in ["bold", "expressive", "authoritative"]:
        sizes = {
            "headline": int(sizes["headline"] * 1.1),
            "subheadline": sizes["subheadline"],
            "body": sizes["body"],
            "caption": sizes["caption"],
            "tag": sizes["tag"]
        }
    # Subtle/refined personalities get smaller, more refined sizes
    elif personality_lower in ["subtle", "refined", "elegant"]:
        sizes = {
            "headline": int(sizes["headline"] * 0.9),
            "subheadline": int(sizes["subheadline"] * 1.1),
            "body": sizes["body"],
            "caption": sizes["caption"],
            "tag": sizes["tag"]
        }
    
    return sizes


# =============================================================================
# INTEGRATION WITH DESIGN DNA
# =============================================================================

def typography_from_design_dna(dna_dict: Dict[str, Any]) -> TypographyConfig:
    """
    Create TypographyConfig from Design DNA dictionary.
    
    Convenience function for integration with design_dna_extractor.
    """
    typography_dna = dna_dict.get("typography", {})
    philosophy = dna_dict.get("philosophy", {})
    spatial = dna_dict.get("spatial", {})
    
    return get_typography_config(
        headline_personality=typography_dna.get("headline_personality", "bold"),
        weight_contrast=typography_dna.get("weight_contrast", "medium"),
        spacing_character=typography_dna.get("spacing_character", "balanced"),
        density=spatial.get("density", "balanced"),
        design_style=philosophy.get("primary_style", "corporate"),
        formality=philosophy.get("formality", 0.5)
    )

