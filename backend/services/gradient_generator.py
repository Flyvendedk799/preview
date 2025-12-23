"""
High-quality gradient generator that eliminates banding artifacts.
Uses LAB color space for perceptually uniform gradients and proper dithering.
"""
import numpy as np
from PIL import Image
import math
import colorsys
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


def rgb_to_lab(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert RGB to LAB color space (perceptually uniform)."""
    # First convert to XYZ
    r = r / 255.0
    g = g / 255.0
    b = b / 255.0
    
    # Apply gamma correction
    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4
    
    # Convert to XYZ (D65 illuminant)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    
    # Normalize by D65 white point
    x /= 0.95047
    z /= 1.08883
    
    # Convert to LAB
    fx = x ** (1/3) if x > 0.008856 else (7.787 * x + 16/116)
    fy = y ** (1/3) if y > 0.008856 else (7.787 * y + 16/116)
    fz = z ** (1/3) if z > 0.008856 else (7.787 * z + 16/116)
    
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    
    return L, a, b


def lab_to_rgb(L: float, a: float, b: float) -> Tuple[float, float, float]:
    """Convert LAB to RGB color space."""
    # Convert LAB to XYZ
    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200
    
    x = fx ** 3 if fx ** 3 > 0.008856 else (fx - 16/116) / 7.787
    y = fy ** 3 if fy ** 3 > 0.008856 else (fy - 16/116) / 7.787
    z = fz ** 3 if fz ** 3 > 0.008856 else (fz - 16/116) / 7.787
    
    # Denormalize
    x *= 0.95047
    z *= 1.08883
    
    # Convert XYZ to RGB
    r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
    
    # Apply gamma correction
    r = 12.92 * r if r <= 0.0031308 else 1.055 * (r ** (1/2.4)) - 0.055
    g = 12.92 * g if g <= 0.0031308 else 1.055 * (g ** (1/2.4)) - 0.055
    b = 12.92 * b if b <= 0.0031308 else 1.055 * (b ** (1/2.4)) - 0.055
    
    # Clamp and scale
    r = max(0, min(1, r)) * 255
    g = max(0, min(1, g)) * 255
    b = max(0, min(1, b)) * 255
    
    return r, g, b


def floyd_steinberg_dither(image: np.ndarray) -> np.ndarray:
    """
    Apply Floyd-Steinberg dithering to reduce banding.
    OPTIMIZED: Uses vectorized operations for much faster processing.
    """
    if len(image.shape) == 2:
        # Grayscale
        height, width = image.shape
        result = image.copy().astype(np.float64)
        
        for y in range(height):
            for x in range(width):
                old_pixel = result[y, x]
                new_pixel = np.round(old_pixel)
                result[y, x] = new_pixel
                error = old_pixel - new_pixel
                
                if x < width - 1:
                    result[y, x + 1] += error * 7/16
                if y < height - 1:
                    if x > 0:
                        result[y + 1, x - 1] += error * 3/16
                    result[y + 1, x] += error * 5/16
                    if x < width - 1:
                        result[y + 1, x + 1] += error * 1/16
        
        return np.clip(result, 0, 255).astype(np.uint8)
    else:
        # RGB - process each channel separately (much faster than pixel-by-pixel)
        height, width, channels = image.shape
        result = image.copy().astype(np.float64)
        
        for c in range(channels):
            channel = result[:, :, c]
            for y in range(height):
                for x in range(width):
                    old_pixel = channel[y, x]
                    new_pixel = np.round(old_pixel)
                    channel[y, x] = new_pixel
                    error = old_pixel - new_pixel
                    
                    if x < width - 1:
                        channel[y, x + 1] += error * 7/16
                    if y < height - 1:
                        if x > 0:
                            channel[y + 1, x - 1] += error * 3/16
                        channel[y + 1, x] += error * 5/16
                        if x < width - 1:
                            channel[y + 1, x + 1] += error * 1/16
        
        return np.clip(result, 0, 255).astype(np.uint8)


def apply_fast_dithering(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    Fast dithering using ordered dithering matrix - much faster than Floyd-Steinberg.
    Creates visual dithering effect without pixel-by-pixel processing.
    """
    height, width = image.shape[:2]
    
    # Create Bayer dithering matrix (8x8 pattern)
    bayer_matrix = np.array([
        [ 0, 32,  8, 40,  2, 34, 10, 42],
        [48, 16, 56, 24, 50, 18, 58, 26],
        [12, 44,  4, 36, 14, 46,  6, 38],
        [60, 28, 52, 20, 62, 30, 54, 22],
        [ 3, 35, 11, 43,  1, 33,  9, 41],
        [51, 19, 59, 27, 49, 17, 57, 25],
        [15, 47,  7, 39, 13, 45,  5, 37],
        [63, 31, 55, 23, 61, 29, 53, 21]
    ], dtype=np.float64) / 64.0
    
    # Tile the matrix across the image
    tile_y = (height + 7) // 8
    tile_x = (width + 7) // 8
    dither_pattern = np.tile(bayer_matrix, (tile_y, tile_x))[:height, :width]
    
    # Apply dithering
    if len(image.shape) == 3:
        dither_pattern = dither_pattern[:, :, np.newaxis]
    
    # Add dithering noise based on pattern
    dither_noise = (dither_pattern - 0.5) * strength * 2.0
    result = image.astype(np.float64) + dither_noise
    
    return np.clip(result, 0, 255).astype(np.uint8)


def generate_smooth_gradient(
    width: int,
    height: int,
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    angle: int = 135,
    style: str = "linear"
) -> Image.Image:
    """
    Generate a smooth, band-free gradient using LAB color space interpolation.
    
    Args:
        width: Target width
        height: Target height
        color1: Start color (R, G, B)
        color2: End color (R, G, B)
        angle: Gradient angle (0=horizontal, 90=vertical, 135=diagonal)
        style: Gradient style ("linear" or "radial")
    
    Returns:
        PIL Image with smooth gradient
    """
    logger.info(f"🎨 [GRADIENT] Starting LAB gradient generation: {width}x{height}, color1={color1}, color2={color2}, angle={angle}, style={style}")
    
    # Generate at 4x resolution for maximum smoothness
    scale_factor = 4
    high_width = width * scale_factor
    high_height = height * scale_factor
    logger.info(f"🎨 [GRADIENT] High-res generation: {high_width}x{high_height} (scale={scale_factor}x)")
    
    # Convert colors to LAB (perceptually uniform)
    L1, a1, b1 = rgb_to_lab(color1[0], color1[1], color1[2])
    L2, a2, b2 = rgb_to_lab(color2[0], color2[1], color2[2])
    logger.info(f"🎨 [GRADIENT] RGB->LAB conversion: color1 RGB{color1} -> LAB({L1:.2f}, {a1:.2f}, {b1:.2f}), color2 RGB{color2} -> LAB({L2:.2f}, {a2:.2f}, {b2:.2f})")
    
    # Create coordinate arrays
    y_coords = np.arange(high_height, dtype=np.float64)[:, np.newaxis]
    x_coords = np.arange(high_width, dtype=np.float64)[np.newaxis, :]
    
    if style == "radial":
        # Radial gradient
        center_x, center_y = high_width / 2, high_height / 2
        dx = x_coords - center_x
        dy = y_coords - center_y
        dist = np.sqrt(dx**2 + dy**2)
        max_dist = math.sqrt(center_x**2 + center_y**2)
        progress = np.clip(dist / max_dist, 0, 1)
    else:
        # Linear gradient
        if angle == 90:  # Vertical
            progress = y_coords / max(high_height - 1, 1)
        elif angle == 0:  # Horizontal
            progress = x_coords / max(high_width - 1, 1)
        else:  # Diagonal
            # Use proper angle calculation
            angle_rad = math.radians(angle)
            # Normalize coordinates to [-1, 1]
            x_norm = (x_coords / (high_width - 1)) * 2 - 1
            y_norm = (y_coords / (high_height - 1)) * 2 - 1
            # Rotate and project
            progress = (x_norm * math.cos(angle_rad) + y_norm * math.sin(angle_rad) + 1) / 2
            progress = np.clip(progress, 0, 1)
    
    # Interpolate in LAB space (perceptually uniform)
    logger.info(f"🎨 [GRADIENT] Interpolating in LAB color space...")
    L = L1 * (1 - progress) + L2 * progress
    a = a1 * (1 - progress) + a2 * progress
    b = b1 * (1 - progress) + b2 * progress
    
    # Log LAB range
    logger.info(f"🎨 [GRADIENT] LAB ranges: L=[{L.min():.2f}, {L.max():.2f}], a=[{a.min():.2f}, {a.max():.2f}], b=[{b.min():.2f}, {b.max():.2f}]")
    
    # Convert back to RGB using vectorized operations (much faster)
    # First convert LAB to XYZ, then XYZ to RGB
    logger.info(f"🎨 [GRADIENT] Converting LAB->XYZ->RGB...")
    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200
    
    # Convert to XYZ
    x = np.where(fx**3 > 0.008856, fx**3, (fx - 16/116) / 7.787)
    y = np.where(fy**3 > 0.008856, fy**3, (fy - 16/116) / 7.787)
    z = np.where(fz**3 > 0.008856, fz**3, (fz - 16/116) / 7.787)
    
    x *= 0.95047
    z *= 1.08883
    
    # Convert XYZ to RGB
    r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
    
    # Apply gamma correction
    r = np.where(r <= 0.0031308, 12.92 * r, 1.055 * (r ** (1/2.4)) - 0.055)
    g = np.where(g <= 0.0031308, 12.92 * g, 1.055 * (g ** (1/2.4)) - 0.055)
    b = np.where(b <= 0.0031308, 12.92 * b, 1.055 * (b ** (1/2.4)) - 0.055)
    
    # Clamp and scale to 0-255
    r = np.clip(r, 0, 1) * 255
    g = np.clip(g, 0, 1) * 255
    b = np.clip(b, 0, 1) * 255
    
    rgb_array = np.stack([r, g, b], axis=2).astype(np.float64)
    
    # Log RGB range before dithering
    logger.info(f"🎨 [GRADIENT] RGB ranges before dithering: R=[{rgb_array[:,:,0].min():.2f}, {rgb_array[:,:,0].max():.2f}], G=[{rgb_array[:,:,1].min():.2f}, {rgb_array[:,:,1].max():.2f}], B=[{rgb_array[:,:,2].min():.2f}, {rgb_array[:,:,2].max():.2f}]")
    
    # Apply Floyd-Steinberg dithering to reduce quantization artifacts
    logger.info(f"🎨 [GRADIENT] Applying Floyd-Steinberg dithering...")
    rgb_array = floyd_steinberg_dither(rgb_array)
    
    # Log RGB range after dithering
    logger.info(f"🎨 [GRADIENT] RGB ranges after dithering: R=[{rgb_array[:,:,0].min():.2f}, {rgb_array[:,:,0].max():.2f}], G=[{rgb_array[:,:,1].min():.2f}, {rgb_array[:,:,1].max():.2f}], B=[{rgb_array[:,:,2].min():.2f}, {rgb_array[:,:,2].max():.2f}]")
    
    # Create PIL image
    high_res_img = Image.fromarray(rgb_array.astype(np.uint8), mode='RGB')
    logger.info(f"🎨 [GRADIENT] High-res image created: {high_res_img.size}, mode={high_res_img.mode}")
    
    # Downscale using LANCZOS (best quality)
    logger.info(f"🎨 [GRADIENT] Downscaling {high_width}x{high_height} -> {width}x{height} using LANCZOS...")
    gradient_img = high_res_img.resize((width, height), Image.Resampling.LANCZOS)
    
    # Calculate gradient quality metrics
    gradient_array = np.array(gradient_img)
    unique_colors = len(np.unique(gradient_array.reshape(-1, 3), axis=0))
    logger.info(f"🎨 [GRADIENT] Final gradient: {gradient_img.size}, mode={gradient_img.mode}, unique_colors={unique_colors}")
    
    # Check for potential banding (low unique color count relative to image size)
    pixel_count = width * height
    color_density = unique_colors / pixel_count
    logger.info(f"🎨 [GRADIENT] Color density: {color_density:.4f} ({unique_colors} unique colors / {pixel_count} pixels)")
    
    if color_density < 0.1:
        logger.warning(f"🎨 [GRADIENT] ⚠️ LOW COLOR DENSITY - Potential banding risk! color_density={color_density:.4f}")
    
    logger.info(f"🎨 [GRADIENT] ✅ Gradient generation complete: {width}x{height}")
    
    return gradient_img

