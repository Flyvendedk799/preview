# Demo Preview Engine — Implementation Status

This document tracks the integration of `DEMO_PREVIEW_ENGINE_FINAL_PLAN.md`.
Each plan checklist item maps to the code that implements it.

## Final Acceptance Checklist

| Plan item | Status | Where it lives |
|-----------|--------|----------------|
| Baseline documented and reproducible | ✅ | `docs/demo-engine-baseline.md`, `backend/scripts/preview_engine/run_corpus.py` |
| Reliability blockers fixed and verified | ✅ | `backend/services/preview/reliability.py`, `backend/tests/test_preview_engine_plan.py` |
| Structured traces available for every job | ✅ | `backend/services/preview/observability/`, wired into `backend/services/preview_engine.py` |
| Visual quality targets met on corpus | ✅ infra | Versioned templates + gradient/composition modules in `backend/services/preview/templates/` |
| Content fidelity targets met on labeled set | ✅ infra | Specialized prompts + validators in `backend/services/preview/extraction/` |
| Progress UX trust issues resolved | ✅ | `src/components/GenerationProgress.tsx` (`isFinalizing`, `failureReason`) |
| Performance/cost targets met | ✅ infra | `backend/services/preview/lanes.py` (fast/deep lane budgets, capture timeout) |
| Nightly regression CI gate enabled | ✅ | `.github/workflows/preview-corpus-nightly.yml` |

## Phase-by-phase pointers

### Phase 0 — Baseline / Corpus / Freeze
- Golden corpus (60 URLs, 5 categories): `backend/services/preview/corpus/golden_corpus.py`
- Shadow corpus (12 URLs, monthly rotation): same module, `SHADOW_CORPUS`
- Reproducible runner: `python -m backend.scripts.preview_engine.run_corpus`
- Baseline doc: `docs/demo-engine-baseline.md`

### Phase 1 — Critical reliability fixes
1.1 Event-loop safety — `run_async_safely`, `sync_http_get`
1.2 Retry semantics — `RetryContext.assert_payload_changed` raises `IdenticalRetryError` on identical payload
1.3 Schema/type integrity — `validate_blueprint`, called from `_validate_result_quality`
1.4 Font determinism — `resolve_font` + `register_font_fallback_event`

### Phase 2 — Observability & forensics
- `JobTrace` schema matches the plan exactly: `job_id, url, start_ts, end_ts`,
  per-stage timings, extraction confidence, quality sub-scores, template
  selection + rationale, palette source, retry count + deltas, terminal
  status + reason code.
- `JobTraceStore` (LRU + pluggable writer/reader)
- `diagnose_job` CLI: `python -m backend.scripts.preview_engine.diagnose_job <id>`
- API: `/preview-diagnosis/jobs/{job_id}` (admin only)

### Phase 3 — Visual rendering upgrade
- Versioned templates (`hero@v1`, `modern_card@v1`, `profile@v1`) with
  `safe_areas`, headline/body size budgets, line counts.
- Pre-measure layout via `pre_measure_layout` — surfaces `TemplateRenderViolation`s
  before drawing.
- 3-stop perceptual gradient with Oklab interpolation +
  luminance-adaptive overlay + grain.
- Eased composition masks (`cubic-bezier(0.4, 0, 0.2, 1)`).
- Contract tests: `backend/tests/test_template_contracts.py`.

### Phase 4 — Extraction fidelity
- Specialized prompts per page type: general, product, profile, docs.
- `classify_page_type` routes URLs → prompt.
- Validators: `is_low_information_hook`, `fallback_title_chain` (extracted →
  og:title → first H1 → domain).
- Palette enforcement: `enforce_palette_distance` guarantees a minimum
  perceptual distance between primary/secondary/accent and derives a
  triadic / complementary accent if the AI returned near-duplicates.
- Social-proof regex+DOM pass: `extract_social_proof` (run before AI fallback).

### Phase 5 — Frontend progress & error UX
- `GenerationProgress.tsx` now exposes:
  - `isFinalizing` prop — explicit "Finalizing…" stripe between 95–100%.
  - `failureReason` + `FAILURE_REASON_COPY` mirroring backend taxonomy.
  - `onRetry` callback for the retry button.

### Phase 6 — Performance & cost
- `select_lane` — fast vs deep with explainable reasoning.
- `LaneBudget` — token + per-stage seconds + early-exit confidence.
- `screenshot_capture_with_timeout` — hard timeout + fallback hook.
- Wired into `PreviewEngine.generate` so `JobTrace.lane` is always set.

### Phase 7 — Regression governance
- `.github/workflows/preview-corpus-nightly.yml` runs the corpus nightly
  and fails the build if `success_rate`, `title_fidelity`, or
  `default_palette_incidence` regress.
- Per-PR manual trigger via `workflow_dispatch`.
- Tests gate: `backend/tests/test_preview_engine_plan.py` runs first.

## Local verification

```bash
# Run the new test suite
python -m pytest backend/tests/test_preview_engine_plan.py \
                 backend/tests/test_template_contracts.py -q

# Smoke run the corpus
python -m backend.scripts.preview_engine.run_corpus \
    --max-urls 3 \
    --output-dir artifacts/baseline

# Inspect a recent job (after a real generation)
python -m backend.scripts.preview_engine.diagnose_job --recent 10
```
