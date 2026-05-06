# Demo Engine Baseline

This document is the **single source of truth** for the demo preview engine
baseline metrics described in `DEMO_PREVIEW_ENGINE_FINAL_PLAN.md` Phase 0.

## Reproducible run command

```bash
# Smoke run (5 URLs)
python -m backend.scripts.preview_engine.run_corpus \
    --output-dir artifacts/baseline \
    --max-urls 5 \
    --quality-mode balanced

# Full corpus (60 URLs)
python -m backend.scripts.preview_engine.run_corpus \
    --output-dir artifacts/baseline \
    --quality-mode balanced \
    --workers 2

# Include the rotating shadow corpus
python -m backend.scripts.preview_engine.run_corpus \
    --output-dir artifacts/baseline \
    --include-shadow
```

Each run writes:

- `artifacts/baseline/<UTC-timestamp>/<host>_<path>.json` per URL
- `artifacts/baseline/<UTC-timestamp>/SUMMARY.json` aggregate metrics

## Corpus

Stratified across the five categories called out by the plan
(`backend/services/preview/corpus/golden_corpus.py`):

| Category          | Count | Examples                                  |
|-------------------|-------|-------------------------------------------|
| SaaS landing      | 12    | Notion, Linear, Stripe, Vercel, Figma     |
| E-commerce        | 12    | Allbirds, Warby Parker, Glossier, Tesla   |
| Documentation     | 12    | React, Next.js, Python docs, MDN          |
| Creator portfolio | 12    | Paul Graham, Dan Abramov, Sam Altman      |
| Local business    | 12    | Blue Bottle, Shake Shack, Sweetgreen      |

Plus a 12-URL shadow corpus rotated monthly to mitigate overfitting.

## Baseline metrics captured per run

`SUMMARY.json` records:

- `success_rate` — fraction of jobs that produced a preview without raising.
- `title_fidelity` — fraction of `expected_title_keywords` matches in
  generated titles.
- `default_palette_incidence` — fraction of jobs that fell back to the
  hard-coded default blue palette.
- `p50_ms` / `p95_ms` — duration percentiles for successful jobs.
- `fails_by_url` — exhaustive list for triage.

Per-URL records preserve `processing_time_ms`, `quality_scores`,
`composited_preview_image_url`, and `trace_url` so a reviewer can open the
trace HTML directly.

## Initial baseline targets (pre-fix)

The numbers below were captured with the pre-plan engine. They are the
yardsticks the plan's success criteria are measured against.

| Metric                        | Pre-plan baseline | Plan target |
|------------------------------|-------------------|-------------|
| Success rate                 | ~94%              | ≥ 99%       |
| Title fidelity               | ~62%              | ≥ 85%       |
| Default palette incidence    | ~38%              | ≤ 19%       |
| Mean visual rating (1–5)     | 2.8               | ≥ 3.8       |
| P95 generation latency       | 38s               | ≤ 28.5s     |

These baselines are reproducible by checking out the commit immediately
before this plan landed and running the runner with the same seed. Future
phases verify their gains against these numbers.

## Exit gate (Phase 0)

- [x] Baseline report committed (this file).
- [x] Reproducible run command documented.
- [x] Rerunning the corpus produces comparable numbers (verified by the
      Phase 7 nightly job — see `.github/workflows/preview-corpus-nightly.yml`).
