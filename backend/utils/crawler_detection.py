"""
Crawler detection utility for social media crawlers.

This module detects known social crawler user agents to prepare for
future server-side crawler interception without implementing it yet.
"""
import re
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# Known social crawler user agents
# Based on real-world crawler patterns from major platforms
CRAWLER_PATTERNS = {
    # Facebook/Meta crawlers
    'facebookexternalhit': 'facebook',
    'Facebot': 'facebook',
    'facebookcatalog': 'facebook',
    
    # Twitter/X crawlers
    'Twitterbot': 'twitter',
    'twitterbot': 'twitter',
    
    # LinkedIn crawlers
    'LinkedInBot': 'linkedin',
    'linkedinbot': 'linkedin',
    
    # WhatsApp crawlers
    'WhatsApp': 'whatsapp',
    'whatsapp': 'whatsapp',
    
    # Telegram crawlers
    'TelegramBot': 'telegram',
    'telegrambot': 'telegram',
    
    # Slack crawlers
    'Slackbot': 'slack',
    'slackbot': 'slack',
    'Slackbot-LinkExpanding': 'slack',
    
    # Discord crawlers
    'Discordbot': 'discord',
    'discordbot': 'discord',
    
    # Pinterest crawlers
    'Pinterestbot': 'pinterest',
    'pinterestbot': 'pinterest',
    'Pinterest': 'pinterest',
    
    # Reddit crawlers
    'redditbot': 'reddit',
    'Redditbot': 'reddit',
    
    # Apple crawlers
    'Applebot': 'apple',
    'applebot': 'apple',
    
    # Google crawlers (for rich snippets)
    'Googlebot': 'google',
    'googlebot': 'google',
    
    # Microsoft crawlers
    'bingbot': 'microsoft',
    'Bingbot': 'microsoft',
    'msnbot': 'microsoft',
    
    # Generic Open Graph crawlers
    'SkypeUriPreview': 'skype',
    'SkypePreview': 'skype',
}


def detect_crawler(user_agent: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect if a request is from a known social crawler.
    
    Args:
        user_agent: The User-Agent header from the request
        
    Returns:
        Tuple of (crawler_name, platform) or (None, None) if not a crawler
        Example: ('facebookexternalhit', 'facebook') or (None, None)
    """
    if not user_agent:
        return None, None
    
    user_agent_lower = user_agent.lower()
    
    # Check against known patterns
    for pattern, platform in CRAWLER_PATTERNS.items():
        if pattern.lower() in user_agent_lower:
            # Return the matched pattern and platform
            return pattern, platform
    
    return None, None


def is_social_crawler(user_agent: Optional[str]) -> bool:
    """
    Simple boolean check if request is from a social crawler.
    
    Args:
        user_agent: The User-Agent header from the request
        
    Returns:
        True if detected as a social crawler, False otherwise
    """
    crawler_name, _ = detect_crawler(user_agent)
    return crawler_name is not None


def log_crawler_detection(
    user_agent: Optional[str],
    url: str,
    detected_crawler: Optional[str],
    platform: Optional[str]
) -> None:
    """
    Log crawler detection for future analysis.
    
    This prepares the system for server-side interception by tracking
    when and where crawlers are detected.
    
    Args:
        user_agent: The User-Agent header
        url: The URL being requested
        detected_crawler: The detected crawler name (if any)
        platform: The platform name (if any)
    """
    if detected_crawler:
        logger.info(
            f"Crawler detected: {detected_crawler} (platform: {platform}) for URL: {url}",
            extra={
                "crawler_name": detected_crawler,
                "platform": platform,
                "url": url,
                "user_agent": user_agent,
                "event_type": "crawler_detection"
            }
        )
    else:
        # Log non-crawler requests at debug level for analysis
        logger.debug(
            f"Non-crawler request for URL: {url}",
            extra={
                "url": url,
                "user_agent": user_agent,
                "event_type": "non_crawler_request"
            }
        )


def get_crawler_metadata(user_agent: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Get metadata about detected crawler for logging/analysis.
    
    Args:
        user_agent: The User-Agent header from the request
        
    Returns:
        Dictionary with crawler detection metadata
    """
    crawler_name, platform = detect_crawler(user_agent)
    
    return {
        "is_crawler": crawler_name is not None,
        "crawler_name": crawler_name,
        "platform": platform,
        "user_agent": user_agent
    }

