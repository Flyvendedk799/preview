"""High-quality metadata extraction from HTML using BeautifulSoup."""
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup


def clean_text(value: str) -> str:
    """
    Clean text by trimming whitespace, removing line breaks, and collapsing spaces.
    
    Args:
        value: Raw text string
        
    Returns:
        Cleaned text string
    """
    if not value:
        return ""
    
    # Remove line breaks and tabs
    text = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Collapse multiple spaces into single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text


def extract_metadata_from_html(html: str) -> Dict[str, Optional[str]]:
    """
    Extract high-quality metadata from HTML using BeautifulSoup.
    
    Returns layered metadata with priority fallbacks.
    
    Args:
        html: HTML content as string
        
    Returns:
        Dictionary with extracted metadata fields
    """
    soup = BeautifulSoup(html, 'lxml')
    
    metadata = {
        "title": None,
        "og_title": None,
        "description": None,
        "og_description": None,
        "og_image": None,
        "canonical_url": None,
        "h1": None,
        "text_summary": None,
    }
    
    # Extract <title>
    title_tag = soup.find('title')
    if title_tag:
        metadata["title"] = clean_text(title_tag.get_text())
    
    # Extract Open Graph title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        metadata["og_title"] = clean_text(og_title['content'])
    
    # Extract meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        metadata["description"] = clean_text(meta_desc['content'])
    
    # Extract Open Graph description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        metadata["og_description"] = clean_text(og_desc['content'])
    
    # Extract Open Graph image
    og_img = soup.find('meta', property='og:image')
    if og_img and og_img.get('content'):
        metadata["og_image"] = clean_text(og_img['content'])
    
    # Extract canonical URL
    canonical = soup.find('link', rel='canonical')
    if canonical and canonical.get('href'):
        metadata["canonical_url"] = clean_text(canonical['href'])
    
    # Extract first H1 (strong fallback for title)
    h1_tag = soup.find('h1')
    if h1_tag:
        metadata["h1"] = clean_text(h1_tag.get_text())
    
    # Extract text summary (first 2-3 paragraphs of readable text)
    paragraphs = soup.find_all('p')
    text_chunks = []
    for p in paragraphs[:3]:  # First 3 paragraphs
        text = clean_text(p.get_text())
        if text and len(text) > 20:  # Only meaningful paragraphs
            text_chunks.append(text)
    
    if text_chunks:
        metadata["text_summary"] = ' '.join(text_chunks[:200])  # Limit to ~200 chars
    
    # Calculate priority values
    priority_title = (
        metadata["og_title"] or
        metadata["title"] or
        metadata["h1"] or
        None
    )
    
    priority_description = (
        metadata["og_description"] or
        metadata["description"] or
        metadata["text_summary"] or
        None
    )
    
    return {
        **metadata,
        "priority_title": priority_title,
        "priority_description": priority_description,
    }

