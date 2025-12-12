"""
Context-Aware Extraction - Intelligent Content Extraction Based on Page Context

Enhances extraction by understanding page context:
- Page type (landing, product, blog, etc.)
- User intent
- Content hierarchy
- Semantic relationships
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PageContext:
    """Page context information."""
    page_type: str  # landing, product, blog, profile, etc.
    user_intent: str  # purchase, learn, connect, etc.
    content_hierarchy: List[str]  # Ordered list of content importance
    semantic_relationships: Dict[str, List[str]]  # Related content groups


class ContextAwareExtractor:
    """
    Context-aware content extraction.
    
    Uses page context to:
    - Prioritize relevant content
    - Understand content relationships
    - Extract with intent awareness
    """
    
    def __init__(self):
        """Initialize context-aware extractor."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_context(
        self,
        url: str,
        html_content: str,
        page_classification: Optional[Any] = None
    ) -> PageContext:
        """
        Analyze page context.
        
        Args:
            url: Page URL
            html_content: HTML content
            page_classification: Page classification result
            
        Returns:
            PageContext with analyzed information
        """
        # Determine page type
        page_type = "unknown"
        if page_classification:
            page_type = getattr(page_classification, 'primary_category', 'unknown')
            if hasattr(page_type, 'value'):
                page_type = page_type.value
        
        # Infer user intent from page type
        intent_map = {
            "landing": "learn",
            "product": "purchase",
            "blog": "read",
            "profile": "connect",
            "service": "inquire",
            "portfolio": "explore"
        }
        user_intent = intent_map.get(page_type.lower(), "browse")
        
        # Extract content hierarchy (simplified - would use NLP/AI)
        content_hierarchy = self._extract_content_hierarchy(html_content)
        
        # Extract semantic relationships
        semantic_relationships = self._extract_semantic_relationships(html_content)
        
        context = PageContext(
            page_type=page_type,
            user_intent=user_intent,
            content_hierarchy=content_hierarchy,
            semantic_relationships=semantic_relationships
        )
        
        self.logger.info(
            f"Context analyzed: type={page_type}, intent={user_intent}, "
            f"hierarchy_size={len(content_hierarchy)}"
        )
        
        return context
    
    def extract_with_context(
        self,
        html_content: str,
        context: PageContext
    ) -> Dict[str, Any]:
        """
        Extract content with context awareness.
        
        Args:
            html_content: HTML content
            context: Page context
            
        Returns:
            Extracted content prioritized by context
        """
        # Use context to prioritize extraction
        # For landing pages, prioritize headline and CTA
        # For product pages, prioritize product name and price
        # For blog posts, prioritize title and excerpt
        
        extracted = {}
        
        if context.page_type.lower() == "landing":
            # Landing page: prioritize headline, value prop, CTA
            extracted["priority_fields"] = ["title", "subtitle", "cta_text"]
        elif context.page_type.lower() == "product":
            # Product page: prioritize product name, price, features
            extracted["priority_fields"] = ["title", "price", "features", "credibility_items"]
        elif context.page_type.lower() == "blog":
            # Blog post: prioritize title, excerpt, author
            extracted["priority_fields"] = ["title", "description", "author"]
        else:
            # Default: standard priority
            extracted["priority_fields"] = ["title", "description"]
        
        # Use content hierarchy to order results
        extracted["content_order"] = context.content_hierarchy
        
        self.logger.info(
            f"Context-aware extraction: priority_fields={extracted['priority_fields']}"
        )
        
        return extracted
    
    def _extract_content_hierarchy(
        self,
        html_content: str
    ) -> List[str]:
        """
        Extract content hierarchy from HTML.
        
        Args:
            html_content: HTML content
            
        Returns:
            Ordered list of content elements by importance
        """
        # Simplified extraction - would use proper HTML parsing
        hierarchy = []
        
        # Look for h1 tags (highest priority)
        if "<h1" in html_content.lower():
            hierarchy.append("h1")
        
        # Look for h2 tags
        if "<h2" in html_content.lower():
            hierarchy.append("h2")
        
        # Look for meta description
        if 'name="description"' in html_content.lower():
            hierarchy.append("meta_description")
        
        # Look for og:title
        if 'property="og:title"' in html_content.lower():
            hierarchy.append("og_title")
        
        return hierarchy
    
    def _extract_semantic_relationships(
        self,
        html_content: str
    ) -> Dict[str, List[str]]:
        """
        Extract semantic relationships between content elements.
        
        Args:
            html_content: HTML content
            
        Returns:
            Dictionary mapping content types to related elements
        """
        relationships = {}
        
        # Group related elements (simplified)
        if "price" in html_content.lower() or "$" in html_content:
            relationships["pricing"] = ["price", "currency", "discount"]
        
        if "rating" in html_content.lower() or "review" in html_content.lower():
            relationships["social_proof"] = ["rating", "reviews", "testimonials"]
        
        return relationships

