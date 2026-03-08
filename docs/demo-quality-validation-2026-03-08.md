# Demo Generation Quality Validation (2026-03-08)

## Scope
Issue: `AIL-3`  
Area: `/api/v1/demo-v2/jobs` and unified preview engine cache policy.

## Root Causes Identified
1. Low-quality/fallback outputs were cacheable and reusable.
2. Cache invalidation did not include `demo:preview:v3:{quality_mode}:*` key prefixes (`fast`, `balanced`, `ultra`), so stale v3 results could survive regeneration attempts.

## Changes Implemented
1. Added strict cache eligibility policy in `PreviewEngine`:
   - Reject cache read/write for fallback outputs (`quality_scores.is_fallback`).
   - Reject cache read/write when debug final decision is `fallback` or `below_target_pass`.
   - In strict quality mode (`enforce_target_quality=True`), require cached metrics to meet configured thresholds (`overall`, `design_fidelity`, optional `visual`).
2. Expanded URL-level invalidation prefixes:
   - `demo:preview:v3:fast:`
   - `demo:preview:v3:balanced:`
   - `demo:preview:v3:ultra:`

## Before vs After
Before:
- A weak/fallback preview could be cached and repeatedly served for the same URL.
- Toggling cache disable/invalidate could miss v3-quality-mode keys, preserving stale results.

After:
- Fallback/below-target results are never persisted to cache and are not served from cache.
- Invalidation now clears all active v3 quality-mode cache namespaces for the URL.

## Measurable Quality Criteria
1. `CacheFallbackReuseRate = 0` for v3 demo generation (fallback results are ineligible for cache read/write).
2. `InvalidateCoverage = 3/3` for v3 mode prefixes (`fast`, `balanced`, `ultra`) per URL invalidation call.
3. In strict mode, cached results must satisfy:
   - `overall >= quality_threshold`
   - `design_fidelity >= min_soft_pass_fidelity`
   - `visual >= min_soft_pass_visual` when visual threshold is enabled

## Validation Status
- Code-level validation: completed via targeted unit tests added in `backend/tests/test_preview_cache_quality_policy.py`.
- Runtime test execution: blocked in this environment (`pytest` missing in virtualenv).
