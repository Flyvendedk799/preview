"""AI-powered preview generation service using OpenAI."""
import json
import re
from typing import Dict, Optional, List
import requests
from openai import OpenAI
from backend.core.config import settings
from backend.schemas.brand import BrandSettings
from backend.services.metadata_extractor import extract_metadata_from_html
from backend.services.semantic_extractor import extract_semantic_structure
from backend.services.content_priority_extractor import extract_priority_content


from backend.services.retry_utils import sync_retry
import requests.exceptions

@sync_retry(max_attempts=3, base_delay=1.0, retry_on=(requests.exceptions.RequestException,))
def fetch_page_html(url: str) -> str:
    """
    Fetch HTML content from a URL with retry logic.
    
    Args:
        url: The URL to fetch
        
    Returns:
        HTML content as string, or empty string on failure
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)  # Increased to 10s max
        response.raise_for_status()
        return response.text
    except Exception as e:
        # Log error without exposing sensitive data
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching HTML from URL: {type(e).__name__}")
        return ""


def extract_basic_metadata(html: str) -> Dict[str, Optional[str]]:
    """
    Extract basic metadata from HTML using simple string operations.
    
    Args:
        html: HTML content as string
        
    Returns:
        Dictionary with title, description, og_image
    """
    metadata = {
        "title": None,
        "description": None,
        "og_image": None,
    }
    
    # Extract title from <title> tag
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    
    # Extract meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )
    if desc_match:
        metadata["description"] = desc_match.group(1).strip()
    
    # Extract og:image
    og_image_match = re.search(
        r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )
    if og_image_match:
        metadata["og_image"] = og_image_match.group(1).strip()
    
    return metadata


def generate_ai_preview(url: str, brand_settings: BrandSettings, html_content: Optional[str] = None) -> Dict[str, Optional[str]]:
    """
    Generate AI-enhanced preview data using OpenAI with semantic understanding and variants.
    
    Args:
        url: The URL to generate preview for
        brand_settings: User's brand settings for context
        html_content: Optional pre-fetched HTML content (if None, will fetch)
        
    Returns:
        Dictionary with title, description, keywords, tone, type, reasoning, image_url,
        variant_a, variant_b, variant_c, rewritten_text
    """
    # Step 1: Fetch HTML if not provided
    if html_content is None:
        html_content = fetch_page_html(url)
    
    # Step 2: Extract high-quality metadata using BeautifulSoup
    metadata = extract_metadata_from_html(html_content)
    
    # Step 2.5: Extract semantic structure
    semantic = extract_semantic_structure(html_content)
    
    # Step 2.6: Extract priority content based on UI/UX signals
    priority_content = extract_priority_content(html_content, url)
    
    # Step 3: Parse URL for domain and path
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path
    
    # Step 3: Derive brand tone from brand settings
    brand_tone = _derive_brand_tone(brand_settings)
    
    # Step 4: Prepare enhanced prompt for OpenAI with semantic understanding
    prompt = f"""You are a world-class preview generation assistant. Analyze the following URL and generate high-quality, accurate previews with multiple variants.

URL: {url}
Domain: {domain}
Path: {path}

PAGE TYPE & PRIORITY CONTENT (HIGHEST PRIORITY - USE THIS FIRST):
- Detected Page Type: {priority_content.get('page_type', 'unknown')}
- Primary Title (from UI/UX analysis): {priority_content.get('primary_title', 'Not found')}
- Primary Description (from UI/UX analysis): {priority_content.get('primary_description', 'Not found')}
- Key Attributes: {priority_content.get('key_attributes', {})}
- Content Priority Score: {priority_content.get('content_priority_score', 0.0)}
- Visual Elements: {', '.join(priority_content.get('visual_elements', [])[:3])}

SEMANTIC CONTENT ANALYSIS:
- Intent: {semantic.get('intent', 'unknown')}
- Sentiment: {semantic.get('sentiment', 'neutral')}
- Primary Content: {semantic.get('primary_content', '')[:500]}
- Topic Keywords: {', '.join(semantic.get('topic_keywords', [])[:10])}
- Named Entities: {', '.join(semantic.get('named_entities', [])[:5])}

EXTRACTED METADATA (fallback if priority content unavailable):
- Title (priority): {metadata.get('priority_title', 'Not found')}
  - OG Title: {metadata.get('og_title', 'Not found')}
  - HTML Title: {metadata.get('title', 'Not found')}
  - H1: {metadata.get('h1', 'Not found')}
- Description (priority): {metadata.get('priority_description', 'Not found')}
  - OG Description: {metadata.get('og_description', 'Not found')}
  - Meta Description: {metadata.get('description', 'Not found')}
  - Text Summary: {metadata.get('text_summary', 'Not found')[:200] if metadata.get('text_summary') else 'Not found'}
- OG Image: {metadata.get('og_image', 'Not found')}
- Canonical URL: {metadata.get('canonical_url', 'Not found')}

BRAND CONTEXT:
- Primary Color: {brand_settings.primary_color}
- Secondary Color: {brand_settings.secondary_color}
- Accent Color: {brand_settings.accent_color}
- Font Family: {brand_settings.font_family}
- Brand Tone: {brand_tone}

COMPETITOR-GRADE SEO GUIDELINES:
- Titles should be 50-60 characters, include primary keyword, be compelling
- Descriptions should be 150-160 characters, include call-to-action, be persuasive
- Keywords should be relevant, searchable, and match user intent
- Tone should match brand voice and content sentiment

YOUR TASK:
1. Generate MAIN preview (title, description) based on semantic analysis + metadata
2. Generate VARIANT A: More concise, action-oriented version
3. Generate VARIANT B: More descriptive, benefit-focused version
4. Generate VARIANT C: More emotional, story-driven version
5. Extract 5-7 relevant keywords from semantic analysis
6. Determine tone that matches brand voice and content sentiment
7. Predict type based on intent and content structure
8. Provide detailed reasoning for all choices

CRITICAL INSTRUCTIONS:
1. PRIORITY ORDER: Use Priority Content FIRST (from UI/UX analysis), then fall back to metadata
2. For PROFILE pages: Focus on the person/expert name, their competencies/skills, location, and what they offer
3. For PRODUCT pages: Focus on product name, key features, and price
4. For ARTICLE pages: Focus on article title and main topic
5. NEVER use generic site-wide descriptions - always extract the SPECIFIC content for this page
6. Base ALL output on the Priority Content when available (it represents what users actually see)
7. Each variant must be unique but accurate to the content
8. Variants should test different messaging angles (concise vs descriptive vs emotional)
9. Keep titles 50-60 chars, descriptions 150-160 chars
10. Keywords must be relevant and searchable
11. Tone must align with brand voice: {brand_tone}

Return your response as valid JSON with these exact keys:
{{
    "title": "string (main, 50-60 chars)",
    "description": "string (main, 150-160 chars)",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "tone": "professional | fun | bold | casual | technical | creative | neutral",
    "type": "product | blog | landing | unknown",
    "variant_a": {{
        "title": "string (concise, action-oriented, 50-60 chars)",
        "description": "string (150-160 chars)"
    }},
    "variant_b": {{
        "title": "string (descriptive, benefit-focused, 50-60 chars)",
        "description": "string (150-160 chars)"
    }},
    "variant_c": {{
        "title": "string (emotional, story-driven, 50-60 chars)",
        "description": "string (150-160 chars)"
    }},
    "reasoning": "detailed explanation of semantic analysis, variant strategies, and choices"
}}
"""
    
    # Step 4: Call OpenAI Chat Completions API
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o for best results
            messages=[
                {
                    "role": "system",
                    "content": "You are a preview generation assistant. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        # Parse JSON response
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'^```\s*', '', content)
            content = re.sub(r'```\s*$', '', content)
        
        ai_data = json.loads(content)
        
        # Step 5: Return AI result with variants (image_url will be handled by screenshot generation in pipeline)
        return {
            "title": ai_data.get("title") or metadata.get("priority_title") or "Untitled Page",
            "description": ai_data.get("description") or metadata.get("priority_description") or None,
            "keywords": ai_data.get("keywords", []),
            "tone": ai_data.get("tone", "neutral"),
            "type": ai_data.get("type", "unknown"),
            "reasoning": ai_data.get("reasoning", ""),
            "variant_a": ai_data.get("variant_a", {}),
            "variant_b": ai_data.get("variant_b", {}),
            "variant_c": ai_data.get("variant_c", {}),
            "image_url": metadata.get("og_image") or "",  # Fallback, will be replaced by screenshot
        }
        
    except json.JSONDecodeError as e:
        # Log error without exposing sensitive data
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error parsing AI response: {type(e).__name__}")
        # Fallback to extracted metadata
        fallback_title = metadata.get("priority_title") or "Untitled Page"
        fallback_desc = metadata.get("priority_description") or ""
        return {
            "title": fallback_title,
            "description": fallback_desc,
            "keywords": semantic.get("topic_keywords", [])[:5],
            "tone": "neutral",
            "type": semantic.get("intent", "unknown").replace(" page", "").replace(" article", ""),
            "reasoning": f"Fallback: Used semantic intent '{semantic.get('intent')}' and extracted metadata",
            "variant_a": {"title": fallback_title[:60], "description": fallback_desc[:160]},
            "variant_b": {"title": fallback_title[:60], "description": fallback_desc[:160]},
            "variant_c": {"title": fallback_title[:60], "description": fallback_desc[:160]},
            "image_url": metadata.get("og_image") or "",
        }
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fallback to extracted metadata
        fallback_title = metadata.get("priority_title") or "Untitled Page"
        fallback_desc = metadata.get("priority_description") or ""
        return {
            "title": fallback_title,
            "description": fallback_desc,
            "keywords": semantic.get("topic_keywords", [])[:5],
            "tone": "neutral",
            "type": semantic.get("intent", "unknown").replace(" page", "").replace(" article", ""),
            "reasoning": f"Error fallback: {str(e)}",
            "variant_a": {"title": fallback_title[:60], "description": fallback_desc[:160]},
            "variant_b": {"title": fallback_title[:60], "description": fallback_desc[:160]},
            "variant_c": {"title": fallback_title[:60], "description": fallback_desc[:160]},
            "image_url": metadata.get("og_image") or "",
        }


def _derive_brand_tone(brand_settings: BrandSettings) -> str:
    """
    Derive brand tone from brand settings (colors, font).
    
    Returns a tone description string.
    """
    # Analyze colors for tone hints
    primary = brand_settings.primary_color.lower()
    secondary = brand_settings.secondary_color.lower()
    accent = brand_settings.accent_color.lower()
    
    tone_hints = []
    
    # Color analysis
    if any(c in primary for c in ['ff', 'f00', 'e00']):  # Red tones
        tone_hints.append("bold")
    if any(c in primary for c in ['00f', '009', '006']):  # Blue tones
        tone_hints.append("professional")
    if any(c in primary for c in ['0f0', '0a0', '090']):  # Green tones
        tone_hints.append("natural")
    if any(c in accent for c in ['ff', 'f00']):  # Bright accents
        tone_hints.append("energetic")
    
    # Font analysis
    font_lower = brand_settings.font_family.lower()
    if 'serif' in font_lower or 'times' in font_lower:
        tone_hints.append("traditional")
    elif 'mono' in font_lower or 'code' in font_lower:
        tone_hints.append("technical")
    elif 'sans' in font_lower or 'inter' in font_lower or 'roboto' in font_lower:
        tone_hints.append("modern")
    
    # Default tone
    if not tone_hints:
        return "clean, modern, minimalistic"
    
    # Combine hints
    unique_hints = list(set(tone_hints))
    if len(unique_hints) == 1:
        return unique_hints[0]
    else:
        return ", ".join(unique_hints[:2])

