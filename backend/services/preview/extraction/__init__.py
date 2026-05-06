"""Phase 4 — Extraction Fidelity Pipeline."""
from backend.services.preview.extraction.prompts import (
    PageType,
    classify_page_type,
    get_extraction_prompt,
)
from backend.services.preview.extraction.validators import (
    HookValidationResult,
    fallback_title_chain,
    is_low_information_hook,
    validate_hook,
)
from backend.services.preview.extraction.palette import (
    PaletteValidationResult,
    enforce_palette_distance,
)
from backend.services.preview.extraction.social_proof import (
    extract_social_proof,
    NumericProof,
)

__all__ = [
    "PageType",
    "classify_page_type",
    "get_extraction_prompt",
    "HookValidationResult",
    "fallback_title_chain",
    "is_low_information_hook",
    "validate_hook",
    "PaletteValidationResult",
    "enforce_palette_distance",
    "extract_social_proof",
    "NumericProof",
]
