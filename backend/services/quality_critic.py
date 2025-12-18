"""
Quality Critic - AI-powered preview quality evaluation.

This module implements a Quality Critic agent that evaluates generated previews
and provides specific improvement suggestions. It's the core of the closed-loop
quality iteration system.

Key Responsibilities:
1. Evaluate preview quality across multiple dimensions
2. Identify specific weaknesses
3. Generate actionable improvement suggestions
4. Determine if a preview meets quality threshold
"""

import logging
import json
import base64
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from io import BytesIO

from openai import OpenAI
from PIL import Image

from backend.core.config import settings

logger = logging.getLogger(__name__)


class QualityVerdict(str, Enum):
    """Quality verdict categories."""
    EXCELLENT = "excellent"  # 0.85+ - Ready to ship
    GOOD = "good"  # 0.70-0.84 - Acceptable
    FAIR = "fair"  # 0.55-0.69 - Needs improvement
    POOR = "poor"  # <0.55 - Requires iteration


class ImprovementPriority(str, Enum):
    """Priority levels for improvements."""
    CRITICAL = "critical"  # Must fix before shipping
    HIGH = "high"  # Should fix if time allows
    MEDIUM = "medium"  # Nice to have
    LOW = "low"  # Minor polish


@dataclass
class QualityScore:
    """Detailed quality scores."""
    hook_strength: float  # How compelling is the headline
    trust_signals: float  # Are there credible trust indicators
    clarity: float  # Can you understand it instantly
    design_fidelity: float  # Does it honor the original design
    click_motivation: float  # Would someone click this
    overall: float  # Weighted average
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "hook_strength": self.hook_strength,
            "trust_signals": self.trust_signals,
            "clarity": self.clarity,
            "design_fidelity": self.design_fidelity,
            "click_motivation": self.click_motivation,
            "overall": self.overall
        }


@dataclass
class ImprovementAction:
    """A specific improvement action."""
    action: str  # What to do
    target: str  # What element to change (title, colors, layout, etc.)
    priority: ImprovementPriority
    expected_impact: str  # What improvement to expect
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "priority": self.priority.value,
            "expected_impact": self.expected_impact
        }


@dataclass
class CritiqueResult:
    """Result from quality critique."""
    scores: QualityScore
    verdict: QualityVerdict
    biggest_weakness: str
    improvement_actions: List[ImprovementAction]
    evaluation_notes: Dict[str, str]
    should_iterate: bool
    iteration_focus: Optional[str]  # What to focus on in next iteration
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": self.scores.to_dict(),
            "verdict": self.verdict.value,
            "biggest_weakness": self.biggest_weakness,
            "improvement_actions": [a.to_dict() for a in self.improvement_actions],
            "evaluation_notes": self.evaluation_notes,
            "should_iterate": self.should_iterate,
            "iteration_focus": self.iteration_focus,
            "confidence": self.confidence
        }


class QualityCritic:
    """
    AI-powered quality critic for preview evaluation.
    
    Uses GPT-4o to analyze previews and provide detailed feedback
    for quality improvement.
    """
    
    def __init__(self, quality_threshold: float = 0.80):
        """
        Initialize the quality critic.
        
        Args:
            quality_threshold: Minimum quality score to pass (0-1)
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=45)
        self.quality_threshold = quality_threshold
        logger.info(f"🎯 QualityCritic initialized (threshold={quality_threshold})")
    
    def critique(
        self,
        preview_image_bytes: Optional[bytes],
        preview_data: Dict[str, Any],
        design_dna: Optional[Dict[str, Any]] = None,
        original_url: Optional[str] = None
    ) -> CritiqueResult:
        """
        Critique a generated preview.
        
        Args:
            preview_image_bytes: The generated preview image
            preview_data: Preview metadata (title, description, etc.)
            design_dna: Original design DNA for fidelity comparison
            original_url: Original URL for context
            
        Returns:
            CritiqueResult with scores and improvement suggestions
        """
        logger.info("🔍 Starting quality critique")
        
        try:
            # Build critique prompt
            prompt = self._build_critique_prompt(preview_data, design_dna, original_url)
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": self._build_user_content(prompt, preview_image_bytes)
                }
            ]
            
            # Call GPT-4o
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
                temperature=0.2
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            result = self._parse_critique_response(content)
            
            logger.info(
                f"✅ Critique complete: verdict={result.verdict.value}, "
                f"overall={result.scores.overall:.2f}, "
                f"should_iterate={result.should_iterate}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Critique failed: {e}", exc_info=True)
            # Return a conservative default
            return self._create_fallback_result()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the critic."""
        return """You are a Quality Critic - brutally honest about preview quality.

Your job is to evaluate social media previews and provide actionable feedback.
Be HONEST - most previews are "fair" or "good". Reserve "excellent" for truly exceptional work.

=== SCORING CRITERIA ===

1. HOOK STRENGTH (0-1): Is the headline compelling?
   - 0.9+: "I NEED to click this" - Urgent, specific, irresistible
   - 0.7-0.8: "This looks interesting" - Clear value, somewhat specific
   - 0.5-0.6: "Meh, might click" - Generic but readable
   - <0.5: "Skip" - Vague, boring, or confusing

2. TRUST SIGNALS (0-1): Does this look trustworthy?
   - Has specific numbers (review counts, user stats)?
   - Has recognizable proof (awards, logos)?
   - Looks professional, not spammy?
   - Makes believable claims?

3. CLARITY (0-1): Can you understand it in 2 seconds?
   - One clear message or competing messages?
   - Right amount of info (not too much or too little)?
   - Visual hierarchy clear?

4. DESIGN FIDELITY (0-1): Does it honor the original design?
   - Colors match the brand?
   - Typography feels consistent?
   - Spacing and density appropriate?
   - Would brand fans recognize it?

5. CLICK MOTIVATION (0-1): Would someone click?
   - Clear benefit to clicking?
   - Creates curiosity or FOMO?
   - Would someone share this?

=== OUTPUT FORMAT ===
Return valid JSON with your critique.

Be specific in improvement actions - vague suggestions aren't helpful."""
    
    def _build_critique_prompt(
        self,
        preview_data: Dict[str, Any],
        design_dna: Optional[Dict[str, Any]],
        original_url: Optional[str]
    ) -> str:
        """Build the critique prompt."""
        parts = ["Critique this preview:\n"]
        
        if original_url:
            parts.append(f"Original URL: {original_url}\n")
        
        parts.append(f"\n=== PREVIEW DATA ===\n")
        parts.append(f"Title: {preview_data.get('title', 'N/A')}\n")
        parts.append(f"Subtitle: {preview_data.get('subtitle', 'N/A')}\n")
        parts.append(f"Description: {preview_data.get('description', 'N/A')}\n")
        
        if preview_data.get('tags'):
            parts.append(f"Tags: {', '.join(preview_data['tags'][:5])}\n")
        
        if preview_data.get('social_proof'):
            parts.append(f"Social Proof: {preview_data['social_proof']}\n")
        
        if design_dna:
            parts.append(f"\n=== ORIGINAL DESIGN DNA ===\n")
            if design_dna.get('design_philosophy'):
                parts.append(f"Style: {design_dna['design_philosophy'].get('style', 'N/A')}\n")
            if design_dna.get('color_psychology'):
                parts.append(f"Color Mood: {design_dna['color_psychology'].get('overall_mood', 'N/A')}\n")
            if design_dna.get('typography_personality'):
                typo = design_dna['typography_personality']
                if isinstance(typo, dict):
                    parts.append(f"Typography: {typo.get('heading_style', 'N/A')}\n")
        
        parts.append("""
=== YOUR TASK ===
1. Score each criterion (0-1)
2. Provide brief notes for each
3. Determine verdict (excellent/good/fair/poor)
4. Identify the BIGGEST weakness
5. Provide 2-3 specific improvement actions
6. Determine if iteration is needed (score < 0.80)

Return JSON:
{
    "scores": {
        "hook_strength": 0.0-1.0,
        "trust_signals": 0.0-1.0,
        "clarity": 0.0-1.0,
        "design_fidelity": 0.0-1.0,
        "click_motivation": 0.0-1.0,
        "overall": 0.0-1.0
    },
    "evaluation_notes": {
        "hook_notes": "What works/doesn't about the headline",
        "trust_notes": "What proof exists or is missing",
        "clarity_notes": "How clear is the message",
        "fidelity_notes": "How well does it match original design",
        "click_notes": "Would you click?"
    },
    "verdict": "excellent|good|fair|poor",
    "biggest_weakness": "The ONE thing to fix first",
    "improvement_actions": [
        {"action": "Specific action", "target": "title|colors|layout|social_proof", "priority": "critical|high|medium|low", "expected_impact": "What will improve"}
    ],
    "should_iterate": true|false,
    "iteration_focus": "What to focus on next iteration",
    "confidence": 0.0-1.0
}
""")
        
        return "".join(parts)
    
    def _build_user_content(
        self,
        prompt: str,
        preview_image_bytes: Optional[bytes]
    ) -> List[Dict[str, Any]]:
        """Build user content including image if available."""
        content = [{"type": "text", "text": prompt}]
        
        if preview_image_bytes:
            try:
                # Prepare image
                image = Image.open(BytesIO(preview_image_bytes))
                
                # Convert to RGB if needed
                if image.mode in ('RGBA', 'P', 'LA'):
                    bg = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    if image.mode in ('RGBA', 'LA'):
                        bg.paste(image, mask=image.split()[-1])
                    image = bg
                
                # Encode
                buffer = BytesIO()
                image.save(buffer, format='JPEG', quality=90)
                image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "high"
                    }
                })
            except Exception as e:
                logger.warning(f"Could not prepare image for critique: {e}")
        
        return content
    
    def _parse_critique_response(self, content: str) -> CritiqueResult:
        """Parse the critique response from GPT-4o."""
        # Clean JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                return self._create_fallback_result()
        
        # Parse scores
        scores_data = data.get("scores", {})
        scores = QualityScore(
            hook_strength=scores_data.get("hook_strength", 0.6),
            trust_signals=scores_data.get("trust_signals", 0.6),
            clarity=scores_data.get("clarity", 0.6),
            design_fidelity=scores_data.get("design_fidelity", 0.6),
            click_motivation=scores_data.get("click_motivation", 0.6),
            overall=scores_data.get("overall", 0.6)
        )
        
        # Parse verdict
        verdict_str = data.get("verdict", "fair").lower()
        try:
            verdict = QualityVerdict(verdict_str)
        except ValueError:
            verdict = QualityVerdict.FAIR
        
        # Parse improvement actions
        actions = []
        for action_data in data.get("improvement_actions", []):
            try:
                priority = ImprovementPriority(action_data.get("priority", "medium").lower())
            except ValueError:
                priority = ImprovementPriority.MEDIUM
            
            actions.append(ImprovementAction(
                action=action_data.get("action", ""),
                target=action_data.get("target", "unknown"),
                priority=priority,
                expected_impact=action_data.get("expected_impact", "")
            ))
        
        # Determine if iteration is needed
        should_iterate = data.get("should_iterate", scores.overall < self.quality_threshold)
        
        return CritiqueResult(
            scores=scores,
            verdict=verdict,
            biggest_weakness=data.get("biggest_weakness", "Unknown"),
            improvement_actions=actions,
            evaluation_notes=data.get("evaluation_notes", {}),
            should_iterate=should_iterate,
            iteration_focus=data.get("iteration_focus"),
            confidence=data.get("confidence", 0.8)
        )
    
    def _create_fallback_result(self) -> CritiqueResult:
        """Create a fallback result when critique fails."""
        return CritiqueResult(
            scores=QualityScore(
                hook_strength=0.6,
                trust_signals=0.6,
                clarity=0.6,
                design_fidelity=0.6,
                click_motivation=0.6,
                overall=0.6
            ),
            verdict=QualityVerdict.FAIR,
            biggest_weakness="Unable to complete evaluation",
            improvement_actions=[],
            evaluation_notes={"error": "Critique failed, using defaults"},
            should_iterate=False,
            iteration_focus=None,
            confidence=0.3
        )


# Singleton instance
_critic_instance: Optional[QualityCritic] = None


def get_quality_critic(threshold: float = 0.80) -> QualityCritic:
    """Get or create the quality critic singleton."""
    global _critic_instance
    if _critic_instance is None:
        _critic_instance = QualityCritic(threshold)
    return _critic_instance


def critique_preview(
    preview_image_bytes: Optional[bytes],
    preview_data: Dict[str, Any],
    design_dna: Optional[Dict[str, Any]] = None,
    original_url: Optional[str] = None
) -> CritiqueResult:
    """Convenience function to critique a preview."""
    critic = get_quality_critic()
    return critic.critique(preview_image_bytes, preview_data, design_dna, original_url)

