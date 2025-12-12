"""
Adaptive Template Engine.

Generates dynamic preview compositions based on Design DNA.
Instead of fixed templates, this engine adapts to the design philosophy
of each website, creating unique previews that honor the original design.

Key Features:
- Dynamic composition selection based on design philosophy
- Adaptive typography application
- Intelligent color and gradient usage
- Visual effects based on brand personality
- Layout rhythm from spatial intelligence
"""

import logging
import math
from io import BytesIO
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from backend.services.design_dna_extractor import DesignDNA
from backend.services.typography_intelligence import (
    TypographyConfig, 
    get_typography_config,
    get_pillow_font_path,
    calculate_adaptive_font_size,
    get_optimal_line_breaks,
    get_text_shadow_params
)
from backend.services.color_psychology import (
    ColorConfig,
    get_color_config,
    hex_to_rgb,
    rgb_to_hex,
    lighten_color,
    darken_color,
    get_optimal_text_color,
    generate_gradient_colors,
    get_contrast_ratio
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630


# =============================================================================
# COMPOSITION STYLES
# =============================================================================

class CompositionStyle:
    """Base class for composition styles."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        """Get layout zones (x, y, w, h) for content placement."""
        raise NotImplementedError


class MinimalLuxuryComposition(CompositionStyle):
    """Minimalist luxury: generous whitespace, centered content, refined."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        padding = int(width * 0.12)  # 12% padding = luxurious
        return {
            "logo": (padding, padding, 80, 80),
            "headline": (padding, int(height * 0.35), width - padding * 2, int(height * 0.3)),
            "subtitle": (padding, int(height * 0.55), width - padding * 2, int(height * 0.15)),
            "proof": (padding, height - padding - 40, width - padding * 2, 40),
            "accent_bar": (0, height - 6, width, 6)
        }


class BoldExpressiveComposition(CompositionStyle):
    """Bold expressive: large headlines, dynamic angles, high contrast."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        padding = int(width * 0.06)  # Tighter padding
        return {
            "logo": (padding, padding, 100, 100),
            "headline": (padding, int(height * 0.25), width - padding * 2, int(height * 0.4)),
            "subtitle": (padding, int(height * 0.6), width - padding * 2, int(height * 0.15)),
            "proof": (width - padding - 250, padding, 250, 50),
            "accent_bar": (0, 0, 12, height)  # Side bar instead of bottom
        }


class ProfessionalCleanComposition(CompositionStyle):
    """Professional clean: balanced, trustworthy, corporate."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        padding = int(width * 0.07)
        return {
            "logo": (padding, padding, 72, 72),
            "headline": (padding, int(height * 0.30), width - padding * 2, int(height * 0.25)),
            "subtitle": (padding, int(height * 0.52), width - padding * 2, int(height * 0.12)),
            "description": (padding, int(height * 0.64), int(width * 0.6), int(height * 0.15)),
            "proof": (padding, height - padding - 36, width - padding * 2, 36),
            "accent_bar": (0, 0, width, 8)
        }


class EditorialCreativeComposition(CompositionStyle):
    """Editorial creative: magazine-style, asymmetric, artistic."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        padding = int(width * 0.08)
        return {
            "logo": (padding, padding, 64, 64),
            "headline": (padding, int(height * 0.20), int(width * 0.7), int(height * 0.35)),
            "subtitle": (padding, int(height * 0.52), int(width * 0.6), int(height * 0.12)),
            "image_zone": (int(width * 0.65), int(height * 0.15), int(width * 0.3), int(height * 0.5)),
            "proof": (padding, height - padding - 40, int(width * 0.5), 40),
            "accent_bar": (0, height - 4, int(width * 0.4), 4)
        }


class BrutalistStarkComposition(CompositionStyle):
    """Brutalist stark: harsh, minimal decoration, raw typography."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        padding = int(width * 0.05)
        return {
            "headline": (padding, int(height * 0.15), width - padding * 2, int(height * 0.5)),
            "subtitle": (padding, int(height * 0.60), width - padding * 2, int(height * 0.15)),
            "proof": (padding, height - padding - 30, width - padding * 2, 30),
            # No logo zone, no accent bar - brutalist
        }


class OrganicNaturalComposition(CompositionStyle):
    """Organic natural: flowing, soft, nature-inspired."""
    
    @staticmethod
    def get_layout_zones(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
        padding = int(width * 0.1)
        return {
            "logo": (padding, padding, 70, 70),
            "headline": (padding, int(height * 0.30), width - padding * 2, int(height * 0.28)),
            "subtitle": (padding, int(height * 0.55), width - padding * 2, int(height * 0.12)),
            "proof": (int(width * 0.3), height - padding - 35, int(width * 0.4), 35),  # Centered
            "accent_bar": (int(width * 0.35), height - 6, int(width * 0.3), 6)  # Centered bar
        }


# Map design styles to compositions
COMPOSITION_MAP = {
    "minimal-luxury": MinimalLuxuryComposition,
    "bold-expressive": BoldExpressiveComposition,
    "professional-clean": ProfessionalCleanComposition,
    "editorial-creative": EditorialCreativeComposition,
    "brutalist-stark": BrutalistStarkComposition,
    "organic-natural": OrganicNaturalComposition,
    "adaptive-balanced": ProfessionalCleanComposition  # Default
}


# =============================================================================
# VISUAL EFFECTS
# =============================================================================

def apply_gradient_background(
    image: Image.Image,
    colors: List[Tuple[int, int, int]],
    angle: int = 135,
    style: str = "linear"
) -> Image.Image:
    """Apply gradient background to image."""
    width, height = image.size
    draw = ImageDraw.Draw(image)
    
    if len(colors) < 2:
        colors = [colors[0], darken_color(colors[0], 0.3)]
    
    if style == "linear":
        # Calculate gradient direction
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        for y in range(height):
            for x in range(width):
                # Calculate position along gradient axis
                t = (x * cos_a + y * sin_a) / (width * abs(cos_a) + height * abs(sin_a))
                t = max(0, min(1, t))
                
                # Interpolate color
                if len(colors) == 2:
                    r = int(colors[0][0] * (1 - t) + colors[1][0] * t)
                    g = int(colors[0][1] * (1 - t) + colors[1][1] * t)
                    b = int(colors[0][2] * (1 - t) + colors[1][2] * t)
                else:
                    # Multi-stop gradient
                    idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
                    local_t = (t * (len(colors) - 1)) - idx
                    r = int(colors[idx][0] * (1 - local_t) + colors[idx + 1][0] * local_t)
                    g = int(colors[idx][1] * (1 - local_t) + colors[idx + 1][1] * local_t)
                    b = int(colors[idx][2] * (1 - local_t) + colors[idx + 1][2] * local_t)
                
                draw.point((x, y), fill=(r, g, b))
    
    elif style == "radial":
        cx, cy = width // 2, height // 2
        max_dist = math.sqrt(cx**2 + cy**2)
        
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                t = min(dist / max_dist, 1.0)
                
                r = int(colors[0][0] * (1 - t) + colors[-1][0] * t)
                g = int(colors[0][1] * (1 - t) + colors[-1][1] * t)
                b = int(colors[0][2] * (1 - t) + colors[-1][2] * t)
                
                draw.point((x, y), fill=(r, g, b))
    
    return image


def apply_noise_texture(image: Image.Image, intensity: float = 0.03) -> Image.Image:
    """Apply subtle noise texture for sophisticated look."""
    import random
    
    pixels = image.load()
    width, height = image.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y][:3]
            
            noise = int((random.random() - 0.5) * 255 * intensity)
            
            r = max(0, min(255, r + noise))
            g = max(0, min(255, g + noise))
            b = max(0, min(255, b + noise))
            
            pixels[x, y] = (r, g, b)
    
    return image


def apply_vignette(image: Image.Image, intensity: float = 0.3) -> Image.Image:
    """Apply vignette effect for depth."""
    width, height = image.size
    
    # Create radial gradient mask
    mask = Image.new('L', (width, height), 255)
    mask_draw = ImageDraw.Draw(mask)
    
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt(cx**2 + cy**2)
    
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            t = dist / max_dist
            
            # Stronger at edges
            brightness = int(255 * (1 - t * t * intensity))
            mask_draw.point((x, y), fill=brightness)
    
    # Apply mask
    image = Image.composite(image, Image.new('RGB', (width, height), (0, 0, 0)), mask)
    
    return image


def add_glassmorphism_card(
    image: Image.Image,
    zone: Tuple[int, int, int, int],
    blur_radius: int = 10,
    opacity: float = 0.8
) -> Image.Image:
    """Add glassmorphism card effect."""
    x, y, w, h = zone
    
    # Extract region
    region = image.crop((x, y, x + w, y + h))
    
    # Blur
    blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    # Add white overlay
    overlay = Image.new('RGBA', (w, h), (255, 255, 255, int(255 * opacity * 0.3)))
    
    # Composite
    blurred = blurred.convert('RGBA')
    blurred = Image.alpha_composite(blurred, overlay)
    
    # Paste back
    image.paste(blurred.convert('RGB'), (x, y))
    
    return image


# =============================================================================
# TEXT RENDERING
# =============================================================================

def draw_text_with_effects(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    font,
    color: Tuple[int, int, int],
    shadow_params: Dict[str, Any] = None,
    letter_spacing: float = 0,
    text_case: str = "normal"
) -> int:
    """
    Draw text with optional effects (shadow, letter spacing, case).
    
    Returns the height of the rendered text.
    """
    x, y = position
    
    # Apply case transformation
    if text_case == "uppercase":
        text = text.upper()
    elif text_case == "lowercase":
        text = text.lower()
    elif text_case == "capitalize":
        text = text.title()
    
    # Draw shadow if enabled
    if shadow_params and shadow_params.get("enabled"):
        shadow_color = shadow_params["color"]
        shadow_alpha = shadow_params["alpha"]
        offset = shadow_params["offset"]
        
        # Multiple shadow layers for depth
        for i in range(3):
            layer_offset = (offset[0] + i, offset[1] + i)
            layer_alpha = max(0, shadow_alpha - i * 20)
            shadow_rgb = tuple(int(c * layer_alpha / 255) for c in shadow_color)
            draw.text((x + layer_offset[0], y + layer_offset[1]), text, font=font, fill=shadow_rgb)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=color)
    
    # Get text height
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]
    except:
        return font.size if hasattr(font, 'size') else 40


def load_pillow_font(font_list: List[str], size: int, bold: bool = True):
    """Load a Pillow font with fallbacks."""
    from PIL import ImageFont
    
    font_path = get_pillow_font_path(font_list, prefer_bold=bold)
    
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass
    
    # Fallback paths
    fallback_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    
    if not bold:
        fallback_paths = [p.replace("-Bold", "") for p in fallback_paths]
    
    for path in fallback_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    
    return ImageFont.load_default()


# =============================================================================
# ADAPTIVE TEMPLATE ENGINE
# =============================================================================

@dataclass
class PreviewContent:
    """Content to render in the preview."""
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    proof_text: Optional[str] = None
    cta_text: Optional[str] = None
    tags: List[str] = None
    logo_base64: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AdaptiveTemplateEngine:
    """
    Main engine for generating design-intelligent preview images.
    
    Adapts composition, typography, colors, and effects based on Design DNA.
    """
    
    def __init__(self, design_dna: DesignDNA):
        self.dna = design_dna
        self.width = OG_IMAGE_WIDTH
        self.height = OG_IMAGE_HEIGHT
        
        # Initialize configurations
        self.typography = get_typography_config(
            headline_personality=design_dna.typography.headline_personality,
            weight_contrast=design_dna.typography.weight_contrast,
            spacing_character=design_dna.typography.spacing_character,
            density=design_dna.spatial.density,
            design_style=design_dna.philosophy.primary_style,
            formality=design_dna.philosophy.formality
        )
        
        self.colors = get_color_config(
            primary_hex=design_dna.color_psychology.primary_hex,
            secondary_hex=design_dna.color_psychology.secondary_hex,
            accent_hex=design_dna.color_psychology.accent_hex,
            background_hex=design_dna.color_psychology.background_hex,
            text_hex=design_dna.color_psychology.text_hex,
            dominant_emotion=design_dna.color_psychology.dominant_emotion,
            color_strategy=design_dna.color_psychology.color_strategy,
            design_style=design_dna.philosophy.primary_style,
            light_dark_balance=design_dna.color_psychology.light_dark_balance
        )
        
        # Select composition
        template_style = design_dna.get_template_recommendation()
        self.composition_class = COMPOSITION_MAP.get(template_style, ProfessionalCleanComposition)
        base_zones = self.composition_class.get_layout_zones(self.width, self.height)
        
        # Apply layout patterns from Design DNA
        self.zones = self._adjust_zones_for_layout(base_zones)
        
        # Visual effects
        self.effects = design_dna.get_visual_effects()
    
    def _adjust_zones_for_layout(self, base_zones: Dict[str, Tuple[int, int, int, int]]) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Adjust layout zones based on layout_patterns from Design DNA.
        
        Args:
            base_zones: Original zones from composition class
            
        Returns:
            Adjusted zones based on layout patterns
        """
        layout_patterns = getattr(self.dna, 'layout_patterns', None)
        if not layout_patterns:
            return base_zones
        
        content_structure = getattr(layout_patterns, 'content_structure', 'centered')
        content_width = getattr(layout_patterns, 'content_width', 'medium')
        section_spacing = getattr(layout_patterns, 'section_spacing', 'normal')
        
        adjusted_zones = base_zones.copy()
        
        # Adjust content width
        if content_width != 'full':
            width_adjustments = {
                'narrow': 0.6,  # 60% of width
                'medium': 0.75,  # 75% of width
                'wide': 0.9  # 90% of width
            }
            
            width_factor = width_adjustments.get(content_width, 0.75)
            center_x = self.width // 2
            
            # Adjust horizontal zones (headline, subtitle, description)
            for zone_name in ['headline', 'subtitle', 'description']:
                if zone_name in adjusted_zones:
                    x, y, w, h = adjusted_zones[zone_name]
                    new_w = int(w * width_factor)
                    new_x = center_x - (new_w // 2)
                    adjusted_zones[zone_name] = (new_x, y, new_w, h)
        
        # Adjust content structure (centered, left-aligned, etc.)
        if content_structure == 'left-aligned':
            # Shift zones to the left
            padding = int(self.width * 0.07)
            for zone_name in ['headline', 'subtitle', 'description', 'proof']:
                if zone_name in adjusted_zones:
                    x, y, w, h = adjusted_zones[zone_name]
                    adjusted_zones[zone_name] = (padding, y, w, h)
        elif content_structure == 'asymmetric':
            # Create asymmetric layout (shift some elements)
            for zone_name in ['subtitle', 'description']:
                if zone_name in adjusted_zones:
                    x, y, w, h = adjusted_zones[zone_name]
                    # Shift right by 10%
                    adjusted_zones[zone_name] = (x + int(self.width * 0.1), y, w, h)
        
        # Adjust section spacing
        spacing_multipliers = {
            'tight': 0.7,
            'normal': 1.0,
            'generous': 1.3,
            'very-generous': 1.6
        }
        
        spacing_mult = spacing_multipliers.get(section_spacing, 1.0)
        
        # Adjust vertical spacing between zones
        zone_order = ['logo', 'headline', 'subtitle', 'description', 'proof']
        prev_y_end = 0
        
        for zone_name in zone_order:
            if zone_name in adjusted_zones:
                x, y, w, h = adjusted_zones[zone_name]
                if prev_y_end > 0:
                    # Calculate spacing
                    current_spacing = y - prev_y_end
                    new_spacing = int(current_spacing * spacing_mult)
                    new_y = prev_y_end + new_spacing
                    adjusted_zones[zone_name] = (x, new_y, w, h)
                prev_y_end = y + h
        
        return adjusted_zones
    
    def generate(
        self,
        content: PreviewContent,
        screenshot_bytes: Optional[bytes] = None
    ) -> bytes:
        """
        Generate the preview image.
        
        Args:
            content: Content to render
            screenshot_bytes: Optional screenshot for background
            
        Returns:
            PNG image bytes
        """
        # Create base image
        image = Image.new('RGB', (self.width, self.height), self.colors.background)
        
        # Apply background
        image = self._apply_background(image, screenshot_bytes)
        
        # STEP 1: Apply card styling (if card style is specified)
        image = self._apply_card_styling(image)
        
        draw = ImageDraw.Draw(image)
        
        # Render content in zones
        # CRITICAL: Always render logo if available (brand identity)
        self._render_accent_bar(draw)
        if content.logo_base64:
            self._render_logo(image, content.logo_base64)
        else:
            logger.warning("No logo provided to adaptive template engine - brand identity may be missing")
        
        self._render_headline(draw, content.title)
        self._render_subtitle(draw, content.subtitle)
        self._render_description(draw, content.description)
        self._render_proof(draw, content.proof_text)
        
        # Apply post-effects (including UI component styling)
        image = self._apply_post_effects(image)
        
        # Output
        buffer = BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        return buffer.getvalue()
    
    def _apply_background(
        self,
        image: Image.Image,
        screenshot_bytes: Optional[bytes] = None
    ) -> Image.Image:
        """Apply background based on design style and visual effects from Design DNA."""
        style = self.dna.philosophy.primary_style.lower()
        visual_effects = getattr(self.dna, 'visual_effects', None)
        
        # Check if gradients are enabled in visual effects
        gradients_enabled = False
        gradient_direction = "horizontal"
        if visual_effects:
            gradients_enabled = getattr(visual_effects, 'gradients', 'none') != 'none'
            gradient_direction = getattr(visual_effects, 'gradient_direction', 'horizontal')
        
        # Use gradient background (from color config or visual effects)
        if self.colors.gradient_type != "none" or gradients_enabled:
            # Determine gradient style from visual_effects
            gradient_style = "linear"
            if visual_effects:
                gradient_type = getattr(visual_effects, 'gradients', 'none')
                if gradient_type == "radial":
                    gradient_style = "radial"
                elif gradient_type in ["conic", "diagonal"]:
                    gradient_style = "linear"  # Use linear for diagonal/conic
            
            # Calculate angle from gradient_direction
            angle_map = {
                "horizontal": 0,
                "vertical": 90,
                "diagonal": 135,
                "radial": 0  # Radial doesn't use angle
            }
            angle = angle_map.get(gradient_direction, 135)
            
            image = apply_gradient_background(
                image,
                self.colors.gradient_colors,
                angle=angle,
                style=gradient_style
            )
        
        # Add screenshot as subtle background for certain styles
        if screenshot_bytes and style in ["bold", "playful", "maximalist"]:
            try:
                screenshot = Image.open(BytesIO(screenshot_bytes)).convert('RGB')
                screenshot = screenshot.resize((self.width, self.height), Image.Resampling.LANCZOS)
                
                # Darken and blur
                screenshot = screenshot.filter(ImageFilter.GaussianBlur(radius=3))
                enhancer = ImageEnhance.Brightness(screenshot)
                screenshot = enhancer.enhance(0.4)
                
                # Blend with gradient
                image = Image.blend(image, screenshot, alpha=0.2)
            except:
                pass
        
        # Apply textures from visual_effects
        image = self._apply_textures(image)
        
        return image
    
    def _apply_textures(self, image: Image.Image) -> Image.Image:
        """Apply visual textures based on Design DNA."""
        visual_effects = getattr(self.dna, 'visual_effects', None)
        if not visual_effects:
            return image
        
        textures = getattr(visual_effects, 'visual_textures', [])
        style = self.dna.philosophy.primary_style.lower()
        
        # Apply textures based on visual_textures list
        if 'grainy' in textures or 'noise' in textures:
            image = apply_noise_texture(image, intensity=0.03)
        elif 'paper' in textures:
            image = apply_noise_texture(image, intensity=0.02)
        elif 'fabric' in textures:
            image = apply_noise_texture(image, intensity=0.015)
        elif 'smooth' in textures:
            # No texture for smooth
            pass
        
        # Fallback: Apply texture for sophisticated styles if no texture specified
        if not textures and style in ["luxurious", "editorial"]:
            image = apply_noise_texture(image, intensity=0.02)
        
        return image
    
    def _apply_shadows(self, image: Image.Image, element_zone: Tuple[int, int, int, int]) -> Image.Image:
        """
        Apply shadows to a specific element zone based on visual_effects.shadows.
        
        Args:
            image: Image to apply shadow to
            element_zone: (x, y, w, h) zone to apply shadow to
            
        Returns:
            Image with shadow applied
        """
        visual_effects = getattr(self.dna, 'visual_effects', None)
        if not visual_effects:
            return image
        
        shadows = getattr(visual_effects, 'shadows', 'subtle')
        if shadows == 'none':
            return image
        
        x, y, w, h = element_zone
        
        # Shadow parameters based on intensity
        shadow_params = {
            'subtle': {'offset': 2, 'blur': 3, 'opacity': 30},
            'medium': {'offset': 4, 'blur': 6, 'opacity': 50},
            'dramatic': {'offset': 8, 'blur': 12, 'opacity': 70}
        }
        
        params = shadow_params.get(shadows, shadow_params['subtle'])
        
        # Create shadow layer
        shadow = Image.new('RGBA', (w + params['offset'] * 2, h + params['offset'] * 2), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle(
            [(params['offset'], params['offset']), (params['offset'] + w, params['offset'] + h)],
            fill=(0, 0, 0, params['opacity'])
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=params['blur']))
        
        # Paste shadow
        image.paste(shadow, (x - params['offset'], y - params['offset']), shadow)
        
        return image
    
    def _apply_borders(self, image: Image.Image, element_zone: Tuple[int, int, int, int], draw: ImageDraw.Draw) -> None:
        """
        Apply borders to a specific element zone based on visual_effects.borders.
        
        Args:
            image: Image (for reference)
            element_zone: (x, y, w, h) zone to apply border to
            draw: ImageDraw object to draw border
        """
        visual_effects = getattr(self.dna, 'visual_effects', None)
        if not visual_effects:
            return
        
        borders = getattr(visual_effects, 'borders', 'thin')
        border_style = getattr(visual_effects, 'border_style', 'solid')
        
        if borders == 'none':
            return
        
        x, y, w, h = element_zone
        
        # Border width based on borders setting
        border_width_map = {
            'thin': 1,
            'medium': 2,
            'thick': 4
        }
        border_width = border_width_map.get(borders, 1)
        
        # Border color (use text color or accent)
        border_color = self.colors.text if self.dna.color_psychology.light_dark_balance > 0.5 else (255, 255, 255)
        
        # Apply border style
        if border_style == 'solid':
            draw.rectangle([(x, y), (x + w, y + h)], outline=border_color, width=border_width)
        elif border_style == 'dashed':
            # Draw dashed border (simplified - draw multiple small rectangles)
            dash_length = 8
            gap_length = 4
            current_x = x
            while current_x < x + w:
                draw.rectangle([(current_x, y), (min(current_x + dash_length, x + w), y + border_width)], fill=border_color)
                current_x += dash_length + gap_length
            # Repeat for other sides if needed
        elif border_style == 'dotted':
            # Draw dotted border
            dot_spacing = 4
            for dot_x in range(x, x + w, dot_spacing):
                draw.ellipse([(dot_x, y), (dot_x + border_width, y + border_width)], fill=border_color)
            # Repeat for other sides if needed
    
    def _apply_card_styling(self, image: Image.Image) -> Image.Image:
        """
        Apply card styling based on UI components from Design DNA.
        
        Creates a card with appropriate style (flat, elevated, bordered, glassmorphic, neumorphic)
        and shadow intensity.
        """
        ui_components = getattr(self.dna, 'ui_components', None)
        if not ui_components:
            return image
        
        card_style = getattr(ui_components, 'card_style', 'flat')
        card_shadow = getattr(ui_components, 'card_shadow', 'subtle')
        
        # For flat style, no card needed (content directly on background)
        if card_style == 'flat':
            return image
        
        # Define card zone (most of the image, with padding)
        card_padding = int(self.width * 0.04)  # 4% padding
        card_x = card_padding
        card_y = card_padding
        card_w = self.width - (card_padding * 2)
        card_h = self.height - (card_padding * 2)
        
        # Create card image
        card_image = Image.new('RGBA', (card_w, card_h), (255, 255, 255, 255))
        card_draw = ImageDraw.Draw(card_image)
        
        # Apply card style
        if card_style == 'elevated':
            # Elevated card with shadow
            card_draw.rectangle([(0, 0), (card_w, card_h)], fill=(255, 255, 255))
        elif card_style == 'bordered':
            # Card with border
            border_width = 2
            card_draw.rectangle([(0, 0), (card_w, card_h)], fill=(255, 255, 255))
            card_draw.rectangle([(0, 0), (card_w, card_h)], outline=self.colors.text, width=border_width)
        elif card_style == 'glassmorphic':
            # Glassmorphic effect
            return add_glassmorphism_card(image, (card_x, card_y, card_w, card_h))
        elif card_style == 'neumorphic':
            # Neumorphic effect (soft shadows)
            card_draw.rectangle([(0, 0), (card_w, card_h)], fill=(245, 245, 245))
        
        # Apply shadow based on card_shadow intensity
        if card_shadow != 'none':
            shadow_offset = {'subtle': 2, 'medium': 4, 'dramatic': 8}.get(card_shadow, 2)
            shadow_blur = {'subtle': 3, 'medium': 6, 'dramatic': 12}.get(card_shadow, 3)
            
            # Create shadow layer
            shadow = Image.new('RGBA', (card_w + shadow_offset * 2, card_h + shadow_offset * 2), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rectangle(
                [(shadow_offset, shadow_offset), (shadow_offset + card_w, shadow_offset + card_h)],
                fill=(0, 0, 0, 40 if card_shadow == 'subtle' else 60 if card_shadow == 'medium' else 80)
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
            
            # Paste shadow first
            image.paste(shadow, (card_x - shadow_offset, card_y - shadow_offset), shadow)
        
        # Paste card on top
        image.paste(card_image.convert('RGB'), (card_x, card_y))
        
        return image
    
    def _render_accent_bar(self, draw: ImageDraw.Draw):
        """Render accent color bar with UI component styling from Design DNA."""
        if "accent_bar" not in self.zones:
            return
        
        x, y, w, h = self.zones["accent_bar"]
        
        # Apply UI component styling from Design DNA
        ui_components = getattr(self.dna, 'ui_components', None)
        visual_effects = getattr(self.dna, 'visual_effects', None)
        
        # Use button style to determine bar style
        button_style = "flat"
        button_shape = "rounded"
        button_border_radius = "medium"
        if ui_components:
            button_style = getattr(ui_components, 'button_style', 'flat')
            button_shape = getattr(ui_components, 'button_shape', 'rounded')
            button_border_radius = getattr(ui_components, 'button_border_radius', 'medium')
        
        # Apply visual effects
        shadow_intensity = "subtle"
        gradients_enabled = False
        gradient_direction = "horizontal"
        if visual_effects:
            shadow_intensity = getattr(visual_effects, 'shadows', 'subtle')
            gradients_enabled = getattr(visual_effects, 'gradients', 'none') != 'none'
            gradient_direction = getattr(visual_effects, 'gradient_direction', 'horizontal')
        
        # Calculate border radius based on button_border_radius
        radius_map = {'none': 0, 'small': 4, 'medium': 8, 'large': 16, 'pill': h // 2}
        radius = radius_map.get(button_border_radius, 8)
        
        # Render based on button style
        if button_style == "gradient" and gradients_enabled:
            # Gradient bar
            from backend.services.color_psychology import generate_gradient_colors
            gradient_colors = generate_gradient_colors(
                self.colors.accent,
                self.colors.secondary,
                steps=min(w, 100)  # Limit steps for performance
            )
            
            # Apply gradient based on direction
            if gradient_direction == "horizontal":
                for i in range(min(w, len(gradient_colors))):
                    color_idx = int((i / w) * (len(gradient_colors) - 1))
                    draw.rectangle([(x + i, y), (x + i + 1, y + h)], fill=gradient_colors[color_idx])
            elif gradient_direction == "vertical":
                for i in range(min(h, len(gradient_colors))):
                    color_idx = int((i / h) * (len(gradient_colors) - 1))
                    draw.rectangle([(x, y + i), (x + w, y + i + 1)], fill=gradient_colors[color_idx])
            else:
                # Default to horizontal
                for i in range(min(w, len(gradient_colors))):
                    color_idx = int((i / w) * (len(gradient_colors) - 1))
                    draw.rectangle([(x + i, y), (x + i + 1, y + h)], fill=gradient_colors[color_idx])
        elif button_style == "outlined":
            # Outlined bar
            border_width = 2
            if radius > 0:
                # Rounded rectangle outline
                draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius, outline=self.colors.accent, width=border_width)
            else:
                draw.rectangle([(x, y), (x + w, y + h)], outline=self.colors.accent, width=border_width)
        elif button_style == "ghost":
            # Ghost/transparent bar with border
            border_width = 1
            if radius > 0:
                draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius, outline=self.colors.accent, width=border_width, fill=None)
            else:
                draw.rectangle([(x, y), (x + w, y + h)], outline=self.colors.accent, width=border_width)
        else:
            # Solid bar (flat, raised, etc.)
            if radius > 0 and button_shape in ['rounded', 'pill']:
                draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius, fill=self.colors.accent)
            else:
                draw.rectangle([(x, y), (x + w, y + h)], fill=self.colors.accent)
        
        # Add shadow if specified (applied in post-processing for better quality)
        # Shadow will be applied in _apply_post_effects if needed
    
    def _render_logo(self, image: Image.Image, logo_base64: Optional[str]):
        """Render logo if available."""
        if "logo" not in self.zones or not logo_base64:
            return
        
        x, y, w, h = self.zones["logo"]
        
        try:
            import base64
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(BytesIO(logo_data)).convert('RGBA')
            
            # Resize preserving aspect ratio
            logo_ratio = logo_img.width / logo_img.height
            if logo_ratio > 1:
                new_w = min(w, logo_img.width)
                new_h = int(new_w / logo_ratio)
            else:
                new_h = min(h, logo_img.height)
                new_w = int(new_h * logo_ratio)
            
            logo_img = logo_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Create white background for logo if needed
            if self.dna.color_psychology.light_dark_balance < 0.4:
                bg = Image.new('RGBA', (new_w + 16, new_h + 16), (255, 255, 255, 240))
                image.paste(bg.convert('RGB'), (x - 8, y - 8))
            
            image.paste(logo_img, (x, y), logo_img)
        except Exception as e:
            logger.warning(f"Failed to render logo: {e}")
    
    def _render_headline(self, draw: ImageDraw.Draw, title: str):
        """Render main headline with full typography DNA application."""
        if "headline" not in self.zones or not title:
            return
        
        x, y, w, h = self.zones["headline"]
        
        # Get typography DNA values
        letter_spacing = getattr(self.dna.typography, 'letter_spacing', 'normal')
        line_height_dna = getattr(self.dna.typography, 'line_height', 'normal')
        case_strategy = getattr(self.dna.typography, 'case_strategy', 'mixed')
        font_size_hierarchy = getattr(self.dna.typography, 'font_size_hierarchy', '')
        
        # Calculate font size (considering hierarchy if specified)
        base_size = self.typography.headline_size
        font_size = calculate_adaptive_font_size(title, base_size, w, min_size=48, max_size=160)
        
        # Adjust font size based on hierarchy description if available
        if font_size_hierarchy and "headline" in font_size_hierarchy.lower():
            # Try to extract ratio from hierarchy description
            import re
            ratio_match = re.search(r'(\d+\.?\d*)x', font_size_hierarchy.lower())
            if ratio_match:
                ratio = float(ratio_match.group(1))
                # Adjust relative to body size (assuming body is ~24px)
                body_size = 24
                font_size = max(48, min(160, int(body_size * ratio)))
        
        # Load font
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=True)
        
        # Apply case strategy
        if case_strategy == "uppercase-accent":
            # Uppercase for emphasis
            title = title.upper()
        elif case_strategy == "lowercase-casual":
            # Lowercase for casual feel
            title = title.lower()
        # "mixed" keeps original case
        
        # Determine text color
        bg_luminance = self.dna.color_psychology.light_dark_balance
        if bg_luminance < 0.5:
            text_color = (255, 255, 255)
        else:
            text_color = self.colors.text
        
        # Get shadow params
        shadow_params = get_text_shadow_params(
            text_color,
            self.typography.shadow_intensity,
            self.dna.philosophy.primary_style
        )
        
        # Wrap text
        lines = get_optimal_line_breaks(title, font_size, w, max_lines=2)
        
        # Calculate line height based on DNA
        line_height_multipliers = {
            'tight': 1.1,
            'normal': 1.2,
            'relaxed': 1.4,
            'very-relaxed': 1.6
        }
        line_height_mult = line_height_multipliers.get(line_height_dna, 1.2)
        line_height = int(font_size * line_height_mult)
        
        current_y = y
        for line in lines:
            # Calculate letter spacing
            letter_spacing_px = self._get_letter_spacing_px(letter_spacing, font_size)
            
            # Render with letter spacing
            self._draw_text_with_letter_spacing(
                draw,
                (x, current_y),
                line,
                font,
                text_color,
                letter_spacing_px,
                shadow_params=shadow_params
            )
            current_y += line_height
    
    def _render_subtitle(self, draw: ImageDraw.Draw, subtitle: Optional[str]):
        """Render subtitle/tagline with typography DNA."""
        if "subtitle" not in self.zones or not subtitle:
            return
        
        x, y, w, h = self.zones["subtitle"]
        
        # Get typography DNA values
        letter_spacing = getattr(self.dna.typography, 'letter_spacing', 'normal')
        line_height_dna = getattr(self.dna.typography, 'line_height', 'normal')
        case_strategy = getattr(self.dna.typography, 'case_strategy', 'mixed')
        
        font_size = self.typography.subheadline_size
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=True)
        
        # Apply case strategy
        if case_strategy == "uppercase-accent":
            subtitle = subtitle.upper()
        elif case_strategy == "lowercase-casual":
            subtitle = subtitle.lower()
        
        # Apply color usage pattern for subtitle
        text_color = self._get_color_for_element("subtitle")
        
        lines = get_optimal_line_breaks(subtitle, font_size, w, max_lines=2)
        
        # Calculate line height based on DNA
        line_height_multipliers = {
            'tight': 1.1,
            'normal': 1.2,
            'relaxed': 1.4,
            'very-relaxed': 1.6
        }
        line_height_mult = line_height_multipliers.get(line_height_dna, 1.2)
        line_height = int(font_size * line_height_mult)
        
        current_y = y
        letter_spacing_px = self._get_letter_spacing_px(letter_spacing, font_size)
        
        for line in lines:
            if letter_spacing_px != 0:
                self._draw_text_with_letter_spacing(draw, (x, current_y), line, font, text_color, letter_spacing_px)
            else:
                draw.text((x, current_y), line, font=font, fill=text_color)
            current_y += line_height
    
    def _render_description(self, draw: ImageDraw.Draw, description: Optional[str]):
        """Render description text with typography DNA."""
        if "description" not in self.zones or not description:
            return
        
        x, y, w, h = self.zones["description"]
        
        # Get typography DNA values
        letter_spacing = getattr(self.dna.typography, 'letter_spacing', 'normal')
        line_height_dna = getattr(self.dna.typography, 'line_height', 'normal')
        case_strategy = getattr(self.dna.typography, 'case_strategy', 'mixed')
        
        font_size = self.typography.body_size
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=False)
        
        # Apply case strategy
        if case_strategy == "uppercase-accent":
            description = description.upper()
        elif case_strategy == "lowercase-casual":
            description = description.lower()
        
        # Apply color usage pattern for description
        text_color = self._get_color_for_element("description")
        
        lines = get_optimal_line_breaks(description, font_size, w, max_lines=2)
        
        # Calculate line height based on DNA
        line_height_multipliers = {
            'tight': 1.1,
            'normal': 1.2,
            'relaxed': 1.4,
            'very-relaxed': 1.6
        }
        line_height_mult = line_height_multipliers.get(line_height_dna, 1.2)
        line_height = int(font_size * line_height_mult)
        
        current_y = y
        letter_spacing_px = self._get_letter_spacing_px(letter_spacing, font_size)
        
        for line in lines:
            if letter_spacing_px != 0:
                self._draw_text_with_letter_spacing(draw, (x, current_y), line, font, text_color, letter_spacing_px)
            else:
                draw.text((x, current_y), line, font=font, fill=text_color)
            current_y += line_height
    
    def _render_proof(self, draw: ImageDraw.Draw, proof_text: Optional[str]):
        """Render social proof."""
        if "proof" not in self.zones or not proof_text:
            return
        
        x, y, w, h = self.zones["proof"]
        
        font_size = self.typography.caption_size
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=True)
        
        # Apply color usage pattern for proof text
        text_color = self._get_color_for_element("proof")
        
        draw.text((x, y), proof_text, font=font, fill=text_color)
    
    def _apply_post_effects(self, image: Image.Image) -> Image.Image:
        """Apply post-processing effects including visual effects from Design DNA."""
        style = self.dna.philosophy.primary_style.lower()
        visual_effects = getattr(self.dna, 'visual_effects', None)
        
        # Apply shadows if specified (vignette for overall image shadow)
        if visual_effects:
            shadows = getattr(visual_effects, 'shadows', 'subtle')
            if shadows == 'dramatic':
                image = apply_vignette(image, intensity=0.3)
            elif shadows == 'medium':
                image = apply_vignette(image, intensity=0.15)
            elif shadows == 'subtle':
                image = apply_vignette(image, intensity=0.08)
        
        # Vignette for dramatic/luxurious styles (if not already applied)
        if style in ["luxurious", "dramatic"] or self.dna.philosophy.visual_tension == "dramatic":
            if not visual_effects or getattr(visual_effects, 'shadows', 'subtle') == 'none':
                image = apply_vignette(image, intensity=0.2)
        
        # Apply overlay patterns if specified
        if visual_effects:
            overlay_patterns = getattr(visual_effects, 'overlay_patterns', 'none')
            if overlay_patterns != 'none':
                image = self._apply_overlay_patterns(image, overlay_patterns)
        
        # Apply special effects (glassmorphism, neumorphism, etc.)
        if visual_effects:
            effects = getattr(visual_effects, 'effects', [])
            if 'glassmorphism' in effects:
                # Apply glassmorphism to entire image (subtle)
                image = add_glassmorphism_card(image, (0, 0, self.width, self.height), blur_radius=5, opacity=0.1)
        
        # Slight sharpening for technical styles
        if style == "technical":
            image = image.filter(ImageFilter.SHARPEN)
        
        return image
    
    def _get_letter_spacing_px(self, letter_spacing: str, font_size: int) -> float:
        """Convert letter spacing string to pixels."""
        spacing_map = {
            'tight': -font_size * 0.02,  # -2% of font size
            'normal': 0,
            'wide': font_size * 0.05,  # +5% of font size
            'very-wide': font_size * 0.10  # +10% of font size
        }
        return spacing_map.get(letter_spacing, 0)
    
    def _draw_text_with_letter_spacing(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font,
        color: Tuple[int, int, int],
        letter_spacing_px: float,
        shadow_params: Dict[str, Any] = None
    ) -> None:
        """
        Draw text with custom letter spacing.
        
        PIL doesn't support letter spacing directly, so we draw each character separately.
        """
        x, y = position
        
        # Draw shadow if enabled
        if shadow_params and shadow_params.get("enabled"):
            shadow_color = shadow_params["color"]
            shadow_alpha = shadow_params["alpha"]
            offset = shadow_params["offset"]
            
            current_x = x
            for char in text:
                # Draw shadow
                for i in range(3):
                    layer_offset = (offset[0] + i, offset[1] + i)
                    layer_alpha = max(0, shadow_alpha - i * 20)
                    shadow_rgb = tuple(int(c * layer_alpha / 255) for c in shadow_color)
                    draw.text((current_x + layer_offset[0], y + layer_offset[1]), char, font=font, fill=shadow_rgb)
                
                # Get character width
                try:
                    bbox = draw.textbbox((0, 0), char, font=font)
                    char_width = bbox[2] - bbox[0]
                except:
                    # Fallback: estimate width based on font size
                    char_width = font.size if hasattr(font, 'size') else 20
                
                current_x += char_width + letter_spacing_px
        
        # Draw main text
        current_x = x
        for char in text:
            draw.text((current_x, y), char, font=font, fill=color)
            
            # Get character width
            try:
                bbox = draw.textbbox((0, 0), char, font=font)
                char_width = bbox[2] - bbox[0]
            except:
                # Fallback: estimate width based on font size
                char_width = font.size if hasattr(font, 'size') else 20
            
            current_x += char_width + letter_spacing_px
    
    def _get_color_for_element(self, element_type: str) -> Tuple[int, int, int]:
        """
        Get color for element based on color_usage_pattern and accent_usage from Design DNA.
        
        Args:
            element_type: Type of element (headline, subtitle, description, accent_bar, etc.)
            
        Returns:
            RGB color tuple
        """
        color_usage_pattern = getattr(self.dna.color_psychology, 'color_usage_pattern', '')
        accent_usage = getattr(self.dna.color_psychology, 'accent_usage', '')
        saturation_character = getattr(self.dna.color_psychology, 'saturation_character', 'balanced')
        
        # Parse color usage pattern to determine color for element
        pattern_lower = color_usage_pattern.lower()
        accent_lower = accent_usage.lower()
        
        # Determine base color based on usage pattern
        if element_type == "headline":
            if "primary" in pattern_lower and "headline" in pattern_lower:
                base_color = self.colors.primary
            elif "accent" in pattern_lower and "headline" in pattern_lower:
                base_color = self.colors.accent
            else:
                # Default: use text color
                bg_luminance = self.dna.color_psychology.light_dark_balance
                base_color = (255, 255, 255) if bg_luminance < 0.5 else self.colors.text
        elif element_type == "subtitle":
            if "secondary" in pattern_lower and "subtitle" in pattern_lower:
                base_color = self.colors.secondary
            else:
                # Default: muted text color
                bg_luminance = self.dna.color_psychology.light_dark_balance
                base_color = (230, 230, 235) if bg_luminance < 0.5 else self.colors.text_muted
        elif element_type == "description":
            # Description typically uses muted colors
            bg_luminance = self.dna.color_psychology.light_dark_balance
            base_color = (180, 180, 190) if bg_luminance < 0.5 else self.colors.text_muted
        elif element_type == "accent_bar":
            # Accent bar uses accent color
            if "accent" in accent_lower or "cta" in accent_lower or "button" in accent_lower:
                base_color = self.colors.accent
            else:
                base_color = self.colors.accent  # Default to accent
        elif element_type == "proof":
            # Proof text uses accent color for attention
            style = self.dna.philosophy.primary_style.lower()
            if style in ["bold", "playful", "maximalist"]:
                base_color = self.colors.accent
            else:
                bg_luminance = self.dna.color_psychology.light_dark_balance
                base_color = (255, 255, 255) if bg_luminance < 0.5 else self.colors.text
        else:
            # Default: use text color
            bg_luminance = self.dna.color_psychology.light_dark_balance
            base_color = (255, 255, 255) if bg_luminance < 0.5 else self.colors.text
        
        # Apply saturation adjustment
        if saturation_character == "vivid":
            # Increase saturation (make colors more vibrant)
            base_color = tuple(min(255, int(c * 1.1)) for c in base_color)
        elif saturation_character == "muted":
            # Decrease saturation (make colors more muted)
            base_color = tuple(int(c * 0.85) for c in base_color)
        elif saturation_character == "desaturated":
            # Strongly desaturate (towards grayscale)
            gray = int(sum(base_color) / 3)
            base_color = tuple(int(c * 0.5 + gray * 0.5) for c in base_color)
        
        return base_color
    
    def _apply_overlay_patterns(self, image: Image.Image, pattern_type: str) -> Image.Image:
        """Apply overlay patterns (dots, grid, lines, geometric) to image."""
        width, height = image.size
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        pattern_color = (0, 0, 0, 20)  # Subtle overlay
        
        if pattern_type == 'dots':
            # Dot pattern
            dot_spacing = 20
            dot_size = 2
            for y in range(0, height, dot_spacing):
                for x in range(0, width, dot_spacing):
                    overlay_draw.ellipse([(x - dot_size, y - dot_size), (x + dot_size, y + dot_size)], fill=pattern_color)
        elif pattern_type == 'grid':
            # Grid pattern
            grid_spacing = 40
            for x in range(0, width, grid_spacing):
                overlay_draw.line([(x, 0), (x, height)], fill=pattern_color, width=1)
            for y in range(0, height, grid_spacing):
                overlay_draw.line([(0, y), (width, y)], fill=pattern_color, width=1)
        elif pattern_type == 'lines':
            # Horizontal lines
            line_spacing = 30
            for y in range(0, height, line_spacing):
                overlay_draw.line([(0, y), (width, y)], fill=pattern_color, width=1)
        elif pattern_type == 'geometric':
            # Geometric pattern (diagonal lines)
            line_spacing = 50
            for i in range(0, width + height, line_spacing):
                overlay_draw.line([(i, 0), (0, i)], fill=pattern_color, width=1)
        
        # Composite overlay onto image
        image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        return image


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_adaptive_preview(
    design_dna: DesignDNA,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    proof_text: Optional[str] = None,
    logo_base64: Optional[str] = None,
    screenshot_bytes: Optional[bytes] = None
) -> bytes:
    """
    Convenience function to generate an adaptive preview.
    
    Args:
        design_dna: Design DNA from extraction
        title: Main headline
        subtitle: Optional subtitle
        description: Optional description
        proof_text: Optional social proof
        logo_base64: Optional logo image
        screenshot_bytes: Optional screenshot for background
        
    Returns:
        PNG image bytes
    """
    content = PreviewContent(
        title=title,
        subtitle=subtitle,
        description=description,
        proof_text=proof_text,
        logo_base64=logo_base64
    )
    
    engine = AdaptiveTemplateEngine(design_dna)
    return engine.generate(content, screenshot_bytes)


def generate_preview_from_dna_dict(
    dna_dict: Dict[str, Any],
    content_dict: Dict[str, Any],
    screenshot_bytes: Optional[bytes] = None
) -> bytes:
    """
    Generate preview from dictionary representations.
    
    Useful for integration with existing pipeline.
    """
    from backend.services.design_dna_extractor import (
        DesignDNA, DesignPhilosophy, TypographyDNA, ColorPsychology,
        SpatialIntelligence, HeroElement, BrandPersonality,
        UIComponents, VisualEffects, LayoutPatterns
    )
    
    # Reconstruct DesignDNA from dict with all components
    philosophy_data = dna_dict.get("philosophy", {})
    typography_data = dna_dict.get("typography", {})
    color_data = dna_dict.get("color_psychology", {})
    spatial_data = dna_dict.get("spatial", {})
    hero_data = dna_dict.get("hero_element", {})
    brand_data = dna_dict.get("brand_personality", {})
    ui_data = dna_dict.get("ui_components", {})
    effects_data = dna_dict.get("visual_effects", {})
    layout_data = dna_dict.get("layout_patterns", {})
    
    # Build DesignDNA with all components
    dna = DesignDNA(
        philosophy=DesignPhilosophy(**philosophy_data),
        typography=TypographyDNA(**typography_data),
        color_psychology=ColorPsychology(**color_data),
        spatial=SpatialIntelligence(**spatial_data),
        hero_element=HeroElement(**hero_data),
        brand_personality=BrandPersonality(**brand_data),
        ui_components=UIComponents(**ui_data) if ui_data else UIComponents(button_style="flat"),
        visual_effects=VisualEffects(**effects_data) if effects_data else VisualEffects(shadows="subtle"),
        layout_patterns=LayoutPatterns(**layout_data) if layout_data else LayoutPatterns(content_structure="centered"),
        confidence=dna_dict.get("confidence", 0.7)
    )
    
    content = PreviewContent(
        title=content_dict.get("title", ""),
        subtitle=content_dict.get("subtitle"),
        description=content_dict.get("description"),
        proof_text=content_dict.get("proof_text"),
        logo_base64=content_dict.get("logo_base64")
    )
    
    engine = AdaptiveTemplateEngine(dna)
    return engine.generate(content, screenshot_bytes)

