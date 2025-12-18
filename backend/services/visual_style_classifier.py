"""
Visual Style Classifier - Classifies webpage design styles for template selection.

This module analyzes screenshots to classify design styles into categories
that inform template selection and styling decisions.

Categories:
- Minimal: Clean, lots of whitespace, simple typography
- Bold: Strong colors, large type, high contrast
- Corporate: Professional, structured, traditional
- Playful: Fun colors, rounded shapes, informal
- Technical: Dark mode, monospace, developer-focused
- Editorial: Magazine-style, image-heavy, sophisticated
- Luxurious: High-end, elegant, refined
- Brutalist: Raw, unconventional, artistic
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DesignStyle(str, Enum):
    """Design style categories."""
    MINIMAL = "minimal"
    BOLD = "bold"
    CORPORATE = "corporate"
    PLAYFUL = "playful"
    TECHNICAL = "technical"
    EDITORIAL = "editorial"
    LUXURIOUS = "luxurious"
    BRUTALIST = "brutalist"
    UNKNOWN = "unknown"


class ColorMood(str, Enum):
    """Color mood categories."""
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    VIBRANT = "vibrant"
    MUTED = "muted"
    DARK = "dark"
    LIGHT = "light"


class LayoutDensity(str, Enum):
    """Layout density categories."""
    SPARSE = "sparse"  # Lots of whitespace
    BALANCED = "balanced"  # Moderate density
    DENSE = "dense"  # Packed with content


@dataclass
class StyleClassification:
    """Result of style classification."""
    primary_style: DesignStyle
    secondary_style: Optional[DesignStyle]
    color_mood: ColorMood
    layout_density: LayoutDensity
    confidence: float
    
    # Style parameters for template rendering
    border_radius: str  # none, sm, md, lg, full
    shadow_intensity: str  # none, subtle, moderate, dramatic
    typography_weight: str  # light, regular, medium, bold, black
    spacing_scale: str  # tight, normal, relaxed, spacious
    
    # Additional style cues
    uses_gradients: bool
    uses_glassmorphism: bool
    is_dark_mode: bool
    has_illustrations: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary_style": self.primary_style.value,
            "secondary_style": self.secondary_style.value if self.secondary_style else None,
            "color_mood": self.color_mood.value,
            "layout_density": self.layout_density.value,
            "confidence": self.confidence,
            "border_radius": self.border_radius,
            "shadow_intensity": self.shadow_intensity,
            "typography_weight": self.typography_weight,
            "spacing_scale": self.spacing_scale,
            "uses_gradients": self.uses_gradients,
            "uses_glassmorphism": self.uses_glassmorphism,
            "is_dark_mode": self.is_dark_mode,
            "has_illustrations": self.has_illustrations
        }


class VisualStyleClassifier:
    """
    Classifies webpage design styles from screenshots and extracted data.
    
    Uses a combination of:
    1. Color analysis (palette, contrast, mood)
    2. Layout analysis (density, spacing, alignment)
    3. Typography analysis (weights, sizes, styles)
    4. Visual effect detection (shadows, gradients, blur)
    """
    
    def __init__(self):
        """Initialize the classifier."""
        logger.info("🎨 VisualStyleClassifier initialized")
    
    def classify(
        self,
        design_dna: Dict[str, Any],
        color_palette: Optional[Dict[str, str]] = None,
        layout_data: Optional[Dict[str, Any]] = None
    ) -> StyleClassification:
        """
        Classify the design style from extracted data.
        
        Args:
            design_dna: Design DNA from extraction
            color_palette: Extracted color palette
            layout_data: Layout analysis data
            
        Returns:
            StyleClassification with style category and parameters
        """
        # Extract style indicators
        style_indicators = self._extract_style_indicators(
            design_dna, color_palette, layout_data
        )
        
        # Score each style category
        style_scores = self._score_styles(style_indicators)
        
        # Determine primary and secondary styles
        sorted_styles = sorted(
            style_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_style = sorted_styles[0][0]
        primary_confidence = sorted_styles[0][1]
        
        secondary_style = None
        if len(sorted_styles) > 1 and sorted_styles[1][1] > 0.3:
            secondary_style = sorted_styles[1][0]
        
        # Determine color mood
        color_mood = self._classify_color_mood(
            design_dna, color_palette
        )
        
        # Determine layout density
        layout_density = self._classify_density(design_dna, layout_data)
        
        # Derive style parameters
        style_params = self._derive_style_parameters(
            primary_style, design_dna, style_indicators
        )
        
        # Detect special effects
        effects = self._detect_effects(design_dna)
        
        classification = StyleClassification(
            primary_style=primary_style,
            secondary_style=secondary_style,
            color_mood=color_mood,
            layout_density=layout_density,
            confidence=primary_confidence,
            border_radius=style_params["border_radius"],
            shadow_intensity=style_params["shadow_intensity"],
            typography_weight=style_params["typography_weight"],
            spacing_scale=style_params["spacing_scale"],
            uses_gradients=effects["gradients"],
            uses_glassmorphism=effects["glassmorphism"],
            is_dark_mode=effects["dark_mode"],
            has_illustrations=effects["illustrations"]
        )
        
        logger.info(
            f"🎨 Style classified: {primary_style.value} "
            f"(conf={primary_confidence:.2f}), "
            f"mood={color_mood.value}, "
            f"density={layout_density.value}"
        )
        
        return classification
    
    def _extract_style_indicators(
        self,
        design_dna: Dict[str, Any],
        color_palette: Optional[Dict[str, str]],
        layout_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract style indicators from all sources."""
        indicators = {
            "has_high_contrast": False,
            "has_low_contrast": False,
            "uses_bright_colors": False,
            "uses_muted_colors": False,
            "uses_dark_bg": False,
            "has_lots_of_whitespace": False,
            "has_dense_content": False,
            "uses_large_type": False,
            "uses_monospace": False,
            "uses_serif": False,
            "uses_geometric_shapes": False,
            "uses_organic_shapes": False,
            "has_rounded_corners": False,
            "uses_shadows": False,
            "uses_gradients": False,
            "has_illustrations": False,
            "is_image_heavy": False
        }
        
        # Extract from design_dna
        if design_dna:
            philosophy = design_dna.get("design_philosophy", {})
            style = philosophy.get("style", "").lower()
            
            # Style keywords
            if "minimal" in style:
                indicators["has_lots_of_whitespace"] = True
            if "bold" in style or "dramatic" in style:
                indicators["has_high_contrast"] = True
                indicators["uses_large_type"] = True
            if "playful" in style or "fun" in style:
                indicators["uses_bright_colors"] = True
                indicators["has_rounded_corners"] = True
            if "technical" in style or "developer" in style:
                indicators["uses_monospace"] = True
                indicators["uses_dark_bg"] = True
            if "editorial" in style or "magazine" in style:
                indicators["is_image_heavy"] = True
                indicators["uses_serif"] = True
            if "luxury" in style or "elegant" in style:
                indicators["uses_muted_colors"] = True
                indicators["uses_serif"] = True
            
            # Typography
            typography = design_dna.get("typography_personality", {})
            if isinstance(typography, dict):
                font_type = typography.get("font_type", "")
                if "mono" in font_type:
                    indicators["uses_monospace"] = True
                if "serif" in font_type and "sans" not in font_type:
                    indicators["uses_serif"] = True
                
                heading_style = typography.get("heading_style", "")
                if "bold" in heading_style or "black" in heading_style:
                    indicators["uses_large_type"] = True
            
            # Visual effects
            effects = design_dna.get("visual_effects", {})
            if isinstance(effects, dict):
                shadow = effects.get("shadow_style", "")
                if shadow and shadow != "flat" and shadow != "none":
                    indicators["uses_shadows"] = True
                
                gradients = effects.get("gradient_usage", "")
                if gradients and gradients != "none":
                    indicators["uses_gradients"] = True
            
            # Spacing
            spacing = design_dna.get("spacing_rhythm", {})
            if isinstance(spacing, dict):
                density = spacing.get("density", "")
                if density in ["spacious", "ultra-minimal"]:
                    indicators["has_lots_of_whitespace"] = True
                elif density in ["compact", "tight"]:
                    indicators["has_dense_content"] = True
        
        # Extract from color palette
        if color_palette:
            primary = color_palette.get("primary", "#000000").lower()
            # Check for dark backgrounds
            if self._is_dark_color(primary):
                indicators["uses_dark_bg"] = True
            # Check for bright/vibrant colors
            if self._is_vibrant_color(primary):
                indicators["uses_bright_colors"] = True
        
        return indicators
    
    def _score_styles(
        self,
        indicators: Dict[str, Any]
    ) -> Dict[DesignStyle, float]:
        """Score each design style based on indicators."""
        scores = {style: 0.0 for style in DesignStyle}
        
        # Minimal scoring
        if indicators["has_lots_of_whitespace"]:
            scores[DesignStyle.MINIMAL] += 0.4
        if not indicators["uses_gradients"]:
            scores[DesignStyle.MINIMAL] += 0.2
        if not indicators["has_dense_content"]:
            scores[DesignStyle.MINIMAL] += 0.2
        
        # Bold scoring
        if indicators["has_high_contrast"]:
            scores[DesignStyle.BOLD] += 0.3
        if indicators["uses_large_type"]:
            scores[DesignStyle.BOLD] += 0.3
        if indicators["uses_bright_colors"]:
            scores[DesignStyle.BOLD] += 0.2
        
        # Corporate scoring
        if not indicators["uses_bright_colors"]:
            scores[DesignStyle.CORPORATE] += 0.2
        if not indicators["has_rounded_corners"]:
            scores[DesignStyle.CORPORATE] += 0.2
        if indicators["uses_shadows"]:
            scores[DesignStyle.CORPORATE] += 0.2
        
        # Playful scoring
        if indicators["uses_bright_colors"]:
            scores[DesignStyle.PLAYFUL] += 0.3
        if indicators["has_rounded_corners"]:
            scores[DesignStyle.PLAYFUL] += 0.3
        if indicators["has_illustrations"]:
            scores[DesignStyle.PLAYFUL] += 0.2
        
        # Technical scoring
        if indicators["uses_monospace"]:
            scores[DesignStyle.TECHNICAL] += 0.4
        if indicators["uses_dark_bg"]:
            scores[DesignStyle.TECHNICAL] += 0.3
        
        # Editorial scoring
        if indicators["is_image_heavy"]:
            scores[DesignStyle.EDITORIAL] += 0.3
        if indicators["uses_serif"]:
            scores[DesignStyle.EDITORIAL] += 0.3
        
        # Luxurious scoring
        if indicators["uses_muted_colors"]:
            scores[DesignStyle.LUXURIOUS] += 0.3
        if indicators["uses_serif"]:
            scores[DesignStyle.LUXURIOUS] += 0.2
        if indicators["has_lots_of_whitespace"]:
            scores[DesignStyle.LUXURIOUS] += 0.2
        
        # Brutalist scoring
        if not indicators["uses_shadows"]:
            scores[DesignStyle.BRUTALIST] += 0.2
        if indicators["has_high_contrast"]:
            scores[DesignStyle.BRUTALIST] += 0.2
        if not indicators["has_rounded_corners"]:
            scores[DesignStyle.BRUTALIST] += 0.2
        
        # Normalize scores
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return scores
    
    def _classify_color_mood(
        self,
        design_dna: Dict[str, Any],
        color_palette: Optional[Dict[str, str]]
    ) -> ColorMood:
        """Classify the overall color mood."""
        if design_dna:
            color_psych = design_dna.get("color_psychology", {})
            if isinstance(color_psych, dict):
                mood = color_psych.get("overall_mood", "").lower()
                if mood in ["warm", "energetic", "passionate"]:
                    return ColorMood.WARM
                if mood in ["cool", "calm", "trustworthy"]:
                    return ColorMood.COOL
                if mood in ["vibrant", "playful", "exciting"]:
                    return ColorMood.VIBRANT
                if mood in ["muted", "sophisticated", "elegant"]:
                    return ColorMood.MUTED
        
        if color_palette:
            primary = color_palette.get("primary", "#000000")
            if self._is_dark_color(primary):
                return ColorMood.DARK
            if self._is_light_color(primary):
                return ColorMood.LIGHT
            if self._is_warm_color(primary):
                return ColorMood.WARM
            if self._is_cool_color(primary):
                return ColorMood.COOL
        
        return ColorMood.NEUTRAL
    
    def _classify_density(
        self,
        design_dna: Dict[str, Any],
        layout_data: Optional[Dict[str, Any]]
    ) -> LayoutDensity:
        """Classify the layout density."""
        if design_dna:
            spacing = design_dna.get("spacing_rhythm", {})
            if isinstance(spacing, dict):
                density = spacing.get("density", "").lower()
                if density in ["spacious", "ultra-minimal", "generous"]:
                    return LayoutDensity.SPARSE
                if density in ["compact", "tight", "dense"]:
                    return LayoutDensity.DENSE
        
        if layout_data:
            whitespace = layout_data.get("whitespace", {})
            if isinstance(whitespace, dict):
                density = whitespace.get("density", "").lower()
                if density in ["generous", "minimal"]:
                    return LayoutDensity.SPARSE
                if density in ["tight", "compact"]:
                    return LayoutDensity.DENSE
        
        return LayoutDensity.BALANCED
    
    def _derive_style_parameters(
        self,
        primary_style: DesignStyle,
        design_dna: Dict[str, Any],
        indicators: Dict[str, Any]
    ) -> Dict[str, str]:
        """Derive specific style parameters for template rendering."""
        params = {
            "border_radius": "md",
            "shadow_intensity": "subtle",
            "typography_weight": "medium",
            "spacing_scale": "normal"
        }
        
        # Style-specific defaults
        if primary_style == DesignStyle.MINIMAL:
            params["border_radius"] = "sm"
            params["shadow_intensity"] = "none"
            params["typography_weight"] = "light"
            params["spacing_scale"] = "spacious"
        
        elif primary_style == DesignStyle.BOLD:
            params["border_radius"] = "lg"
            params["shadow_intensity"] = "moderate"
            params["typography_weight"] = "bold"
            params["spacing_scale"] = "normal"
        
        elif primary_style == DesignStyle.CORPORATE:
            params["border_radius"] = "sm"
            params["shadow_intensity"] = "subtle"
            params["typography_weight"] = "regular"
            params["spacing_scale"] = "normal"
        
        elif primary_style == DesignStyle.PLAYFUL:
            params["border_radius"] = "lg"
            params["shadow_intensity"] = "moderate"
            params["typography_weight"] = "medium"
            params["spacing_scale"] = "relaxed"
        
        elif primary_style == DesignStyle.TECHNICAL:
            params["border_radius"] = "sm"
            params["shadow_intensity"] = "none"
            params["typography_weight"] = "regular"
            params["spacing_scale"] = "tight"
        
        elif primary_style == DesignStyle.EDITORIAL:
            params["border_radius"] = "none"
            params["shadow_intensity"] = "subtle"
            params["typography_weight"] = "regular"
            params["spacing_scale"] = "relaxed"
        
        elif primary_style == DesignStyle.LUXURIOUS:
            params["border_radius"] = "sm"
            params["shadow_intensity"] = "subtle"
            params["typography_weight"] = "light"
            params["spacing_scale"] = "spacious"
        
        elif primary_style == DesignStyle.BRUTALIST:
            params["border_radius"] = "none"
            params["shadow_intensity"] = "none"
            params["typography_weight"] = "bold"
            params["spacing_scale"] = "tight"
        
        # Override with design DNA if available
        if design_dna:
            effects = design_dna.get("visual_effects", {})
            if isinstance(effects, dict):
                shadow = effects.get("shadow_style", "")
                if shadow == "dramatic" or shadow == "prominent":
                    params["shadow_intensity"] = "dramatic"
                elif shadow == "neumorphic":
                    params["shadow_intensity"] = "neumorphic"
        
        return params
    
    def _detect_effects(
        self,
        design_dna: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Detect special visual effects."""
        effects = {
            "gradients": False,
            "glassmorphism": False,
            "dark_mode": False,
            "illustrations": False
        }
        
        if not design_dna:
            return effects
        
        visual_effects = design_dna.get("visual_effects", {})
        if isinstance(visual_effects, dict):
            gradient_usage = visual_effects.get("gradient_usage", "")
            if gradient_usage and gradient_usage != "none":
                effects["gradients"] = True
            
            blur_effects = visual_effects.get("blur_effects", "")
            if blur_effects and "glass" in blur_effects.lower():
                effects["glassmorphism"] = True
        
        color_psych = design_dna.get("color_psychology", {})
        if isinstance(color_psych, dict):
            mood = color_psych.get("overall_mood", "").lower()
            if "dark" in mood or mood in ["mysterious", "dramatic"]:
                effects["dark_mode"] = True
        
        return effects
    
    def _is_dark_color(self, hex_color: str) -> bool:
        """Check if a hex color is dark."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b)
            return luminance < 80
        except:
            return False
    
    def _is_light_color(self, hex_color: str) -> bool:
        """Check if a hex color is light."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b)
            return luminance > 200
        except:
            return False
    
    def _is_vibrant_color(self, hex_color: str) -> bool:
        """Check if a hex color is vibrant (high saturation)."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            saturation = (max_c - min_c) / max_c if max_c > 0 else 0
            return saturation > 0.7
        except:
            return False
    
    def _is_warm_color(self, hex_color: str) -> bool:
        """Check if a hex color is warm (red/orange/yellow)."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return r > b and r > 100
        except:
            return False
    
    def _is_cool_color(self, hex_color: str) -> bool:
        """Check if a hex color is cool (blue/green/purple)."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return b > r and b > 100
        except:
            return False


# Singleton instance
_classifier_instance: Optional[VisualStyleClassifier] = None


def get_style_classifier() -> VisualStyleClassifier:
    """Get or create the style classifier singleton."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = VisualStyleClassifier()
    return _classifier_instance


def classify_style(
    design_dna: Dict[str, Any],
    color_palette: Optional[Dict[str, str]] = None,
    layout_data: Optional[Dict[str, Any]] = None
) -> StyleClassification:
    """Convenience function to classify style."""
    classifier = get_style_classifier()
    return classifier.classify(design_dna, color_palette, layout_data)

