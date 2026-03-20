# UX Spec — Demo Flow Touchpoints (MyMetaView 6.0)

**Reference:** [AIL-196](/AIL/issues/AIL-196), [AIL-187](/AIL/issues/AIL-187) (400% demo engine)

**Purpose:** Execution-ready specifications for user journey, quality mode selection, and batch completion feedback. Aligned with 400% faster demo generation experience.

---

## 1. User Journey Map

### Current flow (5.0)
1. **Configure** — Paste URLs (one per line) → Submit
2. **Submitting** — Job creation (~0.5s)
3. **Generating** — Poll every 1.5s, progress bar + grid placeholders
4. **Results** — Success / Partial / Error with retry or edit URLs

### Target flow (6.0)

| Stage | User action | UI feedback | Duration target |
|-------|-------------|-------------|-----------------|
| **1. Configure** | Paste URLs, choose quality (new), submit | Inline validation; quality picker visible | < 3s |
| **2. Submitting** | — | Optimistic: switch to generating immediately; "Connecting…" | < 1s |
| **3. Generating** | — | Progressive grid (items appear as ready); per-URL status; estimated time hint | fast: ~2–4s/URL, balanced: ~4–8s, ultra: ~8–15s |
| **4. Results** | Review, retry failed, edit URLs, export | Clear success/partial/error; action buttons; copy/share | Instant |

**Perceived speed:** Reduce time-to-first-result by surfacing **fast** mode and progressive feedback. Users who choose speed over quality get visible results sooner.

---

## 2. Quality Mode Selection UX

### Problem
API supports `quality_mode` (fast, balanced, ultra, auto). UI uses fixed default (`balanced`). Users cannot opt into speed for simple pages.

### Spec: Quality Mode Picker

**Placement:** Inside the configure form, above the URL textarea, below the "New demo preview" header.

**Component:**
- Label: "Quality vs speed"
- Control: Segmented control or compact radio group
- Options (4):

| Value | Label | Subtext / Tooltip |
|-------|-------|--------------------|
| `fast` | Fast | ~2–4s · Best for simple pages |
| `balanced` | Balanced | ~4–8s · Default for most pages |
| `ultra` | Ultra | ~8–15s · Best quality, complex layouts |
| `auto` | Auto | System picks based on URL |

**Default:** `balanced` (keep current behavior).

**Interaction:**
- Click/tap to select; selected state uses primary (sky) accent.
- Tooltip or inline help on hover/focus for subtext.
- Disabled during `submitting` or `generating` (mode locked for that run).

**Accessibility:**
- `aria-label="Quality mode: fast, balanced, ultra, or auto"`
- Each option: `role="radio"`, `aria-checked`, keyboard nav.

**Data flow:**
- `DemoGenerationExperience` accepts optional `qualityMode` prop and `onQualityModeChange` callback.
- `DemoGenerationPage` passes through to `submitBatchJob({ qualityMode })`.
- If `onQualityModeChange` provided, parent can persist preference (e.g. localStorage).

**Wire to API:** Already supported — `quality_mode` in `POST /api/v1/demo-v2/batch` body.

---

## 3. Batch Completion Feedback

### Current
- Progress bar (0–100%, time-based simulation + real completion)
- Run summary: State, Total scenes, Ready, Needs attention
- Retry failed, Edit URLs

### Spec: Enhancements for 6.0

#### 3.1 Progressive results
- **Already implemented:** Items appear in grid as they complete (poll `/batch/{id}/pages`).
- **Enhancement:** When first item completes, show a brief toast or inline message: "First preview ready — more completing…" (dismiss after 3s or on next poll).
- **Perceived speed:** Users see value before the full batch finishes.

#### 3.2 Completion summary (expand)
- Keep: State, Total, Ready, Needs attention.
- Add: **Est. time saved** when `quality_mode === "fast"` and batch completed: e.g. "Completed in ~X s (fast mode)."
- Add: **Suggested action** for partial/error: "Retry 2 failed" (specific count) or "Edit URLs and try again."

#### 3.3 Batch completion states — copy and CTAs
- **Success:** Primary CTA: "View demo" or "Copy share link" (if export exists). Secondary: "Create another."
- **Partial:** Primary: "Retry failed". Secondary: "Edit URLs", "View successful".
- **Error:** Primary: "Edit URLs". Secondary: "Retry with same URLs" (optional).

#### 3.4 Polling optimization for 400% faster
- **Current:** 1500ms poll interval.
- **Spec:** When `quality_mode === "fast"`, reduce to 800ms during first 10s to surface early results sooner. Revert to 1500ms after 10s or when batch completes.
- **Rationale:** Fast mode yields results in 2–4s per URL; shorter poll reduces perceived latency.

---

## 4. Visual Hierarchy and Motion

### Reduce motion
- Honor `prefers-reduced-motion`. Already implemented; preserve for all new animations.

### New elements
- Quality picker: No heavy animation; instant state change.
- Completion toast: Fade in/out, 0.2s; or use `aria-live` only if prefers-reduced-motion.

---

## 5. Implementation Checklist

- [ ] Add quality mode picker to `DemoGenerationExperience` (or `DemoGenerationPage` if form lives there).
- [ ] Pass `qualityMode` from picker to `onCreateJob` / `submitBatchJob`.
- [ ] Add `pollIntervalMs` override when `qualityMode === "fast"` (e.g. 800ms for first 10s).
- [ ] Extend StatusSummary with optional "Est. time saved" and suggested-actions line.
- [ ] Add optional completion toast for first-item-ready (or defer to P2).
- [ ] Ensure `DemoGenerationPage` wires `qualityMode` from URL/state if needed for deep links.

---

## 6. Reference

- **Quality profiles:** [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md)
- **Batch API:** [API_DOCS_DEMO_ENGINE_6.0.md](./API_DOCS_DEMO_ENGINE_6.0.md) § Batch
- **Current components:** `DemoGenerationExperience.tsx`, `DemoGenerationPage.tsx`, `demo-batch-api.ts`
