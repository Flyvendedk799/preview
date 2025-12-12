"""
Product Intelligence System

Extracts comprehensive product-specific information from web pages.
Goes far beyond basic extraction to capture:
- Pricing (current, original, discounts, deals)
- Availability (stock levels, pre-orders)
- Reviews & Ratings (with exact numbers)
- Product details (brand, category, specs)
- Features (key selling points)
- Variants (colors, sizes)
- Badges & Trust signals
- Urgency indicators (deal ends, low stock)
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ProductCategory(Enum):
    """Product categories for specialized handling."""
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


class BadgeType(Enum):
    """Types of product badges/labels."""
    BEST_SELLER = "best_seller"
    AMAZONS_CHOICE = "amazons_choice"
    TOP_RATED = "top_rated"
    NEW_ARRIVAL = "new_arrival"
    LIMITED_EDITION = "limited_edition"
    VERIFIED_SELLER = "verified_seller"
    FREE_SHIPPING = "free_shipping"
    SALE = "sale"
    CLEARANCE = "clearance"
    LOW_STOCK = "low_stock"
    EDITORS_PICK = "editors_pick"
    TRENDING = "trending"
    NUMBER_ONE = "number_one"


@dataclass
class PricingInfo:
    """Detailed pricing information."""
    current_price: Optional[str] = None
    current_price_value: Optional[float] = None  # Numeric value
    original_price: Optional[str] = None
    original_price_value: Optional[float] = None  # Numeric value
    discount_percentage: Optional[int] = None
    discount_amount: Optional[str] = None
    currency: str = "USD"
    currency_symbol: str = "$"
    is_on_sale: bool = False
    deal_ends: Optional[str] = None  # "Ends in 2 hours", "Sale ends Dec 25"
    subscription_price: Optional[str] = None  # For subscription products


@dataclass
class AvailabilityInfo:
    """Product availability information."""
    in_stock: bool = True
    stock_level: Optional[str] = None  # "Low Stock", "Only 3 left"
    stock_quantity: Optional[int] = None  # Exact number if available
    availability_date: Optional[str] = None  # For pre-orders
    limited_quantity: bool = False
    backorder_available: bool = False


@dataclass
class RatingInfo:
    """Comprehensive rating & review information."""
    rating: Optional[float] = None  # 4.8
    rating_display: Optional[str] = None  # "4.8 out of 5 stars"
    review_count: Optional[int] = None  # 2847
    review_count_display: Optional[str] = None  # "2,847 reviews"
    rating_breakdown: Optional[Dict[int, int]] = None  # {5: 1200, 4: 500, ...}
    verified_purchase_count: Optional[int] = None
    verified_purchase_percentage: Optional[int] = None
    answered_questions: Optional[int] = None


@dataclass
class ProductDetails:
    """Core product details."""
    brand: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None  # "Electronics"
    subcategory: Optional[str] = None  # "Laptops"
    product_type: ProductCategory = ProductCategory.GENERAL
    asin_or_sku: Optional[str] = None  # Product ID
    upc: Optional[str] = None


@dataclass
class ProductFeatures:
    """Product features and specifications."""
    key_features: List[str] = field(default_factory=list)  # Top 3-5 bullet points
    specifications: Dict[str, str] = field(default_factory=dict)
    description_highlights: List[str] = field(default_factory=list)
    whats_in_box: List[str] = field(default_factory=list)


@dataclass
class ProductVariants:
    """Product variant information."""
    has_variants: bool = False
    variant_types: List[str] = field(default_factory=list)  # ["Color", "Size"]
    available_colors: List[str] = field(default_factory=list)
    available_sizes: List[str] = field(default_factory=list)
    selected_variant: Optional[str] = None


@dataclass
class TrustSignals:
    """Trust and credibility signals."""
    badges: List[str] = field(default_factory=list)  # ["Best Seller", "Amazon's Choice"]
    badge_types: List[BadgeType] = field(default_factory=list)
    shipping_info: Optional[str] = None  # "Free Shipping", "Prime"
    return_policy: Optional[str] = None  # "Free Returns", "30-day return"
    warranty: Optional[str] = None  # "2-year warranty"
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = None
    verified_seller: bool = False
    certifications: List[str] = field(default_factory=list)  # ["USDA Organic", "Fair Trade"]


@dataclass
class UrgencySignals:
    """Urgency and scarcity indicators."""
    has_urgency: bool = False
    deal_countdown: Optional[str] = None  # "Ends in 2 hours"
    limited_stock: bool = False
    stock_message: Optional[str] = None  # "Only 3 left"
    popularity_signal: Optional[str] = None  # "500+ bought this week"
    trending: bool = False
    fast_selling: bool = False


@dataclass
class ProductInformation:
    """
    Comprehensive product information.
    
    This is the complete data structure that the Product Intelligence system
    extracts from product pages.
    """
    # Core info
    product_name: Optional[str] = None
    product_subtitle: Optional[str] = None
    
    # Structured data
    pricing: PricingInfo = field(default_factory=PricingInfo)
    availability: AvailabilityInfo = field(default_factory=AvailabilityInfo)
    rating: RatingInfo = field(default_factory=RatingInfo)
    details: ProductDetails = field(default_factory=ProductDetails)
    features: ProductFeatures = field(default_factory=ProductFeatures)
    variants: ProductVariants = field(default_factory=ProductVariants)
    trust_signals: TrustSignals = field(default_factory=TrustSignals)
    urgency_signals: UrgencySignals = field(default_factory=UrgencySignals)
    
    # Metadata
    extraction_confidence: float = 0.0
    extraction_timestamp: Optional[str] = None


class ProductIntelligenceExtractor:
    """
    Extract comprehensive product information from AI analysis and HTML.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract(
        self,
        ai_analysis: Dict[str, Any],
        html_content: Optional[str] = None,
        url: Optional[str] = None
    ) -> ProductInformation:
        """
        Extract comprehensive product information.
        
        Args:
            ai_analysis: AI-extracted data (from GPT-4 Vision)
            html_content: Raw HTML (optional, for fallback)
            url: Product page URL (optional, for context)
        
        Returns:
            ProductInformation with all extracted data
        """
        self.logger.info("🛍️ Extracting product intelligence...")
        
        product_info = ProductInformation()
        product_info.extraction_timestamp = datetime.utcnow().isoformat()
        
        # Extract pricing
        product_info.pricing = self._extract_pricing(ai_analysis, html_content)
        
        # Extract availability
        product_info.availability = self._extract_availability(ai_analysis, html_content)
        
        # Extract ratings & reviews
        product_info.rating = self._extract_rating(ai_analysis, html_content)
        
        # Extract product details
        product_info.details = self._extract_details(ai_analysis, url)
        
        # Extract features
        product_info.features = self._extract_features(ai_analysis)
        
        # Extract variants
        product_info.variants = self._extract_variants(ai_analysis)
        
        # Extract trust signals
        product_info.trust_signals = self._extract_trust_signals(ai_analysis)
        
        # Extract urgency signals
        product_info.urgency_signals = self._extract_urgency_signals(
            product_info.pricing,
            product_info.availability,
            product_info.trust_signals
        )
        
        # Extract product name
        product_info.product_name = ai_analysis.get("title") or ai_analysis.get("the_hook")
        product_info.product_subtitle = ai_analysis.get("subtitle") or ai_analysis.get("the_tagline")
        
        # Calculate extraction confidence
        product_info.extraction_confidence = self._calculate_confidence(product_info)
        
        self.logger.info(
            f"✅ Product intelligence extracted: "
            f"Price: {product_info.pricing.current_price}, "
            f"Rating: {product_info.rating.rating}, "
            f"Badges: {len(product_info.trust_signals.badges)}, "
            f"Urgency: {product_info.urgency_signals.has_urgency}"
        )
        
        return product_info
    
    def _extract_pricing(self, ai_analysis: Dict[str, Any], html_content: Optional[str]) -> PricingInfo:
        """Extract comprehensive pricing information."""
        pricing = PricingInfo()
        
        # Get pricing data from AI analysis
        pricing_data = ai_analysis.get("pricing", {})
        
        # Current price
        current_price = pricing_data.get("current_price") or ai_analysis.get("price")
        if current_price:
            pricing.current_price = str(current_price)
            pricing.current_price_value = self._parse_price_value(current_price)
            pricing.currency_symbol = self._extract_currency_symbol(current_price)
        
        # Original price (before discount)
        original_price = pricing_data.get("original_price") or pricing_data.get("was_price")
        if original_price:
            pricing.original_price = str(original_price)
            pricing.original_price_value = self._parse_price_value(original_price)
            pricing.is_on_sale = True
        
        # Discount percentage
        discount_pct = pricing_data.get("discount_percentage") or pricing_data.get("discount_percent")
        if discount_pct:
            if isinstance(discount_pct, str):
                # Extract number from "30%", "-30%", "30% OFF"
                match = re.search(r'(\d+)', str(discount_pct))
                if match:
                    pricing.discount_percentage = int(match.group(1))
            else:
                pricing.discount_percentage = int(discount_pct)
            pricing.is_on_sale = True
        
        # Calculate discount if we have both prices
        if pricing.current_price_value and pricing.original_price_value:
            if not pricing.discount_percentage:
                discount = ((pricing.original_price_value - pricing.current_price_value) / 
                           pricing.original_price_value * 100)
                pricing.discount_percentage = int(round(discount))
            
            discount_amt = pricing.original_price_value - pricing.current_price_value
            pricing.discount_amount = f"{pricing.currency_symbol}{discount_amt:.2f}"
            pricing.is_on_sale = True
        
        # Deal end time
        deal_ends = pricing_data.get("deal_ends") or pricing_data.get("sale_ends")
        if deal_ends:
            pricing.deal_ends = str(deal_ends)
        
        return pricing
    
    def _extract_availability(self, ai_analysis: Dict[str, Any], html_content: Optional[str]) -> AvailabilityInfo:
        """Extract product availability information."""
        availability = AvailabilityInfo()
        
        avail_data = ai_analysis.get("availability", {})
        
        # In stock status
        in_stock = avail_data.get("in_stock")
        if in_stock is not None:
            availability.in_stock = bool(in_stock)
        
        # Stock level message
        stock_level = avail_data.get("stock_level") or avail_data.get("stock_message")
        if stock_level:
            stock_level_str = str(stock_level).lower()
            availability.stock_level = str(stock_level)
            
            # Check for limited quantity indicators
            if any(word in stock_level_str for word in ["only", "left", "low stock", "hurry", "limited"]):
                availability.limited_quantity = True
            
            # Extract exact quantity if present
            # "Only 3 left", "5 items remaining"
            match = re.search(r'(\d+)\s*(?:left|remaining|items?|in stock)', stock_level_str)
            if match:
                availability.stock_quantity = int(match.group(1))
        
        # Availability date (for pre-orders)
        avail_date = avail_data.get("availability_date") or avail_data.get("ships_on")
        if avail_date:
            availability.availability_date = str(avail_date)
        
        return availability
    
    def _extract_rating(self, ai_analysis: Dict[str, Any], html_content: Optional[str]) -> RatingInfo:
        """Extract rating and review information."""
        rating_info = RatingInfo()
        
        rating_data = ai_analysis.get("rating", {})
        
        # Star rating
        rating_value = rating_data.get("value") or ai_analysis.get("social_proof_rating")
        if rating_value:
            # Handle various formats: "4.8", "4.8/5", "4.8 stars", 4.8
            if isinstance(rating_value, (int, float)):
                rating_info.rating = float(rating_value)
            else:
                match = re.search(r'([\d.]+)', str(rating_value))
                if match:
                    rating_info.rating = float(match.group(1))
            
            if rating_info.rating:
                rating_info.rating_display = f"{rating_info.rating:.1f} out of 5 stars"
        
        # Review count
        review_count = rating_data.get("count") or rating_data.get("review_count") or ai_analysis.get("review_count")
        if review_count:
            # Handle formats: "2,847", "2847 reviews", "2.8K reviews"
            review_count_str = str(review_count)
            
            # Handle "K" notation (2.8K = 2800)
            if 'k' in review_count_str.lower():
                match = re.search(r'([\d.]+)\s*k', review_count_str.lower())
                if match:
                    rating_info.review_count = int(float(match.group(1)) * 1000)
            else:
                # Extract number, removing commas
                match = re.search(r'([\d,]+)', review_count_str)
                if match:
                    rating_info.review_count = int(match.group(1).replace(',', ''))
            
            if rating_info.review_count:
                rating_info.review_count_display = f"{rating_info.review_count:,} reviews"
        
        # Answered questions
        questions = rating_data.get("answered_questions")
        if questions:
            match = re.search(r'(\d+)', str(questions))
            if match:
                rating_info.answered_questions = int(match.group(1))
        
        return rating_info
    
    def _extract_details(self, ai_analysis: Dict[str, Any], url: Optional[str]) -> ProductDetails:
        """Extract product detail information."""
        details = ProductDetails()
        
        details_data = ai_analysis.get("product_details", {})
        
        # Brand
        brand = details_data.get("brand") or ai_analysis.get("brand")
        if brand:
            details.brand = str(brand)
        
        # Model
        model = details_data.get("model") or details_data.get("model_number")
        if model:
            details.model = str(model)
        
        # Category
        category = details_data.get("category") or ai_analysis.get("product_category")
        if category:
            details.category = str(category)
            # Map to ProductCategory enum
            details.product_type = self._map_to_product_category(category)
        
        # Subcategory
        subcategory = details_data.get("subcategory")
        if subcategory:
            details.subcategory = str(subcategory)
        
        return details
    
    def _extract_features(self, ai_analysis: Dict[str, Any]) -> ProductFeatures:
        """Extract product features and specifications."""
        features = ProductFeatures()
        
        features_data = ai_analysis.get("features", {})
        
        # Key features (bullet points)
        key_features = features_data.get("key_features") or ai_analysis.get("key_features") or []
        if isinstance(key_features, list):
            features.key_features = [str(f) for f in key_features if f]
        
        # Specifications
        specs = features_data.get("specifications") or ai_analysis.get("specifications") or {}
        if isinstance(specs, dict):
            features.specifications = {str(k): str(v) for k, v in specs.items()}
        
        # Description highlights
        highlights = features_data.get("highlights") or ai_analysis.get("description_highlights") or []
        if isinstance(highlights, list):
            features.description_highlights = [str(h) for h in highlights if h]
        
        return features
    
    def _extract_variants(self, ai_analysis: Dict[str, Any]) -> ProductVariants:
        """Extract product variant information."""
        variants = ProductVariants()
        
        variants_data = ai_analysis.get("variants", {})
        
        # Colors
        colors = variants_data.get("colors") or variants_data.get("available_colors") or []
        if colors and isinstance(colors, list):
            variants.available_colors = [str(c) for c in colors if c]
            variants.has_variants = True
            if "Color" not in variants.variant_types:
                variants.variant_types.append("Color")
        
        # Sizes
        sizes = variants_data.get("sizes") or variants_data.get("available_sizes") or []
        if sizes and isinstance(sizes, list):
            variants.available_sizes = [str(s) for s in sizes if s]
            variants.has_variants = True
            if "Size" not in variants.variant_types:
                variants.variant_types.append("Size")
        
        return variants
    
    def _extract_trust_signals(self, ai_analysis: Dict[str, Any]) -> TrustSignals:
        """Extract trust and credibility signals."""
        trust = TrustSignals()
        
        trust_data = ai_analysis.get("trust_signals", {})
        
        # Badges
        badges = trust_data.get("badges") or ai_analysis.get("badges") or []
        if isinstance(badges, list):
            trust.badges = [str(b) for b in badges if b]
            # Map to BadgeType enum
            trust.badge_types = self._map_to_badge_types(trust.badges)
        
        # Shipping
        shipping = trust_data.get("shipping") or ai_analysis.get("shipping_info")
        if shipping:
            trust.shipping_info = str(shipping)
        
        # Returns
        returns = trust_data.get("returns") or trust_data.get("return_policy")
        if returns:
            trust.return_policy = str(returns)
        
        # Warranty
        warranty = trust_data.get("warranty")
        if warranty:
            trust.warranty = str(warranty)
        
        # Seller info
        seller = trust_data.get("seller_name")
        if seller:
            trust.seller_name = str(seller)
        
        seller_rating = trust_data.get("seller_rating")
        if seller_rating:
            try:
                trust.seller_rating = float(seller_rating)
            except:
                pass
        
        # Certifications
        certs = trust_data.get("certifications") or []
        if isinstance(certs, list):
            trust.certifications = [str(c) for c in certs if c]
        
        return trust
    
    def _extract_urgency_signals(
        self,
        pricing: PricingInfo,
        availability: AvailabilityInfo,
        trust_signals: TrustSignals
    ) -> UrgencySignals:
        """
        Extract and synthesize urgency signals.
        
        Urgency comes from:
        - Deal countdowns
        - Limited stock
        - Popularity indicators
        - Sales/clearance badges
        """
        urgency = UrgencySignals()
        
        # Deal countdown
        if pricing.deal_ends:
            urgency.deal_countdown = pricing.deal_ends
            urgency.has_urgency = True
        
        # Limited stock
        if availability.limited_quantity or availability.stock_quantity:
            urgency.limited_stock = True
            urgency.stock_message = availability.stock_level
            urgency.has_urgency = True
        
        # Check badges for urgency
        for badge in trust_signals.badges:
            badge_lower = badge.lower()
            if any(word in badge_lower for word in ["trending", "hot", "popular", "selling fast"]):
                urgency.trending = True
                urgency.popularity_signal = badge
                urgency.has_urgency = True
        
        # Check if fast selling
        if any(badge_type in [BadgeType.TRENDING, BadgeType.BEST_SELLER] for badge_type in trust_signals.badge_types):
            urgency.fast_selling = True
            urgency.has_urgency = True
        
        return urgency
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _parse_price_value(self, price_str: str) -> Optional[float]:
        """Extract numeric value from price string."""
        if not price_str:
            return None
        
        # Remove currency symbols and commas
        # "$1,234.56" -> 1234.56
        cleaned = re.sub(r'[^\d.]', '', str(price_str))
        
        try:
            return float(cleaned)
        except:
            return None
    
    def _extract_currency_symbol(self, price_str: str) -> str:
        """Extract currency symbol from price string."""
        if not price_str:
            return "$"
        
        # Common currency symbols
        for symbol in ['$', '€', '£', '¥', '₹']:
            if symbol in str(price_str):
                return symbol
        
        return "$"
    
    def _map_to_product_category(self, category_str: str) -> ProductCategory:
        """Map category string to ProductCategory enum."""
        if not category_str:
            return ProductCategory.GENERAL
        
        category_lower = category_str.lower()
        
        # Electronics
        if any(word in category_lower for word in ["electronics", "computer", "laptop", "phone", "tablet", "tech", "gadget"]):
            return ProductCategory.ELECTRONICS
        
        # Fashion
        if any(word in category_lower for word in ["fashion", "clothing", "apparel", "shoes", "accessories", "wear"]):
            return ProductCategory.FASHION
        
        # Beauty
        if any(word in category_lower for word in ["beauty", "cosmetics", "makeup", "skincare", "fragrance"]):
            return ProductCategory.BEAUTY
        
        # Food
        if any(word in category_lower for word in ["food", "grocery", "snack", "beverage", "drink"]):
            return ProductCategory.FOOD
        
        # Home
        if any(word in category_lower for word in ["home", "furniture", "decor", "kitchen", "appliance"]):
            return ProductCategory.HOME
        
        # Books
        if any(word in category_lower for word in ["book", "reading", "literature"]):
            return ProductCategory.BOOKS
        
        # Digital
        if any(word in category_lower for word in ["digital", "software", "download", "subscription"]):
            return ProductCategory.DIGITAL
        
        # Toys
        if any(word in category_lower for word in ["toy", "game", "kids", "children"]):
            return ProductCategory.TOYS
        
        # Sports
        if any(word in category_lower for word in ["sport", "fitness", "outdoor", "athletic"]):
            return ProductCategory.SPORTS
        
        # Automotive
        if any(word in category_lower for word in ["automotive", "car", "vehicle", "auto"]):
            return ProductCategory.AUTOMOTIVE
        
        # Jewelry
        if any(word in category_lower for word in ["jewelry", "jewellery", "watch", "ring"]):
            return ProductCategory.JEWELRY
        
        return ProductCategory.GENERAL
    
    def _map_to_badge_types(self, badges: List[str]) -> List[BadgeType]:
        """Map badge strings to BadgeType enum."""
        badge_types = []
        
        for badge in badges:
            badge_lower = badge.lower()
            
            if "best seller" in badge_lower or "bestseller" in badge_lower:
                badge_types.append(BadgeType.BEST_SELLER)
            elif "amazon's choice" in badge_lower or "amazons choice" in badge_lower:
                badge_types.append(BadgeType.AMAZONS_CHOICE)
            elif "top rated" in badge_lower:
                badge_types.append(BadgeType.TOP_RATED)
            elif "new arrival" in badge_lower or "new" in badge_lower:
                badge_types.append(BadgeType.NEW_ARRIVAL)
            elif "limited edition" in badge_lower:
                badge_types.append(BadgeType.LIMITED_EDITION)
            elif "free shipping" in badge_lower or "free delivery" in badge_lower:
                badge_types.append(BadgeType.FREE_SHIPPING)
            elif "sale" in badge_lower:
                badge_types.append(BadgeType.SALE)
            elif "clearance" in badge_lower:
                badge_types.append(BadgeType.CLEARANCE)
            elif "trending" in badge_lower or "hot" in badge_lower:
                badge_types.append(BadgeType.TRENDING)
            elif "#1" in badge_lower or "number 1" in badge_lower or "no. 1" in badge_lower:
                badge_types.append(BadgeType.NUMBER_ONE)
            elif "editor" in badge_lower:
                badge_types.append(BadgeType.EDITORS_PICK)
        
        return badge_types
    
    def _calculate_confidence(self, product_info: ProductInformation) -> float:
        """Calculate extraction confidence score."""
        score = 0.0
        max_score = 0.0
        
        # Pricing (30%)
        max_score += 30
        if product_info.pricing.current_price:
            score += 20
        if product_info.pricing.is_on_sale and product_info.pricing.discount_percentage:
            score += 10
        
        # Ratings (25%)
        max_score += 25
        if product_info.rating.rating:
            score += 15
        if product_info.rating.review_count:
            score += 10
        
        # Features (20%)
        max_score += 20
        if product_info.features.key_features:
            score += 10
        if product_info.features.specifications:
            score += 10
        
        # Trust signals (15%)
        max_score += 15
        if product_info.trust_signals.badges:
            score += 10
        if product_info.trust_signals.shipping_info:
            score += 5
        
        # Details (10%)
        max_score += 10
        if product_info.details.brand:
            score += 5
        if product_info.details.category:
            score += 5
        
        return score / max_score if max_score > 0 else 0.0


# =============================================================================
# Convenience Functions
# =============================================================================

def extract_product_intelligence(
    ai_analysis: Dict[str, Any],
    html_content: Optional[str] = None,
    url: Optional[str] = None
) -> ProductInformation:
    """
    Convenience function to extract product intelligence.
    
    Usage:
        product_info = extract_product_intelligence(ai_analysis)
        
        if product_info.pricing.is_on_sale:
            print(f"Sale! {product_info.pricing.discount_percentage}% off")
        
        if product_info.urgency_signals.has_urgency:
            print(f"Urgency: {product_info.urgency_signals.deal_countdown}")
    """
    extractor = ProductIntelligenceExtractor()
    return extractor.extract(ai_analysis, html_content, url)
