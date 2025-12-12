"""
Multi-Modal Fusion Engine with Quality Framework.

Intelligently fuses HTML metadata, semantic analysis, and AI vision
with quality gates ensuring consistent quality across all sources.
"""
from typing import Dict, Any, Optional, Tuple
import logging
from backend.services.metadata_extractor import extract_metadata_from_html
from backend.services.semantic_extractor import extract_semantic_structure
from backend.services.quality_framework import QualityFramework, QualityScore
from backend.services.design_extraction_framework import DesignExtractor, DesignElements

logger = logging.getLogger(__name__)


class MultiModalFusionEngine:
    """
    Framework-based multi-modal fusion with quality gates.
    
    Ensures:
    1. Quality gates for all sources
    2. Design preservation
    3. Consistent quality regardless of source
    4. Intelligent source selection based on quality scores
    """
    
    def __init__(self):
        self.quality_framework = QualityFramework()
        self.design_extractor = DesignExtractor()
        logger.info("Multi-Modal Fusion Engine initialized")
    
    def extract_preview_content(
        self,
        html_content: str,
        screenshot_bytes: bytes,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract preview content using framework-based multi-modal fusion.
        
        Framework ensures:
        1. Quality gates for all sources
        2. Design preservation
        3. Consistent quality regardless of source
        
        Args:
            html_content: HTML content
            screenshot_bytes: Screenshot bytes
            url: URL for context
            
        Returns:
            Dictionary with preview content and quality metrics
        """
        logger.info(f"Starting multi-modal fusion for: {url[:50]}...")
        
        # Step 1: Extract from all sources
        html_data = self._extract_from_html(html_content)
        semantic_data = self._extract_from_semantic(html_content)
        
        # Step 2: Validate quality for HTML and semantic sources
        html_scores = self.quality_framework.validate_content(
            html_data.get("title"),
            html_data.get("description"),
            "html"
        )
        
        semantic_scores = self.quality_framework.validate_content(
            semantic_data.get("title"),
            semantic_data.get("description"),
            "semantic"
        )
        
        # Step 3: Determine if vision is needed
        html_has_good_title = (
            html_scores.get("title") and
            html_scores["title"].passed_gates and
            html_scores["title"].confidence >= 0.7
        )
        html_has_good_description = (
            html_scores.get("description") and
            html_scores["description"].passed_gates and
            html_scores["description"].confidence >= 0.7
        )
        
        # Only use vision if HTML is insufficient
        vision_data = None
        vision_scores = {}
        
        if not (html_has_good_title and html_has_good_description):
            logger.info("HTML metadata insufficient, using vision extraction")
            vision_data = self._extract_from_vision(screenshot_bytes, url, html_content)
            
            if vision_data:
                vision_scores = self.quality_framework.validate_content(
                    vision_data.get("title"),
                    vision_data.get("description"),
                    "vision"
                )
        else:
            logger.info("HTML metadata sufficient, skipping vision extraction")
        
        # Step 4: Extract design elements
        design_elements = self.design_extractor.extract_design(
            html_content,
            screenshot_bytes,
            url
        )
        
        # Validate design quality
        design_dict = {
            "color_palette": design_elements.color_palette,
            "typography": design_elements.typography,
            "layout_structure": design_elements.layout_structure,
            "design_style": design_elements.design_style
        }
        design_score = self.quality_framework.validate_design(
            design_dict,
            "fusion"
        )
        
        # Step 5: Fuse with quality-based selection
        fused = self._fuse_with_quality_gates(
            html_data, html_scores,
            semantic_data, semantic_scores,
            vision_data, vision_scores,
            design_elements, design_score
        )
        
        logger.info(
            f"Fusion complete: "
            f"title_source={fused['sources'].get('title')}, "
            f"desc_source={fused['sources'].get('description')}, "
            f"confidence={fused['confidence']:.2f}"
        )
        
        return fused
    
    def _extract_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract from HTML metadata."""
        try:
            metadata = extract_metadata_from_html(html_content)
            
            return {
                "title": metadata.get("og_title") or metadata.get("title") or metadata.get("h1"),
                "description": metadata.get("og_description") or metadata.get("description"),
                "image": metadata.get("og_image"),
                "source": "html"
            }
        except Exception as e:
            logger.warning(f"HTML extraction failed: {e}")
            return {"source": "html"}
    
    def _extract_from_semantic(self, html_content: str) -> Dict[str, Any]:
        """Extract from semantic HTML analysis."""
        try:
            semantic = extract_semantic_structure(html_content)
            
            # Extract title from semantic structure
            title = None
            if semantic.get("primary_content"):
                # Try to extract title from primary content
                lines = semantic["primary_content"].split('\n')
                for line in lines[:3]:  # Check first 3 lines
                    if len(line.strip()) > 10 and len(line.strip()) < 100:
                        title = line.strip()
                        break
            
            # Extract description
            description = semantic.get("primary_content", "")[:300]
            
            return {
                "title": title,
                "description": description,
                "tags": semantic.get("topic_keywords", [])[:5],
                "source": "semantic"
            }
        except Exception as e:
            logger.warning(f"Semantic extraction failed: {e}")
            return {"source": "semantic"}
    
    def _extract_from_vision(
        self,
        screenshot_bytes: bytes,
        url: str,
        html_content: str
    ) -> Optional[Dict[str, Any]]:
        """Extract from AI vision analysis."""
        try:
            from openai import OpenAI
            from backend.core.config import settings
            import base64
            import json
            from io import BytesIO
            from PIL import Image
            
            # Prepare image
            image = Image.open(BytesIO(screenshot_bytes))
            max_dim = 2048
            if image.width > max_dim or image.height > max_dim:
                ratio = min(max_dim / image.width, max_dim / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            if image.mode in ('RGBA', 'P', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                image = background
            
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=90)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Improved vision prompt focused on visible content
            prompt = """Analyze this webpage screenshot and extract the most important VISIBLE content.

MISSION: Extract what users actually SEE on the page, focusing on visual hierarchy.

=== WHAT TO EXTRACT ===

1. **VISIBLE TITLE** (the largest, most prominent text)
   - Usually at the top or center
   - Largest font size
   - Most visually prominent
   - Extract EXACT text as shown

2. **VISIBLE DESCRIPTION** (secondary prominent text)
   - Usually below or near the title
   - Describes what the page is about
   - Extract EXACT text as shown

3. **VISIBLE IMAGE** (most relevant image)
   - Logo (top-left or center)
   - Hero image (large, prominent)
   - Product image (if product page)
   - Profile photo (if profile page)

=== EXTRACTION PRINCIPLES ===
- Extract EXACT text as it appears (preserve capitalization, punctuation)
- Focus on VISUAL PROMINENCE (largest, boldest, most central)
- Ignore navigation menus, footers, cookie notices
- Don't paraphrase or "improve" - extract exactly what's shown

=== OUTPUT ===
{
    "visible_title": "<largest, most prominent text>",
    "visible_description": "<secondary text that describes the page>",
    "primary_image": {
        "description": "<what the image shows>",
        "bbox": {"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}
    },
    "page_type": "<profile|product|article|company|unknown>",
    "confidence": 0.0-1.0
}
"""
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing webpage screenshots. Extract visible content accurately. Output valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Low temperature for accuracy
            )
            
            content = response.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            return {
                "title": result.get("visible_title"),
                "description": result.get("visible_description"),
                "image": result.get("primary_image"),
                "page_type": result.get("page_type"),
                "confidence": result.get("confidence", 0.0),
                "source": "vision"
            }
        except Exception as e:
            logger.warning(f"Vision extraction failed: {e}")
            return None
    
    def _fuse_with_quality_gates(
        self,
        html_data: Dict[str, Any],
        html_scores: Dict[str, QualityScore],
        semantic_data: Dict[str, Any],
        semantic_scores: Dict[str, QualityScore],
        vision_data: Optional[Dict[str, Any]],
        vision_scores: Dict[str, QualityScore],
        design_elements: DesignElements,
        design_score: QualityScore
    ) -> Dict[str, Any]:
        """
        Fuse results using quality gates to ensure consistent quality.
        
        Strategy:
        1. Filter candidates that pass quality gates
        2. Choose best quality score
        3. Fallback gracefully if no candidates pass
        """
        sources_used = {}
        
        # Title fusion with quality gates
        title_candidates = [
            (html_data.get("title"), html_scores.get("title"), "html"),
            (semantic_data.get("title"), semantic_scores.get("title"), "semantic"),
        ]
        
        if vision_data:
            title_candidates.append(
                (vision_data.get("title"), vision_scores.get("title"), "vision")
            )
        
        # Filter candidates that pass quality gates
        valid_titles = [
            (title, score, src) for title, score, src in title_candidates
            if title and score and score.passed_gates
        ]
        
        if valid_titles:
            # Choose best quality score
            best_title = max(valid_titles, key=lambda x: x[1].confidence)
            title = best_title[0]
            sources_used["title"] = best_title[2]
            title_confidence = best_title[1].confidence
        else:
            # Fallback: use best available even if doesn't pass gates
            fallback_titles = [
                (title, score, src) for title, score, src in title_candidates
                if title and score
            ]
            if fallback_titles:
                best_title = max(fallback_titles, key=lambda x: x[1].confidence)
                title = best_title[0]
                sources_used["title"] = best_title[2]
                title_confidence = best_title[1].confidence
            else:
                # Last resort fallback
                from urllib.parse import urlparse
                parsed = urlparse(url)
                title = parsed.netloc.replace('www.', '').replace('.', ' ').title()
                sources_used["title"] = "fallback"
                title_confidence = 0.3
        
        # Description fusion with quality gates (same logic)
        desc_candidates = [
            (html_data.get("description"), html_scores.get("description"), "html"),
            (semantic_data.get("description"), semantic_scores.get("description"), "semantic"),
        ]
        
        if vision_data:
            desc_candidates.append(
                (vision_data.get("description"), vision_scores.get("description"), "vision")
            )
        
        valid_descs = [
            (desc, score, src) for desc, score, src in desc_candidates
            if desc and score and score.passed_gates
        ]
        
        if valid_descs:
            best_desc = max(valid_descs, key=lambda x: x[1].confidence)
            description = best_desc[0]
            sources_used["description"] = best_desc[2]
            desc_confidence = best_desc[1].confidence
        else:
            fallback_descs = [
                (desc, score, src) for desc, score, src in desc_candidates
                if desc and score
            ]
            if fallback_descs:
                best_desc = max(fallback_descs, key=lambda x: x[1].confidence)
                description = best_desc[0]
                sources_used["description"] = best_desc[2]
                desc_confidence = best_desc[1].confidence
            else:
                description = f"Learn more about {title}"
                sources_used["description"] = "fallback"
                desc_confidence = 0.3
        
        # Image fusion
        image_candidates = [
            (html_data.get("image"), html_scores.get("title", QualityScore(0.0, 0.0, "html", [], False, None)).confidence, "html"),
        ]
        
        if vision_data and vision_data.get("image"):
            image_candidates.append(
                (vision_data.get("image"), vision_scores.get("title", QualityScore(0.0, 0.0, "vision", [], False, None)).confidence, "vision")
            )
        
        valid_images = [
            (img, conf, src) for img, conf, src in image_candidates
            if img
        ]
        
        if valid_images:
            best_image = max(valid_images, key=lambda x: x[1])
            image = best_image[0]
            sources_used["image"] = best_image[2]
        else:
            image = None
            sources_used["image"] = "none"
        
        # Calculate overall confidence
        overall_confidence = (title_confidence + desc_confidence) / 2
        
        # Design quality
        design_passed = design_score.passed_gates
        
        return {
            "title": title,
            "description": description[:300],  # Limit length
            "tags": semantic_data.get("tags", []),
            "image": image,
            "confidence": overall_confidence,
            "sources": sources_used,
            "design": {
                "color_palette": design_elements.color_palette,
                "typography": design_elements.typography,
                "layout_structure": design_elements.layout_structure,
                "design_style": design_elements.design_style,
                "quality_passed": design_passed,
                "quality_score": design_score.confidence
            },
            "quality_scores": {
                "title": title_confidence,
                "description": desc_confidence,
                "design": design_score.confidence,
                "overall": overall_confidence
            }
        }
