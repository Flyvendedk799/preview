# Deployment Runbook — MyMetaView 3.5

**Reference:** AIL-105, [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md), [DEPLOYMENT.md](../DEPLOYMENT.md)

## Overview

This runbook covers deploy, verify, and rollback for MyMetaView 3.5, including quality profiles and the 10x pipeline.

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

3. **Frontend**
   - Build: `npm ci && npm run build`
   - Output: `dist`

### 3.5-Specific

- Quality profiles: `fast`, `balanced`, `ultra`, `auto` — wired via `DemoPreviewRequest.quality_mode`
- Cache prefix: `demo:preview:v3:{mode}:{url_hash}` — see [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md)
- No extra env vars for 3.5; profiles use existing OpenAI/R2 config

---

## 2. Verify

### Health

```bash
curl -s "$API_URL/health"
```

### Demo Preview (3.5)

```bash
curl -X POST "$API_URL/demo-v2/preview" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com", "quality_mode": "ultra"}'
```

### Quality Profile Check

- **fast**: Simple URL (e.g. `https://example.com/about`) — expect ~2–4s
- **balanced**: Product URL — expect ~4–8s
- **ultra**: Complex URL (e.g. `https://stripe.com/pricing`) — expect ~8–15s
- **auto**: Omit `quality_mode` — system resolves from URL heuristics

### Logs

- Look for `get_cache_prefix_for_mode` / `quality_mode` in request logs
- Cache hits: `demo:preview:v3:ultra:...` (or fast/balanced)

---

## 3. Rollback

### Code Rollback

1. Revert to previous commit on Railway
2. Redeploy via Railway dashboard or CLI
3. Run migrations only if schema changed: `railway run alembic downgrade -1` (if needed)

### Cache Invalidation

- URL change invalidates cache automatically
- Admin toggle (if implemented) invalidates by prefix
- Manual: clear Redis keys matching `demo:preview:v3:*` if needed

### 3.5 Rollback

- Quality profiles are backward-compatible; default `ultra` matches prior behavior
- If reverting to pre-3.5: remove `quality_mode` handling from routes and use legacy cache key

---

## 4. 10x Pipeline References

- **AIL-97**: Technical architecture for 10x generation quality
- **AIL-99**: Robustness, caching, quality profiles (shipped in PR #20)
- **AIL-112**: Model + prompt upgrades (phase 2, planned follow-on)
- **QUALITY_PROFILE_SPEC.md**: Profile definitions, cache key, API

---

## Quick Reference

| Action   | Command / Check                                      |
|----------|------------------------------------------------------|
| Deploy   | Railway deploy + `alembic upgrade head`              |
| Health   | `GET /health`                                        |
| Demo     | `POST /demo-v2/preview` with `quality_mode`          |
| Cache    | `demo:preview:v3:{mode}:{url_hash}`                  |
| Rollback | Revert commit, redeploy, optional cache clear        |
