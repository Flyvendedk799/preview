# MyMetaView 6.5 — Demo Quality Fix Workstream

**Reference:** [AIL-207](/AIL/issues/AIL-207) (parent), [AIL-206](/AIL/issues/AIL-206) (program)
**Target:** Restore proper meta preview images (fix gradient-only regression)
**Ownership:** Founding Engineer (diagnosis, coordination); Backend/Frontend (implementation); Junior Dev (Git) for final PR.

---

## 1. Problem Statement

MyMetaView 6.0 regressed demo generations — outputs are **gradient backgrounds instead of proper meta preview images**. Same symptom as reported in AIL-207: demos show gradient-only output instead of designed previews with title, subtitle, description, logo, and layout.

---

## 2. Root Cause Hypotheses (Diagnosis)

Based on codebase analysis, likely failure points:

| # | Area | Path | Hypothesis |
|---|------|------|------------|
| **A** | Quality gates | `preview_engine.py` | Quality gates may be rejecting valid AI results too aggressively, forcing fallback path. Fallback (`_build_fallback_result`) produces "minimal" preview — if `generate_and_upload_preview_image` fails or returns gradient-only in edge cases, that becomes the output. |
| **B** | Adaptive template | `preview_image_generator.py`, `adaptive_template_engine.py` | DNA-aware path (`generate_dna_aware_preview`) or classic path (`generate_designed_preview`) may return gradient-only when: (1) `design_dna` is missing/malformed → DNA path returns None; (2) content (title, text) rendering fails silently; (3) `_apply_background` uses gradient when screenshot is invalid/missing, and later steps fail. |
| **C** | Fallback composited image | `preview_engine._build_fallback_result` | Fallback explicitly calls `generate_and_upload_preview_image` with HTML-extracted data. If blueprint/colors are minimal, template may render gradient-only. Verify fallback always produces full preview (title + layout), not just gradient. |
| **D** | Cache / quality mode | `demo:preview:v3:{mode}:*` | 6.0 added quality profiles (`fast`, `balanced`, `ultra`). Stale or low-quality cached results may be served. Cache policy (demo-quality-validation-2026-03-08) rejects fallback writes, but read path might serve gradient-only from pre-6.0 cache. |

---

## 3. Pipeline Flow (For Diagnosis)

```
demo_batch_job / demo_preview_job
    → PreviewEngine.generate()
        → AI reasoning, brand extraction, quality orchestration
        → If quality gates PASS: generate_and_upload_preview_image (full pipeline)
        → If quality gates FAIL: _build_fallback_result (HTML fallback)
    → preview_image_generator.generate_and_upload_preview_image
        → If design_dna: generate_dna_aware_preview (AdaptiveTemplateEngine)
        → Else: generate_designed_preview (classic templates)
```

**Gradient-only occurs when:** The final composited image has gradient background but no text/content overlay. This can happen if (a) content rendering is skipped/fails, or (b) fallback path produces minimal output.

---

## 4. Workstream (Subtasks)

| # | Area | Owner | Description |
|---|------|-------|-------------|
| **A** | Backend diagnosis & fix | Backend Engineer | Trace gradient-only output: add logging at preview_engine fallback path, preview_image_generator entry, adaptive_template_engine. Identify whether fallback path, DNA path, or classic path produces gradient-only. Fix root cause (quality gate thresholds, fallback template, or content rendering). |
| **B** | Frontend verification | Frontend Engineer | Verify demo UI displays full preview images correctly. Confirm no client-side cropping/fallback that could show gradient-only. Check batch results rendering. |
| **C** | Final PR | Junior Dev (Git) | Consolidate backend + frontend changes, run pytest and frontend build, push PR. Link AIL-209, AIL-207. @Process Chain Manager for review. |

---

## 5. Unblocking Specs

### For Backend Engineer (A)

**Files to inspect:**
- `backend/services/preview_engine.py` — quality gates, fallback path, `_build_fallback_result`
- `backend/services/preview_image_generator.py` — `generate_and_upload_preview_image`, `generate_dna_aware_preview`, `generate_designed_preview`
- `backend/services/adaptive_template_engine.py` — `generate()`, `_apply_background`, content rendering

**Actions:**
1. Add targeted logging: when fallback path is taken; when `generate_and_upload_preview_image` returns; when DNA vs classic path is used.
2. Run demo batch against 2–3 fixture URLs; capture logs for gradient-only vs proper output.
3. Fix: adjust quality thresholds, ensure fallback produces full preview, or fix content rendering in adaptive/classic path.

### For Frontend Engineer (B)

**Files:** `src/pages/Demo.tsx`, `DemoGenerationPage.tsx`, `src/api/demo-batch-api.ts`

- Confirm preview image URL is displayed at full size (no crop to gradient region).
- Verify batch results show `composited_preview_image_url` correctly.

### For Junior Dev (Git) (C)

- Wait for Backend and Frontend tasks done.
- Pull changes, run `python -m pytest backend/tests/` and frontend build.
- Open PR linking AIL-209, AIL-207.
- @Process Chain Manager to review.

---

## 6. Completion Criterion

From [AIL-207](/AIL/issues/AIL-207): **@Junior Dev (Git) must push a PR to git.**

---

## 7. References

- [MYMETAVIEW_6.0_DEMO_ENGINE_WORKSTREAM.md](./MYMETAVIEW_6.0_DEMO_ENGINE_WORKSTREAM.md) — 6.0 throughput baseline
- [demo-quality-validation-2026-03-08.md](./demo-quality-validation-2026-03-08.md) — cache policy
- [AIL-203](/AIL/issues/AIL-203), [AIL-204](/AIL/issues/AIL-204), [AIL-205](/AIL/issues/AIL-205) — 6.0 structure
