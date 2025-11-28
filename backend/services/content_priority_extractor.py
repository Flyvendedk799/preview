"""Enhanced content extraction that prioritizes UI/UX-important content."""
import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup


def extract_priority_content(html: str, url: str) -> Dict[str, any]:
    """
    Extract the most important content from a page based on UI/UX signals.
    
    This function analyzes the page structure to identify what content is
    most visually prominent and important, then extracts that content.
    
    Args:
        html: HTML content as string
        url: URL string for pattern matching
        
    Returns:
        Dictionary with prioritized content fields:
        {
            "page_type": str,  # "profile", "product", "article", "landing", "unknown"
            "primary_title": str,  # Most important title on the page
            "primary_description": str,  # Most important description/bio
            "key_attributes": Dict,  # Structured data (name, rating, price, etc.)
            "visual_elements": List[str],  # Important images, icons
            "content_priority_score": float,  # Confidence score
        }
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    # Detect page type first
    page_type = _detect_page_type(soup, url)
    
    # Extract content based on page type
    if page_type == "profile":
        return _extract_profile_content(soup, url)
    elif page_type == "product":
        return _extract_product_content(soup, url)
    elif page_type == "article":
        return _extract_article_content(soup, url)
    else:
        return _extract_generic_content(soup, url)


def _detect_page_type(soup: BeautifulSoup, url: str) -> str:
    """Detect page type based on URL patterns, meta tags, and content structure."""
    url_lower = url.lower()
    
    # Check Open Graph type
    og_type = soup.find('meta', property='og:type')
    if og_type and og_type.get('content'):
        og_type_val = og_type.get('content').lower()
        if 'profile' in og_type_val or 'person' in og_type_val:
            return "profile"
        elif 'product' in og_type_val:
            return "product"
        elif 'article' in og_type_val:
            return "article"
    
    # Check URL patterns
    profile_patterns = [
        r'/profile[s]?/',
        r'/user[s]?/',
        r'/expert[s]?/',
        r'/member[s]?/',
        r'/people/',
        r'/shared/expert/',
        r'/person/',
    ]
    for pattern in profile_patterns:
        if re.search(pattern, url_lower):
            return "profile"
    
    product_patterns = [
        r'/product[s]?/',
        r'/shop/',
        r'/item[s]?/',
        r'/p/',
    ]
    for pattern in product_patterns:
        if re.search(pattern, url_lower):
            return "product"
    
    article_patterns = [
        r'/blog/',
        r'/post[s]?/',
        r'/article[s]?/',
        r'/news/',
    ]
    for pattern in article_patterns:
        if re.search(pattern, url_lower):
            return "article"
    
    # Check content structure for profile indicators
    body_text = soup.get_text().lower()
    
    # Profile indicators
    profile_keywords = [
        'kompetencer', 'competencies', 'skills', 'expertise',
        'rating', 'anmeldelser', 'reviews', 'follow', 'følg',
        'contact', 'kontakt', 'send forespørgsel', 'about',
        'om', 'bio', 'biography', 'location', 'lokation'
    ]
    profile_score = sum(1 for keyword in profile_keywords if keyword in body_text)
    
    # Product indicators
    product_keywords = [
        'add to cart', 'buy now', 'price', '$', '€', '£', 'kr',
        'in stock', 'out of stock', 'sku', 'shipping'
    ]
    product_score = sum(1 for keyword in product_keywords if keyword in body_text)
    
    # Article indicators
    article_keywords = [
        'published', 'author', 'read more', 'comments', 'category',
        'tag', 'archive', 'by ', 'written by'
    ]
    article_score = sum(1 for keyword in article_keywords if keyword in body_text)
    
    # Check for profile-specific UI elements
    profile_ui_elements = soup.find_all(['button', 'a'], string=re.compile(
        r'follow|følg|contact|kontakt|send|message|besked', re.I
    ))
    if len(profile_ui_elements) > 0:
        profile_score += 2
    
    # Check for profile image (circular avatar)
    profile_images = soup.find_all('img', class_=re.compile(
        r'avatar|profile|user|expert|person', re.I
    ))
    if len(profile_images) > 0:
        profile_score += 1
    
    # Determine type based on scores
    if profile_score > product_score and profile_score > article_score and profile_score >= 2:
        return "profile"
    elif product_score > article_score and product_score >= 2:
        return "product"
    elif article_score >= 2:
        return "article"
    
    return "unknown"


def _extract_profile_content(soup: BeautifulSoup, url: str) -> Dict[str, any]:
    """Extract content from a profile page."""
    result = {
        "page_type": "profile",
        "primary_title": None,
        "primary_description": None,
        "key_attributes": {},
        "visual_elements": [],
        "content_priority_score": 0.0,
    }
    
    # Extract profile name (highest priority)
    # Look for h1, og:title, or prominent heading
    h1 = soup.find('h1')
    if h1:
        result["primary_title"] = h1.get_text(strip=True)
        result["content_priority_score"] += 0.4
    
    # Check og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        if not result["primary_title"] or len(og_title.get('content')) < len(result["primary_title"]):
            result["primary_title"] = og_title.get('content').strip()
            result["content_priority_score"] += 0.3
    
    # Extract description/bio
    # Look for "About", "Om", "Bio" sections
    about_sections = soup.find_all(['div', 'section'], class_=re.compile(
        r'about|om|bio|biography|description|beskrivelse', re.I
    ))
    for section in about_sections:
        paragraphs = section.find_all('p')
        if paragraphs:
            bio_text = ' '.join([p.get_text(strip=True) for p in paragraphs[:2]])
            if bio_text and len(bio_text) > 20:
                result["primary_description"] = bio_text[:300]  # Limit length
                result["content_priority_score"] += 0.3
                break
    
    # Fallback to meta description
    if not result["primary_description"]:
        meta_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result["primary_description"] = meta_desc.get('content').strip()
            result["content_priority_score"] += 0.2
    
    # Extract key attributes
    # Location
    location_patterns = [
        r'location|lokation|location|sted|place',
        r'Danmark|Denmark|Copenhagen|København',
    ]
    body_text = soup.get_text()
    for pattern in location_patterns:
        location_elem = soup.find(string=re.compile(pattern, re.I))
        if location_elem:
            parent = location_elem.find_parent()
            if parent:
                location_text = parent.get_text(strip=True)
                if 'Danmark' in location_text or 'Denmark' in location_text:
                    result["key_attributes"]["location"] = "Danmark"
                    result["content_priority_score"] += 0.1
                    break
    
    # Rating/Reviews
    rating_elem = soup.find(string=re.compile(r'rating|anmeldelser|reviews|stars', re.I))
    if rating_elem:
        parent = rating_elem.find_parent()
        if parent:
            rating_text = parent.get_text(strip=True)
            # Extract number pattern
            rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
            if rating_match:
                result["key_attributes"]["rating"] = rating_match.group(1)
                result["content_priority_score"] += 0.1
    
    # Competencies/Skills
    competencies = []
    # Look for tags, badges, pills with competency keywords
    competency_keywords = ['kompetencer', 'competencies', 'skills', 'expertise', 'tags']
    for keyword in competency_keywords:
        competency_section = soup.find(['div', 'section'], class_=re.compile(keyword, re.I))
        if competency_section:
            tags = competency_section.find_all(['span', 'div', 'a'], class_=re.compile(
                r'tag|badge|pill|chip|label', re.I
            ))
            for tag in tags[:5]:  # Limit to 5
                tag_text = tag.get_text(strip=True)
                if tag_text and len(tag_text) > 2:
                    competencies.append(tag_text)
            if competencies:
                result["key_attributes"]["competencies"] = competencies
                result["content_priority_score"] += 0.2
                break
    
    # Extract profile image
    profile_images = soup.find_all('img', class_=re.compile(
        r'avatar|profile|user|expert|person', re.I
    ))
    if not profile_images:
        # Look for images in profile-like containers
        profile_containers = soup.find_all(['div', 'section'], class_=re.compile(
            r'profile|user|expert|person', re.I
        ))
        for container in profile_containers:
            img = container.find('img')
            if img and img.get('src'):
                profile_images.append(img)
                break
    
    # Also check og:image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        result["visual_elements"].append(og_image.get('content'))
        result["content_priority_score"] += 0.1
    
    for img in profile_images[:1]:  # Take first profile image
        src = img.get('src') or img.get('data-src')
        if src:
            result["visual_elements"].append(src)
            result["content_priority_score"] += 0.1
            break
    
    return result


def _extract_product_content(soup: BeautifulSoup, url: str) -> Dict[str, any]:
    """Extract content from a product page."""
    result = {
        "page_type": "product",
        "primary_title": None,
        "primary_description": None,
        "key_attributes": {},
        "visual_elements": [],
        "content_priority_score": 0.0,
    }
    
    # Similar logic but for products (price, features, etc.)
    # Implementation similar to profile but focused on product attributes
    h1 = soup.find('h1')
    if h1:
        result["primary_title"] = h1.get_text(strip=True)
        result["content_priority_score"] += 0.4
    
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        if not result["primary_title"]:
            result["primary_title"] = og_title.get('content').strip()
            result["content_priority_score"] += 0.3
    
    # Extract price
    price_elem = soup.find(string=re.compile(r'\d+[.,]\d+\s*(kr|€|\$|£)', re.I))
    if price_elem:
        result["key_attributes"]["price"] = price_elem.strip()
        result["content_priority_score"] += 0.2
    
    # Extract description
    meta_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        result["primary_description"] = meta_desc.get('content').strip()
        result["content_priority_score"] += 0.3
    
    # Extract product image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        result["visual_elements"].append(og_image.get('content'))
        result["content_priority_score"] += 0.1
    
    return result


def _extract_article_content(soup: BeautifulSoup, url: str) -> Dict[str, any]:
    """Extract content from an article/blog page."""
    result = {
        "page_type": "article",
        "primary_title": None,
        "primary_description": None,
        "key_attributes": {},
        "visual_elements": [],
        "content_priority_score": 0.0,
    }
    
    # Extract article title
    h1 = soup.find('h1')
    if h1:
        result["primary_title"] = h1.get_text(strip=True)
        result["content_priority_score"] += 0.4
    
    # Extract article description/excerpt
    article_tag = soup.find('article')
    if article_tag:
        paragraphs = article_tag.find_all('p', limit=2)
        if paragraphs:
            result["primary_description"] = ' '.join([p.get_text(strip=True) for p in paragraphs])[:300]
            result["content_priority_score"] += 0.3
    
    # Extract author
    author_elem = soup.find(['span', 'div'], class_=re.compile(r'author|by', re.I))
    if author_elem:
        result["key_attributes"]["author"] = author_elem.get_text(strip=True)
        result["content_priority_score"] += 0.1
    
    return result


def _extract_generic_content(soup: BeautifulSoup, url: str) -> Dict[str, any]:
    """Extract content from generic/unknown page types."""
    result = {
        "page_type": "unknown",
        "primary_title": None,
        "primary_description": None,
        "key_attributes": {},
        "visual_elements": [],
        "content_priority_score": 0.0,
    }
    
    # Extract h1
    h1 = soup.find('h1')
    if h1:
        result["primary_title"] = h1.get_text(strip=True)
        result["content_priority_score"] += 0.3
    
    # Extract og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        if not result["primary_title"]:
            result["primary_title"] = og_title.get('content').strip()
            result["content_priority_score"] += 0.2
    
    # Extract description
    meta_desc = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        result["primary_description"] = meta_desc.get('content').strip()
        result["content_priority_score"] += 0.2
    
    return result

