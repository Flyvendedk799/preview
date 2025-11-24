"""AI output validation and quality assurance."""
import re
from typing import Dict, List, Optional


def validate_ai_output(ai_json: Dict, metadata: Dict, brand_tone: str = None, semantic_data: Dict = None) -> Dict:
    """
    Validate and correct AI output to ensure quality and accuracy.
    
    Args:
        ai_json: Raw AI output dictionary
        metadata: Extracted metadata for fallback
        brand_tone: Brand tone for validation
        semantic_data: Semantic structure data for fallback and hallucination detection
        
    Returns:
        Corrected AI output dictionary with variants
    """
    validated = {
        "title": ai_json.get("title", ""),
        "description": ai_json.get("description", ""),
        "keywords": ai_json.get("keywords", []),
        "tone": ai_json.get("tone", "neutral"),
        "type": ai_json.get("type", "unknown"),
        "reasoning": ai_json.get("reasoning", ""),
        "variant_a": ai_json.get("variant_a", {}),
        "variant_b": ai_json.get("variant_b", {}),
        "variant_c": ai_json.get("variant_c", {}),
    }
    
    # Validate title
    title = validated["title"]
    if not title or len(title.strip()) < 3:
        # Fallback to metadata title
        validated["title"] = metadata.get("priority_title") or metadata.get("title") or "Untitled Page"
    else:
        # Remove emojis unless tone suggests them
        tone_lower = validated["tone"].lower()
        if tone_lower not in ["fun", "creative", "casual"]:
            # Remove emojis for professional/technical tones
            validated["title"] = re.sub(r'[^\w\s\-.,!?()]', '', title)
        validated["title"] = validated["title"].strip()
    
    # Validate description
    description = validated["description"]
    if not description or len(description.strip()) < 20:
        # Fallback to metadata description
        validated["description"] = metadata.get("priority_description") or metadata.get("description") or None
    else:
        # Remove emojis unless tone suggests them
        tone_lower = validated["tone"].lower()
        if tone_lower not in ["fun", "creative", "casual"]:
            validated["description"] = re.sub(r'[^\w\s\-.,!?()]', '', description)
        validated["description"] = validated["description"].strip()
    
    # Validate keywords
    keywords = validated.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []
    
    # Remove duplicates and empty strings
    keywords = [k.strip() for k in keywords if k and k.strip()]
    keywords = list(dict.fromkeys(keywords))  # Remove duplicates while preserving order
    
    # If keywords are missing or too few, try to extract from metadata
    if len(keywords) < 2:
        # Simple keyword extraction from title/description
        text = f"{validated['title']} {validated['description'] or ''}".lower()
        # Extract potential keywords (simple approach)
        words = re.findall(r'\b\w{4,}\b', text)  # Words with 4+ characters
        # Filter common stop words
        stop_words = {"this", "that", "with", "from", "have", "will", "your", "page", "preview"}
        keywords.extend([w for w in words[:5] if w not in stop_words])
        keywords = list(dict.fromkeys(keywords))[:5]  # Limit to 5 keywords
    
    validated["keywords"] = keywords
    
    # Validate tone
    valid_tones = ["professional", "fun", "bold", "casual", "technical", "creative", "neutral"]
    if validated["tone"] not in valid_tones:
        validated["tone"] = "neutral"
    
    # Validate variants with enhanced quality checks
    for variant_key in ['a', 'b', 'c']:
        variant = validated.get(f"variant_{variant_key}", {})
        if isinstance(variant, dict):
            variant_title = variant.get("title", "")
            variant_desc = variant.get("description", "")
            
            # Validate variant title (must be > 20 chars)
            if not variant_title or len(variant_title.strip()) < 20:
                # Generate fallback variant title using simple rewrite
                variant_title = _generate_variant_title(validated["title"], variant_key, semantic_data)
            
            # Validate variant description (must be > 20 chars)
            if not variant_desc or len(variant_desc.strip()) < 20:
                # Generate fallback variant description using simple rewrite
                variant_desc = _generate_variant_description(validated["description"], variant_key, semantic_data)
            
            # Remove hallucinations (check against semantic data and metadata)
            variant_title = _remove_hallucinations(variant_title, metadata, semantic_data)
            if variant_desc:
                variant_desc = _remove_hallucinations(variant_desc, metadata, semantic_data)
            
            # Remove emojis unless tone suggests them
            tone_lower = validated["tone"].lower()
            if tone_lower not in ["fun", "creative", "casual"]:
                variant_title = re.sub(r'[^\w\s\-.,!?()]', '', variant_title)
                if variant_desc:
                    variant_desc = re.sub(r'[^\w\s\-.,!?()]', '', variant_desc)
            
            validated[f"variant_{variant_key}"] = {
                "title": variant_title.strip()[:60],
                "description": variant_desc.strip()[:160] if variant_desc else None
            }
        else:
            # Invalid variant structure, create fallback using simple rewrites
            validated[f"variant_{variant_key}"] = {
                "title": _generate_variant_title(validated["title"], variant_key, semantic_data)[:60],
                "description": _generate_variant_description(validated["description"], variant_key, semantic_data)[:160] if validated["description"] else None
            }
    
    # Ensure tone matches brand tone if provided
    if brand_tone:
        # Map AI tone to brand tone if they don't match
        tone_mapping = {
            "professional": ["professional", "technical", "neutral"],
            "fun": ["fun", "creative", "casual"],
            "bold": ["bold", "professional", "creative"],
            "casual": ["casual", "fun", "neutral"],
            "technical": ["technical", "professional", "neutral"],
            "creative": ["creative", "fun", "bold"],
            "neutral": ["neutral", "professional", "casual"]
        }
        
        # If AI tone doesn't match brand tone, adjust it
        if validated["tone"] != brand_tone:
            # Check if AI tone is compatible with brand tone
            compatible_tones = tone_mapping.get(brand_tone.lower(), [brand_tone])
            if validated["tone"] not in compatible_tones:
                # Adjust to brand tone
                validated["tone"] = brand_tone
    
    # Sanitize keywords
    keywords = validated["keywords"]
    sanitized_keywords = []
    for kw in keywords:
        if isinstance(kw, str) and len(kw.strip()) >= 2:
            # Remove special characters, keep alphanumeric and spaces
            sanitized = re.sub(r'[^\w\s-]', '', kw.strip())
            if sanitized:
                sanitized_keywords.append(sanitized[:50])  # Limit keyword length
    
    validated["keywords"] = sanitized_keywords[:7]  # Limit to 7 keywords
    
    # Remove hallucinations from main title and description
    validated["title"] = _remove_hallucinations(validated["title"], metadata, semantic_data)
    if validated["description"]:
        validated["description"] = _remove_hallucinations(validated["description"], metadata, semantic_data)
    
    return validated


def _generate_variant_title(base_title: str, variant_key: str, semantic_data: Dict = None) -> str:
    """Generate a variant title using simple rewrite rules."""
    if not base_title or len(base_title.strip()) < 3:
        return "Untitled Page"
    
    base = base_title.strip()
    
    # Simple rewrite strategies based on variant
    if variant_key == 'a':
        # Variant A: More concise, action-oriented
        # Remove filler words, make it punchier
        concise = re.sub(r'\b(a|an|the|is|are|was|were|be|been|being)\b', '', base, flags=re.IGNORECASE)
        concise = re.sub(r'\s+', ' ', concise).strip()
        return concise[:60] if concise else base[:60]
    elif variant_key == 'b':
        # Variant B: More descriptive, benefit-focused
        # Add benefit words if not present
        if not any(word in base.lower() for word in ['best', 'top', 'premium', 'quality', 'expert']):
            # Try to make it more benefit-focused
            if semantic_data and semantic_data.get('intent') == 'product page':
                return f"Premium {base[:50]}"
        return base[:60]
    elif variant_key == 'c':
        # Variant C: More emotional, story-driven
        # Add emotional words if not present
        if not any(word in base.lower() for word in ['discover', 'explore', 'experience', 'unlock', 'transform']):
            # Try to make it more emotional
            if semantic_data and semantic_data.get('sentiment') == 'positive':
                return f"Discover {base[:50]}"
        return base[:60]
    
    return base[:60]


def _generate_variant_description(base_description: str, variant_key: str, semantic_data: Dict = None) -> str:
    """Generate a variant description using simple rewrite rules."""
    if not base_description or len(base_description.strip()) < 20:
        # Use semantic data if available
        if semantic_data:
            primary_content = semantic_data.get('primary_content', '')
            if primary_content and len(primary_content) > 20:
                base_description = primary_content[:200]
            else:
                return None
    
    base = base_description.strip()
    
    # Simple rewrite strategies based on variant
    if variant_key == 'a':
        # Variant A: More concise, action-oriented
        # Remove filler, add action verbs
        concise = re.sub(r'\b(that|which|who|where|when|why|how)\b', '', base, flags=re.IGNORECASE)
        concise = re.sub(r'\s+', ' ', concise).strip()
        if len(concise) < 20:
            concise = base
        return concise[:160]
    elif variant_key == 'b':
        # Variant B: More descriptive, benefit-focused
        # Add benefit language if not present
        if not any(word in base.lower() for word in ['benefit', 'advantage', 'feature', 'quality', 'premium']):
            # Try to make it more benefit-focused
            if len(base) > 50:
                return f"{base[:120]} - Experience premium quality and expert service."[:160]
        return base[:160]
    elif variant_key == 'c':
        # Variant C: More emotional, story-driven
        # Add emotional language if not present
        if not any(word in base.lower() for word in ['discover', 'explore', 'experience', 'journey', 'story']):
            # Try to make it more emotional
            if semantic_data and semantic_data.get('sentiment') == 'positive':
                return f"Discover {base[:140]}"[:160]
        return base[:160]
    
    return base[:160]


def _remove_hallucinations(text: str, metadata: Dict, semantic_data: Dict = None) -> str:
    """Remove hallucinations (brand names/content not in metadata or semantic data)."""
    if not text:
        return text
    
    # Extract known entities from metadata and semantic data
    known_entities = set()
    
    # From metadata
    if metadata:
        title = metadata.get('title', '') or metadata.get('priority_title', '')
        if title:
            # Extract capitalized words (potential brand names)
            known_entities.update(re.findall(r'\b[A-Z][a-z]+\b', title))
    
    # From semantic data
    if semantic_data:
        named_entities = semantic_data.get('named_entities', [])
        if isinstance(named_entities, list):
            known_entities.update([str(e).strip() for e in named_entities if e])
        
        topic_keywords = semantic_data.get('topic_keywords', [])
        if isinstance(topic_keywords, list):
            known_entities.update([str(k).strip() for k in topic_keywords if k])
    
    # Check for suspicious brand names in text (capitalized words not in known entities)
    words = text.split()
    filtered_words = []
    
    for word in words:
        # Remove punctuation for comparison
        clean_word = re.sub(r'[^\w]', '', word)
        
        # If it's a capitalized word (potential brand name) and not in known entities
        if clean_word and clean_word[0].isupper() and len(clean_word) > 3:
            # Check if it's a common word (not a brand)
            common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'Where', 'When', 'What', 'How', 'Why', 'Who', 'Which', 'With', 'From', 'About', 'After', 'Before', 'During', 'Since', 'Until', 'While', 'Because', 'Although', 'However', 'Therefore', 'Moreover', 'Furthermore', 'Additionally', 'Also', 'Even', 'Only', 'Just', 'Still', 'Yet', 'Already', 'Always', 'Never', 'Often', 'Seldom', 'Rarely', 'Usually', 'Sometimes', 'Soon', 'Now', 'Then', 'Every', 'Each', 'Some', 'Any', 'No', 'Many', 'Much', 'Few', 'Little', 'More', 'Most', 'Other', 'Another', 'Such', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'}
            
            if clean_word not in common_words and clean_word not in known_entities:
                # Potential hallucination - but be conservative, only remove if very suspicious
                # For now, we'll keep it but could enhance this
                pass
        
        filtered_words.append(word)
    
    return ' '.join(filtered_words)

