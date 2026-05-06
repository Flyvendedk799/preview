"""Preview engine support modules implementing DEMO_PREVIEW_ENGINE_FINAL_PLAN.

This package contains the modular phases of the demo preview engine fix plan:
  - corpus:        Phase 0 — Golden URL corpus + baseline runner
  - observability: Phase 2 — Structured per-job trace + reason codes
  - extraction:    Phase 4 — Specialized prompts + deterministic validators
  - templates:     Phase 3 — Versioned template contracts
  - lanes:         Phase 6 — Dual-lane (fast/deep) orchestration

Each sub-module is importable in isolation and is wired into the existing
PreviewEngine via lightweight glue rather than a rewrite, so reverts are cheap.
"""
