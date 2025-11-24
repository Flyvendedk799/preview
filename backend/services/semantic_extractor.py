"""Semantic content extraction from HTML without AI."""
import re
from typing import Dict, List
from bs4 import BeautifulSoup


def extract_semantic_structure(html: str) -> Dict[str, any]:
    """
    Extract semantic structure from HTML content.
    
    Uses BeautifulSoup + heuristics + regex to understand content without AI.
    
    Returns:
        {
            "primary_content": str,
            "secondary_content": str,
            "intent": str,
            "sentiment": str,
            "topic_keywords": List[str],
            "named_entities": List[str],
        }
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    # Extract primary content (main, article, or first h1 + surrounding content)
    primary_content = ""
    secondary_content = ""
    
    # Try to find main content areas
    main_tag = soup.find('main')
    article_tag = soup.find('article')
    content_div = soup.find('div', class_=re.compile(r'content|main|article|post', re.I))
    
    if main_tag:
        primary_content = main_tag.get_text(separator=' ', strip=True)
    elif article_tag:
        primary_content = article_tag.get_text(separator=' ', strip=True)
    elif content_div:
        primary_content = content_div.get_text(separator=' ', strip=True)
    else:
        # Fallback: get text from body, prioritize headings and paragraphs
        body = soup.find('body')
        if body:
            # Get h1-h3 and first few paragraphs
            headings = body.find_all(['h1', 'h2', 'h3'])
            paragraphs = body.find_all('p', limit=5)
            primary_parts = []
            for h in headings:
                primary_parts.append(h.get_text(strip=True))
            for p in paragraphs:
                primary_parts.append(p.get_text(strip=True))
            primary_content = ' '.join(primary_parts)
    
    # Extract secondary content (sidebars, footers, etc.)
    sidebar = soup.find(['aside', 'nav'], class_=re.compile(r'sidebar|nav|menu', re.I))
    if sidebar:
        secondary_content = sidebar.get_text(separator=' ', strip=True)
    
    # Determine intent based on URL patterns and content structure
    intent = _detect_intent(soup, primary_content)
    
    # Detect sentiment (simple heuristic based on positive/negative words)
    sentiment = _detect_sentiment(primary_content)
    
    # Extract topic keywords (from headings, meta keywords, and frequent words)
    topic_keywords = _extract_topic_keywords(soup, primary_content)
    
    # Extract named entities (simple pattern matching for common entities)
    named_entities = _extract_named_entities(primary_content)
    
    return {
        "primary_content": primary_content[:2000],  # Limit length
        "secondary_content": secondary_content[:1000],
        "intent": intent,
        "sentiment": sentiment,
        "topic_keywords": topic_keywords,
        "named_entities": named_entities,
    }


def _detect_intent(soup: BeautifulSoup, content: str) -> str:
    """Detect page intent based on structure and content."""
    content_lower = content.lower()
    
    # Check meta tags
    og_type = soup.find('meta', property='og:type')
    if og_type and og_type.get('content'):
        og_type_val = og_type.get('content').lower()
        if 'article' in og_type_val or 'blog' in og_type_val:
            return "blog article"
        elif 'product' in og_type_val:
            return "product page"
        elif 'website' in og_type_val:
            return "landing page"
    
    # Check URL patterns (if available in content)
    url_patterns = {
        r'/product[s]?/': 'product page',
        r'/shop/': 'product page',
        r'/blog/': 'blog article',
        r'/post[s]?/': 'blog article',
        r'/article[s]?/': 'blog article',
        r'/pricing': 'landing page',
        r'/about': 'landing page',
        r'/contact': 'landing page',
    }
    
    # Check content structure
    h1 = soup.find('h1')
    if h1:
        h1_text = h1.get_text().lower()
        if any(word in h1_text for word in ['product', 'buy', 'shop', 'purchase']):
            return "product page"
        if any(word in h1_text for word in ['blog', 'article', 'post', 'news']):
            return "blog article"
    
    # Check for e-commerce indicators
    if any(word in content_lower for word in ['add to cart', 'buy now', 'price', '$', '€', '£']):
        return "product page"
    
    # Check for blog indicators
    if any(word in content_lower for word in ['published', 'author', 'read more', 'comments']):
        return "blog article"
    
    # Default to landing page
    return "landing page"


def _detect_sentiment(content: str) -> str:
    """Simple sentiment detection based on word patterns."""
    content_lower = content.lower()
    
    positive_words = [
        'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best',
        'perfect', 'awesome', 'brilliant', 'outstanding', 'superb', 'delighted',
        'happy', 'pleased', 'satisfied', 'thrilled', 'impressed'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'disappointed',
        'frustrated', 'angry', 'sad', 'unhappy', 'poor', 'failed', 'broken',
        'error', 'problem', 'issue', 'complaint'
    ]
    
    positive_count = sum(1 for word in positive_words if word in content_lower)
    negative_count = sum(1 for word in negative_words if word in content_lower)
    
    if positive_count > negative_count * 1.5:
        return "positive"
    elif negative_count > positive_count * 1.5:
        return "negative"
    else:
        return "neutral"


def _extract_topic_keywords(soup: BeautifulSoup, content: str) -> List[str]:
    """Extract topic keywords from meta tags and content."""
    keywords = []
    
    # Get meta keywords
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords and meta_keywords.get('content'):
        keywords.extend([k.strip() for k in meta_keywords.get('content').split(',')[:10]])
    
    # Extract from headings
    headings = soup.find_all(['h1', 'h2', 'h3'])
    for heading in headings[:5]:
        text = heading.get_text(strip=True)
        # Extract significant words (3+ chars, not common words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords.extend(words[:3])
    
    # Extract from meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc_words = re.findall(r'\b[a-zA-Z]{4,}\b', meta_desc.get('content').lower())
        keywords.extend(desc_words[:5])
    
    # Remove duplicates and common stop words
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
    keywords = [k for k in keywords if k.lower() not in stop_words and len(k) >= 3]
    
    # Return unique keywords, limited to 15
    seen = set()
    unique_keywords = []
    for k in keywords:
        k_lower = k.lower()
        if k_lower not in seen:
            seen.add(k_lower)
            unique_keywords.append(k)
            if len(unique_keywords) >= 15:
                break
    
    return unique_keywords


def _extract_named_entities(content: str) -> List[str]:
    """Extract named entities using simple pattern matching."""
    entities = []
    
    # Extract capitalized phrases (potential proper nouns)
    # Pattern: Capitalized word followed by optional capitalized words
    capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    matches = re.findall(capitalized_pattern, content)
    
    # Filter out common words and short phrases
    common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'Where', 'When', 'What', 'How', 'Why', 'Which', 'Who'}
    for match in matches:
        if len(match) >= 4 and match not in common_words:
            # Check if it's not a sentence start (preceded by period/question/exclamation)
            entities.append(match)
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, content)
    entities.extend(emails[:3])
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, content)
    entities.extend(urls[:3])
    
    # Return unique entities, limited to 10
    seen = set()
    unique_entities = []
    for e in entities:
        e_lower = e.lower()
        if e_lower not in seen:
            seen.add(e_lower)
            unique_entities.append(e)
            if len(unique_entities) >= 10:
                break
    
    return unique_entities

