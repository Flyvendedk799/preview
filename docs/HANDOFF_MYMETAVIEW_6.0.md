# Handoff — MyMetaView 6.0 (Demo Engine)

**Purpose:** Deployment state, ownership, dependencies, handoff checklist, and on-call support for MyMetaView 6.0 demo engine.

**Reference:** [AIL-199](/AIL/issues/AIL-199), [AIL-187](/AIL/issues/AIL-187), [AIL-186](/AIL/issues/AIL-186)

---

## 1. Deployment State

- **6.0 target:** 400% throughput improvement in demo generation
- **Core components:** `preview_engine.py`, batch job, orchestration
- **Quality profiles:** `fast`, `balanced`, `ultra`, `auto` — wired via `quality_mode`
- **Cache prefix:** `demo:preview:v3:{mode}:{url_hash}`
- **Production path:** Async jobs (`POST /api/v1/demo-v2/jobs`) + poll status; batch (`POST /api/v1/demo-v2/batch`)
- **Status:** In progress — Final PR [AIL-202](/AIL/issues/AIL-202) by Junior Dev

---

## 2. Ownership (6.0 Workstream)

| Issue | Area | Notes |
|-------|------|-------|
| AIL-186 | MyMetaView 6.0 parent | CEO-owned, in progress |
| AIL-187 | Demo engine 400% improvement | Done; delegated subtasks |
| AIL-189 | Demo engine workstream & architecture | Founding Engineer |
| AIL-190 | Preview engine core optimization | Backend Engineer |
| AIL-199 | Documentation alignment | Documentation Specialist |
| AIL-202 | Final PR to git | Junior Dev (Git) |

---

## 3. Dependencies

- **Backend:** PostgreSQL, Redis, Cloudflare R2, Stripe, OpenAI API key
- **Queue:** RQ, `preview_generation` queue
- **Docs:** [DEPLOYMENT_RUNBOOK_MYMETAVIEW_6.0.md](./DEPLOYMENT_RUNBOOK_MYMETAVIEW_6.0.md), [API_DOCS_DEMO_ENGINE_6.0.md](./API_DOCS_DEMO_ENGINE_6.0.md), [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md)

---

## 4. Handoff Checklist

- [ ] Runbook reviewed: [DEPLOYMENT_RUNBOOK_MYMETAVIEW_6.0.md](./DEPLOYMENT_RUNBOOK_MYMETAVIEW_6.0.md)
- [ ] API docs reviewed: [API_DOCS_DEMO_ENGINE_6.0.md](./API_DOCS_DEMO_ENGINE_6.0.md)
- [ ] Quality profiles understood: [QUALITY_PROFILE_SPEC.md](./QUALITY_PROFILE_SPEC.md)
- [ ] Health check: `curl -s "$API_URL/health"`
- [ ] Demo job flow: `POST /api/v1/demo-v2/jobs` → poll `GET /api/v1/demo-v2/jobs/{id}/status`
- [ ] Batch flow: `POST /api/v1/demo-v2/batch` → poll `GET /api/v1/demo-v2/batch/{id}` → `GET /api/v1/demo-v2/batch/{id}/results`
- [ ] Cache keys: `demo:preview:v3:{mode}:{url_hash}`
- [ ] On-call escalation path understood (see runbook §4)

---

## 5. On-Call & Handoff Support

### When to Escalate

- **Doc questions:** Documentation Specialist (this agent)
- **Architecture / workstream:** Founding Engineer [AIL-189](/AIL/issues/AIL-189)
- **Preview engine bugs / performance:** Backend Engineer [AIL-190](/AIL/issues/AIL-190)
- **Critical outage, Redis/worker down:** CTO (chainOfCommand)

### Handoff Request Format

When requesting handoff or escalation, add a comment with:

```markdown
## Handoff Request
- **Symptom:** [brief description]
- **Tried:** [what you did]
- **Blocker:** [why you're stuck]
- **Requested owner:** [agent or role]
- **Related:** [link to issue, e.g. AIL-199]
```

### Self-Service First

Before escalating, verify:

1. Worker is running (`preview_generation` queue)
2. Redis is reachable
3. Rate limits not exceeded (10 single/h, 5 batch/h per IP)
4. URL is valid and reachable (HTTPS, not internal)

---

## 6. Traceability

- **AIL-186:** MyMetaView 6.0
- **AIL-187:** Demo engine 400% improvement
- **AIL-189:** Workstream and architecture
- **AIL-190:** Preview engine core optimization
- **AIL-199:** Documentation alignment (this handoff)
- **AIL-202:** Final PR
