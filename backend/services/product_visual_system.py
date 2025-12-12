"""
Product Visual Rendering System

Defines how product-specific information should be visually rendered
for maximum conversion impact.

This module translates ProductInformation into visual specifications:
- Urgency signals (deal countdowns, low stock alerts)
- Pricing display (discounts, strikethrough, badges)
- Trust signals (ratings, badges, reviews)
- Dynamic visual hierarchy

Used by:
- OG image generator (preview_image_generator.py)
- Frontend templates (ReconstructedPreview.tsx)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class UrgencyLevel(Enum):
    """Urgency signal intensity levels."""
    CRITICAL = "critical"  # Red, pulsing, maximum attention
    HIGH = "high"          # Orange/amber, prominent
    MEDIUM = "medium"      # Yellow, noticeable
    LOW = "low"            # Subtle indicator
    NONE = "none"          # No urgency


class PriceDisplayStyle(Enum):
    """Pricing display visual styles."""
    SALE_HERO = "sale_hero"          # Maximum impact for big sales
    DISCOUNT = "discount"            # Standard discount display
    PREMIUM = "premium"              # Elegant, understated
    REGULAR = "regular"              # Standard pricing
    SUBSCRIPTION = "subscription"    # Recurring pricing


@dataclass
class ColorSpec:
    """Color specification with hex and RGB."""
    hex: str
    rgb: Tuple[int, int, int]
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'ColorSpec':
        """Create ColorSpec from hex string."""
        hex_clean = hex_color.lstrip('#')
        if len(hex_clean) == 3:
            hex_clean = ''.join([c*2 for c in hex_clean])
        
        try:
            rgb = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
            return cls(hex=f"#{hex_clean}", rgb=rgb)
        except:
            # Fallback to blue
            return cls(hex="#3B82F6", rgb=(59, 130, 246))


@dataclass
class UrgencyBanner:
    """Visual specification for urgency banner."""
    show: bool = False
    message: str = ""
    urgency_level: UrgencyLevel = UrgencyLevel.NONE
    bg_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#DC2626"))
    text_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#FFFFFF"))
    font_size: int = 28
    font_weight: str = "bold"
    position: str = "top"  # "top", "near_price"
    pulse_animation: bool = False
    icon: Optional[str] = None  # "🔥", "⏰", "⚠️"


@dataclass
class DiscountBadge:
    """Visual specification for discount badge."""
    show: bool = False
    text: str = ""  # "-30%", "SALE"
    bg_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#DC2626"))
    text_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#FFFFFF"))
    font_size: int = 36
    font_weight: str = "extra-bold"
    position: str = "top-right-corner"  # "top-right-corner", "near-price", "floating"
    shape: str = "rounded"  # "rounded", "angled", "circular"
    size: str = "large"  # "small", "medium", "large", "extra-large"
    pulse: bool = False


@dataclass
class PriceSpec:
    """Visual specification for price display."""
    # Current price
    current_price: str
    current_price_font_size: int = 40
    current_price_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#1F2937"))
    current_price_weight: str = "bold"
    
    # Original price (if on sale)
    original_price: Optional[str] = None
    original_price_font_size: int = 24
    original_price_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#9CA3AF"))
    show_strikethrough: bool = False
    
    # Display style
    display_style: PriceDisplayStyle = PriceDisplayStyle.REGULAR
    
    # Prominence multiplier (1.0 = default, 1.5 = 50% larger, etc.)
    prominence_multiplier: float = 1.0


@dataclass
class RatingSpec:
    """Visual specification for rating display."""
    show: bool = False
    rating_value: Optional[float] = None
    review_count: Optional[int] = None
    
    # Visual style
    star_size: int = 24
    star_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#F59E0B"))
    number_size: int = 28
    number_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#1F2937"))
    number_weight: str = "bold"
    
    # Prominence (for exceptional ratings)
    is_exceptional: bool = False  # 4.8+ rating
    show_glow: bool = False
    highlight_background: bool = False
    
    # Display options
    show_count: bool = True
    count_format: str = "{count:,} reviews"  # Or "({count:,})"
    layout: str = "horizontal"  # "horizontal", "stacked"


@dataclass
class BadgeSpec:
    """Visual specification for trust badge."""
    text: str
    bg_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#F59E0B"))
    text_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#FFFFFF"))
    font_size: int = 22
    icon: Optional[str] = None  # "🏆", "✓", "⭐"
    position: str = "top-left"  # "top-left", "top-right", "near-title"
    prominence: float = 0.8  # 0.0-1.0, affects size/visibility


@dataclass
class StockIndicator:
    """Visual specification for stock level indicator."""
    show: bool = False
    message: str = ""  # "Only 5 left", "Low stock"
    urgency_level: UrgencyLevel = UrgencyLevel.NONE
    bg_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#FBBF24"))
    text_color: ColorSpec = field(default_factory=lambda: ColorSpec.from_hex("#78350F"))
    font_size: int = 22
    icon: str = "⚠️"
    position: str = "near-price"


@dataclass
class ProductVisualSpec:
    """
    Complete visual specification for a product preview.
    
    This defines HOW to visually render all product information
    for maximum conversion impact.
    """
    # Urgency signals
    urgency_banner: Optional[UrgencyBanner] = None
    stock_indicator: Optional[StockIndicator] = None
    
    # Pricing
    price: Optional[PriceSpec] = None
    discount_badge: Optional[DiscountBadge] = None
    
    # Trust signals
    rating: Optional[RatingSpec] = None
    badges: List[BadgeSpec] = field(default_factory=list)  # Top 2-3 badges
    
    # Visual hierarchy adjustments
    title_size_multiplier: float = 1.0  # Adjust title size based on context
    image_prominence: float = 1.0  # Adjust image size/position
    
    # Overall urgency level (determines overall visual treatment)
    overall_urgency: UrgencyLevel = UrgencyLevel.NONE


class ProductVisualRenderer:
    """
    Generates visual specifications for product previews.
    
    Takes ProductInformation and converts it into concrete visual specs
    that can be rendered by UI or image generation systems.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_visual_spec(self, product_info_dict: Dict[str, Any]) -> ProductVisualSpec:
        """
        Generate complete visual specification from product intelligence.
        
        Args:
            product_info_dict: Product intelligence data (from _product_intelligence in preview reasoning)
        
        Returns:
            ProductVisualSpec with all visual rendering instructions
        """
        spec = ProductVisualSpec()
        
        # Extract data sections
        pricing = product_info_dict.get("pricing", {})
        availability = product_info_dict.get("availability", {})
        rating = product_info_dict.get("rating", {})
        urgency = product_info_dict.get("urgency", {})
        trust_signals = product_info_dict.get("trust_signals", {})
        
        # Generate pricing display
        if pricing.get("current_price"):
            spec.price = self._generate_price_spec(pricing)
        
        # Generate discount badge
        if pricing.get("is_on_sale") and pricing.get("discount_percentage"):
            spec.discount_badge = self._generate_discount_badge(pricing)
        
        # Generate urgency banner
        if urgency.get("has_urgency"):
            spec.urgency_banner = self._generate_urgency_banner(urgency, pricing)
        
        # Generate stock indicator
        if availability.get("limited_quantity") or availability.get("stock_level"):
            spec.stock_indicator = self._generate_stock_indicator(availability)
        
        # Generate rating display
        if rating.get("rating"):
            spec.rating = self._generate_rating_spec(rating)
        
        # Generate badges (top 2)
        if trust_signals.get("badges"):
            spec.badges = self._generate_badge_specs(trust_signals.get("badges", []))
        
        # Determine overall urgency level
        spec.overall_urgency = self._determine_overall_urgency(urgency, availability, pricing)
        
        # Adjust visual hierarchy based on urgency
        if spec.overall_urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            spec.title_size_multiplier = 0.95  # Slightly smaller title to emphasize urgency/price
        
        self.logger.info(f"📐 Visual spec generated: urgency={spec.overall_urgency.value}, sale={spec.discount_badge is not None}")
        
        return spec
    
    def _generate_price_spec(self, pricing: Dict[str, Any]) -> PriceSpec:
        """Generate price display specification."""
        is_on_sale = pricing.get("is_on_sale", False)
        discount_pct = pricing.get("discount_percentage", 0)
        
        if is_on_sale and discount_pct >= 30:
            # BIG SALE - Maximum visual impact
            return PriceSpec(
                current_price=pricing["current_price"],
                current_price_font_size=56,  # 40% larger
                current_price_color=ColorSpec.from_hex("#DC2626"),  # RED
                current_price_weight="extra-bold",
                original_price=pricing.get("original_price"),
                original_price_font_size=28,
                original_price_color=ColorSpec.from_hex("#9CA3AF"),
                show_strikethrough=True,
                display_style=PriceDisplayStyle.SALE_HERO,
                prominence_multiplier=1.4
            )
        
        elif is_on_sale and discount_pct >= 15:
            # MODERATE SALE - Prominent
            return PriceSpec(
                current_price=pricing["current_price"],
                current_price_font_size=48,
                current_price_color=ColorSpec.from_hex("#EF4444"),  # Red-orange
                current_price_weight="bold",
                original_price=pricing.get("original_price"),
                original_price_font_size=24,
                original_price_color=ColorSpec.from_hex("#9CA3AF"),
                show_strikethrough=True,
                display_style=PriceDisplayStyle.DISCOUNT,
                prominence_multiplier=1.2
            )
        
        elif is_on_sale:
            # SMALL SALE - Standard discount display
            return PriceSpec(
                current_price=pricing["current_price"],
                current_price_font_size=44,
                current_price_color=ColorSpec.from_hex("#1F2937"),
                current_price_weight="bold",
                original_price=pricing.get("original_price"),
                original_price_font_size=22,
                original_price_color=ColorSpec.from_hex("#9CA3AF"),
                show_strikethrough=True,
                display_style=PriceDisplayStyle.DISCOUNT,
                prominence_multiplier=1.1
            )
        
        else:
            # REGULAR PRICE - Standard display
            return PriceSpec(
                current_price=pricing["current_price"],
                current_price_font_size=40,
                current_price_color=ColorSpec.from_hex("#1F2937"),
                current_price_weight="bold",
                display_style=PriceDisplayStyle.REGULAR,
                prominence_multiplier=1.0
            )
    
    def _generate_discount_badge(self, pricing: Dict[str, Any]) -> DiscountBadge:
        """Generate discount badge specification."""
        discount_pct = pricing.get("discount_percentage", 0)
        
        if discount_pct >= 50:
            # HUGE DISCOUNT - Maximum impact
            return DiscountBadge(
                show=True,
                text=f"-{discount_pct}%",
                bg_color=ColorSpec.from_hex("#DC2626"),  # Red
                text_color=ColorSpec.from_hex("#FFFFFF"),
                font_size=48,
                font_weight="extra-bold",
                position="top-right-corner",
                shape="angled",  # Diagonal ribbon effect
                size="extra-large",
                pulse=True  # Pulsing animation
            )
        
        elif discount_pct >= 30:
            # BIG DISCOUNT - Very prominent
            return DiscountBadge(
                show=True,
                text=f"-{discount_pct}%",
                bg_color=ColorSpec.from_hex("#EF4444"),  # Red-orange
                text_color=ColorSpec.from_hex("#FFFFFF"),
                font_size=40,
                font_weight="extra-bold",
                position="top-right-corner",
                shape="rounded",
                size="large",
                pulse=True
            )
        
        elif discount_pct >= 15:
            # MODERATE DISCOUNT - Prominent
            return DiscountBadge(
                show=True,
                text=f"-{discount_pct}% OFF",
                bg_color=ColorSpec.from_hex("#F59E0B"),  # Amber/gold
                text_color=ColorSpec.from_hex("#FFFFFF"),
                font_size=32,
                font_weight="bold",
                position="top-right-corner",
                shape="rounded",
                size="medium"
            )
        
        else:
            # SMALL DISCOUNT - Subtle
            return DiscountBadge(
                show=True,
                text=f"Save {discount_pct}%",
                bg_color=ColorSpec.from_hex("#10B981"),  # Green
                text_color=ColorSpec.from_hex("#FFFFFF"),
                font_size=24,
                font_weight="bold",
                position="near-price",
                shape="rounded",
                size="small"
            )
    
    def _generate_urgency_banner(self, urgency: Dict[str, Any], pricing: Dict[str, Any]) -> UrgencyBanner:
        """Generate urgency banner specification."""
        deal_countdown = urgency.get("deal_countdown")
        stock_message = urgency.get("stock_message")
        
        # Combine urgency messages
        messages = []
        if deal_countdown:
            messages.append(f"⏰ {deal_countdown.upper()}")
        if stock_message:
            messages.append(f"{stock_message.upper()}")
        
        message = " • ".join(messages)
        
        # Determine urgency level
        if deal_countdown and ("hour" in deal_countdown.lower() or "minute" in deal_countdown.lower()):
            # Countdown in hours/minutes = CRITICAL
            urgency_level = UrgencyLevel.CRITICAL
        elif stock_message and ("only" in stock_message.lower() or "left" in stock_message.lower()):
            # Low stock = HIGH
            urgency_level = UrgencyLevel.HIGH
        else:
            urgency_level = UrgencyLevel.MEDIUM
        
        return UrgencyBanner(
            show=True,
            message=message,
            urgency_level=urgency_level,
            bg_color=ColorSpec.from_hex("#DC2626") if urgency_level == UrgencyLevel.CRITICAL else ColorSpec.from_hex("#EF4444"),
            text_color=ColorSpec.from_hex("#FFFFFF"),
            font_size=28,
            font_weight="bold",
            position="top",
            pulse_animation=(urgency_level == UrgencyLevel.CRITICAL),
            icon="🔥" if urgency_level == UrgencyLevel.CRITICAL else "⚠️"
        )
    
    def _generate_stock_indicator(self, availability: Dict[str, Any]) -> StockIndicator:
        """Generate stock indicator specification."""
        stock_level = availability.get("stock_level", "")
        limited = availability.get("limited_quantity", False)
        
        if limited or "only" in stock_level.lower():
            urgency_level = UrgencyLevel.HIGH
            bg_color = ColorSpec.from_hex("#FBBF24")  # Amber
            text_color = ColorSpec.from_hex("#78350F")  # Dark amber
        elif "low" in stock_level.lower():
            urgency_level = UrgencyLevel.MEDIUM
            bg_color = ColorSpec.from_hex("#FCD34D")  # Light amber
            text_color = ColorSpec.from_hex("#92400E")
        else:
            urgency_level = UrgencyLevel.LOW
            bg_color = ColorSpec.from_hex("#F3F4F6")  # Gray
            text_color = ColorSpec.from_hex("#6B7280")
        
        return StockIndicator(
            show=True,
            message=stock_level,
            urgency_level=urgency_level,
            bg_color=bg_color,
            text_color=text_color,
            font_size=22,
            icon="⚠️" if urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.MEDIUM] else "✓",
            position="near-price"
        )
    
    def _generate_rating_spec(self, rating: Dict[str, Any]) -> RatingSpec:
        """Generate rating display specification."""
        rating_value = rating.get("rating")
        review_count = rating.get("review_count")
        
        if not rating_value:
            return None
        
        is_exceptional = rating_value >= 4.8
        is_good = rating_value >= 4.5
        
        if is_exceptional:
            # EXCEPTIONAL RATING (4.8+) - Maximum prominence
            return RatingSpec(
                show=True,
                rating_value=rating_value,
                review_count=review_count,
                star_size=32,  # Larger stars
                star_color=ColorSpec.from_hex("#F59E0B"),  # Gold
                number_size=36,
                number_color=ColorSpec.from_hex("#F59E0B"),  # Gold number too
                number_weight="extra-bold",
                is_exceptional=True,
                show_glow=True,  # Subtle glow effect
                highlight_background=True,
                show_count=True,
                count_format="• {count:,} reviews",
                layout="horizontal"
            )
        
        elif is_good:
            # GOOD RATING (4.5-4.7) - Prominent
            return RatingSpec(
                show=True,
                rating_value=rating_value,
                review_count=review_count,
                star_size=28,
                star_color=ColorSpec.from_hex("#F59E0B"),
                number_size=32,
                number_color=ColorSpec.from_hex("#1F2937"),
                number_weight="bold",
                is_exceptional=False,
                show_count=True,
                count_format="({count:,})",
                layout="horizontal"
            )
        
        else:
            # DECENT RATING (4.0-4.4) - Standard, don't emphasize
            return RatingSpec(
                show=True,
                rating_value=rating_value,
                review_count=review_count,
                star_size=24,
                star_color=ColorSpec.from_hex("#9CA3AF"),  # Gray
                number_size=26,
                number_color=ColorSpec.from_hex("#6B7280"),
                number_weight="normal",
                is_exceptional=False,
                show_count=False,  # Don't show count for lower ratings
                layout="horizontal"
            )
    
    def _generate_badge_specs(self, badges: List[str]) -> List[BadgeSpec]:
        """Generate badge specifications (prioritized top 2)."""
        # Badge priority order
        priority_map = {
            "best seller": 1.0,
            "bestseller": 1.0,
            "amazon's choice": 0.95,
            "amazons choice": 0.95,
            "#1": 0.9,
            "number 1": 0.9,
            "top rated": 0.85,
            "editor's pick": 0.8,
            "trending": 0.75,
            "new arrival": 0.7,
            "free shipping": 0.65,
            "limited edition": 0.6
        }
        
        # Score and sort badges
        scored_badges = []
        for badge in badges[:10]:  # Only consider top 10
            badge_lower = badge.lower()
            score = 0.5  # Default score
            for keyword, priority in priority_map.items():
                if keyword in badge_lower:
                    score = priority
                    break
            scored_badges.append((badge, score))
        
        # Sort by score, take top 2
        scored_badges.sort(key=lambda x: x[1], reverse=True)
        top_badges = [b[0] for b in scored_badges[:2]]
        
        # Generate specs
        badge_specs = []
        for i, badge_text in enumerate(top_badges):
            # Determine color based on badge type
            badge_lower = badge_text.lower()
            
            if "best seller" in badge_lower or "bestseller" in badge_lower:
                bg_color = ColorSpec.from_hex("#F59E0B")  # Gold
                icon = "🏆"
                prominence = 0.9
            elif "amazon's choice" in badge_lower or "amazons choice" in badge_lower:
                bg_color = ColorSpec.from_hex("#3B82F6")  # Blue
                icon = "⭐"
                prominence = 0.9
            elif "#1" in badge_lower or "number 1" in badge_lower:
                bg_color = ColorSpec.from_hex("#8B5CF6")  # Purple
                icon = "👑"
                prominence = 0.85
            elif "free shipping" in badge_lower:
                bg_color = ColorSpec.from_hex("#10B981")  # Green
                icon = "🚚"
                prominence = 0.7
            else:
                bg_color = ColorSpec.from_hex("#6B7280")  # Gray
                icon = "✓"
                prominence = 0.6
            
            position = "top-left" if i == 0 else "top-right"
            
            badge_specs.append(BadgeSpec(
                text=badge_text,
                bg_color=bg_color,
                text_color=ColorSpec.from_hex("#FFFFFF"),
                font_size=22,
                icon=icon,
                position=position,
                prominence=prominence
            ))
        
        return badge_specs
    
    def _determine_overall_urgency(
        self,
        urgency: Dict[str, Any],
        availability: Dict[str, Any],
        pricing: Dict[str, Any]
    ) -> UrgencyLevel:
        """Determine overall urgency level for the product."""
        has_deal_countdown = bool(urgency.get("deal_countdown"))
        has_low_stock = availability.get("limited_quantity", False)
        has_big_sale = pricing.get("discount_percentage", 0) >= 30
        
        # Deal countdown in hours/minutes = CRITICAL
        if has_deal_countdown:
            countdown = urgency.get("deal_countdown", "").lower()
            if "hour" in countdown or "minute" in countdown:
                return UrgencyLevel.CRITICAL
        
        # Big sale + low stock = CRITICAL
        if has_big_sale and has_low_stock:
            return UrgencyLevel.CRITICAL
        
        # Low stock or moderate sale = HIGH
        if has_low_stock or (pricing.get("discount_percentage", 0) >= 20):
            return UrgencyLevel.HIGH
        
        # Small sale = MEDIUM
        if pricing.get("is_on_sale"):
            return UrgencyLevel.MEDIUM
        
        return UrgencyLevel.NONE


# =============================================================================
# Convenience Functions
# =============================================================================

def generate_product_visual_spec(product_info_dict: Dict[str, Any]) -> ProductVisualSpec:
    """
    Convenience function to generate product visual specification.
    
    Usage:
        # From preview_reasoning data
        product_info = data.get("_product_intelligence", {})
        visual_spec = generate_product_visual_spec(product_info)
        
        # Use in OG image generation
        if visual_spec.urgency_banner:
            render_urgency_banner(visual_spec.urgency_banner)
        
        if visual_spec.price:
            render_price(visual_spec.price)
    """
    renderer = ProductVisualRenderer()
    return renderer.generate_visual_spec(product_info_dict)
