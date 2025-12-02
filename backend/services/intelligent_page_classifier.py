"""
Intelligent Page Type Classification System

A comprehensive, probabilistic framework for classifying web pages and adapting
preview strategies accordingly. This system analyzes multiple signals to make
intelligent, explainable decisions about page intent and optimal preview approach.

ARCHITECTURE:
1. Multi-Signal Analysis: URL patterns, HTML metadata, visual layout, content structure
2. Probabilistic Classification: Confidence scores for each category
3. Explainable Decisions: Clear reasoning for each classification
4. Strategy Adaptation: Preview strategy tailored to page type
5. Graceful Degradation: Fallbacks when confidence is low

DESIGN PRINCIPLES:
- No brittle rules tied to specific websites
- Generalizes across industries and layouts
- Degrades gracefully when signals are weak
- Provides explainable, justifiable classifications
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger(__name__)


class PageCategory(str, Enum):
    """Extensible page categories."""
    PROFILE = "profile"           # Personal pages, freelancers, team members
    COMPANY = "company"           # Company/brand homepages, about pages
    PRODUCT = "product"          # Product pages, e-commerce, pricing
    LANDING = "landing"           # Marketing/landing pages, SaaS homepages
    CONTENT = "content"           # Blog posts, articles, documentation
    TOOL = "tool"                 # App interfaces, dashboards, tools
    UNKNOWN = "unknown"           # Fallback when confidence is low


@dataclass
class ClassificationSignal:
    """A single signal contributing to classification."""
    source: str  # e.g., "url_pattern", "html_metadata", "content_structure"
    category: PageCategory
    confidence: float  # 0.0-1.0
    reasoning: str
    weight: float = 1.0  # Signal importance weight


@dataclass
class PageClassification:
    """Complete classification result with explainability."""
    primary_category: PageCategory
    confidence: float  # 0.0-1.0
    alternative_categories: List[Tuple[PageCategory, float]] = field(default_factory=list)
    signals: List[ClassificationSignal] = field(default_factory=list)
    reasoning: str = ""
    
    # Strategy adaptations based on classification
    preview_strategy: Dict[str, Any] = field(default_factory=dict)


class IntelligentPageClassifier:
    """
    Intelligent page classifier using multi-signal analysis.
    
    Analyzes:
    - URL patterns and structure
    - HTML metadata (og:type, schema.org, etc.)
    - Content structure (headings, CTAs, forms)
    - Visual layout indicators (from AI analysis)
    - Content keywords and patterns
    """
    
    def __init__(self):
        self._url_patterns = self._build_url_patterns()
        self._content_keywords = self._build_content_keywords()
        self._metadata_patterns = self._build_metadata_patterns()
    
    def classify(
        self,
        url: str,
        html_metadata: Optional[Dict[str, Any]] = None,
        content_structure: Optional[Dict[str, Any]] = None,
        ai_analysis: Optional[Dict[str, Any]] = None,
        visual_layout: Optional[Dict[str, Any]] = None
    ) -> PageClassification:
        """
        Classify a page using multi-signal analysis.
        
        Args:
            url: Page URL
            html_metadata: Extracted HTML metadata (og:type, schema.org, etc.)
            content_structure: Semantic structure analysis (headings, CTAs, etc.)
            ai_analysis: AI vision analysis results
            visual_layout: Visual layout indicators
            
        Returns:
            PageClassification with primary category, confidence, and reasoning
        """
        signals: List[ClassificationSignal] = []
        
        # 1. Analyze URL patterns
        url_signals = self._analyze_url_patterns(url)
        signals.extend(url_signals)
        
        # 2. Analyze HTML metadata
        if html_metadata:
            metadata_signals = self._analyze_html_metadata(html_metadata)
            signals.extend(metadata_signals)
        
        # 3. Analyze content structure
        if content_structure:
            structure_signals = self._analyze_content_structure(content_structure)
            signals.extend(structure_signals)
        
        # 4. Analyze AI vision results
        if ai_analysis:
            ai_signals = self._analyze_ai_vision(ai_analysis)
            signals.extend(ai_signals)
        
        # 5. Aggregate signals and determine classification
        classification = self._aggregate_signals(signals)
        
        # 6. Adapt preview strategy based on classification
        classification.preview_strategy = self._determine_preview_strategy(
            classification.primary_category,
            signals,
            content_structure,
            ai_analysis
        )
        
        logger.info(
            f"Page classified as {classification.primary_category.value} "
            f"(confidence: {classification.confidence:.2f}): {classification.reasoning}"
        )
        
        return classification
    
    def _analyze_url_patterns(self, url: str) -> List[ClassificationSignal]:
        """Analyze URL structure and patterns."""
        signals = []
        url_lower = url.lower()
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Profile patterns
        profile_patterns = [
            r'/profile[s]?/',
            r'/user[s]?/',
            r'/expert[s]?/',
            r'/member[s]?/',
            r'/people/',
            r'/person/',
            r'/team/',
            r'/about/.*/.*',  # /about/john-doe
        ]
        profile_matches = sum(1 for p in profile_patterns if re.search(p, path))
        if profile_matches > 0:
            signals.append(ClassificationSignal(
                source="url_pattern",
                category=PageCategory.PROFILE,
                confidence=min(0.7 + (profile_matches * 0.1), 0.95),
                reasoning=f"URL path matches {profile_matches} profile pattern(s): {path}",
                weight=1.2  # URL patterns are strong signals
            ))
        
        # Product patterns
        product_patterns = [
            r'/product[s]?/',
            r'/shop/',
            r'/store/',
            r'/item[s]?/',
            r'/p/',
            r'/buy/',
            r'/purchase/',
            r'/cart/',
            r'/checkout/',
        ]
        product_matches = sum(1 for p in product_patterns if re.search(p, path))
        if product_matches > 0:
            signals.append(ClassificationSignal(
                source="url_pattern",
                category=PageCategory.PRODUCT,
                confidence=min(0.75 + (product_matches * 0.08), 0.95),
                reasoning=f"URL path matches {product_matches} product/e-commerce pattern(s): {path}",
                weight=1.3  # E-commerce URLs are very strong signals
            ))
        
        # Content/article patterns
        content_patterns = [
            r'/blog/',
            r'/post[s]?/',
            r'/article[s]?/',
            r'/news/',
            r'/docs/',
            r'/documentation/',
            r'/guide[s]?/',
            r'/tutorial[s]?/',
        ]
        content_matches = sum(1 for p in content_patterns if re.search(p, path))
        if content_matches > 0:
            signals.append(ClassificationSignal(
                source="url_pattern",
                category=PageCategory.CONTENT,
                confidence=min(0.7 + (content_matches * 0.1), 0.95),
                reasoning=f"URL path matches {content_matches} content/article pattern(s): {path}",
                weight=1.2
            ))
        
        # Landing/marketing patterns
        landing_patterns = [
            r'^/$',  # Homepage
            r'/home',
            r'/landing',
            r'/marketing',
            r'/pricing',  # Pricing pages are landing pages
            r'/features',
            r'/solutions',
        ]
        landing_matches = sum(1 for p in landing_patterns if re.search(p, path))
        if landing_matches > 0:
            signals.append(ClassificationSignal(
                source="url_pattern",
                category=PageCategory.LANDING,
                confidence=min(0.65 + (landing_matches * 0.1), 0.9),
                reasoning=f"URL path matches {landing_matches} landing/marketing pattern(s): {path}",
                weight=1.1
            ))
        
        # Tool/app patterns
        tool_patterns = [
            r'/app/',
            r'/dashboard',
            r'/dashboard/',
            r'/tool[s]?/',
            r'/workspace/',
            r'/console/',
            r'/admin/',
        ]
        tool_matches = sum(1 for p in tool_patterns if re.search(p, path))
        if tool_matches > 0:
            signals.append(ClassificationSignal(
                source="url_pattern",
                category=PageCategory.TOOL,
                confidence=min(0.7 + (tool_matches * 0.1), 0.95),
                reasoning=f"URL path matches {tool_matches} tool/app pattern(s): {path}",
                weight=1.2
            ))
        
        # Company patterns (weaker signal, often combined with others)
        company_patterns = [
            r'/about',
            r'/company',
            r'/team',
            r'/careers',
        ]
        company_matches = sum(1 for p in company_patterns if re.search(p, path))
        if company_matches > 0 and not profile_matches:  # Don't double-count
            signals.append(ClassificationSignal(
                source="url_pattern",
                category=PageCategory.COMPANY,
                confidence=min(0.5 + (company_matches * 0.1), 0.75),
                reasoning=f"URL path matches {company_matches} company pattern(s): {path}",
                weight=0.9
            ))
        
        return signals
    
    def _analyze_html_metadata(self, metadata: Dict[str, Any]) -> List[ClassificationSignal]:
        """Analyze HTML metadata (og:type, schema.org, etc.)."""
        signals = []
        
        # Open Graph type
        og_type = metadata.get("og:type", "").lower()
        if og_type:
            if "profile" in og_type or "person" in og_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.PROFILE,
                    confidence=0.85,
                    reasoning=f"og:type indicates profile: {og_type}",
                    weight=1.4  # og:type is a very strong signal
                ))
            elif "product" in og_type or "item" in og_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.PRODUCT,
                    confidence=0.9,
                    reasoning=f"og:type indicates product: {og_type}",
                    weight=1.4
                ))
            elif "article" in og_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.CONTENT,
                    confidence=0.85,
                    reasoning=f"og:type indicates article: {og_type}",
                    weight=1.4
                ))
            elif "website" in og_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.LANDING,
                    confidence=0.6,
                    reasoning=f"og:type indicates website: {og_type}",
                    weight=1.0
                ))
        
        # Schema.org types
        schema_type_raw = metadata.get("schema_type")
        schema_type = schema_type_raw.lower() if schema_type_raw else ""
        if schema_type:
            if "person" in schema_type or "profilepage" in schema_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.PROFILE,
                    confidence=0.8,
                    reasoning=f"Schema.org type indicates profile: {schema_type}",
                    weight=1.3
                ))
            elif "product" in schema_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.PRODUCT,
                    confidence=0.85,
                    reasoning=f"Schema.org type indicates product: {schema_type}",
                    weight=1.3
                ))
            elif "article" in schema_type or "blogposting" in schema_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.CONTENT,
                    confidence=0.8,
                    reasoning=f"Schema.org type indicates article: {schema_type}",
                    weight=1.3
                ))
            elif "organization" in schema_type or "corporation" in schema_type:
                signals.append(ClassificationSignal(
                    source="html_metadata",
                    category=PageCategory.COMPANY,
                    confidence=0.7,
                    reasoning=f"Schema.org type indicates company: {schema_type}",
                    weight=1.1
                ))
        
        return signals
    
    def _analyze_content_structure(self, structure: Dict[str, Any]) -> List[ClassificationSignal]:
        """Analyze semantic content structure."""
        signals = []
        
        # Check for profile indicators
        has_profile_image = structure.get("has_profile_image", False)
        has_contact_info = structure.get("has_contact_info", False)
        has_social_links = structure.get("has_social_links", False)
        has_bio = structure.get("has_bio", False)
        
        profile_score = sum([
            has_profile_image * 0.3,
            has_contact_info * 0.2,
            has_social_links * 0.2,
            has_bio * 0.3
        ])
        
        if profile_score > 0.3:
            signals.append(ClassificationSignal(
                source="content_structure",
                category=PageCategory.PROFILE,
                confidence=min(profile_score, 0.8),
                reasoning=f"Content structure suggests profile (image: {has_profile_image}, contact: {has_contact_info}, bio: {has_bio})",
                weight=1.1
            ))
        
        # Check for product indicators
        has_price = structure.get("has_price", False)
        has_add_to_cart = structure.get("has_add_to_cart", False)
        has_product_image = structure.get("has_product_image", False)
        has_reviews = structure.get("has_reviews", False)
        
        product_score = sum([
            has_price * 0.3,
            has_add_to_cart * 0.35,
            has_product_image * 0.2,
            has_reviews * 0.15
        ])
        
        if product_score > 0.3:
            signals.append(ClassificationSignal(
                source="content_structure",
                category=PageCategory.PRODUCT,
                confidence=min(product_score, 0.85),
                reasoning=f"Content structure suggests product (price: {has_price}, cart: {has_add_to_cart}, reviews: {has_reviews})",
                weight=1.2
            ))
        
        # Check for landing page indicators
        has_hero_section = structure.get("has_hero_section", False)
        has_cta_buttons = structure.get("has_cta_buttons", False)
        has_features = structure.get("has_features", False)
        has_testimonials = structure.get("has_testimonials", False)
        
        landing_score = sum([
            has_hero_section * 0.3,
            has_cta_buttons * 0.3,
            has_features * 0.2,
            has_testimonials * 0.2
        ])
        
        if landing_score > 0.3:
            signals.append(ClassificationSignal(
                source="content_structure",
                category=PageCategory.LANDING,
                confidence=min(landing_score, 0.75),
                reasoning=f"Content structure suggests landing page (hero: {has_hero_section}, CTAs: {has_cta_buttons}, features: {has_features})",
                weight=1.0
            ))
        
        # Check for content/article indicators
        has_author = structure.get("has_author", False)
        has_publish_date = structure.get("has_publish_date", False)
        has_article_content = structure.get("has_article_content", False)
        has_tags = structure.get("has_tags", False)
        
        content_score = sum([
            has_author * 0.3,
            has_publish_date * 0.25,
            has_article_content * 0.3,
            has_tags * 0.15
        ])
        
        if content_score > 0.3:
            signals.append(ClassificationSignal(
                source="content_structure",
                category=PageCategory.CONTENT,
                confidence=min(content_score, 0.8),
                reasoning=f"Content structure suggests article (author: {has_author}, date: {has_publish_date}, tags: {has_tags})",
                weight=1.1
            ))
        
        # Check for tool/app indicators
        has_dashboard = structure.get("has_dashboard", False)
        has_login = structure.get("has_login", False)
        has_workspace = structure.get("has_workspace", False)
        
        tool_score = sum([
            has_dashboard * 0.4,
            has_login * 0.3,
            has_workspace * 0.3
        ])
        
        if tool_score > 0.3:
            signals.append(ClassificationSignal(
                source="content_structure",
                category=PageCategory.TOOL,
                confidence=min(tool_score, 0.8),
                reasoning=f"Content structure suggests tool/app (dashboard: {has_dashboard}, login: {has_login})",
                weight=1.1
            ))
        
        return signals
    
    def _analyze_ai_vision(self, ai_analysis: Dict[str, Any]) -> List[ClassificationSignal]:
        """Analyze AI vision analysis results."""
        signals = []
        
        page_type = ai_analysis.get("page_type", "").lower()
        confidence = ai_analysis.get("analysis_confidence", 0.5)
        
        # Map AI page types to our categories
        type_mapping = {
            "profile": PageCategory.PROFILE,
            "personal": PageCategory.PROFILE,
            "product": PageCategory.PRODUCT,
            "ecommerce": PageCategory.PRODUCT,
            "marketplace": PageCategory.PRODUCT,
            "article": PageCategory.CONTENT,
            "blog": PageCategory.CONTENT,
            "landing": PageCategory.LANDING,
            "saas": PageCategory.LANDING,
            "startup": PageCategory.LANDING,
            "company": PageCategory.COMPANY,
            "enterprise": PageCategory.COMPANY,
            "tool": PageCategory.TOOL,
            "agency": PageCategory.COMPANY,
            "portfolio": PageCategory.COMPANY,
        }
        
        if page_type in type_mapping:
            mapped_category = type_mapping[page_type]
            # Use AI confidence, but cap it (AI can be overconfident)
            ai_confidence = min(confidence * 0.9, 0.85)
            
            signals.append(ClassificationSignal(
                source="ai_vision",
                category=mapped_category,
                confidence=ai_confidence,
                reasoning=f"AI vision analysis classified as {page_type} (confidence: {confidence:.2f})",
                weight=1.2  # AI vision is a strong signal
            ))
        
        return signals
    
    def _aggregate_signals(self, signals: List[ClassificationSignal]) -> PageClassification:
        """Aggregate signals into final classification."""
        if not signals:
            return PageClassification(
                primary_category=PageCategory.UNKNOWN,
                confidence=0.0,
                reasoning="No classification signals available",
                signals=[]
            )
        
        # Weighted aggregation by category
        category_scores: Dict[PageCategory, float] = {}
        category_signals: Dict[PageCategory, List[ClassificationSignal]] = {}
        
        for signal in signals:
            category = signal.category
            weighted_score = signal.confidence * signal.weight
            
            if category not in category_scores:
                category_scores[category] = 0.0
                category_signals[category] = []
            
            category_scores[category] += weighted_score
            category_signals[category].append(signal)
        
        # Normalize scores (divide by sum of weights for each category)
        for category in category_scores:
            total_weight = sum(s.weight for s in category_signals[category])
            if total_weight > 0:
                category_scores[category] = min(category_scores[category] / total_weight, 1.0)
        
        # Find primary category
        if not category_scores:
            primary = PageCategory.UNKNOWN
            confidence = 0.0
        else:
            primary = max(category_scores.items(), key=lambda x: x[1])[0]
            confidence = category_scores[primary]
        
        # Get alternative categories (sorted by score)
        alternatives = sorted(
            [(cat, score) for cat, score in category_scores.items() if cat != primary],
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Top 3 alternatives
        
        # Build reasoning
        reasoning_parts = []
        for signal in category_signals.get(primary, []):
            reasoning_parts.append(f"{signal.source}: {signal.reasoning}")
        
        if not reasoning_parts:
            reasoning = f"Classified as {primary.value} based on signal aggregation"
        else:
            reasoning = "; ".join(reasoning_parts[:3])  # Top 3 reasons
        
        return PageClassification(
            primary_category=primary,
            confidence=confidence,
            alternative_categories=alternatives,
            signals=signals,
            reasoning=reasoning
        )
    
    def _determine_preview_strategy(
        self,
        category: PageCategory,
        signals: List[ClassificationSignal],
        content_structure: Optional[Dict[str, Any]],
        ai_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Determine preview strategy based on page category.
        
        Returns a strategy dict with:
        - template_type: Which visual template to use
        - priority_elements: What elements to emphasize
        - layout_preferences: Layout-specific guidance
        """
        strategy = {
            "template_type": self._map_category_to_template(category),
            "priority_elements": [],
            "layout_preferences": {},
            "visual_emphasis": {}
        }
        
        if category == PageCategory.PROFILE:
            strategy["priority_elements"] = ["avatar", "name", "bio", "social_proof"]
            strategy["visual_emphasis"] = {
                "avatar": "prominent_circular",
                "name": "large_bold",
                "bio": "concise"
            }
            strategy["layout_preferences"] = {
                "avatar_position": "center_top",
                "content_hierarchy": "name > bio > social"
            }
        
        elif category == PageCategory.PRODUCT:
            strategy["priority_elements"] = ["product_image", "title", "price", "reviews"]
            strategy["visual_emphasis"] = {
                "product_image": "hero_large",
                "price": "prominent",
                "reviews": "visible"
            }
            strategy["layout_preferences"] = {
                "image_position": "primary",
                "content_hierarchy": "image > title > price > reviews"
            }
        
        elif category == PageCategory.LANDING:
            strategy["priority_elements"] = ["hero_image", "headline", "value_prop", "social_proof", "cta"]
            strategy["visual_emphasis"] = {
                "hero_image": "background_overlay",
                "headline": "very_large_bold",
                "value_prop": "clear_concise"
            }
            strategy["layout_preferences"] = {
                "image_position": "background",
                "content_hierarchy": "headline > value_prop > social_proof > cta"
            }
        
        elif category == PageCategory.CONTENT:
            strategy["priority_elements"] = ["article_image", "title", "author", "excerpt"]
            strategy["visual_emphasis"] = {
                "article_image": "header_large",
                "title": "large_readable",
                "excerpt": "preview_text"
            }
            strategy["layout_preferences"] = {
                "image_position": "top",
                "content_hierarchy": "image > title > excerpt"
            }
        
        elif category == PageCategory.TOOL:
            strategy["priority_elements"] = ["screenshot", "name", "key_features", "cta"]
            strategy["visual_emphasis"] = {
                "screenshot": "prominent",
                "name": "clear_bold",
                "features": "bullet_list"
            }
            strategy["layout_preferences"] = {
                "image_position": "split_or_background",
                "content_hierarchy": "name > screenshot > features"
            }
        
        elif category == PageCategory.COMPANY:
            strategy["priority_elements"] = ["logo", "company_name", "value_prop", "social_proof"]
            strategy["visual_emphasis"] = {
                "logo": "prominent",
                "company_name": "large",
                "value_prop": "clear"
            }
            strategy["layout_preferences"] = {
                "logo_position": "top",
                "content_hierarchy": "logo > name > value_prop"
            }
        
        else:  # UNKNOWN
            strategy["priority_elements"] = ["title", "description", "image"]
            strategy["visual_emphasis"] = {
                "title": "large",
                "description": "readable"
            }
            strategy["layout_preferences"] = {
                "content_hierarchy": "title > description"
            }
        
        return strategy
    
    def _map_category_to_template(self, category: PageCategory) -> str:
        """Map page category to frontend template type."""
        mapping = {
            PageCategory.PROFILE: "profile",
            PageCategory.PRODUCT: "product",
            PageCategory.LANDING: "landing",
            PageCategory.CONTENT: "article",
            PageCategory.TOOL: "landing",  # Tools use landing template
            PageCategory.COMPANY: "landing",  # Companies use landing template
            PageCategory.UNKNOWN: "landing",  # Default to landing
        }
        return mapping.get(category, "landing")
    
    def _build_url_patterns(self) -> Dict[str, List[str]]:
        """Build URL pattern database (for future extensibility)."""
        return {}  # Currently handled inline
    
    def _build_content_keywords(self) -> Dict[str, List[str]]:
        """Build content keyword database (for future extensibility)."""
        return {}  # Currently handled inline
    
    def _build_metadata_patterns(self) -> Dict[str, List[str]]:
        """Build metadata pattern database (for future extensibility)."""
        return {}  # Currently handled inline


# Singleton instance
_classifier_instance: Optional[IntelligentPageClassifier] = None


def get_page_classifier() -> IntelligentPageClassifier:
    """Get singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntelligentPageClassifier()
    return _classifier_instance

