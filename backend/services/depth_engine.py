"""
Depth & Shadow Engine - Layer 2 of Design Framework Enhancement.

This module implements professional multi-layer shadow systems, elevation levels,
and depth effects for premium visual quality.

Key Features:
- 5 elevation levels (0-5) with proper shadow composition
- 3-layer shadow system (ambient, penumbra, umbra)
- Context-aware shadows (adapt to backgrounds)
- Neumorphism support for modern designs
- Colored shadows for vibrant styles
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)


class ElevationLevel(int, Enum):
    """Material Design-inspired elevation levels."""
    FLAT = 0       # No shadow (text on solid)
    RESTING = 1    # Cards, default state
    RAISED = 2     # Hover state, badges
    FLOATING = 3   # Modals, dropdowns
    PROMINENT = 4  # Primary CTAs, alerts
    MAXIMUM = 5    # Overlays, key elements


@dataclass
class ShadowLayer:
    """A single shadow layer."""
    x_offset: int
    y_offset: int
    blur_radius: int
    spread: int
    color: Tuple[int, int, int, int]  # RGBA
    blend_mode: str = "normal"  # normal, multiply, overlay


@dataclass
class ShadowComposition:
    """Multi-layer shadow composition."""
    ambient: ShadowLayer    # Soft, large spread
    penumbra: ShadowLayer   # Medium blur
    umbra: ShadowLayer      # Sharp, close
    
    def to_css(self) -> str:
        """Convert to CSS box-shadow string."""
        layers = [self.ambient, self.penumbra, self.umbra]
        shadow_strings = []
        
        for layer in layers:
            r, g, b, a = layer.color
            shadow_strings.append(
                f"{layer.x_offset}px {layer.y_offset}px {layer.blur_radius}px "
                f"{layer.spread}px rgba({r},{g},{b},{a/255:.2f})"
            )
        
        return ", ".join(shadow_strings)


class DepthEngine:
    """
    Creates professional shadow systems and depth effects.
    
    Implements Material Design 3.0-inspired elevation system with
    three-layer shadow composition for realistic depth.
    """
    
    def __init__(self, light_mode: bool = True):
        self.light_mode = light_mode
        
    def get_shadow_composition(
        self,
        elevation: ElevationLevel,
        design_style: str = "modern",
        accent_color: Optional[Tuple[int, int, int]] = None
    ) -> ShadowComposition:
        """
        Get shadow composition for an elevation level.
        
        Args:
            elevation: Elevation level (0-5)
            design_style: Design style (modern, neumorphic, flat, etc.)
            accent_color: Optional accent color for colored shadows
            
        Returns:
            ShadowComposition with three layers
        """
        if elevation == ElevationLevel.FLAT:
            return self._create_no_shadow()
        
        # Get base shadow parameters
        params = self._get_elevation_params(elevation)
        
        # Adjust for design style
        if design_style == "neumorphic":
            return self._create_neumorphic_shadow(params, accent_color)
        elif design_style == "long-shadow":
            return self._create_long_shadow(params, accent_color)
        elif design_style == "colored":
            return self._create_colored_shadow(params, accent_color)
        else:
            return self._create_standard_shadow(params)
    
    def apply_shadow_to_image(
        self,
        image: Image.Image,
        element_bounds: Tuple[int, int, int, int],
        shadow_comp: ShadowComposition,
        canvas_size: Optional[Tuple[int, int]] = None
    ) -> Image.Image:
        """
        Apply shadow composition to an image element.
        
        Args:
            image: Base image
            element_bounds: (x, y, width, height)
            shadow_comp: Shadow composition to apply
            canvas_size: Optional canvas size for proper layering
            
        Returns:
            Image with shadows applied
        """
        x, y, width, height = element_bounds
        
        if canvas_size:
            canvas_width, canvas_height = canvas_size
        else:
            canvas_width = image.width
            canvas_height = image.height
        
        # Create canvas with extra space for shadows
        max_blur = max(
            shadow_comp.ambient.blur_radius,
            shadow_comp.penumbra.blur_radius,
            shadow_comp.umbra.blur_radius
        )
        max_offset = max(
            abs(shadow_comp.ambient.y_offset),
            abs(shadow_comp.penumbra.y_offset),
            abs(shadow_comp.umbra.y_offset)
        )
        
        padding = max_blur + max_offset + 20
        
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Draw shadow layers (back to front)
        for layer in [shadow_comp.ambient, shadow_comp.penumbra, shadow_comp.umbra]:
            shadow_img = self._create_shadow_layer(
                width, height,
                layer.x_offset, layer.y_offset,
                layer.blur_radius, layer.color
            )
            
            # Position shadow
            shadow_x = x + layer.x_offset
            shadow_y = y + layer.y_offset
            
            # Composite onto canvas
            canvas = Image.alpha_composite(canvas, shadow_img if shadow_img.mode == 'RGBA' else shadow_img.convert('RGBA'))
        
        # Draw main element on top
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        canvas.paste(image, (x, y), image)
        
        return canvas
    
    def _get_elevation_params(self, elevation: ElevationLevel) -> Dict[str, Any]:
        """Get shadow parameters for elevation level."""
        # Material Design 3.0 inspired values
        params_map = {
            ElevationLevel.FLAT: {
                "ambient_blur": 0, "ambient_spread": 0, "ambient_alpha": 0,
                "penumbra_blur": 0, "penumbra_spread": 0, "penumbra_alpha": 0,
                "umbra_blur": 0, "umbra_offset": 0, "umbra_alpha": 0
            },
            ElevationLevel.RESTING: {
                "ambient_blur": 2, "ambient_spread": 1, "ambient_alpha": 40,
                "penumbra_blur": 5, "penumbra_spread": 0, "penumbra_alpha": 60,
                "umbra_blur": 2, "umbra_offset": 1, "umbra_alpha": 80
            },
            ElevationLevel.RAISED: {
                "ambient_blur": 4, "ambient_spread": 2, "ambient_alpha": 50,
                "penumbra_blur": 8, "penumbra_spread": 0, "penumbra_alpha": 70,
                "umbra_blur": 3, "umbra_offset": 2, "umbra_alpha": 90
            },
            ElevationLevel.FLOATING: {
                "ambient_blur": 8, "ambient_spread": 4, "ambient_alpha": 60,
                "penumbra_blur": 16, "penumbra_spread": 0, "penumbra_alpha": 80,
                "umbra_blur": 4, "umbra_offset": 4, "umbra_alpha": 100
            },
            ElevationLevel.PROMINENT: {
                "ambient_blur": 12, "ambient_spread": 6, "ambient_alpha": 70,
                "penumbra_blur": 24, "penumbra_spread": 0, "penumbra_alpha": 90,
                "umbra_blur": 6, "umbra_offset": 6, "umbra_alpha": 110
            },
            ElevationLevel.MAXIMUM: {
                "ambient_blur": 16, "ambient_spread": 8, "ambient_alpha": 80,
                "penumbra_blur": 32, "penumbra_spread": 0, "penumbra_alpha": 100,
                "umbra_blur": 8, "umbra_offset": 8, "umbra_alpha": 120
            }
        }
        
        return params_map.get(elevation, params_map[ElevationLevel.RESTING])
    
    def _create_no_shadow(self) -> ShadowComposition:
        """Create empty shadow composition."""
        no_shadow = ShadowLayer(0, 0, 0, 0, (0, 0, 0, 0))
        return ShadowComposition(no_shadow, no_shadow, no_shadow)
    
    def _create_standard_shadow(self, params: Dict[str, Any]) -> ShadowComposition:
        """Create standard three-layer shadow."""
        # Shadow color (black for light mode, colored for dark mode)
        base_color = (0, 0, 0) if self.light_mode else (20, 20, 40)
        
        ambient = ShadowLayer(
            x_offset=0,
            y_offset=params["ambient_blur"] // 2,
            blur_radius=params["ambient_blur"],
            spread=params["ambient_spread"],
            color=(*base_color, params["ambient_alpha"])
        )
        
        penumbra = ShadowLayer(
            x_offset=0,
            y_offset=params["penumbra_blur"] // 4,
            blur_radius=params["penumbra_blur"],
            spread=params["penumbra_spread"],
            color=(*base_color, params["penumbra_alpha"])
        )
        
        umbra = ShadowLayer(
            x_offset=0,
            y_offset=params["umbra_offset"],
            blur_radius=params["umbra_blur"],
            spread=0,
            color=(*base_color, params["umbra_alpha"])
        )
        
        return ShadowComposition(ambient, penumbra, umbra)
    
    def _create_neumorphic_shadow(
        self,
        params: Dict[str, Any],
        accent_color: Optional[Tuple[int, int, int]]
    ) -> ShadowComposition:
        """
        Create neumorphic (soft UI) shadows.
        
        Two shadows: light (top-left) and dark (bottom-right)
        """
        bg_color = (240, 240, 245) if self.light_mode else (30, 30, 35)
        
        # Light shadow (top-left)
        light = ShadowLayer(
            x_offset=-params["umbra_offset"],
            y_offset=-params["umbra_offset"],
            blur_radius=params["penumbra_blur"],
            spread=0,
            color=(*[min(255, c + 15) for c in bg_color], 100)
        )
        
        # Dark shadow (bottom-right)
        dark = ShadowLayer(
            x_offset=params["umbra_offset"],
            y_offset=params["umbra_offset"],
            blur_radius=params["penumbra_blur"],
            spread=0,
            color=(*[max(0, c - 15) for c in bg_color], 100)
        )
        
        # Ambient (subtle)
        ambient = ShadowLayer(
            x_offset=0,
            y_offset=0,
            blur_radius=params["ambient_blur"],
            spread=0,
            color=(0, 0, 0, 20)
        )
        
        return ShadowComposition(ambient, light, dark)
    
    def _create_long_shadow(
        self,
        params: Dict[str, Any],
        accent_color: Optional[Tuple[int, int, int]]
    ) -> ShadowComposition:
        """Create long shadow (flat/material design style)."""
        # Long shadow at 45-degree angle
        length = params["umbra_offset"] * 3
        
        long_shadow = ShadowLayer(
            x_offset=length,
            y_offset=length,
            blur_radius=0,  # Sharp
            spread=0,
            color=(0, 0, 0, 60)
        )
        
        # Soft ambient
        ambient = ShadowLayer(
            x_offset=0,
            y_offset=params["ambient_blur"],
            blur_radius=params["ambient_blur"],
            spread=0,
            color=(0, 0, 0, 30)
        )
        
        return ShadowComposition(ambient, long_shadow, long_shadow)
    
    def _create_colored_shadow(
        self,
        params: Dict[str, Any],
        accent_color: Optional[Tuple[int, int, int]]
    ) -> ShadowComposition:
        """Create colored shadows (vibrant, modern style)."""
        if not accent_color:
            accent_color = (59, 130, 246)  # Default blue
        
        # Darken accent color for shadow
        shadow_color = tuple(int(c * 0.6) for c in accent_color)
        
        ambient = ShadowLayer(
            x_offset=0,
            y_offset=params["ambient_blur"],
            blur_radius=params["ambient_blur"],
            spread=params["ambient_spread"],
            color=(*shadow_color, params["ambient_alpha"])
        )
        
        penumbra = ShadowLayer(
            x_offset=0,
            y_offset=params["penumbra_blur"] // 4,
            blur_radius=params["penumbra_blur"],
            spread=0,
            color=(*shadow_color, params["penumbra_alpha"])
        )
        
        umbra = ShadowLayer(
            x_offset=0,
            y_offset=params["umbra_offset"],
            blur_radius=params["umbra_blur"],
            spread=0,
            color=(*shadow_color, params["umbra_alpha"])
        )
        
        return ShadowComposition(ambient, penumbra, umbra)
    
    def _create_shadow_layer(
        self,
        width: int,
        height: int,
        x_offset: int,
        y_offset: int,
        blur_radius: int,
        color: Tuple[int, int, int, int]
    ) -> Image.Image:
        """Create a single shadow layer as an image."""
        # Add padding for blur
        padding = blur_radius * 2 + abs(x_offset) + abs(y_offset) + 10
        
        # Create shadow canvas
        shadow_width = width + padding * 2
        shadow_height = height + padding * 2
        shadow = Image.new('RGBA', (shadow_width, shadow_height), (0, 0, 0, 0))
        
        # Draw rectangle
        draw = ImageDraw.Draw(shadow)
        rect_x = padding + x_offset
        rect_y = padding + y_offset
        draw.rectangle(
            [(rect_x, rect_y), (rect_x + width, rect_y + height)],
            fill=color
        )
        
        # Apply blur
        if blur_radius > 0:
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        return shadow


def create_inner_shadow(
    image: Image.Image,
    element_bounds: Tuple[int, int, int, int],
    depth: int = 2
) -> Image.Image:
    """
    Create inner shadow effect (for recessed elements).
    
    Args:
        image: Base image
        element_bounds: (x, y, width, height)
        depth: Shadow depth in pixels
        
    Returns:
        Image with inner shadow
    """
    x, y, width, height = element_bounds
    
    # Create mask for element
    mask = Image.new('L', (width, height), 255)
    
    # Create shadow gradient (top-left to bottom-right)
    shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    # Top shadow
    for i in range(depth):
        alpha = int(50 * (1 - i / depth))
        draw.line([(0, i), (width, i)], fill=(0, 0, 0, alpha))
    
    # Left shadow
    for i in range(depth):
        alpha = int(50 * (1 - i / depth))
        draw.line([(i, 0), (i, height)], fill=(0, 0, 0, alpha))
    
    # Paste onto image
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    image.paste(shadow, (x, y), shadow)
    
    return image


def create_glow_effect(
    image: Image.Image,
    element_bounds: Tuple[int, int, int, int],
    glow_color: Tuple[int, int, int],
    intensity: int = 20
) -> Image.Image:
    """
    Create glow effect around element.
    
    Args:
        image: Base image
        element_bounds: (x, y, width, height)
        glow_color: RGB color for glow
        intensity: Glow intensity (blur radius)
        
    Returns:
        Image with glow
    """
    x, y, width, height = element_bounds
    
    # Create glow layer
    padding = intensity * 2
    glow_width = width + padding * 2
    glow_height = height + padding * 2
    glow = Image.new('RGBA', (glow_width, glow_height), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(glow)
    draw.rectangle(
        [(padding, padding), (padding + width, padding + height)],
        fill=(*glow_color, 150)
    )
    
    # Blur for glow effect
    glow = glow.filter(ImageFilter.GaussianBlur(radius=intensity))
    
    # Composite onto image
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    glow_x = x - padding
    glow_y = y - padding
    image = Image.alpha_composite(image, glow)
    
    return image


# Example usage
if __name__ == "__main__":
    # Test shadow generation
    engine = DepthEngine(light_mode=True)
    
    # Test different elevation levels
    for level in [ElevationLevel.RESTING, ElevationLevel.RAISED, ElevationLevel.FLOATING]:
        shadow = engine.get_shadow_composition(level, "modern")
        print(f"\n{level.name} Shadow:")
        print(f"  CSS: {shadow.to_css()}")
    
    # Test colored shadow
    shadow = engine.get_shadow_composition(
        ElevationLevel.PROMINENT,
        "colored",
        accent_color=(255, 100, 100)
    )
    print(f"\nColored Shadow CSS: {shadow.to_css()}")
