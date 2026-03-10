"""
Pydantic validation for AI output schemas (layout reasoning, quality critic).

Used for output schema enforcement with retry on parse failure.
Reference: TECHNICAL_ARCHITECTURE_MYMETAVIEW_3.5.md §2.4, §4.1
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DesignDNAOutput(BaseModel):
    """Design DNA from Stage 1-3 reasoning output."""
    style: str = "corporate"
    mood: str = "balanced"
    formality: float = 0.5
    typography_personality: str = "bold"
    color_emotion: str = "trust"
    spacing_feel: str = "balanced"
    brand_adjectives: List[str] = Field(default_factory=list)
    design_reasoning: str = ""


class ReasoningOutput(BaseModel):
    """Stage 1-3 reasoning output - validated with graceful defaults."""
    primary_headline: Optional[str] = None
    value_statement: Optional[str] = None
    credibility_signals: Optional[str] = None
    page_type: str = "unknown"
    design_dna: Optional[DesignDNAOutput] = None
    analysis_confidence: float = 0.3
    regions: List[Dict[str, Any]] = Field(default_factory=list)
    detected_palette: Optional[Dict[str, str]] = None
    detected_logo: Optional[Dict[str, Any]] = None
    is_individual_profile: bool = False
    detected_person_name: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields from AI


class LayoutResultOutput(BaseModel):
    """Stage 4-6 layout result - validated with graceful defaults."""
    composition_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)
    layout_reasoning: str = ""
    preview_strength: str = "moderate"
    accuracy_score: float = 0.7
    clarity_score: float = 0.7
    engagement_score: float = 0.7
    design_fidelity_score: float = 0.7
    overall_quality: str = "good"
    biggest_weakness: str = ""
    improvement_suggestions: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


def validate_reasoning_output(data: Dict[str, Any]) -> ReasoningOutput:
    """Validate and coerce Stage 1-3 output. Returns validated model or raises."""
    if data.get("design_dna") and isinstance(data["design_dna"], dict):
        data = {**data, "design_dna": DesignDNAOutput(**data["design_dna"])}
    return ReasoningOutput(**data)


def validate_layout_result(data: Dict[str, Any]) -> LayoutResultOutput:
    """Validate and coerce Stage 4-6 output. Returns validated model or raises."""
    return LayoutResultOutput(**data)
