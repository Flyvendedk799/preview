"""
Content Sanitizer - Pre-extraction HTML sanitization.

This module provides comprehensive content sanitization to remove unwanted
elements BEFORE AI analysis, ensuring cleaner extractions:

- Cookie consent dialogs/banners
- GDPR/CCPA privacy notices
- Navigation menus
- Footer content
- Generic popups/modals
- Ads and tracking elements

PHASE 3 IMPLEMENTATION:
- Pre-extraction HTML sanitization
- Post-extraction validation layer
- Content pattern matching

This drastically reduces cookie/navigation content leakage in previews.
"""

import re
import logging
from typing import Optional, List, Set, Tuple
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

# PHASE 2: Error Recovery Integration
try:
    from backend.services.error_recovery import (
        classify_error,
        ErrorType,
        graceful_extract
    )
    ERROR_RECOVERY_AVAILABLE = True
except ImportError:
    ERROR_RECOVERY_AVAILABLE = False


# =============================================================================
# COOKIE/CONSENT PATTERNS
# =============================================================================

COOKIE_ID_PATTERNS = [
    # Cookie-specific
    r'cookie[-_]?banner',
    r'cookie[-_]?consent',
    r'cookie[-_]?notice',
    r'cookie[-_]?bar',
    r'cookie[-_]?popup',
    r'cookie[-_]?modal',
    r'cookie[-_]?dialog',
    r'cookie[-_]?policy',
    r'cookie[-_]?settings',
    r'cookies[-_]?notice',
    r'cookies[-_]?consent',
    
    # GDPR/Privacy
    r'gdpr[-_]?banner',
    r'gdpr[-_]?consent',
    r'gdpr[-_]?notice',
    r'gdpr[-_]?modal',
    r'gdpr[-_]?popup',
    r'privacy[-_]?notice',
    r'privacy[-_]?consent',
    r'privacy[-_]?banner',
    r'privacy[-_]?popup',
    r'privacy[-_]?modal',
    r'ccpa[-_]?notice',
    r'ccpa[-_]?banner',
    
    # Consent management
    r'consent[-_]?banner',
    r'consent[-_]?modal',
    r'consent[-_]?dialog',
    r'consent[-_]?popup',
    r'consent[-_]?manager',
    r'onetrust',
    r'cookiebot',
    r'trustarc',
    r'quantcast',
    
    # Generic consent
    r'accept[-_]?cookies',
    r'manage[-_]?cookies',
    r'preferences[-_]?modal',
    r'tracking[-_]?consent',
]

COOKIE_CLASS_PATTERNS = COOKIE_ID_PATTERNS + [
    r'cc[-_]?banner',
    r'cc[-_]?window',
    r'cc[-_]?floating',
    r'cmp[-_]?modal',
    r'cmp[-_]?banner',
    r'consent[-_]?bar',
    r'notice[-_]?bar',
    r'alert[-_]?cookie',
]


# =============================================================================
# NAVIGATION PATTERNS
# =============================================================================

NAVIGATION_ID_PATTERNS = [
    r'^nav$',
    r'^navigation$',
    r'^main[-_]?nav',
    r'^primary[-_]?nav',
    r'^header[-_]?nav',
    r'^site[-_]?nav',
    r'^top[-_]?nav',
    r'^navbar',
    r'^menu$',
    r'^main[-_]?menu',
    r'^mobile[-_]?menu',
    r'^hamburger[-_]?menu',
    r'^sidebar[-_]?menu',
]

NAVIGATION_CLASS_PATTERNS = NAVIGATION_ID_PATTERNS + [
    r'nav[-_]?links',
    r'nav[-_]?items',
    r'menu[-_]?items',
    r'menu[-_]?links',
    r'header[-_]?links',
]


# =============================================================================
# FOOTER PATTERNS
# =============================================================================

FOOTER_ID_PATTERNS = [
    r'^footer$',
    r'^site[-_]?footer',
    r'^page[-_]?footer',
    r'^main[-_]?footer',
    r'^bottom[-_]?nav',
    r'^footer[-_]?nav',
]

FOOTER_CLASS_PATTERNS = FOOTER_ID_PATTERNS + [
    r'footer[-_]?links',
    r'footer[-_]?content',
    r'footer[-_]?menu',
    r'footer[-_]?widgets',
    r'legal[-_]?links',
    r'terms[-_]?links',
]


# =============================================================================
# OTHER UNWANTED PATTERNS
# =============================================================================

POPUP_PATTERNS = [
    r'popup[-_]?modal',
    r'modal[-_]?overlay',
    r'overlay[-_]?backdrop',
    r'newsletter[-_]?popup',
    r'subscribe[-_]?modal',
    r'exit[-_]?popup',
    r'promo[-_]?modal',
    r'discount[-_]?popup',
    r'welcome[-_]?modal',
]

AD_PATTERNS = [
    r'^ad[-_]?container',
    r'^advertisement',
    r'^ads[-_]?wrapper',
    r'^google[-_]?ads',
    r'^banner[-_]?ad',
    r'^sidebar[-_]?ad',
    r'sponsored[-_]?content',
    r'native[-_]?ad',
]

TRACKING_PATTERNS = [
    r'fb[-_]?pixel',
    r'gtm[-_]?container',
    r'analytics[-_]?tag',
    r'tracking[-_]?code',
]


# =============================================================================
# TEXT CONTENT PATTERNS (for post-extraction filtering)
# =============================================================================

COOKIE_TEXT_PATTERNS = [
    r'we\s+use\s+cookies',
    r'this\s+site\s+uses\s+cookies',
    r'this\s+website\s+uses\s+cookies',
    r'accept\s+all\s+cookies',
    r'accept\s+cookies',
    r'manage\s+cookies',
    r'cookie\s+preferences',
    r'cookie\s+settings',
    r'cookie\s+policy',
    r'by\s+continuing\s+to\s+use\s+this\s+site',
    r'by\s+using\s+this\s+website',
    r'consent\s+to\s+the\s+use\s+of',
    r'agree\s+to\s+our\s+use\s+of\s+cookies',
    r'accept\s+and\s+close',
    r'reject\s+all',
    r'manage\s+preferences',
    r'privacy\s+policy',
    r'gdpr\s+compliance',
    r'data\s+protection',
    r'your\s+privacy',
    r'essential\s+cookies\s+only',
    r'non[-_]?essential\s+cookies',
    r'third[-_]?party\s+cookies',
    r'analytics\s+cookies',
    r'marketing\s+cookies',
]

NAVIGATION_TEXT_PATTERNS = [
    r'^home$',
    r'^about$',
    r'^about\s+us$',
    r'^contact$',
    r'^contact\s+us$',
    r'^services$',
    r'^products$',
    r'^pricing$',
    r'^blog$',
    r'^news$',
    r'^faq$',
    r'^help$',
    r'^support$',
    r'^careers$',
    r'^login$',
    r'^sign\s+in$',
    r'^sign\s+up$',
    r'^register$',
    r'^log\s+out$',
    r'^menu$',
    r'^search$',
]

FOOTER_TEXT_PATTERNS = [
    r'all\s+rights\s+reserved',
    r'©\s*\d{4}',
    r'terms\s+of\s+service',
    r'terms\s+and\s+conditions',
    r'terms\s+of\s+use',
    r'privacy\s+policy',
    r'cookie\s+policy',
    r'legal\s+notice',
    r'disclaimer',
    r'sitemap',
    r'accessibility',
]


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def sanitize_html_for_extraction(html: str, aggressive: bool = False) -> str:
    """
    Remove cookie banners, navigation, footers, and other unwanted elements
    from HTML before AI analysis.
    
    This pre-extraction sanitization ensures cleaner AI extractions by removing
    elements that commonly pollute preview content.
    
    Args:
        html: Raw HTML content
        aggressive: If True, also removes less certain matches
        
    Returns:
        Sanitized HTML string
    """
    if not html or not html.strip():
        return html
    
    logger.debug("🧹 Starting HTML sanitization for extraction...")
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        elements_removed = 0
        
        # Remove HTML comments
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()
            elements_removed += 1
        
        # Remove script and style tags
        for tag in soup.find_all(['script', 'style', 'noscript', 'iframe']):
            tag.decompose()
            elements_removed += 1
        
        # Remove by ID patterns
        all_id_patterns = (
            COOKIE_ID_PATTERNS + 
            NAVIGATION_ID_PATTERNS + 
            FOOTER_ID_PATTERNS + 
            POPUP_PATTERNS + 
            AD_PATTERNS + 
            TRACKING_PATTERNS
        )
        
        for pattern in all_id_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for element in soup.find_all(id=regex):
                element.decompose()
                elements_removed += 1
        
        # Remove by class patterns
        all_class_patterns = (
            COOKIE_CLASS_PATTERNS + 
            NAVIGATION_CLASS_PATTERNS + 
            FOOTER_CLASS_PATTERNS + 
            POPUP_PATTERNS + 
            AD_PATTERNS
        )
        
        for pattern in all_class_patterns:
            regex = re.compile(pattern, re.IGNORECASE)
            for element in soup.find_all(class_=regex):
                element.decompose()
                elements_removed += 1
        
        # Remove common cookie consent elements by tag + attribute combinations
        cookie_elements = soup.find_all(
            lambda tag: (
                tag.get('data-cookie') or
                tag.get('data-consent') or
                tag.get('data-gdpr') or
                tag.get('data-privacy') or
                'cookie' in str(tag.get('role', '')).lower() or
                'consent' in str(tag.get('role', '')).lower()
            )
        )
        for element in cookie_elements:
            element.decompose()
            elements_removed += 1
        
        # Remove hidden elements (often used for cookie dialogs)
        hidden_elements = soup.find_all(
            lambda tag: (
                tag.get('aria-hidden') == 'true' or
                tag.get('hidden') is not None or
                'display:none' in str(tag.get('style', '')) or
                'visibility:hidden' in str(tag.get('style', ''))
            )
        )
        for element in hidden_elements:
            element.decompose()
            elements_removed += 1
        
        # Remove footer tag if present
        for footer in soup.find_all('footer'):
            footer.decompose()
            elements_removed += 1
        
        # Remove nav tags that aren't main content navigation
        for nav in soup.find_all('nav'):
            # Check if it looks like a site-wide nav
            nav_classes = ' '.join(nav.get('class', []))
            nav_id = nav.get('id', '')
            if any(p in nav_classes.lower() or p in nav_id.lower() 
                   for p in ['header', 'site', 'main', 'primary', 'top', 'mobile']):
                nav.decompose()
                elements_removed += 1
        
        # Aggressive mode: also remove less certain matches
        if aggressive:
            # Remove elements with very short text that match navigation patterns
            for element in soup.find_all(['a', 'button', 'span', 'div']):
                text = element.get_text(strip=True)
                if text and len(text) < 30:
                    text_lower = text.lower()
                    for pattern in NAVIGATION_TEXT_PATTERNS:
                        if re.match(pattern, text_lower, re.IGNORECASE):
                            # Don't remove if it's in the main content area
                            parent = element.parent
                            parent_classes = ' '.join(parent.get('class', [])) if parent else ''
                            if 'main' not in parent_classes and 'content' not in parent_classes:
                                element.decompose()
                                elements_removed += 1
                                break
        
        logger.info(f"🧹 Sanitization complete: {elements_removed} elements removed")
        
        return str(soup)
        
    except Exception as e:
        logger.warning(f"HTML sanitization failed: {e}")
        return html


def filter_cookie_content_from_text(text: str) -> Optional[str]:
    """
    Filter out cookie/consent content from extracted text.
    
    This is a post-extraction validation layer that removes any cookie
    content that slipped through HTML sanitization.
    
    Args:
        text: Extracted text content
        
    Returns:
        Cleaned text or None if entire text is cookie-related
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    text_lower = text.lower()
    
    # Check if entire text is cookie-related
    for pattern in COOKIE_TEXT_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Check what percentage of text matches cookie patterns
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                match_len = len(match.group(0))
                if match_len / len(text) > 0.5:  # More than 50% is cookie content
                    logger.debug(f"Filtered cookie content: '{text[:50]}...'")
                    return None
    
    # Remove cookie phrases from text
    cleaned_text = text
    for pattern in COOKIE_TEXT_PATTERNS:
        # Only remove if it's a distinct phrase, not part of legitimate content
        cleaned_text = re.sub(
            rf'(^|\s){pattern}($|\s)',
            ' ',
            cleaned_text,
            flags=re.IGNORECASE
        )
    
    # Clean up whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    # Check if anything meaningful remains
    if not cleaned_text or len(cleaned_text) < 10:
        return None
    
    return cleaned_text


def filter_navigation_content_from_text(text: str) -> Optional[str]:
    """
    Filter out navigation-only content from extracted text.
    
    Args:
        text: Extracted text content
        
    Returns:
        Cleaned text or None if entire text is navigation
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    text_lower = text.lower()
    
    # Check if entire text matches navigation patterns
    for pattern in NAVIGATION_TEXT_PATTERNS:
        if re.match(f'^{pattern}$', text_lower, re.IGNORECASE):
            logger.debug(f"Filtered navigation content: '{text}'")
            return None
    
    return text


def filter_footer_content_from_text(text: str) -> Optional[str]:
    """
    Filter out footer-only content from extracted text.
    
    Args:
        text: Extracted text content
        
    Returns:
        Cleaned text or None if entire text is footer content
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    text_lower = text.lower()
    
    # Check if text is mostly footer content
    footer_match_count = 0
    for pattern in FOOTER_TEXT_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            footer_match_count += 1
    
    # If multiple footer patterns match, it's likely footer content
    if footer_match_count >= 2:
        logger.debug(f"Filtered footer content: '{text[:50]}...'")
        return None
    
    return text


def sanitize_extracted_content(
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Sanitize extracted content by filtering out unwanted patterns.
    
    This comprehensive function applies all post-extraction filters to
    ensure the final content is clean and relevant.
    
    Args:
        title: Extracted title
        description: Extracted description
        tags: Extracted tags
        
    Returns:
        Tuple of (cleaned_title, cleaned_description, cleaned_tags)
    """
    cleaned_title = title
    cleaned_description = description
    cleaned_tags = tags or []
    
    # Filter title
    if cleaned_title:
        cleaned_title = filter_cookie_content_from_text(cleaned_title)
        if cleaned_title:
            cleaned_title = filter_navigation_content_from_text(cleaned_title)
    
    # Filter description
    if cleaned_description:
        cleaned_description = filter_cookie_content_from_text(cleaned_description)
        if cleaned_description:
            cleaned_description = filter_footer_content_from_text(cleaned_description)
    
    # Filter tags
    if cleaned_tags:
        filtered_tags = []
        for tag in cleaned_tags:
            clean_tag = filter_cookie_content_from_text(tag)
            if clean_tag:
                clean_tag = filter_navigation_content_from_text(clean_tag)
                if clean_tag:
                    filtered_tags.append(clean_tag)
        cleaned_tags = filtered_tags
    
    return cleaned_title, cleaned_description, cleaned_tags


def is_likely_cookie_content(text: str) -> bool:
    """
    Quick check if text is likely cookie/consent content.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be cookie content
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for cookie keywords
    cookie_keywords = [
        'cookie', 'consent', 'gdpr', 'privacy', 'accept all',
        'manage preferences', 'essential only', 'ccpa', 'tracking'
    ]
    
    keyword_count = sum(1 for kw in cookie_keywords if kw in text_lower)
    
    return keyword_count >= 2


def is_likely_navigation_content(text: str) -> bool:
    """
    Quick check if text is likely navigation content.
    
    Args:
        text: Text to check
        
    Returns:
        True if text appears to be navigation
    """
    if not text:
        return False
    
    text_lower = text.lower().strip()
    
    # Check for exact navigation matches
    for pattern in NAVIGATION_TEXT_PATTERNS:
        if re.match(f'^{pattern}$', text_lower, re.IGNORECASE):
            return True
    
    return False


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def get_sanitized_main_content(html: str) -> str:
    """
    Extract and return only the main content area, sanitized.
    
    This is useful for focusing AI analysis on the most relevant content.
    
    Args:
        html: Raw HTML
        
    Returns:
        Sanitized main content HTML
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for main content containers
        main_selectors = [
            'main',
            '[role="main"]',
            '#main-content',
            '#main',
            '.main-content',
            '.main',
            '#content',
            '.content',
            'article',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                # Sanitize just the main content
                main_html = str(main_element)
                return sanitize_html_for_extraction(main_html)
        
        # Fallback: sanitize entire HTML
        return sanitize_html_for_extraction(html)
        
    except Exception as e:
        logger.warning(f"Main content extraction failed: {e}")
        return sanitize_html_for_extraction(html)

