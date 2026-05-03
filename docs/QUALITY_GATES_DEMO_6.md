# Quality Gates — Demo Engine 6.0

**Parent:** AIL-187 (Demo engine 400% improvement)  
**Task:** AIL-200 (Pre-push completeness review and quality gates)

## Overview

Quality gates for the MyMetaView demo engine ensure:

1. **Regression tests** — API contracts, schema validation, error handling
2. **Throughput validation** — 400% improvement measurable
3. **Schema contracts** — DemoPreviewRequest, LayoutBlueprint, URL sanitizer

## Running Quality Gates

```bash
cd <project_root>
PYTHONPATH=. python backend/scripts/run_quality_gates.py
```

Exit codes: `0` = GO, `1` = NO-GO, `2` = Cannot run (missing deps).

## 400% Improvement Target

- **Interpretation:** New demo engine must be ~5× faster than baseline (400% improvement = 5× speed).
- **Baseline:** ~60s per preview (from production sampling, e.g. futurematch.dk).
- **Target:** ≤15s per preview (`target_ms_per_preview` in baseline config).
- **Measurement:** `processing_time_ms` in demo-v2 job status response.

## Baseline Configuration

`backend/scripts/demo_throughput_baseline.json`:

| Field | Description |
|-------|-------------|
| `baseline_ms_per_preview` | Pre-6.0 average processing time (ms) |
| `target_ms_per_preview` | Max acceptable time for 400% improvement |
| `min_success_rate` | Fraction of fixture URLs that must pass |
| `fixture_urls` | URLs used for reproducible benchmarking |

## Running Throughput Benchmark (Live)

For manual validation against a deployed API:

```bash
PYTHONPATH=. python backend/scripts/benchmark_demo_throughput.py
PYTHONPATH=. python backend/scripts/benchmark_demo_throughput.py --base-url https://www.mymetaview.com
```

In CI (no live API): `DEMO_BENCHMARK_SKIP_LIVE=1` or `--dry-run` skips live calls and validates logic only.

## Gradient-only preview regression (6.5 / AIL-223)

Demo previews must include visible headline text (and typical card layout), not a bare gradient.

- **Cause (fixed):** Empty or whitespace `title` plus DOM extraction without a usable H1 caused the hero template to skip the headline block, so the composited image was background-only.
- **Mitigation:** `generate_designed_preview` and `generate_and_upload_preview_image` normalize titles to a non-empty display string; hero layout replaces empty DOM headlines; `generate_and_upload_preview_image` falls back to `_generate_fallback_preview` if no bytes are produced.
- **Logging:** Use existing `AIL-210` / `AIL-223` log lines in `preview_engine`, `preview_image_generator`, and `adaptive_template_engine` to see DNA vs classic path and fallback usage.

## Regression Test Coverage

- `test_demo_flow.py` — Demo preview schema, job output, URL validation
- `test_demo_throughput.py` — Throughput validation logic, `processing_time_ms` in responses
- `test_preview_reasoning.py` — Preview reasoning pipeline
- `test_brand_extractor.py` — Brand extraction
- `test_demo_quality_profiles.py` — Quality profiles (fast/balanced/ultra)
- `test_preview_cache_quality_policy.py` — Cache policy

## Updating Baseline

After a confirmed 400% improvement, update the baseline:

```bash
# Run benchmark, then manually edit demo_throughput_baseline.json
# Set baseline_ms_per_preview to new observed average
# Set target_ms_per_preview to desired gate threshold
```
