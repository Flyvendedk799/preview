"""
Preview Iterator - Closed-loop quality improvement system.

This module implements the iteration controller that:
1. Generates a preview
2. Critiques it with the Quality Critic
3. Applies improvements based on critique
4. Repeats until quality threshold is met (max 2 iterations)

This creates a self-improving preview generation system.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from backend.services.quality_critic import (
    QualityCritic, CritiqueResult, QualityVerdict,
    ImprovementPriority, get_quality_critic
)

logger = logging.getLogger(__name__)


class IterationStatus(str, Enum):
    """Status of an iteration."""
    SUCCESS = "success"  # Met quality threshold
    IMPROVED = "improved"  # Quality improved but not met threshold
    NO_IMPROVEMENT = "no_improvement"  # Quality didn't improve
    MAX_ITERATIONS = "max_iterations"  # Hit max iterations
    ERROR = "error"  # Error during iteration


@dataclass
class IterationResult:
    """Result from a single iteration."""
    iteration_number: int
    critique: CritiqueResult
    improvements_applied: List[str]
    quality_before: float
    quality_after: float
    status: IterationStatus
    latency_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration_number": self.iteration_number,
            "critique": self.critique.to_dict(),
            "improvements_applied": self.improvements_applied,
            "quality_before": self.quality_before,
            "quality_after": self.quality_after,
            "status": self.status.value,
            "latency_ms": self.latency_ms
        }


@dataclass
class IterationSummary:
    """Summary of the complete iteration process."""
    iterations_performed: int
    final_quality: float
    quality_improved: bool
    quality_delta: float  # Total improvement
    final_verdict: QualityVerdict
    met_threshold: bool
    total_latency_ms: float
    iteration_results: List[IterationResult]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iterations_performed": self.iterations_performed,
            "final_quality": self.final_quality,
            "quality_improved": self.quality_improved,
            "quality_delta": self.quality_delta,
            "final_verdict": self.final_verdict.value,
            "met_threshold": self.met_threshold,
            "total_latency_ms": self.total_latency_ms,
            "iteration_results": [r.to_dict() for r in self.iteration_results]
        }


class ImprovementApplicator:
    """
    Applies improvements to preview data based on critique suggestions.
    
    This is a simple applicator that modifies preview data based on
    the improvement actions from the quality critic.
    """
    
    def __init__(self):
        """Initialize the applicator."""
        logger.info("🔧 ImprovementApplicator initialized")
    
    def apply_improvements(
        self,
        preview_data: Dict[str, Any],
        critique: CritiqueResult,
        design_dna: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply improvements to preview data based on critique.
        
        Args:
            preview_data: Current preview data
            critique: Critique result with improvement suggestions
            design_dna: Design DNA for reference
            
        Returns:
            Tuple of (improved_data, list of improvements applied)
        """
        improved = preview_data.copy()
        applied = []
        
        # Process each improvement action (prioritize critical and high)
        for action in critique.improvement_actions:
            if action.priority in [ImprovementPriority.CRITICAL, ImprovementPriority.HIGH]:
                result = self._apply_action(improved, action, design_dna)
                if result:
                    applied.append(result)
        
        # Apply iteration focus if specified
        if critique.iteration_focus:
            focus_result = self._apply_focus(improved, critique.iteration_focus, design_dna)
            if focus_result and focus_result not in applied:
                applied.append(focus_result)
        
        logger.info(f"🔧 Applied {len(applied)} improvements")
        
        return improved, applied
    
    def _apply_action(
        self,
        data: Dict[str, Any],
        action,  # ImprovementAction
        design_dna: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Apply a single improvement action."""
        target = action.target.lower()
        
        try:
            if target == "title":
                return self._improve_title(data, action.action)
            elif target == "description":
                return self._improve_description(data, action.action)
            elif target == "social_proof":
                return self._improve_social_proof(data, action.action)
            elif target == "colors":
                return self._improve_colors(data, action.action, design_dna)
            elif target == "layout":
                return self._improve_layout(data, action.action)
            else:
                logger.debug(f"Unknown improvement target: {target}")
                return None
        except Exception as e:
            logger.warning(f"Failed to apply improvement to {target}: {e}")
            return None
    
    def _apply_focus(
        self,
        data: Dict[str, Any],
        focus: str,
        design_dna: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Apply improvement based on iteration focus."""
        focus_lower = focus.lower()
        
        if "title" in focus_lower or "headline" in focus_lower or "hook" in focus_lower:
            return self._improve_title(data, focus)
        elif "trust" in focus_lower or "proof" in focus_lower:
            return self._improve_social_proof(data, focus)
        elif "clarity" in focus_lower or "message" in focus_lower:
            return self._improve_clarity(data)
        elif "color" in focus_lower or "design" in focus_lower:
            return self._improve_colors(data, focus, design_dna)
        
        return None
    
    def _improve_title(self, data: Dict[str, Any], guidance: str) -> Optional[str]:
        """Improve the title based on guidance."""
        current_title = data.get("title", "")
        
        if not current_title:
            return None
        
        # Basic improvements
        improved = current_title
        
        # Trim if too long
        if len(improved) > 70:
            # Try to cut at sentence boundary
            if ". " in improved[:65]:
                improved = improved[:improved.rfind(". ", 0, 65) + 1]
            elif ", " in improved[:65]:
                improved = improved[:improved.rfind(", ", 0, 65)]
            else:
                improved = improved[:65] + "..."
        
        # Capitalize properly
        if improved and improved[0].islower():
            improved = improved[0].upper() + improved[1:]
        
        # Remove trailing punctuation if it's not a sentence
        if improved.endswith(",") or improved.endswith(";"):
            improved = improved[:-1]
        
        if improved != current_title:
            data["title"] = improved
            return f"Title improved: length {len(current_title)} → {len(improved)}"
        
        return None
    
    def _improve_description(self, data: Dict[str, Any], guidance: str) -> Optional[str]:
        """Improve the description based on guidance."""
        current_desc = data.get("description", "")
        
        if not current_desc:
            return None
        
        improved = current_desc
        
        # Ensure description doesn't start with same words as title
        title = data.get("title", "").lower()
        if title and improved.lower().startswith(title[:20]):
            # Try to remove repeated title from description
            improved = improved[len(title):].strip()
            if improved.startswith("-") or improved.startswith(":"):
                improved = improved[1:].strip()
        
        # Trim if too long
        if len(improved) > 160:
            # Smart truncate at sentence
            if ". " in improved[:155]:
                improved = improved[:improved.rfind(". ", 0, 155) + 1]
            else:
                improved = improved[:155] + "..."
        
        # Ensure minimum length
        if len(improved) < 20 and data.get("tags"):
            # Enhance with tags
            tags = data.get("tags", [])[:3]
            if tags:
                tag_text = " • ".join(tags)
                improved = f"{improved} {tag_text}"
        
        if improved != current_desc:
            data["description"] = improved
            return f"Description improved: length {len(current_desc)} → {len(improved)}"
        
        return None
    
    def _improve_social_proof(self, data: Dict[str, Any], guidance: str) -> Optional[str]:
        """Improve social proof visibility."""
        # Check if we have social proof data
        social_proof = data.get("social_proof") or data.get("credibility_items", [])
        
        if not social_proof:
            # Check if we can extract from other fields
            subtitle = data.get("subtitle", "")
            if any(char.isdigit() for char in subtitle):
                # Subtitle might contain social proof
                data["social_proof_highlighted"] = True
                return "Highlighted social proof in subtitle"
        
        # Mark social proof for emphasis
        if social_proof:
            data["social_proof_emphasized"] = True
            return "Emphasized existing social proof"
        
        return None
    
    def _improve_colors(
        self,
        data: Dict[str, Any],
        guidance: str,
        design_dna: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Improve color usage."""
        if not design_dna:
            return None
        
        # Ensure we're using brand colors
        color_psych = design_dna.get("color_psychology", {})
        if isinstance(color_psych, dict):
            if color_psych.get("primary", {}).get("hex"):
                data["use_brand_colors"] = True
                data["primary_color"] = color_psych["primary"]["hex"]
                return "Applied brand primary color"
        
        return None
    
    def _improve_layout(self, data: Dict[str, Any], guidance: str) -> Optional[str]:
        """Improve layout based on guidance."""
        # Mark for layout adjustment
        if "emphasis" in guidance.lower() or "prominence" in guidance.lower():
            data["layout_adjustment"] = "increase_emphasis"
            return "Marked for increased emphasis"
        elif "balance" in guidance.lower():
            data["layout_adjustment"] = "improve_balance"
            return "Marked for better balance"
        
        return None
    
    def _improve_clarity(self, data: Dict[str, Any]) -> Optional[str]:
        """General clarity improvements."""
        improvements = []
        
        # Ensure title and description don't overlap
        title = data.get("title", "").lower()
        desc = data.get("description", "").lower()
        
        if title and desc and desc.startswith(title[:30]):
            # Description repeats title
            data["description"] = data["description"][len(title):].strip()
            if data["description"].startswith(("-", ":", "|")):
                data["description"] = data["description"][1:].strip()
            improvements.append("Removed title repetition from description")
        
        # Check for clear CTA
        if not data.get("cta_text") and data.get("has_cta_slot", True):
            # Add generic CTA
            data["cta_text"] = "Learn More"
            improvements.append("Added CTA")
        
        if improvements:
            return " | ".join(improvements)
        
        return None


class PreviewIterator:
    """
    Orchestrates the closed-loop quality improvement process.
    
    Takes a preview generator callback and iteratively improves
    the output until quality threshold is met.
    """
    
    def __init__(
        self,
        quality_threshold: float = 0.80,
        max_iterations: int = 2
    ):
        """
        Initialize the iterator.
        
        Args:
            quality_threshold: Minimum quality score to pass
            max_iterations: Maximum number of improvement iterations
        """
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        self.critic = get_quality_critic(quality_threshold)
        self.applicator = ImprovementApplicator()
        
        logger.info(
            f"🔄 PreviewIterator initialized "
            f"(threshold={quality_threshold}, max_iter={max_iterations})"
        )
    
    def iterate(
        self,
        initial_preview_data: Dict[str, Any],
        initial_image_bytes: Optional[bytes],
        design_dna: Optional[Dict[str, Any]] = None,
        original_url: Optional[str] = None,
        regenerate_callback: Optional[Callable[[Dict[str, Any]], Tuple[Dict[str, Any], bytes]]] = None
    ) -> Tuple[Dict[str, Any], IterationSummary]:
        """
        Iterate on a preview until quality threshold is met.
        
        Args:
            initial_preview_data: Initial preview data
            initial_image_bytes: Initial preview image
            design_dna: Design DNA for reference
            original_url: Original URL
            regenerate_callback: Optional callback to regenerate preview
            
        Returns:
            Tuple of (final_preview_data, iteration_summary)
        """
        start_time = time.time()
        
        current_data = initial_preview_data.copy()
        current_image = initial_image_bytes
        iteration_results = []
        initial_quality = 0.0
        
        for i in range(self.max_iterations + 1):  # +1 for initial critique
            iter_start = time.time()
            
            # Critique current preview
            critique = self.critic.critique(
                current_image, current_data, design_dna, original_url
            )
            
            quality = critique.scores.overall
            
            # Record initial quality
            if i == 0:
                initial_quality = quality
            
            # Check if we met threshold
            if quality >= self.quality_threshold:
                result = IterationResult(
                    iteration_number=i,
                    critique=critique,
                    improvements_applied=[],
                    quality_before=quality,
                    quality_after=quality,
                    status=IterationStatus.SUCCESS,
                    latency_ms=(time.time() - iter_start) * 1000
                )
                iteration_results.append(result)
                
                logger.info(f"✅ Met quality threshold on iteration {i}")
                break
            
            # Check if we've used all iterations
            if i >= self.max_iterations:
                result = IterationResult(
                    iteration_number=i,
                    critique=critique,
                    improvements_applied=[],
                    quality_before=quality,
                    quality_after=quality,
                    status=IterationStatus.MAX_ITERATIONS,
                    latency_ms=(time.time() - iter_start) * 1000
                )
                iteration_results.append(result)
                
                logger.info(f"⚠️ Max iterations reached, quality={quality:.2f}")
                break
            
            # Apply improvements
            quality_before = quality
            improved_data, applied = self.applicator.apply_improvements(
                current_data, critique, design_dna
            )
            
            # Update current data
            current_data = improved_data
            
            # Regenerate image if callback provided and significant changes
            if regenerate_callback and applied:
                try:
                    current_data, current_image = regenerate_callback(current_data)
                except Exception as e:
                    logger.warning(f"Regeneration failed: {e}")
            
            # Re-critique to measure improvement
            post_critique = self.critic.critique(
                current_image, current_data, design_dna, original_url
            )
            quality_after = post_critique.scores.overall
            
            # Determine status
            if quality_after > quality_before:
                status = IterationStatus.IMPROVED
            else:
                status = IterationStatus.NO_IMPROVEMENT
            
            result = IterationResult(
                iteration_number=i,
                critique=critique,
                improvements_applied=applied,
                quality_before=quality_before,
                quality_after=quality_after,
                status=status,
                latency_ms=(time.time() - iter_start) * 1000
            )
            iteration_results.append(result)
            
            logger.info(
                f"🔄 Iteration {i}: quality {quality_before:.2f} → {quality_after:.2f}, "
                f"applied {len(applied)} improvements"
            )
        
        # Build summary
        final_quality = iteration_results[-1].quality_after if iteration_results else initial_quality
        
        summary = IterationSummary(
            iterations_performed=len(iteration_results),
            final_quality=final_quality,
            quality_improved=final_quality > initial_quality,
            quality_delta=final_quality - initial_quality,
            final_verdict=iteration_results[-1].critique.verdict if iteration_results else QualityVerdict.FAIR,
            met_threshold=final_quality >= self.quality_threshold,
            total_latency_ms=(time.time() - start_time) * 1000,
            iteration_results=iteration_results
        )
        
        logger.info(
            f"📊 Iteration complete: {summary.iterations_performed} iterations, "
            f"quality {initial_quality:.2f} → {final_quality:.2f} "
            f"(delta={summary.quality_delta:+.2f})"
        )
        
        return current_data, summary


# Singleton instance
_iterator_instance: Optional[PreviewIterator] = None


def get_preview_iterator(
    threshold: float = 0.80,
    max_iterations: int = 2
) -> PreviewIterator:
    """Get or create the preview iterator singleton."""
    global _iterator_instance
    if _iterator_instance is None:
        _iterator_instance = PreviewIterator(threshold, max_iterations)
    return _iterator_instance


def iterate_preview(
    initial_preview_data: Dict[str, Any],
    initial_image_bytes: Optional[bytes],
    design_dna: Optional[Dict[str, Any]] = None,
    original_url: Optional[str] = None
) -> Tuple[Dict[str, Any], IterationSummary]:
    """Convenience function to iterate on a preview."""
    iterator = get_preview_iterator()
    return iterator.iterate(
        initial_preview_data, initial_image_bytes, design_dna, original_url
    )

