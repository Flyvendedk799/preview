"""
Agent Executor - Real AI Agent Execution with GPT-4o

This module implements actual agent execution by calling OpenAI's GPT-4o API
with specialized prompts for each agent type.

Agents:
- Visual Analyst: Screenshot analysis, layout detection, UI components
- Content Curator: HTML parsing, content extraction, metadata
- Design Archaeologist: Design DNA extraction, brand identity
- Quality Critic: Preview quality assessment, improvement suggestions
- Context Fusion: Combines outputs from multiple agents
"""

import json
import base64
import logging
import time
import os
from typing import Dict, Any, Optional, List, Tuple
from io import BytesIO
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from openai import OpenAI
from PIL import Image

from backend.core.config import settings
from backend.services.agent_protocol import (
    AgentType, AgentMessage, AgentResponse
)

logger = logging.getLogger(__name__)

# Agent prompt directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "agents"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_type: AgentType
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4000
    requires_vision: bool = False
    system_prompt_file: Optional[str] = None


# Agent configurations
AGENT_CONFIGS: Dict[AgentType, AgentConfig] = {
    AgentType.VISUAL_ANALYST: AgentConfig(
        agent_type=AgentType.VISUAL_ANALYST,
        model="gpt-4o",
        temperature=0.1,
        max_tokens=4000,
        requires_vision=True,
        system_prompt_file="visual_analyst_system.txt"
    ),
    AgentType.CONTENT_CURATOR: AgentConfig(
        agent_type=AgentType.CONTENT_CURATOR,
        model="gpt-4o",
        temperature=0.2,
        max_tokens=3000,
        requires_vision=False,
        system_prompt_file="content_curator_system.txt"
    ),
    AgentType.DESIGN_ARCHAEOLOGIST: AgentConfig(
        agent_type=AgentType.DESIGN_ARCHAEOLOGIST,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=4000,
        requires_vision=True,
        system_prompt_file="design_archaeologist_system.txt"
    ),
    AgentType.QUALITY_CRITIC: AgentConfig(
        agent_type=AgentType.QUALITY_CRITIC,
        model="gpt-4o",
        temperature=0.2,
        max_tokens=2000,
        requires_vision=True,
        system_prompt_file="quality_critic_system.txt"
    ),
    AgentType.CONTEXT_FUSION: AgentConfig(
        agent_type=AgentType.CONTEXT_FUSION,
        model="gpt-4o-mini",  # Faster model for fusion
        temperature=0.1,
        max_tokens=3000,
        requires_vision=False,
        system_prompt_file=None  # Uses inline prompt
    ),
    AgentType.REASONING_CHAIN: AgentConfig(
        agent_type=AgentType.REASONING_CHAIN,
        model="gpt-4o",
        temperature=0.2,
        max_tokens=4000,
        requires_vision=True,
        system_prompt_file=None
    ),
}


class AgentExecutor:
    """
    Executes AI agents with real GPT-4o API calls.
    
    This is the core execution engine that:
    1. Loads agent-specific system prompts
    2. Prepares input data (including images for vision agents)
    3. Calls OpenAI API with appropriate parameters
    4. Parses and validates agent responses
    5. Returns structured AgentResponse objects
    """
    
    def __init__(self):
        """Initialize the agent executor."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)
        self.prompts_cache: Dict[str, str] = {}
        logger.info("🤖 AgentExecutor initialized with GPT-4o")
    
    def execute(self, message: AgentMessage) -> AgentResponse:
        """
        Execute an agent with the given message.
        
        Args:
            message: Agent message with input data and context
            
        Returns:
            AgentResponse with agent output
        """
        start_time = time.time()
        agent_type = message.agent_type
        
        logger.info(f"🚀 Executing agent: {agent_type.value}")
        
        try:
            # Get agent configuration
            config = AGENT_CONFIGS.get(agent_type)
            if not config:
                raise ValueError(f"No configuration for agent type: {agent_type}")
            
            # Load system prompt
            system_prompt = self._load_system_prompt(config)
            
            # Build user message
            user_message = self._build_user_message(message, config)
            
            # Call OpenAI API
            response_data, cost = self._call_openai(
                config, system_prompt, user_message, message.input_data
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Build response
            response = AgentResponse(
                message_id=message.message_id,
                agent_type=agent_type,
                success=True,
                output_data=response_data,
                confidence=response_data.get("confidence", 0.8),
                cost=cost,
                latency_ms=latency_ms,
                reasoning=response_data.get("reasoning", "Agent execution completed")
            )
            
            logger.info(
                f"✅ Agent {agent_type.value} completed: "
                f"confidence={response.confidence:.2f}, "
                f"latency={latency_ms:.0f}ms"
            )
            
            return response
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Agent {agent_type.value} failed: {e}", exc_info=True)
            
            return AgentResponse(
                message_id=message.message_id,
                agent_type=agent_type,
                success=False,
                output_data={},
                confidence=0.0,
                cost=0.0,
                latency_ms=latency_ms,
                errors=[str(e)],
                reasoning=f"Agent execution failed: {e}"
            )
    
    def _load_system_prompt(self, config: AgentConfig) -> str:
        """Load system prompt for an agent."""
        if config.system_prompt_file is None:
            return self._get_inline_prompt(config.agent_type)
        
        # Check cache
        if config.system_prompt_file in self.prompts_cache:
            return self.prompts_cache[config.system_prompt_file]
        
        # Load from file
        prompt_path = PROMPTS_DIR / config.system_prompt_file
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8")
            self.prompts_cache[config.system_prompt_file] = prompt
            return prompt
        else:
            logger.warning(f"Prompt file not found: {prompt_path}, using inline prompt")
            return self._get_inline_prompt(config.agent_type)
    
    def _get_inline_prompt(self, agent_type: AgentType) -> str:
        """Get inline system prompt for agents without files."""
        prompts = {
            AgentType.CONTEXT_FUSION: """You are a Context Fusion Agent that combines outputs from multiple specialized agents.

Your task:
1. Analyze outputs from Visual Analyst, Content Curator, and Design Archaeologist
2. Resolve any conflicts between agents using confidence scores
3. Create a unified, coherent output that combines the best from each agent
4. Identify gaps or inconsistencies that need resolution

Output format: JSON with fused data, confidence scores, and any unresolved conflicts.""",

            AgentType.REASONING_CHAIN: """You are a Reasoning Chain Agent that performs step-by-step analysis.

Your task:
1. Break down the preview generation into logical steps
2. Apply chain-of-thought reasoning to each step
3. Validate each conclusion before proceeding
4. Produce a well-reasoned final output

Output format: JSON with reasoning steps and final conclusions."""
        }
        return prompts.get(agent_type, "You are a helpful AI assistant. Output valid JSON.")
    
    def _build_user_message(
        self,
        message: AgentMessage,
        config: AgentConfig
    ) -> List[Dict[str, Any]]:
        """Build user message content for OpenAI API."""
        content = []
        input_data = message.input_data
        context = message.context
        
        # Build text prompt based on agent type
        text_prompt = self._build_agent_prompt(message.agent_type, input_data, context)
        content.append({"type": "text", "text": text_prompt})
        
        # Add image if vision is required
        if config.requires_vision and "screenshot_bytes" in input_data:
            screenshot_bytes = input_data["screenshot_bytes"]
            image_base64 = self._prepare_image(screenshot_bytes)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}",
                    "detail": "high"
                }
            })
        
        return content
    
    def _build_agent_prompt(
        self,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Build agent-specific user prompt."""
        url = input_data.get("url", context.get("url", "unknown"))
        
        if agent_type == AgentType.VISUAL_ANALYST:
            return self._build_visual_analyst_prompt(url, input_data)
        elif agent_type == AgentType.CONTENT_CURATOR:
            return self._build_content_curator_prompt(url, input_data)
        elif agent_type == AgentType.DESIGN_ARCHAEOLOGIST:
            return self._build_design_archaeologist_prompt(url, input_data)
        elif agent_type == AgentType.QUALITY_CRITIC:
            return self._build_quality_critic_prompt(input_data)
        elif agent_type == AgentType.CONTEXT_FUSION:
            return self._build_context_fusion_prompt(input_data)
        else:
            return f"Analyze this content from {url} and return JSON output."
    
    def _build_visual_analyst_prompt(self, url: str, input_data: Dict[str, Any]) -> str:
        """Build Visual Analyst prompt."""
        return f"""Analyze this webpage screenshot with pixel-perfect precision.

URL: {url}

=== EXTRACTION REQUIREMENTS ===

1. **LAYOUT GRID ANALYSIS**
   - Grid type: 12-column, asymmetric, full-width, centered?
   - Column structure: How many columns? Equal or varied widths?
   - Content width: Full-bleed or contained?

2. **VISUAL HIERARCHY MAPPING**
   - Primary element: What's the FIRST thing that catches the eye?
   - Secondary elements: What supports the primary?
   - Tertiary elements: Background/supporting content
   - Visual flow: How does the eye move across the page?

3. **UI COMPONENT DETECTION**
   For each UI component found, extract:
   - Type: button, card, badge, input, navigation, hero, etc.
   - Bounding box: {{"x": 0-1, "y": 0-1, "width": 0-1, "height": 0-1}}
   - Style properties: border-radius, shadow, background
   - Content: text or image description

4. **WHITESPACE RHYTHM**
   - Density: tight, balanced, generous, ultra-minimal?
   - Consistency: consistent or varied spacing?
   - Breathing room: where is negative space used?

5. **IMAGE TREATMENT**
   - Corner radius: sharp, rounded (px estimate), circular?
   - Shadows: none, subtle, prominent, colored?
   - Overlays: none, gradient, solid color, blur?
   - Borders: none, thin, prominent?

=== OUTPUT FORMAT ===
{{
    "layout": {{
        "grid_type": "12-column|asymmetric|full-width|centered",
        "columns": 12,
        "content_width": "contained|full-bleed",
        "max_width_px": 1200
    }},
    "visual_hierarchy": {{
        "primary": {{"type": "headline|image|logo", "content": "...", "bbox": {{...}}}},
        "secondary": [{{"type": "...", "content": "...", "bbox": {{...}}}}],
        "tertiary": [{{"type": "...", "content": "...", "bbox": {{...}}}}]
    }},
    "ui_components": [
        {{
            "type": "button|card|badge|hero|navigation|profile_image",
            "bbox": {{"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}},
            "style": {{
                "border_radius": "none|4px|8px|16px|full",
                "shadow": "none|sm|md|lg|colored",
                "background": "#hex or gradient description"
            }},
            "content": "button text or image description"
        }}
    ],
    "whitespace": {{
        "density": "tight|balanced|generous|minimal",
        "consistency": "consistent|varied",
        "section_spacing": "16px|24px|32px|48px|64px"
    }},
    "image_treatment": {{
        "corner_radius": "none|sm|md|lg|full",
        "shadow_style": "none|subtle|prominent|colored",
        "overlay_type": "none|gradient|solid|blur",
        "border_style": "none|thin|prominent"
    }},
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of analysis"
}}

Be PRECISE with bounding boxes. They should accurately represent element positions."""

    def _build_content_curator_prompt(self, url: str, input_data: Dict[str, Any]) -> str:
        """Build Content Curator prompt."""
        html_content = input_data.get("html_content", "")
        # Truncate HTML to avoid token limits
        html_excerpt = html_content[:15000] if html_content else "No HTML available"
        
        return f"""Extract and prioritize content from this webpage.

URL: {url}

=== HTML CONTENT (excerpt) ===
{html_excerpt}

=== EXTRACTION REQUIREMENTS ===

1. **PRIMARY CONTENT**
   - Title: The main headline/title (exact text)
   - Description: Primary description or tagline
   - Value proposition: Core message or offering

2. **SOCIAL PROOF**
   - Ratings: Star ratings with counts (e.g., "4.9★ (2,847 reviews)")
   - User counts: Customer/user numbers
   - Testimonials: Quote excerpts
   - Trust badges: Awards, certifications, "As seen in"

3. **METADATA**
   - OG title, description, image
   - Meta description
   - Canonical URL
   - Page type indicators

4. **STRUCTURED DATA**
   - Product info: price, availability, brand
   - Person info: name, title, bio
   - Organization info: name, industry
   - Article info: author, date, category

5. **QUALITY ASSESSMENT**
   - Content completeness: Is critical info present?
   - Specificity: Concrete claims vs generic
   - Clarity: Clear messaging or confusing?

=== OUTPUT FORMAT ===
{{
    "primary_content": {{
        "title": "exact title text",
        "description": "main description",
        "value_proposition": "core value/offering",
        "page_type": "product|profile|article|landing|company"
    }},
    "social_proof": {{
        "rating": {{"value": 4.9, "count": 2847, "display": "4.9★ (2,847 reviews)"}},
        "user_count": "50,000+ users",
        "testimonials": ["quote 1", "quote 2"],
        "trust_badges": ["badge 1", "badge 2"]
    }},
    "metadata": {{
        "og_title": "...",
        "og_description": "...",
        "og_image": "url",
        "meta_description": "...",
        "canonical": "url"
    }},
    "structured_data": {{
        "type": "Product|Person|Organization|Article",
        "data": {{}}
    }},
    "quality_assessment": {{
        "completeness_score": 0.0-1.0,
        "specificity_score": 0.0-1.0,
        "clarity_score": 0.0-1.0,
        "issues": ["list of content issues"]
    }},
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of extraction"
}}

Extract EXACT text - do not paraphrase or improve. Prioritize specific claims over generic."""

    def _build_design_archaeologist_prompt(self, url: str, input_data: Dict[str, Any]) -> str:
        """Build Design Archaeologist prompt."""
        return f"""Uncover the DESIGN DNA of this webpage - understand WHY design choices were made.

URL: {url}

=== DESIGN DNA EXTRACTION ===

1. **DESIGN PHILOSOPHY**
   - Style: minimalist, maximalist, brutalist, corporate, playful, luxurious, technical, editorial?
   - Era influence: modern, retro, futuristic, timeless?
   - Inspiration: What design movement or aesthetic does this evoke?

2. **COLOR PSYCHOLOGY**
   - Primary color: hex code and emotional association
   - Secondary color: hex code and purpose
   - Accent color: hex code and usage (CTAs, highlights)
   - Overall mood: What emotions do these colors evoke?
   - Color relationships: complementary, analogous, triadic?

3. **TYPOGRAPHY PERSONALITY**
   - Heading style: bold, elegant, technical, friendly, authoritative?
   - Body style: readable, stylized, minimal?
   - Font characteristics: serif/sans-serif, weight, spacing
   - Type scale: tight, balanced, generous?

4. **BRAND VOICE**
   - If this design could speak, what would it say?
   - Personality adjectives: 3-5 words describing the brand
   - Target audience: Who is this designed for?
   - Emotional response: What should visitors feel?

5. **VISUAL EFFECTS**
   - Shadows: flat, subtle, neumorphic, dramatic?
   - Gradients: none, subtle, bold, mesh?
   - Blur effects: glassmorphism, frosted, none?
   - Animations implied: static, subtle motion, dynamic?

6. **SPACING & RHYTHM**
   - Density: compact, balanced, spacious, ultra-minimal?
   - Section rhythm: consistent, varied, progressive?
   - Element grouping: tight clusters or isolated elements?

=== OUTPUT FORMAT ===
{{
    "design_philosophy": {{
        "style": "minimalist|maximalist|brutalist|corporate|playful|luxurious|technical|editorial",
        "era_influence": "modern|retro|futuristic|timeless",
        "aesthetic_inspiration": "description of design influences"
    }},
    "color_psychology": {{
        "primary": {{"hex": "#XXXXXX", "emotion": "trust|energy|calm|sophistication"}},
        "secondary": {{"hex": "#XXXXXX", "purpose": "background|accent|text"}},
        "accent": {{"hex": "#XXXXXX", "usage": "CTAs|highlights|badges"}},
        "overall_mood": "energetic|calm|professional|playful|luxurious",
        "relationship": "complementary|analogous|triadic|monochromatic"
    }},
    "typography_personality": {{
        "heading_style": "bold|elegant|technical|friendly|authoritative",
        "body_style": "readable|stylized|minimal",
        "font_type": "serif|sans-serif|display|mono",
        "weight_preference": "light|regular|medium|bold|black",
        "type_scale": "tight|balanced|generous"
    }},
    "brand_voice": {{
        "personality": "If this design could speak: ...",
        "adjectives": ["word1", "word2", "word3", "word4", "word5"],
        "target_audience": "description of target audience",
        "emotional_response": "what visitors should feel"
    }},
    "visual_effects": {{
        "shadow_style": "flat|subtle|neumorphic|dramatic",
        "gradient_usage": "none|subtle|bold|mesh",
        "blur_effects": "none|glassmorphism|frosted",
        "motion_implied": "static|subtle|dynamic"
    }},
    "spacing_rhythm": {{
        "density": "compact|balanced|spacious|ultra-minimal",
        "section_rhythm": "consistent|varied|progressive",
        "grouping": "clustered|isolated|mixed"
    }},
    "design_dna_summary": {{
        "one_line": "One sentence capturing the design's soul",
        "key_traits": ["trait1", "trait2", "trait3"],
        "should_preserve": ["critical element 1", "critical element 2"]
    }},
    "confidence": 0.0-1.0,
    "reasoning": "Why these design choices work for this brand"
}}

Think like the designer who created this. Understand the INTENT behind every choice."""

    def _build_quality_critic_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build Quality Critic prompt."""
        preview_data = input_data.get("preview_data", {})
        
        return f"""Critically evaluate this preview. Be BRUTALLY HONEST.

=== PREVIEW DATA ===
{json.dumps(preview_data, indent=2, default=str)}

=== EVALUATION CRITERIA ===

1. **HOOK STRENGTH** (0-1)
   - Is the headline compelling enough to stop scrolling?
   - 0.9+: "I need to click this NOW"
   - 0.7-0.8: "This looks interesting"
   - 0.5-0.6: "Meh, might click"
   - <0.5: "Definitely skip"

2. **TRUST SIGNALS** (0-1)
   - Is there specific social proof with numbers?
   - Are there recognizable trust indicators?
   - Does it look professional or spammy?

3. **CLARITY** (0-1)
   - Can someone understand the value in 2 seconds?
   - Is there one clear message or competing messages?
   - Is the information density appropriate?

4. **DESIGN FIDELITY** (0-1)
   - Does this honor the original site's design language?
   - Are colors, typography consistent with brand?
   - Would someone recognize the brand?

5. **CLICK MOTIVATION** (0-1)
   - What's the reason to click?
   - Is there curiosity gap or FOMO?
   - Would someone share this?

=== OUTPUT FORMAT ===
{{
    "scores": {{
        "hook_strength": 0.0-1.0,
        "trust_signals": 0.0-1.0,
        "clarity": 0.0-1.0,
        "design_fidelity": 0.0-1.0,
        "click_motivation": 0.0-1.0,
        "overall": 0.0-1.0
    }},
    "evaluation": {{
        "hook_notes": "What works/doesn't work about the headline",
        "trust_notes": "What proof exists or is missing",
        "clarity_notes": "Can someone get it instantly?",
        "fidelity_notes": "Does this honor the original design?",
        "click_notes": "Would you actually click?"
    }},
    "verdict": "excellent|good|fair|poor",
    "biggest_weakness": "The ONE thing that would improve this most",
    "improvement_actions": [
        {{"action": "specific action 1", "priority": "high|medium|low", "impact": "expected improvement"}},
        {{"action": "specific action 2", "priority": "high|medium|low", "impact": "expected improvement"}}
    ],
    "confidence": 0.0-1.0,
    "reasoning": "Overall assessment summary"
}}

Be HONEST. Most previews are "fair" or "good". Reserve "excellent" for truly exceptional work."""

    def _build_context_fusion_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build Context Fusion prompt."""
        responses = input_data.get("responses", [])
        
        return f"""Combine these agent outputs into a unified, coherent result.

=== AGENT OUTPUTS ===
{json.dumps(responses, indent=2, default=str)}

=== FUSION REQUIREMENTS ===

1. **RESOLVE CONFLICTS**
   - When agents disagree, prefer higher confidence scores
   - Note any unresolvable conflicts

2. **FILL GAPS**
   - Identify missing information
   - Suggest which agent should provide it

3. **SYNTHESIZE INSIGHTS**
   - Combine visual analysis + content + design DNA
   - Create a unified understanding

4. **QUALITY CONTROL**
   - Flag low-confidence outputs
   - Identify areas needing improvement

=== OUTPUT FORMAT ===
{{
    "fused_content": {{
        "title": "best title from agents",
        "description": "best description",
        "social_proof": "best social proof",
        "page_type": "determined page type"
    }},
    "fused_design": {{
        "primary_color": "#hex",
        "secondary_color": "#hex",
        "accent_color": "#hex",
        "typography_style": "style",
        "design_philosophy": "philosophy"
    }},
    "fused_layout": {{
        "grid_type": "type",
        "visual_hierarchy": "description",
        "key_components": ["list"]
    }},
    "conflicts_resolved": [
        {{"field": "title", "chosen": "value", "alternatives": ["other options"], "reason": "why this was chosen"}}
    ],
    "gaps_identified": [
        {{"field": "missing field", "suggested_source": "agent that should provide it"}}
    ],
    "quality_flags": [
        {{"issue": "description", "severity": "high|medium|low", "agent": "source agent"}}
    ],
    "overall_confidence": 0.0-1.0,
    "reasoning": "How the fusion was performed"
}}

Create a coherent, high-quality unified output from all agent contributions."""

    def _prepare_image(self, screenshot_bytes: bytes) -> str:
        """Prepare screenshot for vision API."""
        try:
            image = Image.open(BytesIO(screenshot_bytes))
            
            # Resize if too large
            max_dim = 2048
            if image.width > max_dim or image.height > max_dim:
                ratio = min(max_dim / image.width, max_dim / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB
            if image.mode in ('RGBA', 'P', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                image = background
            
            # Encode to base64
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=90)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            logger.warning(f"Image preparation failed: {e}, using raw encoding")
            return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    def _call_openai(
        self,
        config: AgentConfig,
        system_prompt: str,
        user_content: List[Dict[str, Any]],
        input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], float]:
        """Call OpenAI API and parse response."""
        try:
            response = self.client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                response_format={"type": "json_object"} if config.model != "gpt-4o" else None
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Clean JSON from markdown if needed
            if content.startswith("```"):
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                else:
                    content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    result = {"raw_response": content, "parse_error": True}
            
            # Calculate cost (approximate)
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
            
            # GPT-4o pricing (approximate)
            if config.model == "gpt-4o":
                cost = (prompt_tokens * 0.005 / 1000) + (completion_tokens * 0.015 / 1000)
            else:
                cost = (prompt_tokens * 0.00015 / 1000) + (completion_tokens * 0.0006 / 1000)
            
            return result, cost
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise


# Singleton executor instance
_executor_instance: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """Get or create the agent executor singleton."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = AgentExecutor()
    return _executor_instance

