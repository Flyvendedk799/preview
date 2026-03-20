# Deployment Runbook — MyMetaView 6.0 (Demo Engine)

**Reference:** [AIL-199](/AIL/issues/AIL-199), [AIL-187](/AIL/issues/AIL-187), [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md), [DEPLOYMENT.md](../DEPLOYMENT.md)

## Overview

This runbook covers deploy, verify, and rollback for MyMetaView 6.0 demo engine. Version 6.0 targets **400% throughput improvement** in demo generation via preview engine optimization, parallelization, caching, and early exits.

---

## 1. Deploy

### Prerequisites

- Railway account, PostgreSQL, Redis, Cloudflare R2, Stripe, OpenAI API key
- See [DEPLOYMENT.md](../DEPLOYMENT.md) for full env var list

### Deploy Steps

1. **Backend**
   - Build: `pip install -r backend/requirements.txt`
   - Start: `gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 2 --timeout 120 backend.main:app`
   - Run migrations: `railway run alembic upgrade head`

2. **Worker**
   - Start: `python -m backend.queue.worker`
   - Queue: `preview_generation` (RQ)

3. **Frontend**
   - Build: `npm ci && npm run build`
   - Output: `dist`

### 6.0-Specific

- **Preview engine:** `backend/services/preview_engine.py` — 400% optimization target (parallelization, caching, early exits)
- **Batch job:** `backend/jobs/demo_batch_job.py` — multi-URL async generation
- **Quality profiles:** `fast`, `balanced`, `ultra`, `auto` — wired via `quality_mode`
- **Cache prefix:** `demo:preview:v3:{mode}:{url_hash}` — see [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md)

---

## 2. Verify

### Health

```bash
curl -s "$API_URL/health"
```

### Demo Preview (Single URL)

```bash
# Sync (may timeout on Railway 60s limit)
curl -X POST "$API_URL/api/v1/demo-v2/preview" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com", "quality_mode": "ultra"}'

# Async (recommended production path)
JOB=$(curl -s -X POST "$API_URL/api/v1/demo-v2/jobs" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com", "quality_mode": "ultra"}' | jq -r '.job_id')
curl -s "$API_URL/api/v1/demo-v2/jobs/$JOB/status" | jq .
```

### Batch Demo

```bash
BATCH=$(curl -s -X POST "$API_URL/api/v1/demo-v2/batch" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com", "https://stripe.com"], "quality_mode": "balanced"}' | jq -r '.job_id')
curl -s "$API_URL/api/v1/demo-v2/batch/$BATCH" | jq .
```

### Quality Profile Check

- **fast**: Simple URL — expect ~2–4s
- **balanced**: Product URL — expect ~4–8s
- **ultra**: Complex URL — expect ~8–15s
- **auto**: Omit `quality_mode` — system resolves from URL heuristics

### Logs

- Look for `get_cache_prefix_for_mode` / `quality_mode` in request logs
- Cache hits: `demo:preview:v3:ultra:...` (or fast/balanced)
- Worker: `preview_generation` queue processing

---

## 3. Rollback

### Code Rollback

1. Revert to previous commit on Railway
2. Redeploy via Railway dashboard or CLI
3. Run migrations only if schema changed: `railway run alembic downgrade -1` (if needed)

### Cache Invalidation

- URL change invalidates cache automatically
- Manual: clear Redis keys matching `demo:preview:v3:*` if needed
- Per-mode prefixes: `demo:preview:v3:fast:`, `demo:preview:v3:balanced:`, `demo:preview:v3:ultra:`

### 6.0 Rollback

- Quality profiles are backward-compatible
- If reverting to pre-6.0: ensure worker queue and batch endpoints are compatible

---

## 4. On-Call & Incident Response

### Primary Contacts

| Role | Escalation | Notes |
|------|------------|-------|
| Documentation Specialist | First responder for doc/runbook questions | [AIL-199](/AIL/issues/AIL-199) |
| Founding Engineer | Demo engine architecture, workstream | [AIL-189](/AIL/issues/AIL-189) |
| Backend Engineer | Preview engine core, performance | [AIL-190](/AIL/issues/AIL-190) |
| CTO | Escalation for critical outages | chainOfCommand |

### Common Issues

| Symptom | Check | Action |
|---------|-------|--------|
| Jobs stuck in `queued` | Redis/RQ worker up? | Restart worker; verify `preview_generation` queue |
| 503 on job create | Redis connection | Verify Railway Redis env vars, connection string |
| Slow previews | Quality mode, cache | Use `fast` for simple URLs; verify cache hits |
| 429 Rate limit | Client IP limits | Single: 10/hour; Batch: 5/hour — wait or escalate |
| Batch timeout | 30m job timeout | Check worker logs; split into smaller batches |

### Handoff Procedure

When escalating or handing off:

1. Update issue with current state and blocker
2. Add comment with: symptom, what you tried, next owner
3. Reassign to appropriate agent via Paperclip
4. Link related issues (e.g. [AIL-187](/AIL/issues/AIL-187))

---

## Quick Reference

| Action   | Command / Check                                      |
|----------|------------------------------------------------------|
| Deploy   | Railway deploy + `alembic upgrade head`              |
| Health   | `GET /health`                                        |
| Demo job | `POST /api/v1/demo-v2/jobs` with `quality_mode`      |
| Job status | `GET /api/v1/demo-v2/jobs/{id}/status`            |
| Batch    | `POST /api/v1/demo-v2/batch`                         |
| Cache    | `demo:preview:v3:{mode}:{url_hash}`                  |
| Rollback | Revert commit, redeploy, optional cache clear        |

---

## Traceability

- **AIL-186:** MyMetaView 6.0 parent
- **AIL-187:** Demo engine 400% improvement
- **AIL-189:** Demo engine workstream and architecture
- **AIL-190:** Preview engine core optimization
- **AIL-199:** Documentation alignment
- **AIL-202:** Final PR (Junior Dev Git)
