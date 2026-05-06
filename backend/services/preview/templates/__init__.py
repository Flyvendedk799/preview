"""Phase 3 — Versioned template modules + contract tests."""
from backend.services.preview.templates.contracts import (
    SafeArea,
    TemplateContract,
    TemplateRenderInput,
    TemplateRenderViolation,
    HERO_CONTRACT_V1,
    MODERN_CARD_CONTRACT_V1,
    PROFILE_CONTRACT_V1,
    TEMPLATE_CONTRACTS,
    get_contract,
    pre_measure_layout,
)
from backend.services.preview.templates.gradient import (
    GradientPalette,
    LuminanceOverlay,
    build_three_stop_gradient,
)
from backend.services.preview.templates.composition import (
    eased_mask,
    apply_blend_separator,
)

__all__ = [
    "SafeArea",
    "TemplateContract",
    "TemplateRenderInput",
    "TemplateRenderViolation",
    "HERO_CONTRACT_V1",
    "MODERN_CARD_CONTRACT_V1",
    "PROFILE_CONTRACT_V1",
    "TEMPLATE_CONTRACTS",
    "get_contract",
    "pre_measure_layout",
    "GradientPalette",
    "LuminanceOverlay",
    "build_three_stop_gradient",
    "eased_mask",
    "apply_blend_separator",
]
