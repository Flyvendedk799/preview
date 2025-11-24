"""Preview type prediction based on metadata and content signals."""
from typing import Dict, Optional
from urllib.parse import urlparse


def predict_preview_type(metadata: Dict, url: str, ai_output: Dict) -> str:
    """
    Predict preview type based on metadata signals, URL patterns, and AI output.
    
    Args:
        metadata: Extracted metadata dictionary
        url: URL string
        ai_output: AI-generated output dictionary
        
    Returns:
        Preview type: "product", "blog", "landing", or "unknown"
    """
    url_lower = url.lower()
    title_lower = (metadata.get("priority_title") or "").lower()
    description_lower = (metadata.get("priority_description") or "").lower()
    
    # Product signals
    product_keywords = [
        "price", "buy", "cart", "add to cart", "sku", "product", "shop",
        "purchase", "checkout", "shipping", "in stock", "out of stock",
        "$", "€", "£", "dollar", "euro", "pound"
    ]
    
    product_score = 0
    for keyword in product_keywords:
        if keyword in title_lower or keyword in description_lower or keyword in url_lower:
            product_score += 1
    
    # Blog signals
    blog_keywords = [
        "blog", "post", "article", "author", "published", "publish date",
        "read more", "comments", "category", "tag", "archive", "by ", "written by"
    ]
    
    blog_score = 0
    for keyword in blog_keywords:
        if keyword in title_lower or keyword in description_lower or keyword in url_lower:
            blog_score += 1
    
    # Landing page signals (homepage, marketing)
    landing_keywords = [
        "home", "welcome", "about", "contact", "services", "features",
        "get started", "sign up", "learn more", "discover", "explore"
    ]
    
    landing_score = 0
    parsed_url = urlparse(url)
    if parsed_url.path == "/" or parsed_url.path == "":
        landing_score += 2  # Homepage is strong signal
    
    for keyword in landing_keywords:
        if keyword in title_lower or keyword in description_lower:
            landing_score += 1
    
    # Determine type based on scores
    if product_score >= 2:
        return "product"
    elif blog_score >= 2:
        return "blog"
    elif landing_score >= 2:
        return "landing"
    elif ai_output.get("type") in ["product", "blog", "landing"]:
        # Fallback to AI prediction if signals are weak
        return ai_output.get("type")
    else:
        return "unknown"

