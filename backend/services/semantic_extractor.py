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
            # Page structure indicators for classification
            "has_profile_image": bool,
            "has_contact_info": bool,
            "has_social_links": bool,
            "has_bio": bool,
            "has_price": bool,
            "has_add_to_cart": bool,
            "has_product_image": bool,
            "has_reviews": bool,
            "has_hero_section": bool,
            "has_cta_buttons": bool,
            "has_features": bool,
            "has_testimonials": bool,
            "has_author": bool,
            "has_publish_date": bool,
            "has_article_content": bool,
            "has_tags": bool,
            "has_dashboard": bool,
            "has_login": bool,
            "has_workspace": bool,
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
    
    # Detect page structure indicators for classification
    structure_indicators = _detect_structure_indicators(soup, primary_content, secondary_content)
    
    return {
        "primary_content": primary_content[:2000],  # Limit length
        "secondary_content": secondary_content[:1000],
        "intent": intent,
        "sentiment": sentiment,
        "topic_keywords": topic_keywords,
        "named_entities": named_entities,
        **structure_indicators  # Merge structure indicators
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


def _detect_structure_indicators(soup: BeautifulSoup, primary_content: str, secondary_content: str) -> Dict[str, bool]:
    """Detect structural indicators that help classify page type."""
    content_lower = (primary_content + " " + secondary_content).lower()
    
    # Profile indicators
    has_profile_image = bool(
        soup.find('img', class_=re.compile(r'avatar|profile|user|expert|person|headshot', re.I)) or
        soup.find('img', alt=re.compile(r'profile|avatar|headshot|portrait', re.I))
    )
    has_contact_info = bool(
        re.search(r'contact|email|phone|address|reach out|get in touch', content_lower) or
        soup.find('a', href=re.compile(r'mailto:|tel:', re.I))
    )
    has_social_links = bool(
        soup.find_all('a', href=re.compile(r'twitter|linkedin|github|facebook|instagram', re.I)) or
        re.search(r'follow|connect|social', content_lower)
    )
    has_bio = bool(
        re.search(r'bio|biography|about me|about.*background|introduction', content_lower) or
        soup.find(['section', 'div'], class_=re.compile(r'bio|about', re.I))
    )
    
    # Product indicators
    has_price = bool(
        re.search(r'\$[\d,]+|€[\d,]+|£[\d,]+|price|cost|pricing|\d+\.\d{2}', content_lower) or
        soup.find(string=re.compile(r'\$|€|£|price', re.I))
    )
    has_add_to_cart = bool(
        re.search(r'add to cart|buy now|purchase|checkout|add.*cart', content_lower) or
        soup.find('button', string=re.compile(r'add|buy|purchase|cart', re.I)) or
        soup.find('a', string=re.compile(r'buy|purchase|cart', re.I))
    )
    has_product_image = bool(
        soup.find('img', class_=re.compile(r'product|item|merchandise', re.I)) or
        soup.find('img', alt=re.compile(r'product|item', re.I))
    )
    has_reviews = bool(
        re.search(r'review|rating|star|★|⭐|\d+ out of \d+', content_lower) or
        soup.find(['div', 'section'], class_=re.compile(r'review|rating|testimonial', re.I))
    )
    
    # Landing page indicators
    has_hero_section = bool(
        soup.find(['section', 'div'], class_=re.compile(r'hero|banner|jumbotron|headline', re.I)) or
        soup.find('h1')  # Most landing pages have prominent H1
    )
    has_cta_buttons = bool(
        soup.find_all('button', string=re.compile(r'get started|sign up|learn more|try|free|demo', re.I)) or
        soup.find_all('a', string=re.compile(r'get started|sign up|learn more|try|free|demo', re.I)) or
        re.search(r'get started|sign up|try.*free|start.*trial', content_lower)
    )
    has_features = bool(
        soup.find(['section', 'div'], class_=re.compile(r'feature|benefit|capability', re.I)) or
        re.search(r'feature|benefit|capability|what.*offer', content_lower)
    )
    has_testimonials = bool(
        soup.find(['section', 'div'], class_=re.compile(r'testimonial|review|quote', re.I)) or
        re.search(r'said|testimonial|customer.*said|client.*said', content_lower)
    )
    
    # Content/article indicators
    has_author = bool(
        soup.find(['span', 'div', 'p'], class_=re.compile(r'author|byline|writer', re.I)) or
        soup.find('meta', attrs={'name': re.compile(r'author', re.I)}) or
        re.search(r'by\s+[A-Z][a-z]+\s+[A-Z]|written by|author', content_lower)
    )
    has_publish_date = bool(
        soup.find(['time', 'span'], class_=re.compile(r'date|published|time', re.I)) or
        soup.find('meta', property='article:published_time') or
        re.search(r'published|posted|date.*\d{4}', content_lower)
    )
    has_article_content = bool(
        soup.find('article') or
        soup.find(['main', 'div'], class_=re.compile(r'article|post|content', re.I))
    )
    has_tags = bool(
        soup.find(['div', 'span'], class_=re.compile(r'tag|category|topic', re.I)) or
        soup.find_all('a', class_=re.compile(r'tag|category', re.I))
    )
    
    # Tool/app indicators
    has_dashboard = bool(
        soup.find(['div', 'section'], class_=re.compile(r'dashboard|workspace|console', re.I)) or
        re.search(r'dashboard|workspace|console|control.*panel', content_lower)
    )
    has_login = bool(
        soup.find('form', class_=re.compile(r'login|sign.*in|auth', re.I)) or
        soup.find('input', type='password') or
        re.search(r'login|sign in|log in|password', content_lower)
    )
    has_workspace = bool(
        soup.find(['div', 'section'], class_=re.compile(r'workspace|editor|canvas', re.I)) or
        re.search(r'workspace|editor|canvas|work.*space', content_lower)
    )
    
    return {
        "has_profile_image": has_profile_image,
        "has_contact_info": has_contact_info,
        "has_social_links": has_social_links,
        "has_bio": has_bio,
        "has_price": has_price,
        "has_add_to_cart": has_add_to_cart,
        "has_product_image": has_product_image,
        "has_reviews": has_reviews,
        "has_hero_section": has_hero_section,
        "has_cta_buttons": has_cta_buttons,
        "has_features": has_features,
        "has_testimonials": has_testimonials,
        "has_author": has_author,
        "has_publish_date": has_publish_date,
        "has_article_content": has_article_content,
        "has_tags": has_tags,
        "has_dashboard": has_dashboard,
        "has_login": has_login,
        "has_workspace": has_workspace,
    }

