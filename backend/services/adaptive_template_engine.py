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
        self.zones = self.composition_class.get_layout_zones(self.width, self.height)
        
        # Visual effects
        self.effects = design_dna.get_visual_effects()
    
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
        """Apply background based on design style."""
        style = self.dna.philosophy.primary_style.lower()
        
        # Use gradient background
        if self.colors.gradient_type != "none":
            image = apply_gradient_background(
                image,
                self.colors.gradient_colors,
                angle=self.colors.gradient_angle,
                style="linear"
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
        
        # Add noise texture for sophisticated styles
        if "grain-texture" in self.effects or style in ["luxurious", "editorial"]:
            image = apply_noise_texture(image, intensity=0.02)
        
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
        if ui_components:
            button_style = getattr(ui_components, 'button_style', 'flat')
            button_shape = getattr(ui_components, 'button_border_radius', 'medium')
        
        # Apply visual effects
        shadow_intensity = "subtle"
        if visual_effects:
            shadow_intensity = getattr(visual_effects, 'shadows', 'subtle')
        
        # Render based on button style
        if button_style == "gradient" and visual_effects and getattr(visual_effects, 'gradients', 'none') != 'none':
            # Gradient bar
            from backend.services.color_psychology import generate_gradient_colors
            gradient_colors = generate_gradient_colors(
                self.colors.accent,
                self.colors.secondary,
                steps=10
            )
            # Simple gradient implementation
            for i, color in enumerate(gradient_colors[:w]):
                draw.rectangle([(x + i, y), (x + i + 1, y + h)], fill=color)
        else:
            # Solid bar (default)
            draw.rectangle([(x, y), (x + w, y + h)], fill=self.colors.accent)
        
        # Add shadow if specified
        if shadow_intensity in ["medium", "dramatic"]:
            # Add subtle shadow effect
            shadow_color = tuple(max(0, c - 30) for c in self.colors.accent)
            draw.rectangle([(x + 2, y + 2), (x + w + 2, y + h + 2)], fill=shadow_color)
            draw.rectangle([(x, y), (x + w, y + h)], fill=self.colors.accent)
    
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
        """Render main headline."""
        if "headline" not in self.zones or not title:
            return
        
        x, y, w, h = self.zones["headline"]
        
        # Calculate font size
        base_size = self.typography.headline_size
        font_size = calculate_adaptive_font_size(title, base_size, w, min_size=48, max_size=160)
        
        # Load font
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=True)
        
        # Determine text color
        # For gradient backgrounds, use white or ensure contrast
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
        
        current_y = y
        line_height = int(font_size * self.typography.headline_line_height)
        
        for line in lines:
            draw_text_with_effects(
                draw,
                (x, current_y),
                line,
                font,
                text_color,
                shadow_params=shadow_params,
                text_case=self.typography.headline_case
            )
            current_y += line_height
    
    def _render_subtitle(self, draw: ImageDraw.Draw, subtitle: Optional[str]):
        """Render subtitle/tagline."""
        if "subtitle" not in self.zones or not subtitle:
            return
        
        x, y, w, h = self.zones["subtitle"]
        
        font_size = self.typography.subheadline_size
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=True)
        
        # Slightly muted color
        bg_luminance = self.dna.color_psychology.light_dark_balance
        if bg_luminance < 0.5:
            text_color = (230, 230, 235)
        else:
            text_color = self.colors.text_muted
        
        lines = get_optimal_line_breaks(subtitle, font_size, w, max_lines=2)
        
        current_y = y
        line_height = int(font_size * self.typography.body_line_height)
        
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=text_color)
            current_y += line_height
    
    def _render_description(self, draw: ImageDraw.Draw, description: Optional[str]):
        """Render description text."""
        if "description" not in self.zones or not description:
            return
        
        x, y, w, h = self.zones["description"]
        
        font_size = self.typography.body_size
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=False)
        
        # Muted color
        bg_luminance = self.dna.color_psychology.light_dark_balance
        if bg_luminance < 0.5:
            text_color = (180, 180, 190)
        else:
            text_color = self.colors.text_muted
        
        lines = get_optimal_line_breaks(description, font_size, w, max_lines=2)
        
        current_y = y
        line_height = int(font_size * self.typography.body_line_height)
        
        for line in lines:
            draw.text((x, current_y), line, font=font, fill=text_color)
            current_y += line_height
    
    def _render_proof(self, draw: ImageDraw.Draw, proof_text: Optional[str]):
        """Render social proof."""
        if "proof" not in self.zones or not proof_text:
            return
        
        x, y, w, h = self.zones["proof"]
        
        font_size = self.typography.caption_size
        font = load_pillow_font(self.typography.pillow_fonts, font_size, bold=True)
        
        # Accent color for proof (draws attention)
        style = self.dna.philosophy.primary_style.lower()
        if style in ["bold", "playful", "maximalist"]:
            text_color = self.colors.accent
        else:
            bg_luminance = self.dna.color_psychology.light_dark_balance
            text_color = (255, 255, 255) if bg_luminance < 0.5 else self.colors.text
        
        draw.text((x, y), proof_text, font=font, fill=text_color)
    
    def _apply_post_effects(self, image: Image.Image) -> Image.Image:
        """Apply post-processing effects."""
        style = self.dna.philosophy.primary_style.lower()
        
        # Vignette for dramatic/luxurious styles
        if style in ["luxurious", "dramatic"] or self.dna.philosophy.visual_tension == "dramatic":
            image = apply_vignette(image, intensity=0.2)
        
        # Slight sharpening for technical styles
        if style == "technical":
            image = image.filter(ImageFilter.SHARPEN)
        
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
        SpatialIntelligence, HeroElement, BrandPersonality
    )
    
    # Reconstruct DesignDNA from dict
    dna = DesignDNA(
        philosophy=DesignPhilosophy(**dna_dict.get("philosophy", {})),
        typography=TypographyDNA(**dna_dict.get("typography", {})),
        color_psychology=ColorPsychology(**dna_dict.get("color_psychology", {})),
        spatial=SpatialIntelligence(**dna_dict.get("spatial", {})),
        hero_element=HeroElement(**dna_dict.get("hero_element", {})),
        brand_personality=BrandPersonality(**dna_dict.get("brand_personality", {})),
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

