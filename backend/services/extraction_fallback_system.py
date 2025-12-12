"""
Multi-Tier Fallback System for Extraction

Ensures we ALWAYS produce a result, even when primary methods fail.

FALLBACK TIERS:
1. Primary: AI vision extraction (GPT-4o with screenshot)
2. Retry: AI vision with correction guidance
3. Fallback 1: HTML semantic extraction (structure analysis)
4. Fallback 2: HTML basic extraction (meta tags, title)
5. Fallback 3: Minimal safe fallback (URL-based guess)

DESIGN PRINCIPLE: Never fail completely. Always produce something.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Callable
from urllib.parse import urlparse
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FallbackResult:
    """Result from fallback extraction."""
    extraction: Dict[str, Any]
    method_used: str
    tier: int
    success: bool
    fallback_reason: str = ""


class ExtractionFallbackSystem:
    """
    Multi-tier fallback system for robust extraction.
    
    Tries progressively simpler methods until one succeeds.
    """
    
    def __init__(self):
        """Initialize fallback system."""
        pass
    
    def extract_with_fallbacks(
        self,
        url: str,
        screenshot_bytes: Optional[bytes] = None,
        html_content: Optional[str] = None,
        primary_extraction_func: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> FallbackResult:
        """
        Attempt extraction with automatic fallbacks.
        
        Args:
            url: Page URL
            screenshot_bytes: Screenshot for AI vision
            html_content: HTML source for parsing
            primary_extraction_func: Primary extraction function
            *args, **kwargs: Additional args for extraction functions
            
        Returns:
            FallbackResult with best available extraction
        """
        # Tier 1: Primary AI vision extraction
        if primary_extraction_func and screenshot_bytes:
            try:
                logger.info("🎯 Tier 1: Primary AI vision extraction")
                result = primary_extraction_func(screenshot_bytes, *args, **kwargs)
                
                if result and result.get("the_hook"):
                    logger.info("✅ Tier 1 successful")
                    return FallbackResult(
                        extraction=result,
                        method_used="ai_vision_primary",
                        tier=1,
                        success=True
                    )
            except Exception as e:
                logger.warning(f"⚠️  Tier 1 failed: {e}")
        
        # Tier 2: HTML semantic extraction
        if html_content:
            try:
                logger.info("🔄 Tier 2: HTML semantic extraction")
                result = self._extract_from_html_semantic(url, html_content)
                
                if result and result.get("the_hook"):
                    logger.info("✅ Tier 2 successful (semantic HTML)")
                    return FallbackResult(
                        extraction=result,
                        method_used="html_semantic",
                        tier=2,
                        success=True,
                        fallback_reason="Primary AI extraction unavailable or failed"
                    )
            except Exception as e:
                logger.warning(f"⚠️  Tier 2 failed: {e}")
        
        # Tier 3: HTML basic extraction (meta tags)
        if html_content:
            try:
                logger.info("🔄 Tier 3: HTML basic extraction")
                result = self._extract_from_html_basic(url, html_content)
                
                if result and result.get("the_hook"):
                    logger.info("✅ Tier 3 successful (basic HTML)")
                    return FallbackResult(
                        extraction=result,
                        method_used="html_basic",
                        tier=3,
                        success=True,
                        fallback_reason="Semantic extraction failed"
                    )
            except Exception as e:
                logger.warning(f"⚠️  Tier 3 failed: {e}")
        
        # Tier 4: Minimal safe fallback (URL-based)
        logger.warning("🆘 Tier 4: Minimal safe fallback (URL-based)")
        result = self._create_minimal_fallback(url)
        
        return FallbackResult(
            extraction=result,
            method_used="minimal_fallback",
            tier=4,
            success=True,
            fallback_reason="All extraction methods failed, using URL-based fallback"
        )
    
    def _extract_from_html_semantic(self, url: str, html: str) -> Dict[str, Any]:
        """
        Extract from HTML using semantic structure analysis.
        
        Looks for:
        - Headings (h1, h2)
        - Meta tags (og:*, twitter:*)
        - Structured data (schema.org)
        - Main content
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract meta tags
        og_title = self._get_meta_tag(soup, 'og:title')
        og_description = self._get_meta_tag(soup, 'og:description')
        twitter_title = self._get_meta_tag(soup, 'twitter:title')
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else None
        
        # Find main heading
        h1 = soup.find('h1')
        h1_text = h1.text.strip() if h1 else None
        
        # Choose best hook
        hook = (
            og_title or
            twitter_title or
            h1_text or
            title or
            "Untitled"
        )
        
        # Clean hook
        hook = self._clean_text(hook)
        
        # Determine page type from URL
        page_type = self._classify_from_url(url)
        
        return {
            "the_hook": hook,
            "social_proof_found": None,
            "key_benefit": og_description if og_description else None,
            "page_type": page_type,
            "detected_person_name": None,
            "is_individual_profile": False,
            "company_indicators": [],
            "analysis_confidence": 0.5,
            "extraction_method": "html_semantic"
        }
    
    def _extract_from_html_basic(self, url: str, html: str) -> Dict[str, Any]:
        """
        Extract from HTML using basic meta tag parsing.
        
        Last resort before URL-only fallback.
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get title
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else None
        
        # Get description
        description_meta = soup.find('meta', attrs={'name': 'description'})
        description = description_meta.get('content') if description_meta else None
        
        # Use title or URL
        hook = title or self._extract_from_url(url) or "Untitled"
        hook = self._clean_text(hook)
        
        page_type = self._classify_from_url(url)
        
        return {
            "the_hook": hook,
            "social_proof_found": None,
            "key_benefit": description,
            "page_type": page_type,
            "detected_person_name": None,
            "is_individual_profile": False,
            "company_indicators": [],
            "analysis_confidence": 0.3,
            "extraction_method": "html_basic"
        }
    
    def _create_minimal_fallback(self, url: str) -> Dict[str, Any]:
        """
        Create minimal fallback from URL only.
        
        This is the absolute last resort - never fails.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # Try to make a reasonable hook from domain
        hook = domain.split('.')[0].capitalize()
        
        page_type = self._classify_from_url(url)
        
        return {
            "the_hook": hook,
            "social_proof_found": None,
            "key_benefit": None,
            "page_type": page_type,
            "detected_person_name": None,
            "is_individual_profile": False,
            "company_indicators": [],
            "analysis_confidence": 0.2,
            "extraction_method": "url_fallback"
        }
    
    def _classify_from_url(self, url: str) -> str:
        """Classify page type from URL patterns."""
        url_lower = url.lower()
        path = urlparse(url).path.lower()
        
        # Profile patterns
        if re.search(r'/profile/[^/]+$', path):
            return "profile"
        if re.search(r'/@[^/]+$', path):
            return "profile"
        if re.search(r'/user/[^/]+$', path):
            return "profile"
        
        # Product patterns
        if '/product' in path or '/shop' in path or '/store' in path:
            return "ecommerce"
        
        # Content patterns
        if '/blog' in path or '/article' in path or '/post' in path:
            return "content"
        
        # Default
        return "landing"
    
    def _extract_from_url(self, url: str) -> Optional[str]:
        """Extract a reasonable name from URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            # Use domain
            domain = parsed.netloc.replace('www.', '')
            return domain.split('.')[0].capitalize()
        
        # Use last path segment
        segments = path.split('/')
        last_segment = segments[-1]
        
        # Clean up
        cleaned = last_segment.replace('-', ' ').replace('_', ' ')
        return cleaned.title()
    
    def _get_meta_tag(self, soup, property_name: str) -> Optional[str]:
        """Get meta tag content."""
        tag = soup.find('meta', attrs={'property': property_name})
        if not tag:
            tag = soup.find('meta', attrs={'name': property_name})
        
        if tag and tag.get('content'):
            return tag.get('content').strip()
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if too long
        if len(text) > 150:
            text = text[:147] + "..."
        
        return text


def extract_with_fallbacks(
    url: str,
    screenshot_bytes: Optional[bytes] = None,
    html_content: Optional[str] = None,
    primary_func: Optional[Callable] = None,
    *args,
    **kwargs
) -> FallbackResult:
    """
    Convenience function for fallback extraction.
    
    Args:
        url: Page URL
        screenshot_bytes: Screenshot for AI vision
        html_content: HTML source
        primary_func: Primary extraction function
        *args, **kwargs: Additional arguments
        
    Returns:
        FallbackResult with best available extraction
    """
    system = ExtractionFallbackSystem()
    return system.extract_with_fallbacks(
        url,
        screenshot_bytes,
        html_content,
        primary_func,
        *args,
        **kwargs
    )
