# Proposal: recommendation-engine

## Problem

Cycle #5 delivered the **fast, search-only** match endpoint that fires after every tap during onboarding. This cycle delivers its companion: the **slow, smart, LLM-ranked** recommendation endpoint that fires once at end-of-onboarding (count=5) and periodically thereafter (count=3 default for weekly check-ins).

Without it, the user-side product can show "here are 5 candidate tools" but cannot say *"here's why each fits **you**, in your words."* The constitutional principle *"Recommend honestly, including 'skip this'"* depends on this endpoint — it's where the LLM ranker can return some candidates tagged `verdict: "skip"` with reasoning explaining the misfit. That's the moment Mesh stops being a search engine and starts being a concierge.

## Solution

A single synchronous endpoint, `POST /api/recommendations`, behind `Depends(require_role("user"))`. Two-step pipeline:

1. **Candidate retrieval** — call `ensure_profile_embedding(user)` (cycle #4), then `similarity_search` with `top_k=20` against the `ToolEmbedding` Weaviate class. No LLM cost.
2. **Rank + reason** — single call to OpenAI `gpt-5` with profile + recent answers + 20 candidates. Returns up to 5 picks with `verdict` (`"try"` or `"skip"`) and personalized `reasoning` text per pick. Uses the OpenAI SDK's structured-output (`beta.chat.completions.parse`) so output shape is enforced, not parsed-from-string.

Results are cached in a new `recommendations` collection per user. Cache hit when `cache_expires_at > now` AND `profile.last_invalidated_at <= generated_at` (cycle #2's invalidation contract). Always cache up to 5 picks; serve `count` requested as the first N of the cached array.

The clarifier step from the original system_design (a third LLM call to extract structured intent before retrieval) is **deferred to V1.5+**. For V1, raw profile embedding → vector search → LLM ranker is enough quality with one fewer round-trip.

## Scope

**In:**
- `recommendations` MongoDB collection: `{user_id, picks[], generated_at, cache_expires_at}`. Unique index on `user_id`.
- `app/db/recommendations.py` collection access layer (read, upsert, invalidation check)
- `app/models/recommendation.py` — `Verdict` literal, `RecommendationPick`, `RecommendationsResponse`, plus the OpenAI structured-output schema model
- `app/recommendations/__init__.py`, `app/recommendations/ranker.py` (single OpenAI call with `gpt-5`), `app/recommendations/engine.py` (orchestrator: cache check → similarity_search → ranker → cache write)
- `POST /api/recommendations` endpoint with optional `{count?: int}` body (default 3, clamped 1–5)
- `MIN_ANSWERS_FOR_RECS = 3` gate: `<3` answers returns `400 no_profile_yet`
- Tests covering all paths (cache hit, cache miss, cache invalidation, count clamping, empty profile, founder rejection, OpenAI failure)
- Conftest helper `mock_openai_chat` autouse fixture that monkey-patches the ranker call so tests run offline without OpenAI billing

**Out (deferred):**
- LLM clarifier step (third pipeline stage to extract structured intent before retrieval) — V1.5+
- BM25 + vector hybrid retrieval — cycle #4 spec already deferred this; pure vector remains
- Celery / async background generation — V1.5+; V1 is synchronous (~1.5–2s per fresh call)
- "Why we skipped X" deep narrative + per-rec links to user's specific answer that drove the pick — V1.5+ once reasoning quality is observed in real cohort
- Email / push delivery of weekly recs — V1.5+; V1 only serves on demand

## Alternatives Considered

1. **Three-stage pipeline (clarifier + retrieval + ranker)** — original system_design plan. Rejected for V1 to keep latency under ~2s and to ship today. The ranker has enough context (profile + last 10 answers + 20 candidates) to produce strong reasoning without a separate clarifier step. V1.5+ can add it as an optional pre-step when we observe quality is bottlenecked by retrieval breadth.
2. **Two endpoints (`/api/recommendations/starter` count=5, `/api/recommendations/weekly` count=3)** — rejected per user call. Single endpoint with `count` param keeps the API surface tight; cadence decision lives in the frontend.
3. **Anthropic Claude `claude-sonnet-4-6`** — rejected per user call. OpenAI `gpt-5` reuses the existing `OPENAI_API_KEY`; one fewer env var, one fewer SDK to maintain. If quality isn't sufficient, a swap to Claude is one constant in `ranker.py`.
4. **Cache the response by `(user_id, count)` tuple** — rejected. Always generate 5; serve count requested as the first N. Saves a cache slot and ensures consistency: top-3 of top-5 IS top-3.
5. **Embed verdict cues in reasoning text and skip the structured field** — rejected. The principle *"Recommend honestly, including skip-this"* is constitutional; the `verdict` field surfaces it as data, not text-parsing. Frontend can render skip-tagged recs differently with no string searching.

## Risks

1. **Cost overrun.** GPT-5 ranker call: ~2K input + 500 output tokens = ~$0.01–0.03 per fresh recommendation. 7-day caching bounds spend at ~$0.03/user/week. Mitigation: hard cache TTL; a single user spamming the endpoint can't generate more than 1 fresh result per profile-mutation. Cost cap monitor is V1.5+.
2. **GPT-5 hallucinating tool slugs.** The ranker is asked to return slugs that exist in the candidate set. Mitigation: server-side validation — any returned slug not in the input candidate set is dropped from the response. If the LLM returns 0 valid picks, fall back to the top-N candidates with stub reasoning ("LLM ranker unavailable; showing similarity-ordered defaults").
3. **OpenAI API timeout / 5xx mid-call.** Synchronous endpoint means caller waits. Mitigation: 30-second timeout on the SDK call; on failure, return a degraded response — top-N candidates from `similarity_search` with stub reasoning per item, response includes a `degraded: true` flag (or just `verdict: "try"` + generic reasoning).
4. **Cache invalidation drift.** If `last_invalidated_at` is bumped without the rec actually going stale (e.g., user toggles a single answer back), the rec is regenerated unnecessarily. Mitigation: acceptable for V1 — false-positive cache invalidation is a wasted $0.03; false-negative would be a stale rec, which is worse.
5. **Reasoning text in non-English.** GPT-5 may produce reasoning in the user's profile language even if catalog is English. V1 ships English-only; reasoning is forced to English via the system prompt. Multi-language is V1.5+.

## Rollback

- Drop the `recommendations` collection.
- Remove `app/recommendations/`, `app/api/recommendations.py`, `app/db/recommendations.py`, `app/models/recommendation.py`.
- Unmount the router in `app/main.py`.
- Revert this cycle's commits.

No downstream cycle depends on this endpoint. Rollback cost is bounded.
