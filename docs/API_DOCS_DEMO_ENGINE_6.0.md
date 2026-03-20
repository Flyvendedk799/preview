# API Docs — Demo Engine 6.0

**Reference:** [AIL-199](/AIL/issues/AIL-199), [routes_demo_optimized.py](../backend/api/v1/routes_demo_optimized.py)

**Base URL:** `https://www.mymetaview.com/api/v1` (production) or `http://localhost:8000/api/v1` (local)

**Interactive docs:** `https://www.mymetaview.com/docs` (see [NGINX_DOCS_PROXY_SETUP.md](../NGINX_DOCS_PROXY_SETUP.md))

---

## Overview

Demo engine 6.0 provides synchronous and asynchronous preview generation for URLs. Use **async jobs** for production (avoids Railway 60s timeout). Use **batch** for multi-URL workloads.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/demo-v2/preview` | POST | Sync preview (may timeout) |
| `/demo-v2/jobs` | POST | Create async job |
| `/demo-v2/jobs/{id}/status` | GET | Poll job status |
| `/demo-v2/batch` | POST | Create batch job |
| `/demo-v2/batch/{id}` | GET | Batch status |
| `/demo-v2/batch/{id}/results` | GET | Batch results |

---

## Quality Modes

| Mode | Use Case | Latency | Quality |
|------|----------|---------|---------|
| `fast` | Simple pages | ~2–4s | Good |
| `balanced` | Product/feature pages | ~4–8s | Better |
| `ultra` | Complex pages | ~8–15s | Best |
| `auto` | Resolved from URL | Varies | Varies |

See [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md) for details.

---

## Sync Preview (Single URL)

**`POST /demo-v2/preview`**

May timeout on long-running requests. Prefer async jobs for production.

### Request

```json
{
  "url": "https://stripe.com/pricing",
  "quality_mode": "ultra"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string (URL) | Yes | — | Target URL |
| `quality_mode` | `"fast"` \| `"balanced"` \| `"ultra"` \| `"auto"` | No | `"ultra"` | Quality profile |

### Response

```json
{
  "url": "https://stripe.com/pricing",
  "title": "...",
  "subtitle": "...",
  "description": "...",
  "blueprint": { "template_type": "...", "overall_quality": "...", ... },
  "composited_preview_image_url": "https://...",
  "processing_time_ms": 8200,
  "is_demo": true,
  ...
}
```

---

## Async Job (Recommended)

**`POST /demo-v2/jobs`** — Create job (returns immediately)

**`GET /demo-v2/jobs/{job_id}/status`** — Poll until `finished` or `failed`

### Create Job Request

```json
{
  "url": "https://stripe.com/pricing",
  "quality_mode": "ultra"
}
```

### Create Job Response (202 Accepted)

```json
{
  "job_id": "abc123-def456-...",
  "status": "queued",
  "message": "Preview generation started. Poll /demo-v2/jobs/{job_id}/status for updates."
}
```

### Status Response

**While running:**

```json
{
  "job_id": "abc123-def456-...",
  "status": "started",
  "result": null,
  "error": null,
  "progress": 0.3,
  "message": "Generating preview..."
}
```

**When finished:**

```json
{
  "job_id": "abc123-def456-...",
  "status": "finished",
  "result": { "url": "...", "title": "...", "composited_preview_image_url": "...", ... },
  "error": null,
  "progress": 1.0,
  "message": "Preview generation complete"
}
```

**When failed:**

```json
{
  "job_id": "abc123-def456-...",
  "status": "failed",
  "result": null,
  "error": "Error message",
  "progress": 0.0,
  "message": "Preview generation failed"
}
```

### Rate Limits

- 10 job creations per IP per hour
- Job timeout: 15 minutes

---

## Batch API

**`POST /demo-v2/batch`** — Create batch job (up to 50 URLs)

**`GET /demo-v2/batch/{batch_id}`** — Poll status

**`GET /demo-v2/batch/{batch_id}/results`** — Get results (when status is `completed` or `failed`)

### Create Batch Request

```json
{
  "urls": [
    "https://example.com",
    "https://stripe.com/pricing"
  ],
  "quality_mode": "balanced",
  "callback_url": "https://your-webhook.com/demo-complete"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `urls` | array of URLs | Yes | — | 1–50 URLs |
| `quality_mode` | `"fast"` \| `"balanced"` \| `"ultra"` | No | `"balanced"` | Quality profile |
| `callback_url` | URL | No | — | Webhook on completion (P8) |

### Create Batch Response (202 Accepted)

```json
{
  "job_id": "batch-uuid-...",
  "status": "queued",
  "total": 2,
  "message": "Batch job created. Poll /demo-v2/batch/{job_id} for status."
}
```

### Batch Status Response

```json
{
  "job_id": "batch-uuid-...",
  "status": "running",
  "total": 2,
  "completed": 1,
  "failed": 0
}
```

`status`: `queued` | `running` | `completed` | `failed`

### Batch Results Response

```json
{
  "job_id": "batch-uuid-...",
  "status": "completed",
  "total": 2,
  "completed": 2,
  "failed": 0,
  "results": [
    {
      "url": "https://example.com",
      "preview_image_url": "https://...",
      "screenshot_url": "https://...",
      "title": "...",
      "error": null
    },
    {
      "url": "https://stripe.com/pricing",
      "preview_image_url": "https://...",
      "screenshot_url": "https://...",
      "title": "...",
      "error": null
    }
  ]
}
```

### Batch Rate Limits

- 5 batch creations per IP per hour
- Batch timeout: 30 minutes

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid URL or request body |
| 404 | Job/batch not found (expired or never existed) |
| 429 | Rate limit exceeded |
| 503 | Redis/RQ temporarily unavailable |

---

## Quick Reference (cURL)

```bash
# Single async
JOB=$(curl -s -X POST https://www.mymetaview.com/api/v1/demo-v2/jobs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://stripe.com", "quality_mode": "ultra"}' | jq -r '.job_id')
curl -s "https://www.mymetaview.com/api/v1/demo-v2/jobs/$JOB/status" | jq .

# Batch
BATCH=$(curl -s -X POST https://www.mymetaview.com/api/v1/demo-v2/batch \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"], "quality_mode": "balanced"}' | jq -r '.job_id')
curl -s "https://www.mymetaview.com/api/v1/demo-v2/batch/$BATCH" | jq .
```
