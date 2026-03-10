"""Shared Pydantic schemas for demo preview endpoints."""
from typing import Optional, List, Literal
from pydantic import BaseModel, HttpUrl, field_validator


class ContextItem(BaseModel):
    """Context item like location, date, etc."""
    icon: str
    text: str


class CredibilityItem(BaseModel):
    """Credibility item like rating, review count."""
    type: str
    value: str


class BrandElements(BaseModel):
    """Extracted brand elements."""
    brand_name: Optional[str] = None
    logo_base64: Optional[str] = None
    hero_image_base64: Optional[str] = None
    favicon_url: Optional[str] = None


class DesignDNA(BaseModel):
    """Design DNA - extracted design philosophy for intelligent rendering."""
    style: str = "corporate"
    mood: str = "balanced"
    formality: float = 0.5
    typography_personality: str = "bold"
    color_emotion: str = "trust"
    spacing_feel: str = "balanced"
    brand_adjectives: List[str] = []
    design_reasoning: str = ""


class LayoutBlueprint(BaseModel):
    """Layout blueprint with full reasoning."""
    template_type: str
    primary_color: str
    secondary_color: str
    accent_color: str
    coherence_score: float
    balance_score: float
    clarity_score: float
    design_fidelity_score: Optional[float] = None
    overall_quality: str
    layout_reasoning: str
    composition_notes: str


class DemoPreviewRequest(BaseModel):
    """Schema for demo preview generation request."""
    url: HttpUrl
    quality_mode: Literal["fast", "balanced", "ultra", "auto"] = "ultra"


class DemoPreviewResponse(BaseModel):
    """Multi-stage reasoned preview response with brand elements and Design DNA."""
    url: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    context_items: List[ContextItem] = []
    credibility_items: List[CredibilityItem] = []
    cta_text: Optional[str] = None
    primary_image_base64: Optional[str] = None
    screenshot_url: Optional[str] = None
    composited_preview_image_url: Optional[str] = None
    brand: Optional[BrandElements] = None
    blueprint: LayoutBlueprint
    design_dna: Optional[DesignDNA] = None
    reasoning_confidence: float
    design_fidelity_score: Optional[float] = None
    processing_time_ms: int
    is_demo: bool = True
    message: str = "AI-reconstructed preview using multi-stage reasoning with Design DNA."
    trace_url: Optional[str] = None


class DemoJobRequest(BaseModel):
    """Schema for demo job creation request."""
    url: HttpUrl
    quality_mode: Literal["fast", "balanced", "ultra"] = "ultra"

    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        """Normalize URL: add https:// if no scheme to avoid 422 from strict HttpUrl."""
        if isinstance(v, str) and v.strip() and "://" not in v:
            return f"https://{v.strip()}"
        return v


class DemoJobResponse(BaseModel):
    """Schema for demo job creation response."""
    job_id: str
    status: str = "queued"
    message: str = "Preview generation started. Poll /demo-v2/jobs/{job_id}/status for updates."


class DemoJobStatusResponse(BaseModel):
    """Schema for demo job status response."""
    job_id: str
    status: str
    result: Optional[DemoPreviewResponse] = None
    error: Optional[str] = None
    progress: Optional[float] = None
    message: Optional[str] = None


# --- Batch API schemas (MyMetaView 4.0 P3) ---

class BatchJobRequest(BaseModel):
    """Schema for batch job creation request."""
    urls: List[HttpUrl]
    quality_mode: Literal["fast", "balanced", "ultra"] = "balanced"
    callback_url: Optional[HttpUrl] = None  # P8: per-job webhook on completion

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one URL is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 URLs per batch")
        return v


class BatchJobResponse(BaseModel):
    """Schema for batch job creation response."""
    job_id: str
    status: str = "queued"
    total: int
    message: str = "Batch job created. Poll /demo-v2/batch/{job_id} for status."


class BatchJobStatusResponse(BaseModel):
    """Schema for batch job status response."""
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    total: int
    completed: int
    failed: int


class BatchResultItem(BaseModel):
    """Single result in a batch (URL + preview image URL)."""
    url: str
    preview_image_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


class BatchJobResultsResponse(BaseModel):
    """Schema for batch job results response."""
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    total: int
    completed: int
    failed: int
    results: List[BatchResultItem] = []


