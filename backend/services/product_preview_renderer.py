"""
Product Preview Renderer - Specialized rendering for e-commerce previews.

This module creates high-conversion product previews with:
1. Price badges with discount highlighting
2. Stock urgency indicators
3. Rating stars with review counts
4. Trust badges (Prime, Free Shipping, etc.)
5. Product-specific layouts

Designed to maximize click-through rates for e-commerce URLs.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class UrgencyLevel(str, Enum):
    """Urgency levels for product availability."""
    CRITICAL = "critical"  # "Only 1 left!"
    HIGH = "high"  # "Only 5 left", "Ends in 2 hours"
    MEDIUM = "medium"  # "Low stock", "Sale ends tomorrow"
    LOW = "low"  # "In stock"
    NONE = "none"


class BadgeType(str, Enum):
    """Types of product badges."""
    BEST_SELLER = "best_seller"
    AMAZON_CHOICE = "amazon_choice"
    TOP_RATED = "top_rated"
    NEW_ARRIVAL = "new_arrival"
    LIMITED_EDITION = "limited_edition"
    SALE = "sale"
    CLEARANCE = "clearance"
    FREE_SHIPPING = "free_shipping"
    PRIME = "prime"
    TRENDING = "trending"
    HOT = "hot"


@dataclass
class PricingDisplay:
    """Pricing information for display."""
    current_price: str  # Formatted price (e.g., "$149.99")
    original_price: Optional[str] = None  # If on sale
    discount_percentage: Optional[int] = None
    discount_text: Optional[str] = None  # "Save 20%"
    currency_symbol: str = "$"
    is_on_sale: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_price": self.current_price,
            "original_price": self.original_price,
            "discount_percentage": self.discount_percentage,
            "discount_text": self.discount_text,
            "currency_symbol": self.currency_symbol,
            "is_on_sale": self.is_on_sale
        }


@dataclass
class RatingDisplay:
    """Rating information for display."""
    stars: float  # 0-5
    review_count: int
    stars_display: str  # "★★★★☆"
    count_display: str  # "2,847 reviews"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stars": self.stars,
            "review_count": self.review_count,
            "stars_display": self.stars_display,
            "count_display": self.count_display
        }


@dataclass
class UrgencyDisplay:
    """Urgency information for display."""
    level: UrgencyLevel
    message: str  # "Only 3 left in stock!"
    countdown: Optional[str] = None  # "Ends in 2h 15m"
    color: str = "#DC2626"  # Red for urgency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "message": self.message,
            "countdown": self.countdown,
            "color": self.color
        }


@dataclass
class ProductBadge:
    """A product badge for display."""
    badge_type: BadgeType
    text: str
    color: str
    background_color: str
    icon: Optional[str] = None  # Icon name or emoji
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "badge_type": self.badge_type.value,
            "text": self.text,
            "color": self.color,
            "background_color": self.background_color,
            "icon": self.icon
        }


@dataclass
class ProductRenderData:
    """Complete product rendering data."""
    title: str
    description: Optional[str]
    pricing: PricingDisplay
    rating: Optional[RatingDisplay]
    urgency: Optional[UrgencyDisplay]
    badges: List[ProductBadge]
    features: List[str]  # Key feature bullets
    brand: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    trust_signals: List[str]  # "Free Shipping", "30-day returns"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "pricing": self.pricing.to_dict(),
            "rating": self.rating.to_dict() if self.rating else None,
            "urgency": self.urgency.to_dict() if self.urgency else None,
            "badges": [b.to_dict() for b in self.badges],
            "features": self.features,
            "brand": self.brand,
            "category": self.category,
            "image_url": self.image_url,
            "trust_signals": self.trust_signals
        }


# Badge styling configurations
BADGE_STYLES: Dict[BadgeType, Dict[str, str]] = {
    BadgeType.BEST_SELLER: {
        "text": "Best Seller",
        "color": "#FFFFFF",
        "background_color": "#F59E0B",
        "icon": "🏆"
    },
    BadgeType.AMAZON_CHOICE: {
        "text": "Amazon's Choice",
        "color": "#FFFFFF",
        "background_color": "#232F3E",
        "icon": "✓"
    },
    BadgeType.TOP_RATED: {
        "text": "Top Rated",
        "color": "#FFFFFF",
        "background_color": "#10B981",
        "icon": "⭐"
    },
    BadgeType.NEW_ARRIVAL: {
        "text": "New",
        "color": "#FFFFFF",
        "background_color": "#3B82F6",
        "icon": "✨"
    },
    BadgeType.LIMITED_EDITION: {
        "text": "Limited Edition",
        "color": "#FFFFFF",
        "background_color": "#8B5CF6",
        "icon": "💎"
    },
    BadgeType.SALE: {
        "text": "Sale",
        "color": "#FFFFFF",
        "background_color": "#DC2626",
        "icon": "🔥"
    },
    BadgeType.CLEARANCE: {
        "text": "Clearance",
        "color": "#FFFFFF",
        "background_color": "#DC2626",
        "icon": "📢"
    },
    BadgeType.FREE_SHIPPING: {
        "text": "Free Shipping",
        "color": "#047857",
        "background_color": "#D1FAE5",
        "icon": "📦"
    },
    BadgeType.PRIME: {
        "text": "Prime",
        "color": "#FFFFFF",
        "background_color": "#00A8E1",
        "icon": "✓"
    },
    BadgeType.TRENDING: {
        "text": "Trending",
        "color": "#FFFFFF",
        "background_color": "#EC4899",
        "icon": "📈"
    },
    BadgeType.HOT: {
        "text": "Hot",
        "color": "#FFFFFF",
        "background_color": "#EF4444",
        "icon": "🔥"
    }
}


class ProductPreviewRenderer:
    """
    Renders product-specific preview elements.
    
    Extracts and formats:
    - Pricing with sale indicators
    - Star ratings
    - Urgency signals
    - Trust badges
    - Key features
    """
    
    def __init__(self):
        """Initialize the renderer."""
        logger.info("🛍️ ProductPreviewRenderer initialized")
    
    def render(
        self,
        preview_data: Dict[str, Any],
        product_intelligence: Optional[Dict[str, Any]] = None
    ) -> ProductRenderData:
        """
        Render product-specific preview data.
        
        Args:
            preview_data: General preview data
            product_intelligence: Extracted product intelligence
            
        Returns:
            ProductRenderData with formatted product elements
        """
        logger.info("🛍️ Rendering product preview")
        
        # Extract basic info
        title = preview_data.get("title", "Product")
        description = preview_data.get("description")
        
        # Extract from product intelligence if available
        pi = product_intelligence or {}
        
        # Build pricing display
        pricing = self._build_pricing(pi, preview_data)
        
        # Build rating display
        rating = self._build_rating(pi, preview_data)
        
        # Build urgency display
        urgency = self._build_urgency(pi, preview_data)
        
        # Build badges
        badges = self._build_badges(pi, preview_data)
        
        # Extract features
        features = self._extract_features(pi, preview_data)
        
        # Extract trust signals
        trust_signals = self._extract_trust_signals(pi, preview_data)
        
        # Build render data
        render_data = ProductRenderData(
            title=title,
            description=description,
            pricing=pricing,
            rating=rating,
            urgency=urgency,
            badges=badges,
            features=features[:5],  # Max 5 features
            brand=pi.get("brand") or preview_data.get("brand"),
            category=pi.get("category") or preview_data.get("category"),
            image_url=preview_data.get("image_url"),
            trust_signals=trust_signals[:3]  # Max 3 trust signals
        )
        
        logger.info(
            f"✅ Product render complete: "
            f"price={pricing.current_price}, "
            f"rating={rating.stars if rating else 'N/A'}★, "
            f"badges={len(badges)}, "
            f"urgency={urgency.level.value if urgency else 'none'}"
        )
        
        return render_data
    
    def _build_pricing(
        self,
        pi: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> PricingDisplay:
        """Build pricing display from extracted data."""
        pricing_data = pi.get("pricing", {})
        
        current_price = pricing_data.get("current_price")
        original_price = pricing_data.get("original_price")
        discount_pct = pricing_data.get("discount_percentage")
        
        # Try to extract from preview data if not in PI
        if not current_price:
            # Look for price patterns in subtitle/description
            text = preview_data.get("subtitle", "") + " " + preview_data.get("description", "")
            current_price = self._extract_price_from_text(text)
        
        # Format prices
        if current_price:
            if not current_price.startswith("$") and not current_price.startswith("€"):
                current_price = f"${current_price}"
        else:
            current_price = ""
        
        if original_price:
            if not original_price.startswith("$") and not original_price.startswith("€"):
                original_price = f"${original_price}"
        
        # Determine if on sale
        is_on_sale = bool(original_price and discount_pct)
        
        # Build discount text
        discount_text = None
        if discount_pct:
            discount_text = f"Save {discount_pct}%"
        
        return PricingDisplay(
            current_price=current_price,
            original_price=original_price,
            discount_percentage=discount_pct,
            discount_text=discount_text,
            currency_symbol="$",
            is_on_sale=is_on_sale
        )
    
    def _build_rating(
        self,
        pi: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> Optional[RatingDisplay]:
        """Build rating display from extracted data."""
        rating_data = pi.get("rating", {})
        
        stars = rating_data.get("value") or rating_data.get("rating")
        count = rating_data.get("count") or rating_data.get("review_count")
        
        # Try to extract from preview data
        if not stars:
            # Look for rating patterns
            text = preview_data.get("subtitle", "") + " " + str(preview_data.get("social_proof", ""))
            stars, count = self._extract_rating_from_text(text)
        
        if not stars:
            return None
        
        # Build star display
        full_stars = int(stars)
        half_star = stars - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        stars_display = "★" * full_stars
        if half_star:
            stars_display += "☆"
        stars_display += "☆" * empty_stars
        
        # Format count
        count_display = ""
        if count:
            if count >= 1000:
                count_display = f"{count:,} reviews"
            else:
                count_display = f"{count} reviews"
        
        return RatingDisplay(
            stars=float(stars),
            review_count=int(count) if count else 0,
            stars_display=stars_display,
            count_display=count_display
        )
    
    def _build_urgency(
        self,
        pi: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> Optional[UrgencyDisplay]:
        """Build urgency display from extracted data."""
        availability = pi.get("availability", {})
        urgency_data = pi.get("urgency", {})
        
        # Check stock level
        stock_level = availability.get("stock_level") or urgency_data.get("stock_message")
        stock_quantity = availability.get("stock_quantity")
        deal_countdown = urgency_data.get("deal_countdown") or pi.get("pricing", {}).get("deal_ends")
        
        # Determine urgency level
        level = UrgencyLevel.NONE
        message = ""
        
        if stock_quantity:
            if stock_quantity <= 3:
                level = UrgencyLevel.CRITICAL
                message = f"Only {stock_quantity} left in stock!"
            elif stock_quantity <= 10:
                level = UrgencyLevel.HIGH
                message = f"Only {stock_quantity} left"
            elif stock_quantity <= 25:
                level = UrgencyLevel.MEDIUM
                message = "Low stock"
        elif stock_level:
            stock_lower = stock_level.lower()
            if "only" in stock_lower or "last" in stock_lower:
                level = UrgencyLevel.HIGH
                message = stock_level
            elif "low" in stock_lower:
                level = UrgencyLevel.MEDIUM
                message = stock_level
        
        # Check deal countdown
        if deal_countdown:
            if level == UrgencyLevel.NONE:
                level = UrgencyLevel.MEDIUM
            message = message or "Limited time deal"
        
        if level == UrgencyLevel.NONE:
            return None
        
        # Determine color
        colors = {
            UrgencyLevel.CRITICAL: "#DC2626",  # Red
            UrgencyLevel.HIGH: "#EA580C",  # Orange
            UrgencyLevel.MEDIUM: "#D97706",  # Amber
            UrgencyLevel.LOW: "#65A30D"  # Lime
        }
        
        return UrgencyDisplay(
            level=level,
            message=message,
            countdown=deal_countdown,
            color=colors.get(level, "#DC2626")
        )
    
    def _build_badges(
        self,
        pi: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> List[ProductBadge]:
        """Build badges from extracted data."""
        badges = []
        
        # Check for badges in product intelligence
        badge_texts = pi.get("badges", []) or pi.get("trust_signals", {}).get("badges", [])
        
        for badge_text in badge_texts[:3]:  # Max 3 badges
            badge_type = self._classify_badge(badge_text)
            style = BADGE_STYLES.get(badge_type, BADGE_STYLES[BadgeType.SALE])
            
            badges.append(ProductBadge(
                badge_type=badge_type,
                text=style["text"],
                color=style["color"],
                background_color=style["background_color"],
                icon=style.get("icon")
            ))
        
        # Add sale badge if on sale and no sale badge yet
        pricing = pi.get("pricing", {})
        if pricing.get("is_on_sale") or pricing.get("discount_percentage"):
            if not any(b.badge_type == BadgeType.SALE for b in badges):
                style = BADGE_STYLES[BadgeType.SALE]
                discount = pricing.get("discount_percentage")
                text = f"{discount}% OFF" if discount else "Sale"
                badges.insert(0, ProductBadge(
                    badge_type=BadgeType.SALE,
                    text=text,
                    color=style["color"],
                    background_color=style["background_color"],
                    icon=style.get("icon")
                ))
        
        return badges[:4]  # Max 4 badges
    
    def _extract_features(
        self,
        pi: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> List[str]:
        """Extract key features."""
        features = []
        
        # From product intelligence
        pi_features = pi.get("features", {}).get("key_features", [])
        features.extend(pi_features)
        
        # From tags
        if preview_data.get("tags"):
            for tag in preview_data["tags"][:3]:
                if tag not in features:
                    features.append(tag)
        
        return features[:5]
    
    def _extract_trust_signals(
        self,
        pi: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> List[str]:
        """Extract trust signals."""
        signals = []
        
        trust_data = pi.get("trust_signals", {})
        
        if trust_data.get("shipping"):
            signals.append(trust_data["shipping"])
        if trust_data.get("returns"):
            signals.append(trust_data["returns"])
        if trust_data.get("warranty"):
            signals.append(trust_data["warranty"])
        
        return signals[:3]
    
    def _extract_price_from_text(self, text: str) -> Optional[str]:
        """Extract price from text using patterns."""
        import re
        
        # Look for price patterns: $XX.XX, €XX.XX, XX.XX USD, etc.
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'€[\d,]+\.?\d*',
            r'£[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:USD|EUR|GBP)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_rating_from_text(self, text: str) -> Tuple[Optional[float], Optional[int]]:
        """Extract rating from text."""
        import re
        
        # Pattern: X.X★ or X.X stars or X.X/5
        rating_patterns = [
            r'(\d+\.?\d*)\s*★',
            r'(\d+\.?\d*)\s*stars?',
            r'(\d+\.?\d*)\s*/\s*5',
            r'(\d+\.?\d*)(?:\s*out\s*of\s*5)?'
        ]
        
        rating = None
        for pattern in rating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    if 0 <= val <= 5:
                        rating = val
                        break
                except:
                    pass
        
        # Look for review count
        count = None
        count_patterns = [
            r'(\d+[,\d]*)\s*reviews?',
            r'\((\d+[,\d]*)\)',
        ]
        
        for pattern in count_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    count = int(match.group(1).replace(",", ""))
                    break
                except:
                    pass
        
        return rating, count
    
    def _classify_badge(self, badge_text: str) -> BadgeType:
        """Classify badge text into badge type."""
        text_lower = badge_text.lower()
        
        if "best seller" in text_lower:
            return BadgeType.BEST_SELLER
        elif "amazon" in text_lower and "choice" in text_lower:
            return BadgeType.AMAZON_CHOICE
        elif "top rated" in text_lower or "highest rated" in text_lower:
            return BadgeType.TOP_RATED
        elif "new" in text_lower:
            return BadgeType.NEW_ARRIVAL
        elif "limited" in text_lower:
            return BadgeType.LIMITED_EDITION
        elif "clearance" in text_lower:
            return BadgeType.CLEARANCE
        elif "free ship" in text_lower:
            return BadgeType.FREE_SHIPPING
        elif "prime" in text_lower:
            return BadgeType.PRIME
        elif "trending" in text_lower:
            return BadgeType.TRENDING
        elif "hot" in text_lower or "fire" in text_lower:
            return BadgeType.HOT
        else:
            return BadgeType.SALE  # Default


# Singleton instance
_renderer_instance: Optional[ProductPreviewRenderer] = None


def get_product_renderer() -> ProductPreviewRenderer:
    """Get or create the product renderer singleton."""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = ProductPreviewRenderer()
    return _renderer_instance


def render_product_preview(
    preview_data: Dict[str, Any],
    product_intelligence: Optional[Dict[str, Any]] = None
) -> ProductRenderData:
    """Convenience function to render a product preview."""
    renderer = get_product_renderer()
    return renderer.render(preview_data, product_intelligence)

