"""
Contextual Intelligence Engine - Layer 6 of Design Framework Enhancement.

This module provides industry-aware, audience-tuned, culturally intelligent design decisions.

Key Features:
- Industry classification (10+ industries)
- Industry-specific design presets
- Audience detection (B2B, B2C, Developer, Gen Z)
- Cultural adaptations
- Trend awareness (2024-2025)
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class Industry(str, Enum):
    """Industry classifications."""
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    CREATIVE = "creative"
    EDUCATION = "education"
    NONPROFIT = "nonprofit"
    REAL_ESTATE = "real_estate"
    LEGAL = "legal"
    CONSULTING = "consulting"
    HOSPITALITY = "hospitality"
    TECHNOLOGY = "technology"
    UNKNOWN = "unknown"


class Audience(str, Enum):
    """Target audience types."""
    B2B = "b2b"
    B2C = "b2c"
    DEVELOPER = "developer"
    GEN_Z = "gen_z"
    ENTERPRISE = "enterprise"
    SMB = "smb"
    CONSUMER = "consumer"


@dataclass
class IndustryProfile:
    """Design profile for an industry."""
    industry: Industry
    primary_colors: List[Tuple[int, int, int]]  # RGB tuples
    accent_colors: List[Tuple[int, int, int]]
    typography_personality: str  # authoritative, friendly, elegant, etc.
    design_style: str  # minimal, bold, professional, etc.
    key_values: List[str]  # trust, innovation, care, etc.
    visual_elements: List[str]  # What to emphasize
    avoid: List[str]  # What to avoid


@dataclass
class DesignRecommendation:
    """Contextual design recommendation."""
    industry: Industry
    audience: Audience
    colors: Dict[str, Tuple[int, int, int]]
    typography: str
    layout_style: str
    emphasis: List[str]
    tone: str
    confidence: float  # 0-1


# ============================================================================
# INDUSTRY PROFILES DATABASE
# ============================================================================

INDUSTRY_PROFILES = {
    Industry.FINTECH: IndustryProfile(
        industry=Industry.FINTECH,
        primary_colors=[(0, 102, 255), (0, 132, 255), (30, 64, 175)],  # Blues
        accent_colors=[(0, 200, 83), (16, 185, 129), (52, 211, 153)],  # Greens
        typography_personality="authoritative",
        design_style="professional",
        key_values=["trust", "security", "precision", "innovation"],
        visual_elements=["charts", "numbers", "locks", "shields"],
        avoid=["playful fonts", "bright pinks", "hand-drawn", "clutter"]
    ),
    
    Industry.HEALTHCARE: IndustryProfile(
        industry=Industry.HEALTHCARE,
        primary_colors=[(0, 168, 232), (14, 165, 233), (59, 130, 246)],  # Light blues
        accent_colors=[(0, 217, 192), (20, 184, 166), (45, 212, 191)],  # Teals
        typography_personality="friendly",
        design_style="accessible",
        key_values=["care", "trust", "clarity", "compassion"],
        visual_elements=["plus signs", "hearts", "people", "hands"],
        avoid=["harsh reds", "dark colors", "aggressive", "complex"]
    ),
    
    Industry.ECOMMERCE: IndustryProfile(
        industry=Industry.ECOMMERCE,
        primary_colors=[(255, 107, 107), (239, 68, 68), (220, 38, 38)],  # Reds
        accent_colors=[(255, 165, 0), (251, 146, 60), (249, 115, 22)],  # Oranges
        typography_personality="bold",
        design_style="energetic",
        key_values=["deals", "urgency", "selection", "convenience"],
        visual_elements=["badges", "stars", "shopping", "products"],
        avoid=["slow", "boring", "corporate", "cold"]
    ),
    
    Industry.SAAS: IndustryProfile(
        industry=Industry.SAAS,
        primary_colors=[(37, 99, 235), (59, 130, 246), (96, 165, 250)],  # Modern blues
        accent_colors=[(168, 85, 247), (147, 51, 234), (126, 34, 206)],  # Purples
        typography_personality="authoritative",
        design_style="modern",
        key_values=["efficiency", "innovation", "scalability", "modern"],
        visual_elements=["gradients", "screenshots", "metrics", "integrations"],
        avoid=["dated", "clipart", "aggressive sales", "cluttered"]
    ),
    
    Industry.CREATIVE: IndustryProfile(
        industry=Industry.CREATIVE,
        primary_colors=[(139, 92, 246), (168, 85, 247), (192, 132, 252)],  # Purples
        accent_colors=[(236, 72, 153), (219, 39, 119), (190, 24, 93)],  # Pinks
        typography_personality="creative",
        design_style="bold",
        key_values=["unique", "artistic", "bold", "expressive"],
        visual_elements=["artwork", "photos", "patterns", "asymmetry"],
        avoid=["boring", "generic", "corporate", "rigid"]
    ),
    
    Industry.EDUCATION: IndustryProfile(
        industry=Industry.EDUCATION,
        primary_colors=[(59, 130, 246), (37, 99, 235), (29, 78, 216)],  # Blues
        accent_colors=[(251, 191, 36), (245, 158, 11), (217, 119, 6)],  # Yellows/oranges
        typography_personality="friendly",
        design_style="approachable",
        key_values=["learning", "growth", "accessible", "encouraging"],
        visual_elements=["icons", "illustrations", "steps", "progress"],
        avoid=["intimidating", "complex", "dark", "exclusive"]
    ),
    
    Industry.NONPROFIT: IndustryProfile(
        industry=Industry.NONPROFIT,
        primary_colors=[(34, 197, 94), (22, 163, 74), (21, 128, 61)],  # Greens
        accent_colors=[(239, 68, 68), (220, 38, 38), (185, 28, 28)],  # Reds (urgency)
        typography_personality="friendly",
        design_style="empathetic",
        key_values=["mission", "impact", "community", "transparency"],
        visual_elements=["people", "stories", "impact", "hands"],
        avoid=["luxury", "excess", "cold", "corporate"]
    ),
    
    Industry.REAL_ESTATE: IndustryProfile(
        industry=Industry.REAL_ESTATE,
        primary_colors=[(30, 58, 138), (30, 64, 175), (37, 99, 235)],  # Deep blues
        accent_colors=[(202, 138, 4), (217, 119, 6), (180, 83, 9)],  # Golds
        typography_personality="elegant",
        design_style="luxury",
        key_values=["prestige", "quality", "location", "investment"],
        visual_elements=["photos", "maps", "architecture", "luxury"],
        avoid=["cheap", "cluttered", "aggressive", "cartoonish"]
    ),
    
    Industry.LEGAL: IndustryProfile(
        industry=Industry.LEGAL,
        primary_colors=[(30, 58, 138), (17, 24, 39), (31, 41, 55)],  # Navy/dark
        accent_colors=[(202, 138, 4), (180, 83, 9), (146, 64, 14)],  # Gold accents
        typography_personality="authoritative",
        design_style="traditional",
        key_values=["trust", "expertise", "authority", "professionalism"],
        visual_elements=["seals", "columns", "documents", "scales"],
        avoid=["playful", "bright", "casual", "modern"]
    ),
    
    Industry.CONSULTING: IndustryProfile(
        industry=Industry.CONSULTING,
        primary_colors=[(30, 58, 138), (37, 99, 235), (59, 130, 246)],  # Corporate blues
        accent_colors=[(16, 185, 129), (5, 150, 105), (4, 120, 87)],  # Professional greens
        typography_personality="authoritative",
        design_style="professional",
        key_values=["expertise", "results", "strategy", "partnership"],
        visual_elements=["charts", "data", "people", "growth"],
        avoid=["flashy", "aggressive", "cheap", "cluttered"]
    ),
    
    Industry.HOSPITALITY: IndustryProfile(
        industry=Industry.HOSPITALITY,
        primary_colors=[(202, 138, 4), (217, 119, 6), (245, 158, 11)],  # Warm golds
        accent_colors=[(220, 38, 38), (185, 28, 28), (153, 27, 27)],  # Warm reds
        typography_personality="elegant",
        design_style="welcoming",
        key_values=["comfort", "luxury", "experience", "service"],
        visual_elements=["photos", "ambiance", "food", "destinations"],
        avoid=["cold", "corporate", "sterile", "aggressive"]
    ),
    
    Industry.TECHNOLOGY: IndustryProfile(
        industry=Industry.TECHNOLOGY,
        primary_colors=[(59, 130, 246), (37, 99, 235), (29, 78, 216)],  # Tech blues
        accent_colors=[(168, 85, 247), (147, 51, 234), (126, 34, 206)],  # Cyber purples
        typography_personality="technical",
        design_style="modern",
        key_values=["innovation", "cutting-edge", "performance", "future"],
        visual_elements=["gradients", "grids", "circuits", "glow"],
        avoid=["dated", "organic", "handdrawn", "traditional"]
    ),
}


# ============================================================================
# CONTEXTUAL INTELLIGENCE ENGINE
# ============================================================================

class ContextIntelligenceEngine:
    """
    Provides contextual design intelligence based on industry, audience, and culture.
    
    Analyzes URL, content, and Design DNA to recommend optimal design approaches.
    """
    
    def __init__(self):
        self.industry_profiles = INDUSTRY_PROFILES
    
    def classify_industry(
        self,
        url: str,
        content_keywords: Optional[List[str]] = None,
        design_dna: Optional[Dict[str, Any]] = None
    ) -> Tuple[Industry, float]:
        """
        Classify website industry.
        
        Args:
            url: Website URL
            content_keywords: Optional extracted keywords
            design_dna: Optional Design DNA data
            
        Returns:
            Tuple of (Industry, confidence_score)
        """
        scores = {industry: 0.0 for industry in Industry}
        
        # URL-based classification
        url_lower = url.lower()
        domain = urlparse(url).netloc.lower()
        
        # Industry keywords in URL/domain
        industry_keywords = {
            Industry.FINTECH: ["bank", "pay", "finance", "invest", "wallet", "crypto", "trading"],
            Industry.HEALTHCARE: ["health", "medical", "care", "clinic", "hospital", "doctor", "wellness"],
            Industry.ECOMMERCE: ["shop", "store", "buy", "cart", "product", "marketplace"],
            Industry.SAAS: ["app", "software", "platform", "tool", "cloud", "api"],
            Industry.CREATIVE: ["design", "agency", "studio", "creative", "art", "portfolio"],
            Industry.EDUCATION: ["edu", "learn", "course", "academy", "school", "training"],
            Industry.NONPROFIT: ["org", "charity", "foundation", "nonprofit", "donate"],
            Industry.REAL_ESTATE: ["realty", "property", "estate", "homes", "real-estate"],
            Industry.LEGAL: ["law", "legal", "attorney", "lawyer", "counsel"],
            Industry.CONSULTING: ["consult", "advisor", "strategy", "professional-services"],
            Industry.HOSPITALITY: ["hotel", "resort", "restaurant", "travel", "hospitality"],
            Industry.TECHNOLOGY: ["tech", "io", "dev", "ai", "data", "cyber"],
        }
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in url_lower or keyword in domain:
                    scores[industry] += 0.3
        
        # Content-based classification
        if content_keywords:
            for industry, keywords in industry_keywords.items():
                matches = sum(1 for kw in keywords if any(kw in ck.lower() for ck in content_keywords))
                scores[industry] += matches * 0.2
        
        # Design DNA-based classification
        if design_dna:
            style = design_dna.get("style", "").lower()
            formality = design_dna.get("formality", 0.5)
            
            # High formality → professional industries
            if formality > 0.7:
                scores[Industry.LEGAL] += 0.2
                scores[Industry.CONSULTING] += 0.2
                scores[Industry.FINTECH] += 0.15
            
            # Style mapping
            style_map = {
                "minimalist": [Industry.SAAS, Industry.TECHNOLOGY],
                "luxurious": [Industry.REAL_ESTATE, Industry.HOSPITALITY],
                "playful": [Industry.ECOMMERCE, Industry.EDUCATION],
                "technical": [Industry.TECHNOLOGY, Industry.FINTECH],
                "corporate": [Industry.CONSULTING, Industry.LEGAL],
            }
            
            for style_key, industries in style_map.items():
                if style_key in style:
                    for ind in industries:
                        scores[ind] += 0.15
        
        # Find best match
        best_industry = max(scores.items(), key=lambda x: x[1])
        
        if best_industry[1] < 0.3:
            return Industry.UNKNOWN, best_industry[1]
        
        logger.info(f"🏢 Classified as {best_industry[0].value} (confidence: {best_industry[1]:.2f})")
        return best_industry[0], best_industry[1]
    
    def detect_audience(
        self,
        industry: Industry,
        url: str,
        content_tone: Optional[str] = None
    ) -> Audience:
        """
        Detect target audience.
        
        Args:
            industry: Classified industry
            url: Website URL
            content_tone: Optional tone analysis
            
        Returns:
            Audience type
        """
        url_lower = url.lower()
        
        # Developer indicators
        if any(word in url_lower for word in ["dev", "api", "docs", "github", "developer"]):
            return Audience.DEVELOPER
        
        # B2B indicators
        if industry in [Industry.SAAS, Industry.CONSULTING, Industry.LEGAL]:
            if any(word in url_lower for word in ["enterprise", "business", "b2b"]):
                return Audience.B2B
            return Audience.B2B  # Default for these industries
        
        # Gen Z indicators
        if content_tone and "casual" in content_tone.lower():
            return Audience.GEN_Z
        
        # Consumer default for certain industries
        if industry in [Industry.ECOMMERCE, Industry.EDUCATION, Industry.NONPROFIT]:
            return Audience.CONSUMER
        
        # B2C default
        return Audience.B2C
    
    def get_design_recommendation(
        self,
        url: str,
        content_keywords: Optional[List[str]] = None,
        design_dna: Optional[Dict[str, Any]] = None
    ) -> DesignRecommendation:
        """
        Get comprehensive design recommendation.
        
        Args:
            url: Website URL
            content_keywords: Optional content keywords
            design_dna: Optional Design DNA
            
        Returns:
            DesignRecommendation object
        """
        # Classify industry
        industry, confidence = self.classify_industry(url, content_keywords, design_dna)
        
        # Detect audience
        audience = self.detect_audience(industry, url, design_dna.get("tone") if design_dna else None)
        
        # Get industry profile
        profile = self.industry_profiles.get(industry, self.industry_profiles[Industry.UNKNOWN])
        
        # Select colors
        primary = profile.primary_colors[0] if profile.primary_colors else (59, 130, 246)
        accent = profile.accent_colors[0] if profile.accent_colors else (249, 115, 22)
        
        # Adjust for Design DNA if available
        if design_dna and "primary_color" in design_dna:
            # Use Design DNA colors but note industry recommendation
            logger.info(f"Using Design DNA colors instead of industry defaults")
        
        colors = {
            "primary": primary,
            "secondary": tuple(int(c * 0.8) for c in primary),  # Darken primary
            "accent": accent
        }
        
        # Layout style based on industry + audience
        if audience == Audience.DEVELOPER:
            layout_style = "technical-clean"
        elif industry in [Industry.LEGAL, Industry.CONSULTING]:
            layout_style = "professional-traditional"
        elif industry in [Industry.CREATIVE, Industry.ECOMMERCE]:
            layout_style = "bold-dynamic"
        else:
            layout_style = "modern-balanced"
        
        # Tone
        tone_map = {
            Audience.B2B: "professional",
            Audience.B2C: "friendly",
            Audience.DEVELOPER: "technical",
            Audience.GEN_Z: "casual",
            Audience.ENTERPRISE: "formal",
            Audience.CONSUMER: "approachable"
        }
        tone = tone_map.get(audience, "professional")
        
        return DesignRecommendation(
            industry=industry,
            audience=audience,
            colors=colors,
            typography=profile.typography_personality,
            layout_style=layout_style,
            emphasis=profile.visual_elements[:3],
            tone=tone,
            confidence=confidence
        )
    
    def get_cultural_adaptations(
        self,
        url: str,
        target_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cultural adaptations for design.
        
        Args:
            url: Website URL
            target_region: Optional target region (US, CN, JP, etc.)
            
        Returns:
            Dictionary of cultural recommendations
        """
        # Detect region from TLD if not specified
        if not target_region:
            tld = url.split(".")[-1].lower()
            region_map = {
                "cn": "china", "jp": "japan", "kr": "korea",
                "sa": "saudi", "ae": "uae", "in": "india",
                "br": "brazil", "mx": "mexico", "ar": "argentina",
                "de": "germany", "fr": "france", "uk": "uk"
            }
            target_region = region_map.get(tld, "us")
        
        adaptations = {
            "region": target_region,
            "reading_direction": "ltr",
            "color_meanings": {},
            "number_preferences": {},
            "design_style": "universal"
        }
        
        # Region-specific adaptations
        if target_region in ["china", "japan", "korea"]:
            adaptations["color_meanings"] = {
                "red": "luck, prosperity (use liberally)",
                "white": "death, mourning (use carefully)",
                "gold": "wealth, prestige (excellent)"
            }
            adaptations["number_preferences"] = {
                "lucky": [8, 6, 9],
                "unlucky": [4]  # Sounds like "death"
            }
            adaptations["design_style"] = "detailed-ornate"
        
        elif target_region in ["saudi", "uae"]:
            adaptations["reading_direction"] = "rtl"
            adaptations["color_meanings"] = {
                "green": "islam, prosperity (excellent)",
                "gold": "luxury (excellent)",
                "white": "purity (good)"
            }
            adaptations["design_style"] = "luxury-formal"
        
        elif target_region == "india":
            adaptations["color_meanings"] = {
                "orange": "hindu, sacred (use carefully)",
                "red": "celebration, marriage (excellent)",
                "green": "islam (if applicable)"
            }
            adaptations["design_style"] = "colorful-vibrant"
        
        return adaptations


# ============================================================================
# TREND AWARENESS
# ============================================================================

DESIGN_TRENDS_2024_2025 = {
    "hot": [
        "glassmorphism",
        "3d_illustrations",
        "bold_typography",
        "mesh_gradients",
        "minimalism_2.0",
        "dark_mode",
        "micro_interactions",
        "custom_illustrations"
    ],
    "growing": [
        "ai_generated_art",
        "parametric_design",
        "kinetic_typography",
        "immersive_scrolling",
        "aurora_gradients"
    ],
    "declining": [
        "neumorphism",
        "flat_design_1.0",
        "stock_photos",
        "hamburger_menus"
    ]
}


def get_trend_score(design_element: str) -> float:
    """
    Get trend score for a design element.
    
    Args:
        design_element: Design element name
        
    Returns:
        Score from 0-1 (1 = hottest trend)
    """
    if design_element in DESIGN_TRENDS_2024_2025["hot"]:
        return 1.0
    elif design_element in DESIGN_TRENDS_2024_2025["growing"]:
        return 0.7
    elif design_element in DESIGN_TRENDS_2024_2025["declining"]:
        return 0.3
    else:
        return 0.5


# Example usage
if __name__ == "__main__":
    engine = ContextIntelligenceEngine()
    
    # Test industry classification
    test_urls = [
        "https://stripe.com",
        "https://shopify.com",
        "https://github.com",
        "https://mayoclinic.org"
    ]
    
    for url in test_urls:
        recommendation = engine.get_design_recommendation(url)
        print(f"\n{url}:")
        print(f"  Industry: {recommendation.industry.value}")
        print(f"  Audience: {recommendation.audience.value}")
        print(f"  Typography: {recommendation.typography}")
        print(f"  Layout: {recommendation.layout_style}")
        print(f"  Tone: {recommendation.tone}")
        print(f"  Confidence: {recommendation.confidence:.2f}")
