"""
Smart Feature Selection

Category-aware prioritization of product features for display.
Different product categories need different features highlighted:
- Electronics: Technical specs (RAM, storage, processor)
- Fashion: Material, fit, care instructions
- Food: Dietary info, ingredients, certifications
- Beauty: Key ingredients, skin type, benefits
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

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


@dataclass
class FeatureScore:
    """Scored feature for prioritization."""
    feature: str
    score: float
    category_relevance: float
    has_numbers: bool
    keyword_matches: int


# =============================================================================
# Category-Specific Feature Keywords
# =============================================================================

FEATURE_KEYWORDS = {
    ProductCategory.ELECTRONICS: {
        # High priority (technical differentiators)
        "high": [
            "battery", "storage", "ram", "memory", "processor", "cpu", "gpu",
            "display", "screen", "camera", "megapixel", "mp", "5g", "4g", "lte",
            "wireless", "bluetooth", "wifi", "charging", "fast charge",
            "water resistant", "waterproof", "ip67", "ip68"
        ],
        # Medium priority
        "medium": [
            "warranty", "ports", "usb", "hdmi", "connectivity",
            "dimensions", "weight", "hours", "mah"
        ],
        # Low priority
        "low": [
            "color", "design", "style", "sleek"
        ]
    },
    
    ProductCategory.FASHION: {
        "high": [
            "cotton", "organic", "sustainable", "recycled", "eco-friendly",
            "made in", "handmade", "artisan", "fair trade",
            "machine wash", "hand wash", "dry clean",
            "stretch", "breathable", "moisture-wicking", "water-resistant"
        ],
        "medium": [
            "fit", "regular fit", "slim fit", "loose fit",
            "material", "fabric", "polyester", "nylon", "wool",
            "size", "sizing"
        ],
        "low": [
            "style", "trendy", "fashionable"
        ]
    },
    
    ProductCategory.BEAUTY: {
        "high": [
            "organic", "natural", "cruelty-free", "vegan", "paraben-free",
            "sulfate-free", "fragrance-free", "hypoallergenic",
            "dermatologist tested", "clinically proven",
            "spf", "sun protection", "vitamin c", "retinol", "hyaluronic acid",
            "for dry skin", "for oily skin", "for sensitive skin"
        ],
        "medium": [
            "moisturizing", "hydrating", "anti-aging", "brightening",
            "exfoliating", "cleansing", "nourishing",
            "ingredients", "formula"
        ],
        "low": [
            "luxury", "premium", "exclusive"
        ]
    },
    
    ProductCategory.FOOD: {
        "high": [
            "organic", "non-gmo", "gluten-free", "vegan", "vegetarian",
            "keto", "paleo", "low carb", "sugar-free", "no added sugar",
            "locally sourced", "farm fresh", "grass-fed", "free-range",
            "fair trade", "kosher", "halal",
            "usda organic", "certified organic"
        ],
        "medium": [
            "natural", "fresh", "preservative-free", "artificial flavor-free",
            "high protein", "high fiber", "low sodium", "low fat",
            "calories", "nutrition"
        ],
        "low": [
            "delicious", "tasty", "flavorful"
        ]
    },
    
    ProductCategory.HOME: {
        "high": [
            "dimensions", "size", "measurements",
            "material", "solid wood", "metal", "fabric",
            "easy assembly", "no assembly", "assembled",
            "warranty", "year warranty",
            "weight capacity", "capacity"
        ],
        "medium": [
            "durable", "sturdy", "strong",
            "care instructions", "cleaning",
            "indoor", "outdoor", "weather-resistant"
        ],
        "low": [
            "stylish", "modern", "contemporary"
        ]
    },
    
    ProductCategory.GENERAL: {
        "high": [
            "warranty", "guarantee", "certified", "approved",
            "quality", "durable", "premium"
        ],
        "medium": [
            "features", "benefits", "includes"
        ],
        "low": [
            "great", "best", "top"
        ]
    }
}


# =============================================================================
# Smart Feature Selector
# =============================================================================

class SmartFeatureSelector:
    """
    Intelligently selects and prioritizes product features for display.
    
    Uses category-aware keyword matching, quantifiable data detection,
    and relevance scoring to pick the most valuable features.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def select_features(
        self,
        features: List[str],
        category: ProductCategory,
        max_features: int = 3
    ) -> List[str]:
        """
        Select top N most relevant features for category.
        
        Args:
            features: List of feature strings
            category: Product category
            max_features: Maximum features to return
        
        Returns:
            List of top N features
        """
        if not features:
            return []
        
        # Score all features
        scored_features = []
        for feature in features:
            score_obj = self._score_feature(feature, category)
            scored_features.append(score_obj)
        
        # Sort by score
        scored_features.sort(key=lambda x: x.score, reverse=True)
        
        # Return top N
        top_features = [f.feature for f in scored_features[:max_features]]
        
        self.logger.info(
            f"📋 Selected {len(top_features)} features for {category.value}: "
            f"{', '.join(top_features[:3])}"
        )
        
        return top_features
    
    def _score_feature(self, feature: str, category: ProductCategory) -> FeatureScore:
        """Score a single feature for relevance."""
        feature_lower = feature.lower()
        
        # Base score
        score = 0.5
        
        # Get category keywords
        keywords = FEATURE_KEYWORDS.get(category, FEATURE_KEYWORDS[ProductCategory.GENERAL])
        
        # Check keyword matches
        keyword_matches = 0
        category_relevance = 0.0
        
        # High priority keywords
        for keyword in keywords.get("high", []):
            if keyword in feature_lower:
                score += 0.3
                keyword_matches += 1
                category_relevance = 1.0
        
        # Medium priority keywords
        for keyword in keywords.get("medium", []):
            if keyword in feature_lower:
                score += 0.15
                keyword_matches += 1
                if category_relevance == 0:
                    category_relevance = 0.6
        
        # Low priority keywords
        for keyword in keywords.get("low", []):
            if keyword in feature_lower:
                score += 0.05
                keyword_matches += 1
                if category_relevance == 0:
                    category_relevance = 0.3
        
        # Bonus for quantifiable data (numbers)
        has_numbers = bool(re.search(r'\d+', feature))
        if has_numbers:
            score += 0.2
        
        # Bonus for specific measurements
        if any(unit in feature_lower for unit in ['gb', 'tb', 'mah', 'mp', 'hz', 'inch', 'cm', 'kg', 'lb', 'oz', 'ml', 'l']):
            score += 0.15
        
        # Bonus for percentages
        if '%' in feature or 'percent' in feature_lower:
            score += 0.1
        
        # Penalty for vague language
        if any(word in feature_lower for word in ['great', 'best', 'top', 'amazing', 'perfect']):
            score -= 0.15
        
        # Penalty for overly long features
        if len(feature) > 80:
            score -= 0.1
        
        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))
        
        return FeatureScore(
            feature=feature,
            score=score,
            category_relevance=category_relevance,
            has_numbers=has_numbers,
            keyword_matches=keyword_matches
        )


# =============================================================================
# Convenience Function
# =============================================================================

def select_smart_features(
    features: List[str],
    category: ProductCategory,
    max_features: int = 3
) -> List[str]:
    """
    Convenience function for smart feature selection.
    
    Usage:
        features = ["100% organic cotton", "Machine washable", "Stylish design"]
        category = ProductCategory.FASHION
        top_features = select_smart_features(features, category, max_features=3)
        # Returns: ["100% organic cotton", "Machine washable"]
        # (Excludes "Stylish design" as it's low priority for fashion)
    """
    selector = SmartFeatureSelector()
    return selector.select_features(features, category, max_features)
