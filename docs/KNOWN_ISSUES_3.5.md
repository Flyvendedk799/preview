# Known Issues — MyMetaView 3.5

**Reference:** AIL-105, AIL-102 (feedback synthesis), AIL-100 (UX validation), AIL-101 (product design)

## 10x Mandate Context

The 3.5 release delivers robustness, caching, and quality profiles. **Measurable quality uplift** (the real 10x lever) comes from model + prompt upgrades (AIL-112, phase 2) — centralized prompts, few-shot examples, schema enforcement. That work is planned as follow-on, not in 3.5.

---

## P0 — Critical (Blockers)

| ID   | Issue                          | Status   | Notes                                      |
|------|--------------------------------|----------|--------------------------------------------|
| P0-1 | None currently                 | —        | 3.5 core path is stable                    |

---

## P1 — High (Conversion / Quality Impact)

| ID   | Issue                                      | Traceability | Notes                                                                 |
|------|--------------------------------------------|--------------|-----------------------------------------------------------------------|
| P1-1 | Modest quality gain from 3.5 alone         | AIL-111      | Null-safety, caching, profiles = correctness; no quality gain. 10x comes from AIL-112. |
| P1-2 | Ultra latency 8–15s for complex pages       | AIL-100      | By design; UX validation accepted. Consider async for long URLs.      |
| P1-3 | Auto mode heuristics may misclassify URLs  | AIL-97       | Complexity score based on path/tokens. Edge cases: manual `quality_mode` override. |

---

## P2 — Medium (Reliability / Edge Cases)

| ID   | Issue                                      | Traceability | Notes                                                                 |
|------|--------------------------------------------|--------------|-----------------------------------------------------------------------|
| P2-1 | `extracted_highlights` null-safety          | AIL-75, AIL-99 | Fixed in PR #20; `_safe_str` guards. Monitor for regressions.        |
| P2-2 | Cache key collision if URL normalization changes | AIL-99     | v3 prefix includes mode; URL hash deterministic. Document normalization rules. |
| P2-3 | Soft pass on fast/balanced can produce lower quality | AIL-97   | Intentional; strict enforcement only on ultra.                        |

---

## P3 — Low (Nice to Have)

| ID   | Issue                                      | Traceability | Notes                                                                 |
|------|--------------------------------------------|--------------|-----------------------------------------------------------------------|
| P3-1 | No admin UI for cache invalidation         | AIL-101      | Manual Redis clear or URL change. Future: admin toggle.               |
| P3-2 | Quality profile not exposed in frontend     | AIL-100      | API supports `quality_mode`; UI uses default.                         |
| P3-3 | Logs lack structured quality_mode metrics   | —            | Add to observability backlog.                                         |

---

## P4 — Informational

| ID   | Issue                                      | Notes                                                                 |
|------|--------------------------------------------|-----------------------------------------------------------------------|
| P4-1 | 7-layer enhancement system (pre-3.5)       | Separate from 3.5 quality profiles. See DEPLOYMENT_STATUS.md.         |
| P4-2 | AIL-112 model + prompt upgrades             | Planned follow-on; not a 3.5 bug.                                     |

---

## Conversion Blockers (Pre-3.5)

Resolved in 3.5:

- **AIL-75**: `extracted_highlights` null → crash. Fixed via `_safe_str` in `preview_reasoning.py`.
- **Cache key**: Quality mode not in key → wrong cache hits. Fixed via `get_cache_prefix_for_mode`.

---

## Traceability

- **AIL-102**: Feedback synthesis — P1-1, P1-2 reflect user/CTO feedback.
- **AIL-100**: UX validation — P1-2, P3-2 reflect UX constraints.
- **AIL-101**: Product design — P3-1 reflects product roadmap.
