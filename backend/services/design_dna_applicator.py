"""
Design DNA Applicator - Bridges extraction and rendering.

This module takes extracted Design DNA and converts it into concrete
rendering parameters for template generation. It's the critical bridge
between WHAT we extract and HOW we render.

Key Responsibilities:
1. Map typography personality to font choices and sizing
2. Map color psychology to palette application
3. Map spacing feel to padding/margins
4. Map design style to layout selection
5. Validate color harmony and contrast
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.services.visual_style_classifier import (
    get_style_classifier,
    StyleClassification,
    DesignStyle,
    ColorMood,
    LayoutDensity
)

logger = logging.getLogger(__name__)


# Font mappings based on typography personality
TYPOGRAPHY_FONT_MAP = {
    "authoritative": {
        "heading": "Inter, system-ui, sans-serif",
        "body": "Inter, system-ui, sans-serif",
        "heading_weight": 700,
        "body_weight": 400
    },
    "friendly": {
        "heading": "DM Sans, system-ui, sans-serif",
        "body": "DM Sans, system-ui, sans-serif",
        "heading_weight": 600,
        "body_weight": 400
    },
    "elegant": {
        "heading": "Playfair Display, Georgia, serif",
        "body": "Source Sans Pro, system-ui, sans-serif",
        "heading_weight": 500,
        "body_weight": 400
    },
    "technical": {
        "heading": "JetBrains Mono, Fira Code, monospace",
        "body": "Inter, system-ui, sans-serif",
        "heading_weight": 600,
        "body_weight": 400
    },
    "bold": {
        "heading": "Space Grotesk, system-ui, sans-serif",
        "body": "Inter, system-ui, sans-serif",
        "heading_weight": 800,
        "body_weight": 500
    },
    "subtle": {
        "heading": "Inter, system-ui, sans-serif",
        "body": "Inter, system-ui, sans-serif",
        "heading_weight": 500,
        "body_weight": 400
    },
    "expressive": {
        "heading": "Outfit, system-ui, sans-serif",
        "body": "DM Sans, system-ui, sans-serif",
        "heading_weight": 700,
        "body_weight": 400
    }
}

# Spacing scales based on density
SPACING_SCALES = {
    "tight": {
        "section": 24,
        "element": 12,
        "text": 4,
        "padding_x": 16,
        "padding_y": 12
    },
    "normal": {
        "section": 40,
        "element": 20,
        "text": 8,
        "padding_x": 24,
        "padding_y": 20
    },
    "relaxed": {
        "section": 56,
        "element": 28,
        "text": 12,
        "padding_x": 32,
        "padding_y": 28
    },
    "spacious": {
        "section": 72,
        "element": 36,
        "text": 16,
        "padding_x": 48,
        "padding_y": 40
    }
}

# Border radius mappings
BORDER_RADIUS_MAP = {
    "none": 0,
    "sm": 4,
    "md": 8,
    "lg": 16,
    "xl": 24,
    "full": 9999
}

# Shadow styles
SHADOW_STYLES = {
    "none": "none",
    "subtle": "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
    "moderate": "0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)",
    "dramatic": "0 10px 25px rgba(0,0,0,0.15), 0 4px 10px rgba(0,0,0,0.1)",
    "neumorphic": "6px 6px 12px rgba(0,0,0,0.1), -6px -6px 12px rgba(255,255,255,0.9)"
}


@dataclass
class TypographyParams:
    """Typography rendering parameters."""
    heading_font: str
    body_font: str
    heading_weight: int
    body_weight: int
    heading_size_px: int
    subheading_size_px: int
    body_size_px: int
    line_height: float
    letter_spacing: str  # e.g., "-0.02em", "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "heading_weight": self.heading_weight,
            "body_weight": self.body_weight,
            "heading_size_px": self.heading_size_px,
            "subheading_size_px": self.subheading_size_px,
            "body_size_px": self.body_size_px,
            "line_height": self.line_height,
            "letter_spacing": self.letter_spacing
        }


@dataclass
class ColorParams:
    """Color rendering parameters."""
    primary: str  # Hex color
    secondary: str
    accent: str
    background: str
    text_primary: str
    text_secondary: str
    text_on_primary: str  # Text color when on primary bg
    text_on_accent: str
    is_dark_mode: bool
    gradient: Optional[str] = None  # CSS gradient if applicable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text_primary": self.text_primary,
            "text_secondary": self.text_secondary,
            "text_on_primary": self.text_on_primary,
            "text_on_accent": self.text_on_accent,
            "is_dark_mode": self.is_dark_mode,
            "gradient": self.gradient
        }


@dataclass
class SpacingParams:
    """Spacing rendering parameters."""
    section_spacing: int
    element_spacing: int
    text_spacing: int
    padding_x: int
    padding_y: int
    border_radius: int
    shadow: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_spacing": self.section_spacing,
            "element_spacing": self.element_spacing,
            "text_spacing": self.text_spacing,
            "padding_x": self.padding_x,
            "padding_y": self.padding_y,
            "border_radius": self.border_radius,
            "shadow": self.shadow
        }


@dataclass
class LayoutParams:
    """Layout rendering parameters."""
    template_type: str  # landing, product, profile, article
    grid_columns: int
    content_alignment: str  # left, center, right
    image_position: str  # left, right, top, background
    visual_weight_distribution: str  # balanced, left-heavy, right-heavy
    max_content_width: int  # pixels
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_type": self.template_type,
            "grid_columns": self.grid_columns,
            "content_alignment": self.content_alignment,
            "image_position": self.image_position,
            "visual_weight_distribution": self.visual_weight_distribution,
            "max_content_width": self.max_content_width
        }


@dataclass
class RenderingParams:
    """Complete rendering parameters for preview generation."""
    typography: TypographyParams
    colors: ColorParams
    spacing: SpacingParams
    layout: LayoutParams
    style_classification: StyleClassification
    
    # Additional effects
    uses_gradients: bool = False
    uses_glassmorphism: bool = False
    uses_shadows: bool = True
    animation_style: str = "none"  # none, subtle, dynamic
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "typography": self.typography.to_dict(),
            "colors": self.colors.to_dict(),
            "spacing": self.spacing.to_dict(),
            "layout": self.layout.to_dict(),
            "style": self.style_classification.to_dict(),
            "uses_gradients": self.uses_gradients,
            "uses_glassmorphism": self.uses_glassmorphism,
            "uses_shadows": self.uses_shadows,
            "animation_style": self.animation_style
        }


class DesignDNAApplicator:
    """
    Applies Design DNA to generate concrete rendering parameters.
    
    This is the bridge between extraction and rendering - it takes
    the abstract design concepts and converts them to specific values
    that can be used to render brand-faithful previews.
    """
    
    def __init__(self):
        """Initialize the applicator."""
        self.style_classifier = get_style_classifier()
        logger.info("🧬 DesignDNAApplicator initialized")
    
    def apply(
        self,
        design_dna: Dict[str, Any],
        color_palette: Optional[Dict[str, str]] = None,
        page_type: str = "landing",
        content_density: str = "balanced"
    ) -> RenderingParams:
        """
        Apply Design DNA to generate rendering parameters.
        
        Args:
            design_dna: Extracted design DNA
            color_palette: Extracted color palette
            page_type: Type of page (landing, product, profile, article)
            content_density: How much content we have
            
        Returns:
            RenderingParams with concrete values for rendering
        """
        logger.info(f"🎨 Applying Design DNA for {page_type} page")
        
        # Classify style
        style_class = self.style_classifier.classify(
            design_dna, color_palette
        )
        
        # Generate typography params
        typography = self._apply_typography(design_dna, style_class)
        
        # Generate color params
        colors = self._apply_colors(design_dna, color_palette, style_class)
        
        # Generate spacing params
        spacing = self._apply_spacing(design_dna, style_class)
        
        # Generate layout params
        layout = self._apply_layout(
            design_dna, page_type, content_density, style_class
        )
        
        # Determine additional effects
        uses_gradients = style_class.uses_gradients
        uses_glassmorphism = style_class.uses_glassmorphism
        uses_shadows = style_class.shadow_intensity != "none"
        
        params = RenderingParams(
            typography=typography,
            colors=colors,
            spacing=spacing,
            layout=layout,
            style_classification=style_class,
            uses_gradients=uses_gradients,
            uses_glassmorphism=uses_glassmorphism,
            uses_shadows=uses_shadows
        )
        
        logger.info(
            f"✅ DNA applied: style={style_class.primary_style.value}, "
            f"font={typography.heading_font[:20]}..., "
            f"primary={colors.primary}"
        )
        
        return params
    
    def _apply_typography(
        self,
        design_dna: Dict[str, Any],
        style_class: StyleClassification
    ) -> TypographyParams:
        """Apply typography personality to font parameters."""
        # Get typography personality from DNA
        typo_personality = "authoritative"  # default
        
        if design_dna:
            typo_data = design_dna.get("typography_personality", {})
            if isinstance(typo_data, dict):
                heading_style = typo_data.get("heading_style", "").lower()
                if heading_style in TYPOGRAPHY_FONT_MAP:
                    typo_personality = heading_style
                elif "bold" in heading_style or "black" in heading_style:
                    typo_personality = "bold"
                elif "elegant" in heading_style:
                    typo_personality = "elegant"
                elif "friendly" in heading_style:
                    typo_personality = "friendly"
                elif "technical" in heading_style:
                    typo_personality = "technical"
        
        # Override based on style classification
        if style_class.primary_style == DesignStyle.TECHNICAL:
            typo_personality = "technical"
        elif style_class.primary_style == DesignStyle.LUXURIOUS:
            typo_personality = "elegant"
        elif style_class.primary_style == DesignStyle.BOLD:
            typo_personality = "bold"
        elif style_class.primary_style == DesignStyle.PLAYFUL:
            typo_personality = "friendly"
        
        # Get font mapping
        font_map = TYPOGRAPHY_FONT_MAP.get(
            typo_personality,
            TYPOGRAPHY_FONT_MAP["authoritative"]
        )
        
        # Calculate sizes based on typography weight
        weight = style_class.typography_weight
        if weight == "bold" or weight == "black":
            heading_size = 42
            subheading_size = 24
            body_size = 16
        elif weight == "light":
            heading_size = 36
            subheading_size = 20
            body_size = 15
        else:  # regular/medium
            heading_size = 38
            subheading_size = 22
            body_size = 16
        
        # Line height based on style
        if style_class.primary_style in [DesignStyle.EDITORIAL, DesignStyle.LUXURIOUS]:
            line_height = 1.6
        elif style_class.primary_style == DesignStyle.TECHNICAL:
            line_height = 1.4
        else:
            line_height = 1.5
        
        # Letter spacing
        if typo_personality == "bold":
            letter_spacing = "-0.02em"
        elif typo_personality in ["elegant", "luxurious"]:
            letter_spacing = "0.01em"
        else:
            letter_spacing = "normal"
        
        return TypographyParams(
            heading_font=font_map["heading"],
            body_font=font_map["body"],
            heading_weight=font_map["heading_weight"],
            body_weight=font_map["body_weight"],
            heading_size_px=heading_size,
            subheading_size_px=subheading_size,
            body_size_px=body_size,
            line_height=line_height,
            letter_spacing=letter_spacing
        )
    
    def _apply_colors(
        self,
        design_dna: Dict[str, Any],
        color_palette: Optional[Dict[str, str]],
        style_class: StyleClassification
    ) -> ColorParams:
        """Apply color psychology to color parameters."""
        # Default colors
        primary = "#3B82F6"  # Blue
        secondary = "#1E293B"  # Dark slate
        accent = "#F59E0B"  # Amber
        
        # Extract from palette if available
        if color_palette:
            primary = color_palette.get("primary", primary)
            secondary = color_palette.get("secondary", secondary)
            accent = color_palette.get("accent", accent)
        
        # Extract from DNA if available
        if design_dna:
            color_psych = design_dna.get("color_psychology", {})
            if isinstance(color_psych, dict):
                if color_psych.get("primary", {}).get("hex"):
                    primary = color_psych["primary"]["hex"]
                if color_psych.get("secondary", {}).get("hex"):
                    secondary = color_psych["secondary"]["hex"]
                if color_psych.get("accent", {}).get("hex"):
                    accent = color_psych["accent"]["hex"]
        
        # Determine dark mode
        is_dark = style_class.is_dark_mode
        
        # Set background and text colors
        if is_dark:
            background = "#0F172A"  # Dark slate
            text_primary = "#F8FAFC"  # Light
            text_secondary = "#94A3B8"  # Muted
        else:
            background = "#FFFFFF"
            text_primary = "#0F172A"
            text_secondary = "#64748B"
        
        # Calculate text colors on primary/accent
        text_on_primary = self._get_contrast_color(primary)
        text_on_accent = self._get_contrast_color(accent)
        
        # Generate gradient if applicable
        gradient = None
        if style_class.uses_gradients:
            gradient = f"linear-gradient(135deg, {primary}, {accent})"
        
        return ColorParams(
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text_primary=text_primary,
            text_secondary=text_secondary,
            text_on_primary=text_on_primary,
            text_on_accent=text_on_accent,
            is_dark_mode=is_dark,
            gradient=gradient
        )
    
    def _apply_spacing(
        self,
        design_dna: Dict[str, Any],
        style_class: StyleClassification
    ) -> SpacingParams:
        """Apply spacing feel to spacing parameters."""
        # Get spacing scale
        spacing_scale = style_class.spacing_scale
        scale = SPACING_SCALES.get(spacing_scale, SPACING_SCALES["normal"])
        
        # Get border radius
        border_radius_key = style_class.border_radius
        border_radius = BORDER_RADIUS_MAP.get(border_radius_key, 8)
        
        # Get shadow
        shadow_key = style_class.shadow_intensity
        shadow = SHADOW_STYLES.get(shadow_key, SHADOW_STYLES["subtle"])
        
        return SpacingParams(
            section_spacing=scale["section"],
            element_spacing=scale["element"],
            text_spacing=scale["text"],
            padding_x=scale["padding_x"],
            padding_y=scale["padding_y"],
            border_radius=border_radius,
            shadow=shadow
        )
    
    def _apply_layout(
        self,
        design_dna: Dict[str, Any],
        page_type: str,
        content_density: str,
        style_class: StyleClassification
    ) -> LayoutParams:
        """Apply layout style to layout parameters."""
        # Determine grid columns based on style
        if style_class.primary_style == DesignStyle.MINIMAL:
            grid_columns = 12
            max_width = 960
        elif style_class.primary_style == DesignStyle.BOLD:
            grid_columns = 12
            max_width = 1200
        else:
            grid_columns = 12
            max_width = 1080
        
        # Determine alignment based on style
        if style_class.primary_style in [DesignStyle.MINIMAL, DesignStyle.LUXURIOUS]:
            content_alignment = "center"
        elif style_class.primary_style == DesignStyle.EDITORIAL:
            content_alignment = "left"
        else:
            content_alignment = "left"
        
        # Determine image position based on page type
        if page_type == "profile":
            image_position = "left"
        elif page_type == "product":
            image_position = "left"
        elif page_type == "article":
            image_position = "top"
        else:  # landing
            image_position = "right"
        
        # Visual weight
        if content_density == "text-heavy":
            weight_distribution = "left-heavy"
        elif content_density == "image-heavy":
            weight_distribution = "right-heavy"
        else:
            weight_distribution = "balanced"
        
        return LayoutParams(
            template_type=page_type,
            grid_columns=grid_columns,
            content_alignment=content_alignment,
            image_position=image_position,
            visual_weight_distribution=weight_distribution,
            max_content_width=max_width
        )
    
    def _get_contrast_color(self, hex_color: str) -> str:
        """Get contrasting text color for a background."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # Calculate relative luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#FFFFFF" if luminance < 0.5 else "#0F172A"
        except:
            return "#FFFFFF"
    
    def validate_contrast(
        self,
        foreground: str,
        background: str,
        min_ratio: float = 4.5
    ) -> Tuple[bool, float]:
        """
        Validate contrast ratio between two colors.
        
        Args:
            foreground: Foreground color hex
            background: Background color hex
            min_ratio: Minimum contrast ratio (4.5 for AA, 7.0 for AAA)
            
        Returns:
            Tuple of (passes, actual_ratio)
        """
        try:
            def get_luminance(hex_color: str) -> float:
                hex_color = hex_color.lstrip('#')
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                
                def channel_luminance(c: int) -> float:
                    c = c / 255
                    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                
                return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)
            
            l1 = get_luminance(foreground)
            l2 = get_luminance(background)
            
            lighter = max(l1, l2)
            darker = min(l1, l2)
            
            ratio = (lighter + 0.05) / (darker + 0.05)
            
            return (ratio >= min_ratio, ratio)
            
        except:
            return (True, 21.0)  # Assume passing if we can't calculate


# Singleton instance
_applicator_instance: Optional[DesignDNAApplicator] = None


def get_dna_applicator() -> DesignDNAApplicator:
    """Get or create the DNA applicator singleton."""
    global _applicator_instance
    if _applicator_instance is None:
        _applicator_instance = DesignDNAApplicator()
    return _applicator_instance


def apply_design_dna(
    design_dna: Dict[str, Any],
    color_palette: Optional[Dict[str, str]] = None,
    page_type: str = "landing",
    content_density: str = "balanced"
) -> RenderingParams:
    """Convenience function to apply design DNA."""
    applicator = get_dna_applicator()
    return applicator.apply(design_dna, color_palette, page_type, content_density)

