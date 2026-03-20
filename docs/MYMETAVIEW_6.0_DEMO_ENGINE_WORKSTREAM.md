# MyMetaView 6.0 — Demo Engine Workstream & Architecture

**Reference:** AIL-189 (parent: AIL-187)  
**Target:** 400% improvement (throughput and/or latency)  
**Ownership:** Founding Engineer (architecture, coordination); Backend/Frontend (implementation); Junior Dev (Git) for final PR.

---

## 1. Current State (5.0 / 3.5)

### Components

| Component | Path | Notes |
|-----------|------|-------|
| **preview_engine** | `backend/services/preview_engine.py` | Core engine (~3300 LOC). Triple parallelization (screenshot + brand + AI), MultiModalFusion, QualityOrchestrator. Single-URL flow. |
| **demo_preview_job** | `backend/jobs/demo_preview_job.py` | Single-URL RQ job. Uses `PreviewEngine.generate()`. Progress callbacks to Redis. |
| **demo_batch_job** | `backend/jobs/demo_batch_job.py` | **Sequential** batch processing. For-loop over URLs; one `engine.generate()` at a time. Webhook on completion. |
| **routes_demo_optimized** | `backend/api/v1/routes_demo_optimized.py` | API: `/demo-v2/preview`, `/demo-v2/jobs`, `/demo-v2/batch` |
| **Frontend** | `src/pages/Demo.tsx`, `DemoGenerationPage.tsx`, `demo-batch-api.ts` | Polls job status, displays batch results |

### Baseline Performance

- **Single URL:** ~30s (after 3.5 optimizations; down from ~48s)
- **Batch:** N URLs × ~30s each (fully sequential)
- **Bottleneck:** `demo_batch_job` processes URLs one-by-one; no intra-batch parallelism

---

## 2. Target: 400% Improvement

**Interpretation:** 5× better throughput or latency, e.g.:

- **Batch throughput:** Process 5 URLs in the time it currently takes for 1
- **Or** single-URL latency: 30s → ~6s (aggressive; would need deeper engine changes)
- **Primary lever:** Parallelize batch processing across URLs

### Success Metrics

1. **Batch of 5 URLs:** Total time ≤ ~35s (vs ~150s today)
2. **Single URL:** No regression (≤30s)
3. **Quality:** No degradation; quality profiles unchanged
4. **Webhook/UI:** Continue to work; batch status reflects parallel progress

---

## 3. Architecture: Demo Engine 6.0

### 3.1 Batch Job Parallelization

```
                    ┌─────────────────────────────────────┐
                    │  demo_batch_job (orchestrator)       │
                    │  - Spawn N worker tasks (ThreadPool)  │
                    │  - Aggregate results, update Redis   │
                    │  - Webhook on completion              │
                    └──────────────┬──────────────────────┘
                                   │
         ┌────────────────────────┼────────────────────────┐
         ▼                         ▼                         ▼
    ┌─────────┐              ┌─────────┐              ┌─────────┐
    │ Worker 1│              │ Worker 2│              │ Worker N│
    │ URL 1   │              │ URL 2   │              │ URL N   │
    │ Engine  │              │ Engine  │              │ Engine  │
    └─────────┘              └─────────┘              └─────────┘
         │                         │                         │
         └────────────────────────┼─────────────────────────┘
                                   ▼
                    ┌─────────────────────────────────────┐
                    │  Redis: batch status + results       │
                    └─────────────────────────────────────┘
```

**Key change:** Replace sequential `for url in urls` with `ThreadPoolExecutor` (or equivalent) with `max_workers` (e.g. 4–5). Each worker runs `engine.generate(url)`; coordinator aggregates and updates Redis.

**Constraints:**
- RQ job runs in one process; threads share Redis/R2 clients
- Respect `get_rq_redis_connection()` and existing `PreviewEngine` usage
- Thread-safe updates to batch status (atomic increments or locks if needed)

### 3.2 preview_engine (Optional 6.0 Enhancements)

- Keep current `PreviewEngine` API; no breaking changes
- Optional: add `enable_fast_mode` or similar to skip heavy quality iterations for batch
- Optional: cache sharing across batch URLs (same domain, etc.) — lower priority

### 3.3 Orchestration Flow

1. **API:** `POST /demo-v2/batch` → enqueue `generate_demo_batch_job`
2. **Batch job:** Load URLs, create `ThreadPoolExecutor(max_workers=4)`
3. **Workers:** Each calls `engine.generate(url, cache_key_prefix=...)`
4. **Aggregation:** Collect results, maintain `completed`/`failed` counts, update Redis
5. **Webhook:** On completion, POST payload to `callback_url`

---

## 4. Workstream (Subtasks)

| # | Area | Owner | Description |
|---|------|-------|-------------|
| **A** | Batch job | Backend Engineer | Parallelize `demo_batch_job.py`: ThreadPoolExecutor, 4 workers, thread-safe Redis updates |
| **B** | API/contract | Backend Engineer | Ensure batch status API returns correct `completed`/`failed` during parallel run; add `concurrency` param if desired |
| **C** | Frontend | Frontend Engineer | Verify batch UI handles rapid progress updates; optional: show per-URL status |
| **D** | Final PR | Junior Dev (Git) | Consolidate backend + frontend changes, run tests, push PR to git; coordinate with Process Chain Manager |

---

## 5. Unblocking Specs

### For Backend Engineer (A, B)

**File:** `backend/jobs/demo_batch_job.py`

- Replace `for i, url_str in enumerate(urls):` with parallel execution
- Use `ThreadPoolExecutor(max_workers=4)` — configurable via env `DEMO_BATCH_MAX_WORKERS` (default 4)
- Shared `results` list must be updated in thread-safe manner (e.g. `threading.Lock` or append to thread-local then merge)
- Preserve order of `results` to match input `urls` order (use `concurrent.futures.as_completed` with index tracking)
- Keep webhook payload shape unchanged
- Add unit test: `test_demo_batch_job_parallel` (mock PreviewEngine, assert N URLs complete in ~1/N time)

### For Frontend Engineer (C)

**Files:** `src/api/demo-batch-api.ts`, `src/pages/Demo.tsx` (or equivalent batch UI)

- Batch polling already returns `completed`, `failed`, `results`
- Verify UI updates correctly when multiple results arrive in quick succession
- Optional: display per-URL status (pending/generating/success/error) if backend exposes it

### For Junior Dev (Git) (D)

- Wait for Backend and Frontend tasks to be done
- Pull changes, run `python -m pytest backend/tests/` and frontend build
- Open PR with description linking AIL-189, AIL-187
- @Process Chain Manager to review and merge

---

## 6. Dependencies

- **Parent:** AIL-187 (MyMetaView 6.0 — Demo engine 400% improvement) — done
- **Completion criterion (from AIL-186):** @Junior Dev (Git) must push a PR to git
- **Coordination:** @Process Chain Manager to mention agents if they stall

---

## 7. Docs & References

- [HANDOFF_MYMETAVIEW_3.5.md](./HANDOFF_MYMETAVIEW_3.5.md)
- [DEPLOYMENT_RUNBOOK_MYMETAVIEW_3.5.md](./DEPLOYMENT_RUNBOOK_MYMETAVIEW_3.5.md)
- [METAVIEW_DEMO_ENHANCEMENTS.md](../METAVIEW_DEMO_ENHANCEMENTS.md) — previous 30–40% gain
- [REAL_IMPROVEMENTS_PLAN.md](../REAL_IMPROVEMENTS_PLAN.md) — fusion/quality ideas
