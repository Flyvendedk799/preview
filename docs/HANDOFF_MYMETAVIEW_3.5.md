# Handoff — MyMetaView 3.5

**Purpose:** Deployment state, ownership, dependencies, and handoff checklist for MyMetaView 3.5.

**Reference:** AIL-105, AIL-96 (grand plan), AIL-95 (3.5 parent)

---

## 1. Deployment State

- **3.5 core:** Shipped in PR #20 — robustness, caching, quality profiles
- **Quality profiles:** `fast`, `balanced`, `ultra`, `auto` — wired via `DemoPreviewRequest.quality_mode`
- **Cache prefix:** `demo:preview:v3:{mode}:{url_hash}`
- **Status:** Production-ready; P0 blockers none; core path stable

---

## 2. Ownership (AIL-97–110)

| Issue Range | Area | Notes |
|-------------|------|-------|
| AIL-97 | Technical architecture | 10x generation quality, quality profiles design |
| AIL-99 | Robustness, caching | Shipped in PR #20; `_safe_str`, cache key per mode |
| AIL-100 | UX validation | Latency acceptance, quality_mode UI exposure |
| AIL-101 | Product design | Admin UI for cache invalidation (future) |
| AIL-102 | Feedback synthesis | User/CTO feedback reflected in known issues |
| AIL-105 | Documentation | This handoff; runbook; known issues |
| AIL-106 | Sales alignment | Technical fact sheet for sales |
| AIL-111 | Quality gain | 3.5 alone = correctness; 10x from AIL-112 |
| AIL-112 | Model + prompt upgrades | Phase 2, planned follow-on |

---

## 3. Dependencies

- **Backend:** PostgreSQL, Redis, Cloudflare R2, Stripe, OpenAI API key
- **Docs:** [DEPLOYMENT_RUNBOOK_MYMETAVIEW_3.5.md](./DEPLOYMENT_RUNBOOK_MYMETAVIEW_3.5.md), [KNOWN_ISSUES_3.5.md](./KNOWN_ISSUES_3.5.md), [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md), [SALES_ALIGNMENT_MYMETAVIEW_3.5.md](./SALES_ALIGNMENT_MYMETAVIEW_3.5.md)
- **Phase 2:** AIL-112 (model + prompt upgrades) for measurable 10x quality uplift

---

## 4. Handoff Checklist

- [ ] Runbook reviewed: [DEPLOYMENT_RUNBOOK_MYMETAVIEW_3.5.md](./DEPLOYMENT_RUNBOOK_MYMETAVIEW_3.5.md)
- [ ] Known issues reviewed: [KNOWN_ISSUES_3.5.md](./KNOWN_ISSUES_3.5.md)
- [ ] Quality profiles understood: [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md)
- [ ] Sales/customer success: [SALES_ALIGNMENT_MYMETAVIEW_3.5.md](./SALES_ALIGNMENT_MYMETAVIEW_3.5.md)
- [ ] Health check: `curl -s "$API_URL/health"`
- [ ] Demo preview: `POST /demo-v2/preview` with `quality_mode` (fast/balanced/ultra)
- [ ] Cache keys: `demo:preview:v3:{mode}:{url_hash}`

---

## 5. Traceability

- **AIL-96:** Grand plan — MyMetaView 3.5 phased milestones
- **AIL-99:** PR #20 — robustness, caching, quality profiles
- **AIL-112:** Phase 2 — model + prompt upgrades (planned)

---

## 6. Upgrade to 6.0

For MyMetaView 6.0 (demo engine 400% improvement), see:

- [HANDOFF_MYMETAVIEW_6.0.md](./HANDOFF_MYMETAVIEW_6.0.md)
- [DEPLOYMENT_RUNBOOK_MYMETAVIEW_6.0.md](./DEPLOYMENT_RUNBOOK_MYMETAVIEW_6.0.md)
- [API_DOCS_DEMO_ENGINE_6.0.md](./API_DOCS_DEMO_ENGINE_6.0.md)
