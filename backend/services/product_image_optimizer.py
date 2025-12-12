"""
Product Image Optimizer

Category-specific image enhancement for maximum visual appeal.
Different product categories benefit from different image treatments:
- Electronics: Sharp, precise, clean
- Fashion: Vibrant, saturated
- Food: Very vibrant, high contrast (appetite appeal)
- Beauty: Soft, brightened, elegant
- Home: Natural, balanced
"""

import logging
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional

try:
    from backend.services.product_intelligence import ProductCategory
except:
    from enum import Enum
    class ProductCategory(Enum):
        ELECTRONICS = "electronics"
        FASHION = "fashion"
        BEAUTY = "beauty"
        FOOD = "food"
        HOME = "home"
        GENERAL = "general"

logger = logging.getLogger(__name__)


class ProductImageOptimizer:
    """
    Optimize product images based on category for maximum appeal.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize(
        self,
        image: Image.Image,
        category: ProductCategory,
        is_on_sale: bool = False
    ) -> Image.Image:
        """
        Optimize image for product category.
        
        Args:
            image: PIL Image
            category: Product category
            is_on_sale: Whether product is on sale (may add warmth/glow)
        
        Returns:
            Optimized PIL Image
        """
        if category == ProductCategory.ELECTRONICS:
            return self._optimize_electronics(image)
        elif category == ProductCategory.FASHION:
            return self._optimize_fashion(image, is_on_sale)
        elif category == ProductCategory.FOOD:
            return self._optimize_food(image)
        elif category == ProductCategory.BEAUTY:
            return self._optimize_beauty(image)
        elif category == ProductCategory.HOME:
            return self._optimize_home(image)
        else:
            return self._optimize_general(image)
    
    def _optimize_electronics(self, image: Image.Image) -> Image.Image:
        """
        Electronics: Sharp, precise, clean.
        Emphasize technical precision.
        """
        # Sharpen for clarity
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120))
        
        # Slight contrast boost for depth
        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(1.05)
        
        self.logger.debug("📱 Optimized for electronics: sharp, precise")
        return image
    
    def _optimize_fashion(self, image: Image.Image, is_on_sale: bool = False) -> Image.Image:
        """
        Fashion: Vibrant, saturated.
        Make colors pop to attract attention.
        """
        # Boost saturation for vibrant colors
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.15)  # +15% saturation
        
        # Slight sharpening for detail
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120))
        
        # If on sale, add warmth (slight red/orange tint creates excitement)
        if is_on_sale:
            # Slight brightness boost
            brightness = ImageEnhance.Brightness(image)
            image = brightness.enhance(1.03)
        
        self.logger.debug("👕 Optimized for fashion: vibrant, saturated")
        return image
    
    def _optimize_food(self, image: Image.Image) -> Image.Image:
        """
        Food: Very vibrant, high contrast.
        Create appetite appeal through vivid colors.
        """
        # STRONG saturation boost for food
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.25)  # +25% saturation
        
        # Increase contrast for depth
        contrast = ImageEnhance.Contrast(image)
        image = contrast.enhance(1.1)  # +10% contrast
        
        # Sharp for detail (texture matters for food)
        image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
        
        # Slight warmth boost (warm colors = appetizing)
        brightness = ImageEnhance.Brightness(image)
        image = brightness.enhance(1.02)
        
        self.logger.debug("🍕 Optimized for food: very vibrant, high contrast")
        return image
    
    def _optimize_beauty(self, image: Image.Image) -> Image.Image:
        """
        Beauty: Soft, brightened, elegant.
        Create aspiration through soft, dreamy imagery.
        """
        # Slight brightness boost for glow
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05)  # +5% brightness
        
        # Subtle saturation increase
        color = ImageEnhance.Color(image)
        image = color.enhance(1.08)  # +8% saturation
        
        # DON'T over-sharpen beauty products (soft = elegant)
        # Very subtle sharpening only
        image = image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=100))
        
        self.logger.debug("💄 Optimized for beauty: soft, brightened, elegant")
        return image
    
    def _optimize_home(self, image: Image.Image) -> Image.Image:
        """
        Home: Natural, balanced.
        Warm, inviting feeling for home goods.
        """
        # Slight warmth
        brightness = ImageEnhance.Brightness(image)
        image = brightness.enhance(1.03)
        
        # Balanced saturation
        color = ImageEnhance.Color(image)
        image = color.enhance(1.05)
        
        # Moderate sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=110))
        
        self.logger.debug("🏠 Optimized for home: natural, balanced, warm")
        return image
    
    def _optimize_general(self, image: Image.Image) -> Image.Image:
        """
        General: Balanced enhancement.
        Works for any product type.
        """
        # Slight saturation boost
        color = ImageEnhance.Color(image)
        image = color.enhance(1.08)
        
        # Slight sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=110))
        
        self.logger.debug("📦 Optimized for general: balanced enhancement")
        return image


# =============================================================================
# Convenience Function
# =============================================================================

def optimize_product_image(
    image: Image.Image,
    category: ProductCategory,
    is_on_sale: bool = False
) -> Image.Image:
    """
    Convenience function for product image optimization.
    
    Usage:
        from PIL import Image
        from backend.services.product_image_optimizer import optimize_product_image
        from backend.services.product_intelligence import ProductCategory
        
        image = Image.open("product.jpg")
        optimized = optimize_product_image(image, ProductCategory.FOOD)
    """
    optimizer = ProductImageOptimizer()
    return optimizer.optimize(image, category, is_on_sale)
