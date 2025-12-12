"""
Product Design System - Category-Aware Visual Design

Defines design profiles for different product categories.
Each category (Electronics, Fashion, Food, Beauty, etc.) gets:
- Specific layout style
- Color scheme preferences
- Typography treatment
- Image handling
- Visual emphasis

Different products need different visual approaches:
- Electronics: Clean, spec-focused, technical
- Fashion: Vibrant, lifestyle imagery, size/color prominent
- Food: Appetizing, close-ups, vibrant colors
- Beauty: Elegant, soft, ingredient-focused
- etc.

This ensures product previews feel native to their category.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# Import product category from product_intelligence
try:
    from backend.services.product_intelligence import ProductCategory
except:
    # Fallback if import fails
    class ProductCategory(Enum):
        ELECTRONICS = "electronics"
        FASHION = "fashion"
        BEAUTY = "beauty"
        FOOD = "food"
        HOME = "home"
        BOOKS = "books"
        DIGITAL = "digital"
        SERVICES = "services"
        TOYS = "toys"
        SPORTS = "sports"
        AUTOMOTIVE = "automotive"
        JEWELRY = "jewelry"
        GENERAL = "general"

logger = logging.getLogger(__name__)


class LayoutStyle(Enum):
    """Layout composition styles."""
    SPLIT = "split"                # 60/40 split (content left, image right)
    HERO = "hero"                  # Large image background, overlay text
    CARD = "card"                  # Card-style with image top, content below
    SHOWCASE = "showcase"          # Product-focused, minimal text
    GRID = "grid"                  # Grid of features/specs
    MINIMAL = "minimal"            # Ultra-minimal, premium feel


class ImageTreatment(Enum):
    """How product images should be handled."""
    CLEAN_BG = "clean_bg"          # Remove background, clean white/gradient
    LIFESTYLE = "lifestyle"         # Keep lifestyle context
    ZOOM = "zoom"                   # Close-up, detailed
    COLLAGE = "collage"             # Multiple images/angles
    TEXTURED = "textured"           # Add texture overlay
    VIBRANT = "vibrant"             # Enhance saturation/vibrancy
    SOFT = "soft"                   # Soft, dreamy enhancement


class ColorScheme(Enum):
    """Color scheme personalities."""
    MINIMAL = "minimal"             # Blacks, whites, grays
    VIBRANT = "vibrant"             # Bold, saturated colors
    LUXE = "luxe"                   # Elegant, sophisticated (golds, deep colors)
    PLAYFUL = "playful"             # Bright, fun colors
    NATURAL = "natural"             # Earthy, organic tones
    TECHNICAL = "technical"         # Blues, techy colors


@dataclass
class CategoryDesignProfile:
    """
    Complete design profile for a product category.
    
    Defines how products in this category should be visually rendered
    for maximum appeal and conversion.
    """
    # Category info
    category: ProductCategory
    category_name: str
    
    # Layout & Composition
    layout_style: LayoutStyle
    image_treatment: ImageTreatment
    color_scheme: ColorScheme
    
    # Typography
    title_weight: str = "bold"  # "normal", "bold", "extra-bold"
    title_size_multiplier: float = 1.0  # 1.0 = default, 1.2 = 20% larger
    use_serif_title: bool = False  # Serif vs sans-serif for title
    
    # Price Display
    price_prominence: str = "prominent"  # "hero", "prominent", "subtle"
    price_position: str = "bottom-left"  # "top-right", "bottom-left", "near-title"
    
    # Visual Elements
    show_gradient: bool = False
    show_texture: bool = False
    show_shadow: bool = True
    corner_radius: str = "medium"  # "none", "small", "medium", "large"
    
    # Image Handling
    image_prominence: float = 1.0  # 1.0 = default, 1.2 = 20% larger
    image_aspect_ratio: str = "16:9"  # "16:9", "1:1", "4:3", "product"
    remove_background: bool = False  # Auto remove image background?
    
    # Trust Signals
    rating_position: str = "below-title"  # "top", "below-title", "near-price"
    rating_style: str = "stars"  # "stars", "number", "both"
    badge_position: str = "top-left"  # "top-left", "top-right", "corner"
    emphasize_reviews: bool = True  # Emphasize review count?
    
    # Feature Display
    feature_style: str = "bullets"  # "bullets", "grid", "badges", "minimal"
    max_features_shown: int = 3  # How many features to show
    show_specs: bool = True  # Show specifications?
    
    # Spacing & Density
    spacing_feel: str = "balanced"  # "compact", "balanced", "spacious"
    content_density: str = "medium"  # "high", "medium", "low"
    
    # Category-specific priorities
    priority_elements: List[str] = field(default_factory=list)
    # e.g., ["product_image", "title", "price", "reviews"] for priority order
    
    # Design reasoning
    design_rationale: str = ""
    conversion_focus: str = ""  # What drives conversion for this category?


# =============================================================================
# CATEGORY DESIGN PROFILES
# =============================================================================

ELECTRONICS_PROFILE = CategoryDesignProfile(
    category=ProductCategory.ELECTRONICS,
    category_name="Electronics",
    
    # Layout
    layout_style=LayoutStyle.SPLIT,
    image_treatment=ImageTreatment.CLEAN_BG,
    color_scheme=ColorScheme.MINIMAL,
    
    # Typography
    title_weight="bold",
    title_size_multiplier=1.0,
    use_serif_title=False,
    
    # Pricing
    price_prominence="prominent",
    price_position="bottom-left",
    
    # Visual
    show_gradient=False,
    show_texture=False,
    show_shadow=True,
    corner_radius="small",
    
    # Image
    image_prominence=1.2,  # Product image is important for electronics
    image_aspect_ratio="1:1",  # Square product shots
    remove_background=True,  # Clean backgrounds look best
    
    # Trust
    rating_position="below-title",
    rating_style="both",  # Stars + number for electronics
    badge_position="top-left",
    emphasize_reviews=True,  # Reviews critical for electronics
    
    # Features
    feature_style="grid",  # Specs in grid format
    max_features_shown=4,  # Show more specs for tech
    show_specs=True,
    
    # Spacing
    spacing_feel="balanced",
    content_density="high",  # More info for electronics
    
    # Priorities
    priority_elements=["product_image", "title", "specs", "price", "reviews"],
    
    # Rationale
    design_rationale="Electronics buyers are spec-focused and research-driven. Clean, technical presentation with prominent specs and reviews builds confidence.",
    conversion_focus="Specifications, reviews, warranty, brand trust"
)


FASHION_PROFILE = CategoryDesignProfile(
    category=ProductCategory.FASHION,
    category_name="Fashion",
    
    # Layout
    layout_style=LayoutStyle.HERO,
    image_treatment=ImageTreatment.LIFESTYLE,
    color_scheme=ColorScheme.VIBRANT,
    
    # Typography
    title_weight="normal",
    title_size_multiplier=1.1,
    use_serif_title=False,
    
    # Pricing
    price_prominence="hero",  # Price very prominent for fashion
    price_position="bottom-left",
    
    # Visual
    show_gradient=True,  # Fashion benefits from gradients
    show_texture=False,
    show_shadow=True,
    corner_radius="medium",
    
    # Image
    image_prominence=1.5,  # Image is KING for fashion
    image_aspect_ratio="4:3",  # Lifestyle shots
    remove_background=False,  # Keep lifestyle context
    
    # Trust
    rating_position="below-title",
    rating_style="stars",  # Just stars, less technical feel
    badge_position="top-right",
    emphasize_reviews=False,  # Less emphasis on review count
    
    # Features
    feature_style="badges",  # Material, fit as badges
    max_features_shown=3,
    show_specs=False,  # No technical specs for fashion
    
    # Spacing
    spacing_feel="spacious",  # Breathing room for fashion
    content_density="low",  # Less clutter
    
    # Priorities
    priority_elements=["product_image", "price", "title", "colors", "sizes"],
    
    # Rationale
    design_rationale="Fashion is visual-first. Large lifestyle images create desire. Price prominence drives impulse purchases. Colors/sizes show variety.",
    conversion_focus="Visual appeal, price, colors/sizes, brand"
)


FOOD_PROFILE = CategoryDesignProfile(
    category=ProductCategory.FOOD,
    category_name="Food",
    
    # Layout
    layout_style=LayoutStyle.HERO,
    image_treatment=ImageTreatment.ZOOM,  # Close-up, appetizing
    color_scheme=ColorScheme.VIBRANT,
    
    # Typography
    title_weight="extra-bold",
    title_size_multiplier=1.15,
    use_serif_title=False,
    
    # Pricing
    price_prominence="prominent",
    price_position="bottom-left",
    
    # Visual
    show_gradient=True,
    show_texture=False,
    show_shadow=True,
    corner_radius="medium",
    
    # Image
    image_prominence=1.6,  # Image is CRITICAL for food
    image_aspect_ratio="16:9",  # Wide, appetizing shots
    remove_background=False,  # Context matters for food
    
    # Trust
    rating_position="below-title",
    rating_style="stars",
    badge_position="top-left",  # "Organic", "Non-GMO" badges
    emphasize_reviews=True,
    
    # Features
    feature_style="badges",  # "Organic", "Gluten-Free" as badges
    max_features_shown=4,  # Show dietary info
    show_specs=False,
    
    # Spacing
    spacing_feel="compact",  # Food can be denser
    content_density="medium",
    
    # Priorities
    priority_elements=["product_image", "title", "badges", "price", "reviews"],
    
    # Rationale
    design_rationale="Food is appetite-driven. Close-up, vibrant images create cravings. Dietary badges (Organic, Non-GMO) build trust. Bold typography matches food boldness.",
    conversion_focus="Visual appeal, dietary certifications, freshness, price"
)


BEAUTY_PROFILE = CategoryDesignProfile(
    category=ProductCategory.BEAUTY,
    category_name="Beauty",
    
    # Layout
    layout_style=LayoutStyle.CARD,
    image_treatment=ImageTreatment.SOFT,  # Soft, elegant
    color_scheme=ColorScheme.LUXE,
    
    # Typography
    title_weight="normal",
    title_size_multiplier=1.0,
    use_serif_title=True,  # Serif for elegance
    
    # Pricing
    price_prominence="prominent",
    price_position="bottom-left",
    
    # Visual
    show_gradient=True,  # Subtle gradients
    show_texture=True,  # Elegant texture
    show_shadow=True,
    corner_radius="large",  # Soft, rounded
    
    # Image
    image_prominence=1.3,
    image_aspect_ratio="1:1",  # Product shots
    remove_background=True,  # Clean, elegant
    
    # Trust
    rating_position="below-title",
    rating_style="both",
    badge_position="top-left",  # "Dermatologist Tested", "Cruelty-Free"
    emphasize_reviews=True,
    
    # Features
    feature_style="bullets",  # Key ingredients as bullets
    max_features_shown=3,
    show_specs=False,
    
    # Spacing
    spacing_feel="spacious",  # Elegant spacing
    content_density="low",  # Clean, minimal
    
    # Priorities
    priority_elements=["product_image", "title", "ingredients", "reviews", "price"],
    
    # Rationale
    design_rationale="Beauty is about aspiration and trust. Elegant, soft visuals create desire. Ingredient transparency and reviews build confidence. Premium feel justifies price.",
    conversion_focus="Ingredients, reviews, skin type fit, brand trust"
)


HOME_PROFILE = CategoryDesignProfile(
    category=ProductCategory.HOME,
    category_name="Home",
    
    # Layout
    layout_style=LayoutStyle.SPLIT,
    image_treatment=ImageTreatment.LIFESTYLE,
    color_scheme=ColorScheme.NATURAL,
    
    # Typography
    title_weight="bold",
    title_size_multiplier=1.0,
    use_serif_title=False,
    
    # Pricing
    price_prominence="prominent",
    price_position="bottom-left",
    
    # Visual
    show_gradient=False,
    show_texture=False,
    show_shadow=True,
    corner_radius="medium",
    
    # Image
    image_prominence=1.3,
    image_aspect_ratio="16:9",
    remove_background=False,
    
    # Trust
    rating_position="below-title",
    rating_style="both",
    badge_position="top-left",
    emphasize_reviews=True,
    
    # Features
    feature_style="bullets",
    max_features_shown=3,
    show_specs=True,  # Dimensions matter for home goods
    
    # Spacing
    spacing_feel="balanced",
    content_density="medium",
    
    # Priorities
    priority_elements=["product_image", "title", "dimensions", "price", "reviews"],
    
    # Rationale
    design_rationale="Home goods need context (lifestyle images). Dimensions/specs critical. Natural, warm feel matches home environment.",
    conversion_focus="Dimensions, materials, durability, reviews"
)


BOOKS_PROFILE = CategoryDesignProfile(
    category=ProductCategory.BOOKS,
    category_name="Books",
    
    # Layout
    layout_style=LayoutStyle.CARD,
    image_treatment=ImageTreatment.CLEAN_BG,
    color_scheme=ColorScheme.MINIMAL,
    
    # Typography
    title_weight="bold",
    title_size_multiplier=1.1,
    use_serif_title=True,  # Serif for books
    
    # Pricing
    price_prominence="subtle",  # Price less important for books
    price_position="bottom-left",
    
    # Visual
    show_gradient=False,
    show_texture=False,
    show_shadow=True,
    corner_radius="small",
    
    # Image
    image_prominence=1.2,  # Book cover important
    image_aspect_ratio="product",  # Book aspect ratio
    remove_background=True,
    
    # Trust
    rating_position="below-title",
    rating_style="both",
    badge_position="top-left",  # "Bestseller", "Award Winner"
    emphasize_reviews=True,  # Reviews critical for books
    
    # Features
    feature_style="bullets",
    max_features_shown=2,
    show_specs=True,  # Pages, format, publisher
    
    # Spacing
    spacing_feel="balanced",
    content_density="medium",
    
    # Priorities
    priority_elements=["cover_image", "title", "author", "reviews", "price"],
    
    # Rationale
    design_rationale="Books are content-driven. Cover art + title + author are key. Reviews heavily influence purchases. Clean, literary feel.",
    conversion_focus="Cover appeal, author credibility, reviews, synopsis"
)


DIGITAL_PROFILE = CategoryDesignProfile(
    category=ProductCategory.DIGITAL,
    category_name="Digital Products",
    
    # Layout
    layout_style=LayoutStyle.MINIMAL,
    image_treatment=ImageTreatment.CLEAN_BG,
    color_scheme=ColorScheme.TECHNICAL,
    
    # Typography
    title_weight="bold",
    title_size_multiplier=1.0,
    use_serif_title=False,
    
    # Pricing
    price_prominence="hero",  # Price very visible for digital
    price_position="bottom-left",
    
    # Visual
    show_gradient=True,  # Tech gradients
    show_texture=False,
    show_shadow=False,  # Flat, modern
    corner_radius="small",
    
    # Image
    image_prominence=1.0,
    image_aspect_ratio="16:9",
    remove_background=True,
    
    # Trust
    rating_position="below-title",
    rating_style="both",
    badge_position="top-left",  # "Instant Download", "Lifetime Access"
    emphasize_reviews=True,
    
    # Features
    feature_style="badges",  # Platform, license type as badges
    max_features_shown=3,
    show_specs=True,
    
    # Spacing
    spacing_feel="spacious",
    content_density="low",
    
    # Priorities
    priority_elements=["icon", "title", "price", "features", "reviews"],
    
    # Rationale
    design_rationale="Digital products need trust signals (reviews, badges). Price prominence important (no shipping). Clean, modern tech aesthetic.",
    conversion_focus="Features, price, instant access, platform compatibility"
)


JEWELRY_PROFILE = CategoryDesignProfile(
    category=ProductCategory.JEWELRY,
    category_name="Jewelry",
    
    # Layout
    layout_style=LayoutStyle.SHOWCASE,
    image_treatment=ImageTreatment.CLEAN_BG,
    color_scheme=ColorScheme.LUXE,
    
    # Typography
    title_weight="normal",
    title_size_multiplier=1.0,
    use_serif_title=True,  # Elegant serif
    
    # Pricing
    price_prominence="subtle",  # Premium pricing shown elegantly
    price_position="bottom-left",
    
    # Visual
    show_gradient=True,  # Luxurious gradients
    show_texture=True,  # Elegant texture
    show_shadow=True,
    corner_radius="large",
    
    # Image
    image_prominence=1.7,  # Image is everything for jewelry
    image_aspect_ratio="1:1",
    remove_background=True,  # Clean, focus on product
    
    # Trust
    rating_position="below-title",
    rating_style="stars",  # Understated
    badge_position="top-left",  # "Handcrafted", "14K Gold"
    emphasize_reviews=False,  # Less emphasis on quantity
    
    # Features
    feature_style="minimal",
    max_features_shown=2,  # Metal, gem type
    show_specs=True,
    
    # Spacing
    spacing_feel="spacious",
    content_density="low",
    
    # Priorities
    priority_elements=["product_image", "title", "material", "price"],
    
    # Rationale
    design_rationale="Jewelry is luxury and aspiration. Showcase the product with elegant, spacious design. Premium feel throughout. Understated pricing.",
    conversion_focus="Visual beauty, craftsmanship, materials, brand prestige"
)


SPORTS_PROFILE = CategoryDesignProfile(
    category=ProductCategory.SPORTS,
    category_name="Sports & Fitness",
    
    # Layout
    layout_style=LayoutStyle.HERO,
    image_treatment=ImageTreatment.LIFESTYLE,
    color_scheme=ColorScheme.VIBRANT,
    
    # Typography
    title_weight="extra-bold",
    title_size_multiplier=1.1,
    use_serif_title=False,
    
    # Pricing
    price_prominence="prominent",
    price_position="bottom-left",
    
    # Visual
    show_gradient=True,
    show_texture=False,
    show_shadow=True,
    corner_radius="medium",
    
    # Image
    image_prominence=1.5,  # Action shots are key
    image_aspect_ratio="16:9",
    remove_background=False,  # Context/action matters
    
    # Trust
    rating_position="below-title",
    rating_style="both",
    badge_position="top-right",
    emphasize_reviews=True,
    
    # Features
    feature_style="badges",  # "Breathable", "Lightweight"
    max_features_shown=3,
    show_specs=True,
    
    # Spacing
    spacing_feel="balanced",
    content_density="medium",
    
    # Priorities
    priority_elements=["product_image", "title", "features", "price", "reviews"],
    
    # Rationale
    design_rationale="Sports/fitness is energetic and aspirational. Dynamic lifestyle images create motivation. Bold typography matches energy. Feature benefits (breathable, lightweight) drive decisions.",
    conversion_focus="Performance features, durability, fit, brand"
)


GENERAL_PROFILE = CategoryDesignProfile(
    category=ProductCategory.GENERAL,
    category_name="General Products",
    
    # Layout
    layout_style=LayoutStyle.SPLIT,
    image_treatment=ImageTreatment.CLEAN_BG,
    color_scheme=ColorScheme.MINIMAL,
    
    # Typography
    title_weight="bold",
    title_size_multiplier=1.0,
    use_serif_title=False,
    
    # Pricing
    price_prominence="prominent",
    price_position="bottom-left",
    
    # Visual
    show_gradient=False,
    show_texture=False,
    show_shadow=True,
    corner_radius="medium",
    
    # Image
    image_prominence=1.2,
    image_aspect_ratio="16:9",
    remove_background=False,
    
    # Trust
    rating_position="below-title",
    rating_style="both",
    badge_position="top-left",
    emphasize_reviews=True,
    
    # Features
    feature_style="bullets",
    max_features_shown=3,
    show_specs=False,
    
    # Spacing
    spacing_feel="balanced",
    content_density="medium",
    
    # Priorities
    priority_elements=["product_image", "title", "price", "reviews"],
    
    # Rationale
    design_rationale="Balanced, universal design that works for any product. Clean, professional, trustworthy.",
    conversion_focus="Price, reviews, clear benefits"
)


# =============================================================================
# Profile Registry
# =============================================================================

CATEGORY_PROFILES: Dict[ProductCategory, CategoryDesignProfile] = {
    ProductCategory.ELECTRONICS: ELECTRONICS_PROFILE,
    ProductCategory.FASHION: FASHION_PROFILE,
    ProductCategory.BEAUTY: BEAUTY_PROFILE,
    ProductCategory.FOOD: FOOD_PROFILE,
    ProductCategory.HOME: HOME_PROFILE,
    ProductCategory.BOOKS: BOOKS_PROFILE,
    ProductCategory.DIGITAL: DIGITAL_PROFILE,
    ProductCategory.JEWELRY: JEWELRY_PROFILE,
    ProductCategory.SPORTS: SPORTS_PROFILE,
    ProductCategory.TOYS: FASHION_PROFILE,  # Similar to fashion (fun, colorful)
    ProductCategory.AUTOMOTIVE: ELECTRONICS_PROFILE,  # Similar to electronics (spec-focused)
    ProductCategory.SERVICES: DIGITAL_PROFILE,  # Similar to digital
    ProductCategory.GENERAL: GENERAL_PROFILE,
}


# =============================================================================
# Product Design System
# =============================================================================

class ProductDesignSystem:
    """
    Central system for category-aware product design.
    
    Provides design profiles for different product categories,
    ensuring visual consistency within categories and appropriate
    differentiation between them.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profiles = CATEGORY_PROFILES
    
    def get_profile(self, category: ProductCategory) -> CategoryDesignProfile:
        """
        Get design profile for a product category.
        
        Args:
            category: ProductCategory enum
        
        Returns:
            CategoryDesignProfile with all design specifications
        """
        profile = self.profiles.get(category, GENERAL_PROFILE)
        self.logger.info(f"🎨 Design profile: {profile.category_name} - {profile.layout_style.value} layout, {profile.color_scheme.value} scheme")
        return profile
    
    def get_profile_by_name(self, category_name: str) -> CategoryDesignProfile:
        """Get design profile by category name string."""
        # Try to find matching category
        for cat, profile in self.profiles.items():
            if cat.value.lower() == category_name.lower():
                return profile
        
        # Fallback to general
        self.logger.warning(f"No profile found for category '{category_name}', using GENERAL")
        return GENERAL_PROFILE
    
    def get_all_profiles(self) -> Dict[ProductCategory, CategoryDesignProfile]:
        """Get all category profiles."""
        return self.profiles


# =============================================================================
# Convenience Functions
# =============================================================================

def get_design_profile(category: ProductCategory) -> CategoryDesignProfile:
    """
    Convenience function to get design profile for a category.
    
    Usage:
        category = ProductCategory.ELECTRONICS
        profile = get_design_profile(category)
        
        # Use profile specs
        layout = profile.layout_style  # LayoutStyle.SPLIT
        show_specs = profile.show_specs  # True for electronics
        price_position = profile.price_prominence  # "prominent"
    """
    system = ProductDesignSystem()
    return system.get_profile(category)


def get_design_profile_by_name(category_name: str) -> CategoryDesignProfile:
    """
    Convenience function to get design profile by category name.
    
    Usage:
        profile = get_design_profile_by_name("electronics")
    """
    system = ProductDesignSystem()
    return system.get_profile_by_name(category_name)
