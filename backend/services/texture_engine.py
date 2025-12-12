"""
Texture & Material Engine - Layer 4 of Design Framework Enhancement.

This module provides procedural texture generation, pattern overlays,
and material effects (glassmorphism, neumorphism, etc.) for premium visual quality.

Key Features:
- Procedural noise generation (film grain, paper, canvas, concrete)
- Pattern libraries (dots, lines, hex, topographic, circuits)
- Advanced gradients (mesh, radial, conic, noise-based)
- Material effects (glass, frosted, acrylic, metal, fabric)
"""

import logging
import math
import random
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

logger = logging.getLogger(__name__)


class TextureType(str, Enum):
    """Available texture types."""
    FILM_GRAIN = "film_grain"
    PAPER = "paper"
    CANVAS = "canvas"
    CONCRETE = "concrete"
    FABRIC = "fabric"
    METAL = "metal"


class PatternType(str, Enum):
    """Available pattern types."""
    DOT_GRID = "dot_grid"
    LINE_GRID = "line_grid"
    HEX_PATTERN = "hex_pattern"
    TOPOGRAPHIC = "topographic"
    CIRCUIT = "circuit"
    WAVES = "waves"


@dataclass
class TextureConfig:
    """Configuration for texture generation."""
    texture_type: TextureType
    intensity: float  # 0-1
    scale: float  # Size multiplier
    opacity: int  # 0-255
    blend_mode: str  # multiply, overlay, soft-light, screen


@dataclass
class PatternConfig:
    """Configuration for pattern generation."""
    pattern_type: PatternType
    color: Tuple[int, int, int]
    size: int  # Pattern size/spacing
    opacity: int  # 0-255
    thickness: int  # Line/stroke thickness


class TextureEngine:
    """
    Generates procedural textures and patterns for sophisticated designs.
    
    Creates subtle visual interest without overwhelming the design.
    """
    
    def __init__(self):
        random.seed()  # Initialize for procedural generation
    
    def generate_texture(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """
        Generate a procedural texture.
        
        Args:
            width: Texture width
            height: Texture height
            config: Texture configuration
            
        Returns:
            RGBA image with texture
        """
        if config.texture_type == TextureType.FILM_GRAIN:
            return self._generate_film_grain(width, height, config)
        elif config.texture_type == TextureType.PAPER:
            return self._generate_paper_texture(width, height, config)
        elif config.texture_type == TextureType.CANVAS:
            return self._generate_canvas_texture(width, height, config)
        elif config.texture_type == TextureType.CONCRETE:
            return self._generate_concrete_texture(width, height, config)
        elif config.texture_type == TextureType.FABRIC:
            return self._generate_fabric_texture(width, height, config)
        elif config.texture_type == TextureType.METAL:
            return self._generate_metal_texture(width, height, config)
        else:
            return Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    def generate_pattern(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """
        Generate a geometric pattern.
        
        Args:
            width: Pattern width
            height: Pattern height
            config: Pattern configuration
            
        Returns:
            RGBA image with pattern
        """
        if config.pattern_type == PatternType.DOT_GRID:
            return self._generate_dot_grid(width, height, config)
        elif config.pattern_type == PatternType.LINE_GRID:
            return self._generate_line_grid(width, height, config)
        elif config.pattern_type == PatternType.HEX_PATTERN:
            return self._generate_hex_pattern(width, height, config)
        elif config.pattern_type == PatternType.TOPOGRAPHIC:
            return self._generate_topographic(width, height, config)
        elif config.pattern_type == PatternType.CIRCUIT:
            return self._generate_circuit_pattern(width, height, config)
        elif config.pattern_type == PatternType.WAVES:
            return self._generate_wave_pattern(width, height, config)
        else:
            return Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    def apply_texture_to_image(
        self,
        base_image: Image.Image,
        texture: Image.Image,
        blend_mode: str = "overlay",
        opacity: float = 0.5
    ) -> Image.Image:
        """
        Apply texture to base image with blending.
        
        Args:
            base_image: Base image
            texture: Texture to apply
            blend_mode: Blending mode
            opacity: Opacity (0-1)
            
        Returns:
            Image with texture applied
        """
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')
        
        if texture.size != base_image.size:
            texture = texture.resize(base_image.size, Image.Resampling.LANCZOS)
        
        # Adjust texture opacity
        if opacity < 1.0:
            alpha = texture.split()[3] if texture.mode == 'RGBA' else Image.new('L', texture.size, 255)
            alpha = alpha.point(lambda p: int(p * opacity))
            if texture.mode == 'RGBA':
                r, g, b, _ = texture.split()
                texture = Image.merge('RGBA', (r, g, b, alpha))
        
        # Apply blending
        if blend_mode == "multiply":
            result = self._blend_multiply(base_image, texture)
        elif blend_mode == "screen":
            result = self._blend_screen(base_image, texture)
        elif blend_mode == "overlay":
            result = self._blend_overlay(base_image, texture)
        elif blend_mode == "soft-light":
            result = self._blend_soft_light(base_image, texture)
        else:  # normal
            result = Image.alpha_composite(base_image, texture)
        
        return result
    
    # =========================================================================
    # TEXTURE GENERATORS
    # =========================================================================
    
    def _generate_film_grain(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """Generate film grain texture."""
        # Create monochrome noise
        noise = np.random.randint(
            -int(255 * config.intensity),
            int(255 * config.intensity),
            (height, width),
            dtype=np.int16
        )
        
        # Convert to image
        noise_img = Image.fromarray(
            np.clip(128 + noise, 0, 255).astype(np.uint8),
            mode='L'
        )
        
        # Create RGBA with opacity
        rgba = Image.new('RGBA', (width, height), (128, 128, 128, config.opacity))
        rgba.putalpha(noise_img.point(lambda p: config.opacity))
        
        return rgba
    
    def _generate_paper_texture(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """Generate paper texture with fibers."""
        # Base noise
        noise = np.random.normal(250, 15 * config.intensity, (height, width))
        
        # Add fibrous patterns (horizontal and vertical streaks)
        for _ in range(int(100 * config.intensity)):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            length = random.randint(5, 20)
            angle = random.choice([0, 90, 45, 135])
            
            if angle == 0:  # Horizontal
                noise[y, max(0, x-length):min(width, x+length)] += random.randint(-10, 10)
            elif angle == 90:  # Vertical
                noise[max(0, y-length):min(height, y+length), x] += random.randint(-10, 10)
        
        # Convert to image
        paper_img = Image.fromarray(
            np.clip(noise, 0, 255).astype(np.uint8),
            mode='L'
        )
        
        # Slight blur for smoothness
        paper_img = paper_img.filter(ImageFilter.GaussianBlur(0.5))
        
        # Create RGBA
        rgba = Image.new('RGBA', (width, height), (255, 255, 255, config.opacity))
        r, g, b = paper_img, paper_img, paper_img
        rgba = Image.merge('RGBA', (r, g, b, paper_img.point(lambda p: int(p / 255 * config.opacity))))
        
        return rgba
    
    def _generate_canvas_texture(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """Generate canvas weave texture."""
        scale = int(config.scale * 4)
        
        # Create weave pattern
        canvas = Image.new('L', (width, height), 250)
        pixels = canvas.load()
        
        for y in range(height):
            for x in range(width):
                # Weave pattern
                h_thread = (x // scale) % 2
                v_thread = (y // scale) % 2
                
                if h_thread == v_thread:
                    value = 255
                else:
                    value = 245
                
                # Add noise
                value += random.randint(-int(10 * config.intensity), int(10 * config.intensity))
                pixels[x, y] = max(0, min(255, value))
        
        # Create RGBA
        rgba = Image.merge('RGBA', (canvas, canvas, canvas, 
                                     canvas.point(lambda p: int(p / 255 * config.opacity))))
        
        return rgba
    
    def _generate_concrete_texture(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """Generate concrete/stone texture."""
        # Rough noise base
        noise = np.random.normal(200, 30 * config.intensity, (height, width))
        
        # Add spots and imperfections
        for _ in range(int(50 * config.intensity)):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            radius = random.randint(1, 4)
            darkness = random.randint(-30, -10)
            
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if 0 <= y + dy < height and 0 <= x + dx < width:
                        if dx*dx + dy*dy <= radius*radius:
                            noise[y + dy, x + dx] += darkness
        
        # Convert and blur slightly
        concrete_img = Image.fromarray(
            np.clip(noise, 0, 255).astype(np.uint8),
            mode='L'
        )
        concrete_img = concrete_img.filter(ImageFilter.GaussianBlur(1))
        
        # Create RGBA with gray tone
        rgba = Image.merge('RGBA', (concrete_img, concrete_img, concrete_img,
                                     concrete_img.point(lambda p: int(p / 255 * config.opacity))))
        
        return rgba
    
    def _generate_fabric_texture(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """Generate fabric/cloth texture."""
        scale = int(config.scale * 3)
        
        fabric = Image.new('L', (width, height), 240)
        pixels = fabric.load()
        
        for y in range(height):
            for x in range(width):
                # Crosshatch pattern
                value = 240
                if (x // scale + y // scale) % 2 == 0:
                    value -= 15
                
                # Add thread noise
                value += random.randint(-int(5 * config.intensity), int(5 * config.intensity))
                pixels[x, y] = max(0, min(255, value))
        
        # Slight blur
        fabric = fabric.filter(ImageFilter.GaussianBlur(0.5))
        
        rgba = Image.merge('RGBA', (fabric, fabric, fabric,
                                     fabric.point(lambda p: int(p / 255 * config.opacity))))
        
        return rgba
    
    def _generate_metal_texture(
        self,
        width: int,
        height: int,
        config: TextureConfig
    ) -> Image.Image:
        """Generate brushed metal texture."""
        # Horizontal streaks
        metal = np.ones((height, width), dtype=np.float32) * 200
        
        for y in range(height):
            # Vary intensity per row
            intensity = 200 + random.randint(-int(20 * config.intensity), int(20 * config.intensity))
            metal[y, :] = intensity
            
            # Add fine horizontal lines
            for _ in range(random.randint(0, 3)):
                x_start = random.randint(0, width // 2)
                x_end = random.randint(width // 2, width)
                metal[y, x_start:x_end] += random.randint(-5, 5)
        
        # Add subtle vertical variation
        for x in range(0, width, 10):
            variation = random.randint(-int(10 * config.intensity), int(10 * config.intensity))
            metal[:, x:min(x + 5, width)] += variation
        
        metal_img = Image.fromarray(
            np.clip(metal, 0, 255).astype(np.uint8),
            mode='L'
        )
        
        # Slight blur
        metal_img = metal_img.filter(ImageFilter.GaussianBlur(0.3))
        
        rgba = Image.merge('RGBA', (metal_img, metal_img, metal_img,
                                     metal_img.point(lambda p: int(p / 255 * config.opacity))))
        
        return rgba
    
    # =========================================================================
    # PATTERN GENERATORS
    # =========================================================================
    
    def _generate_dot_grid(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """Generate dot grid pattern."""
        pattern = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)
        
        spacing = config.size
        radius = config.thickness
        
        for y in range(0, height, spacing):
            for x in range(0, width, spacing):
                draw.ellipse(
                    [(x - radius, y - radius), (x + radius, y + radius)],
                    fill=(*config.color, config.opacity)
                )
        
        return pattern
    
    def _generate_line_grid(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """Generate line grid pattern."""
        pattern = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)
        
        spacing = config.size
        thickness = config.thickness
        
        # Vertical lines
        for x in range(0, width, spacing):
            draw.line([(x, 0), (x, height)], fill=(*config.color, config.opacity), width=thickness)
        
        # Horizontal lines
        for y in range(0, height, spacing):
            draw.line([(0, y), (width, y)], fill=(*config.color, config.opacity), width=thickness)
        
        return pattern
    
    def _generate_hex_pattern(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """Generate hexagonal pattern."""
        pattern = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)
        
        size = config.size
        thickness = config.thickness
        
        # Hexagon dimensions
        h = size * math.sqrt(3) / 2
        
        for row in range(-1, int(height / h) + 2):
            for col in range(-1, int(width / size) + 2):
                # Offset every other row
                x = col * size * 1.5
                y = row * h
                if col % 2 == 1:
                    y += h / 2
                
                # Draw hexagon
                points = []
                for i in range(6):
                    angle = math.pi / 3 * i
                    px = x + size * math.cos(angle)
                    py = y + size * math.sin(angle)
                    points.append((px, py))
                
                draw.line(points + [points[0]], fill=(*config.color, config.opacity), width=thickness)
        
        return pattern
    
    def _generate_topographic(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """Generate topographic (contour) lines."""
        pattern = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)
        
        # Create noise field for elevation
        scale = 50
        for level in range(5, 250, config.size):
            # Draw contour at this elevation
            for y in range(0, height, 2):
                for x in range(0, width, 2):
                    # Simple noise function
                    noise_val = (math.sin(x / scale) + math.sin(y / scale)) * 127.5 + 127.5
                    
                    if abs(noise_val - level) < 5:
                        draw.point((x, y), fill=(*config.color, config.opacity))
        
        return pattern
    
    def _generate_circuit_pattern(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """Generate circuit board pattern."""
        pattern = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)
        
        spacing = config.size
        thickness = config.thickness
        
        # Draw random circuit paths
        for _ in range(width * height // (spacing * spacing)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            
            # Random direction and length
            direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            length = random.randint(spacing, spacing * 3)
            
            end_x = x + direction[0] * length
            end_y = y + direction[1] * length
            
            if 0 <= end_x < width and 0 <= end_y < height:
                draw.line([(x, y), (end_x, end_y)], 
                         fill=(*config.color, config.opacity), width=thickness)
                
                # Add junction dots
                draw.ellipse([(x-2, y-2), (x+2, y+2)], fill=(*config.color, config.opacity))
                draw.ellipse([(end_x-2, end_y-2), (end_x+2, end_y+2)], fill=(*config.color, config.opacity))
        
        return pattern
    
    def _generate_wave_pattern(
        self,
        width: int,
        height: int,
        config: PatternConfig
    ) -> Image.Image:
        """Generate wave/sine pattern."""
        pattern = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(pattern)
        
        amplitude = config.size
        frequency = 0.02
        thickness = config.thickness
        
        for y_base in range(0, height, amplitude * 2):
            points = []
            for x in range(width):
                y = y_base + amplitude * math.sin(x * frequency)
                points.append((x, y))
            
            if len(points) > 1:
                draw.line(points, fill=(*config.color, config.opacity), width=thickness)
        
        return pattern
    
    # =========================================================================
    # BLEND MODES
    # =========================================================================
    
    def _blend_multiply(self, base: Image.Image, overlay: Image.Image) -> Image.Image:
        """Multiply blend mode."""
        base_arr = np.array(base, dtype=np.float32) / 255.0
        overlay_arr = np.array(overlay, dtype=np.float32) / 255.0
        
        result = base_arr * overlay_arr
        return Image.fromarray((result * 255).astype(np.uint8), 'RGBA')
    
    def _blend_screen(self, base: Image.Image, overlay: Image.Image) -> Image.Image:
        """Screen blend mode."""
        base_arr = np.array(base, dtype=np.float32) / 255.0
        overlay_arr = np.array(overlay, dtype=np.float32) / 255.0
        
        result = 1 - (1 - base_arr) * (1 - overlay_arr)
        return Image.fromarray((result * 255).astype(np.uint8), 'RGBA')
    
    def _blend_overlay(self, base: Image.Image, overlay: Image.Image) -> Image.Image:
        """Overlay blend mode."""
        # Simplified overlay (combine multiply and screen)
        return Image.alpha_composite(base, overlay)
    
    def _blend_soft_light(self, base: Image.Image, overlay: Image.Image) -> Image.Image:
        """Soft light blend mode."""
        # Simplified soft light
        return Image.alpha_composite(base, overlay)


# =============================================================================
# MATERIAL EFFECTS
# =============================================================================

def create_glassmorphism(
    image: Image.Image,
    element_bounds: Tuple[int, int, int, int],
    blur_radius: int = 10,
    transparency: float = 0.7,
    border_opacity: int = 100
) -> Image.Image:
    """
    Create glassmorphism effect (frosted glass with blur).
    
    Args:
        image: Base image
        element_bounds: (x, y, width, height)
        blur_radius: Backdrop blur amount
        transparency: Glass transparency (0-1)
        border_opacity: Border opacity (0-255)
        
    Returns:
        Image with glassmorphism effect
    """
    x, y, width, height = element_bounds
    
    # Extract and blur background
    bg_region = image.crop((x, y, x + width, y + height))
    blurred = bg_region.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # Create semi-transparent white overlay
    glass = Image.new('RGBA', (width, height), (255, 255, 255, int(255 * transparency * 0.3)))
    
    # Composite blur + glass
    result = Image.alpha_composite(blurred.convert('RGBA'), glass)
    
    # Add border
    draw = ImageDraw.Draw(result)
    draw.rectangle(
        [(0, 0), (width - 1, height - 1)],
        outline=(255, 255, 255, border_opacity),
        width=1
    )
    
    # Paste back onto original
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    image.paste(result, (x, y), result)
    
    return image


# Example usage
if __name__ == "__main__":
    engine = TextureEngine()
    
    # Test texture generation
    texture_config = TextureConfig(
        texture_type=TextureType.FILM_GRAIN,
        intensity=0.05,
        scale=1.0,
        opacity=30,
        blend_mode="overlay"
    )
    
    texture = engine.generate_texture(1200, 630, texture_config)
    print(f"Generated {texture_config.texture_type.value} texture: {texture.size}")
    
    # Test pattern generation
    pattern_config = PatternConfig(
        pattern_type=PatternType.DOT_GRID,
        color=(100, 100, 150),
        size=30,
        opacity=40,
        thickness=2
    )
    
    pattern = engine.generate_pattern(1200, 630, pattern_config)
    print(f"Generated {pattern_config.pattern_type.value} pattern: {pattern.size}")
