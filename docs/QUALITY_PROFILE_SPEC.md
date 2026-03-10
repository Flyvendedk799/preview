# Quality Profile Spec — MyMetaView 3.5

**Reference:** AIL-97, AIL-99, `agents/coo/EXECUTION_PLAN_MYMETAVIEW_3.5.md` §4

## Overview

Demo preview generation supports three quality profiles plus an `auto` mode that selects based on URL complexity.

| Profile | Use Case | Latency | Quality | Cost |
|---------|----------|---------|---------|------|
| **fast** | Simple pages, low complexity | ~2–4s | Good | Low |
| **balanced** | Medium complexity, product/feature pages | ~4–8s | Better | Medium |
| **ultra** | Complex pages, pricing/enterprise/docs | ~8–15s | Best | High |
| **auto** | Resolved from URL heuristics | Varies | Varies | Varies |

## Behavior by Profile

### fast

- **Multi-agent:** No
- **UI element extraction:** No
- **Quality threshold:** 0.78
- **Max iterations:** 2
- **Soft pass:** Allowed (min 0.66 overall, 0.52 visual, 0.50 fidelity)
- **Target quality enforcement:** No

Best for: landing pages, about pages, simple blogs.

### balanced

- **Multi-agent:** Yes
- **UI element extraction:** Yes
- **Quality threshold:** 0.82
- **Max iterations:** 3
- **Soft pass:** Allowed (min 0.74 overall, 0.62 visual, 0.60 fidelity)
- **Target quality enforcement:** No

Best for: product pages, feature pages, service pages.

### ultra

- **Multi-agent:** Yes
- **UI element extraction:** Yes
- **Quality threshold:** 0.88
- **Max iterations:** 4
- **Soft pass:** Not allowed
- **Target quality enforcement:** Yes (min 0.85 overall, 0.75 visual, 0.72 fidelity)

Best for: pricing, enterprise, docs, comparison pages, complex layouts.

### auto

Resolves to fast/balanced/ultra based on URL complexity heuristics:

- Path depth, query params, fragment
- High-complexity tokens: pricing, features, product, solutions, platform, integrations, compare, enterprise, developer, docs, blog, case-study, customers
- Medium-complexity tokens: about, services, category, search

**Complexity score ≥ 8** → ultra  
**Complexity score ≥ 4** → balanced  
**Otherwise** → fast

## Cache Key

Cache key format: `demo:preview:v3:{resolved_mode}:{url_hash}`

- URL normalized for deterministic hashing
- TTL: 24 hours (configurable)
- Invalidation: URL change or admin toggle

## API

- **Sync:** `POST /demo-v2/preview` — `DemoPreviewRequest` accepts `quality_mode` (default: `ultra`)
- **Async:** `POST /demo-v2/jobs` — `DemoJobRequest` accepts `quality_mode` (default: `ultra`)

## Implementation

- `backend/services/demo_quality_profiles.py` — profile definitions, `resolve_quality_mode`, `get_cache_prefix_for_mode`
- `backend/api/v1/routes_demo_optimized.py` — uses `get_quality_profile` and `get_cache_prefix_for_mode`
- `backend/jobs/demo_preview_job.py` — uses `quality_mode` in cache key prefix
