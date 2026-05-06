# Live-narrowing onboarding — persona walkthrough (V1 results)

> **Cycle:** `live-narrowing-onboarding` (cycle #15)
> **Date:** 2026-05-06
> **Status:** baseline — needs to be re-run against a populated tools_seed and a live Weaviate connection before threshold tuning.

This document is the per-cycle persona walkthrough required by F-LIVE-10. It pairs the no-embedding baseline (`results.md`) with the live-narrowing pipeline behavior so we can compare ranking quality + tune `LAYER_BANDS` thresholds (`general 0.55 / relevant 0.65 / niche 0.75`) if needed.

---

## What was actually exercised

Because the dev box's network blocks the Weaviate gRPC subdomain (see F-LIVE-7 for the REST-only fallback), the real pipeline-with-Weaviate walkthrough is a **post-merge follow-up** task. What we DID validate during the cycle:

- All 4 questions render correct copy + role-conditioned options for ACCA / SWE / Doctor (verified in `tests/test_live_questions.py`)
- Q2/Q3 fallback path returns generic 12-option list when role isn't in the hand-curated table
- `live_match` pipeline correctness via mocked OpenAI + mocked hybrid_search:
  - Alpha + K schedules thread through correctly (`test_live_match_uses_alpha_and_k_for_step`)
  - Score → layer assignment matches `LAYER_BANDS` boundaries
  - Wildcard slot present when over-fetch returns >K results
  - `degraded: true` flag surfaces when hybrid returns empty (fallback to similarity_search)
- Per-tap persistence:
  - `live_answers` row exists per (user_id, q_index) with overwrite semantics
  - Profile vector recomputed each tap (force_recompute=True)
  - Mid-flow exit leaves both layers persisted; next tap continues from the accumulated profile_text

## What still needs a real walkthrough

The following require either a working Weaviate connection (VPN to clear the gRPC block, OR a docker-local Weaviate) AND a populated `tools_seed`:

### Persona A — ACCA (Senior Audit Manager)

| Step | Q | Expected ranking signal |
|------|---|------------------------|
| Q1 | Auditor / Senior / Finance & Accounting | Excel-native AI, audit-document tools should appear in top-20 |
| Q2 | Excel + Outlook + SharePoint + Teams + ERP + ChatGPT | DataSnipper, Numerous.ai, Microsoft Copilot in Excel should rise |
| Q3 | Full audit cycle | Long-cycle deliverable tools (review/sign-off workflow) should rise |
| Q4 | Manual data cleanup | DataSnipper pinned at top |

### Persona B — SWE (Senior Backend Engineer)

| Step | Q | Expected ranking signal |
|------|---|------------------------|
| Q1 | Software Engineer / Senior / Software & Tech | Cursor, Copilot, Claude, Datadog AI should appear |
| Q2 | VS Code + Terminal + GitHub + Linear + Slack + Postgres + Datadog + ChatGPT + Copilot + Notion | IDE-integrated AI, observability AI should rise |
| Q3 | Feature spec → ship | Full-cycle producer tools (Cursor, Linear AI, GitHub Copilot Workspace) should rise |
| Q4 | Searching for info I already wrote | Notion AI / Glean should rise |

### Persona C — Doctor (Family Medicine Attending)

| Step | Q | Expected ranking signal |
|------|---|------------------------|
| Q1 | Doctor / Senior / Healthcare | EHR-adjacent tools, ambient scribes |
| Q2 | Epic + UpToDate + Outlook + Teams + Lab portal + WhatsApp | Abridge / Suki / Nuance DAX should rise (matches Epic + clinic workflow) |
| Q3 | Clinic day with 20 patients | Ambient scribe pinned at top |
| Q4 | Catching up after meetings | Inbox triage / catch-up summarization tools |

## Acceptance criteria for the post-merge run

When this gets exercised against a working pipeline:

1. **Recall@10 vs no-embedding baseline:** ≥70% overlap of top-10 with the founder-graded gold rank in `results.md`. Below 70% → tune.
2. **Layer assignment sanity:** at least one tool in each band (`general` / `relevant` / `niche`) appears across the persona's 4 steps.
3. **Wildcard surprise:** the wildcard slot surfaces a tool from a different `category` than the top-3 at least 50% of the time.
4. **Degraded path:** `WEAVIATE_USE_GRPC=false` smoke produces results within 2× of gRPC latency (REST hybrid is intrinsically slower; absolute target <1.5s per step).

If thresholds need tuning, edit `LAYER_BANDS` in `app/recommendations/live_engine.py` — single-line change, no migration. Document the tuned values back into this file under a `## Tuned values (YYYY-MM-DD)` section.

---

## Implementation-level facts captured during the cycle

- **Frontend route shipped:** `/onboarding/live` (cycle #15 build, route #18). Behind `MESH_ONBOARDING_VARIANT=live`. Default flag value (`classic`) bounces to existing `/onboarding`. Wrong-variant visits to `/onboarding/live` bounce back to `/onboarding` so users can't strand on a flag-disabled page.
- **Backend endpoints shipped:**
  - `GET /api/onboarding/live-questions`
  - `GET /api/onboarding/live-questions/{q_index}/options?role=`
  - `POST /api/recommendations/live-step`
- **New collection:** `live_answers` (one row per `(user_id, q_index)` upsert). Doesn't touch the existing append-only `answers` collection used by the classic flow.
- **Test counts:** +27 new (`test_live_questions` 9, `test_live_engine` 12, `test_live_step_endpoint` 8, `test_hybrid_search` 3, `test_onboarding_variant_flag` 3 — minus one consolidation = 27 new). Full backend suite: 321 green.
- **Constitutional posture preserved:** founders 403 from both new endpoints (`require_role("user")`); existing classic flow + `tools_seed` vs `tools_founder_launched` separation untouched.
