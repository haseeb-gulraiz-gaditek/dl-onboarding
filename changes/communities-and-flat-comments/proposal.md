# Proposal: communities-and-flat-comments

## Problem

Mesh is a two-sided platform. Cycles #1–#6 built the user-side intake (auth, questions, profiles, embeddings, fast match, recommendation engine). The constitutional persona Maya doesn't just want recommendations — she wants to *live somewhere* on Mesh. Cycle #5's onboarding match and cycle #6's weekly concierge tell her *what* to use; communities tell her *who* uses it like she does.

Without communities, Mesh is a recommender — and recommenders are commodity. The principle "communities feel like users live there" is the moat.

Cycle #7 ships the structural shell: communities, posts, flat comments, voting. No frontend; that lives in the parallel React track. No threading (V1.5+). No moderation queue (flag bit only). No karma gates (V1.5+). The constitutional invariant "Never let founder accounts post in user communities" is enforced structurally via `require_role("user")` on every write endpoint.

This cycle also lays the schema cycle #8 (founder-launch-submission-and-verification) and cycle #9 (launch-publish-and-concierge-nudge) build on. A launch in #8 produces a post here via `attached_launch_id`.

## Solution

Six new MongoDB collections + nine endpoints, all behind the constitutional role split.

**Collections:**
- `communities` — Mesh-staff-spawned, slug-keyed.
- `community_memberships` — user_id × community_id with `joined_via`.
- `posts` — single canonical row with `community_id` (home) + `cross_posted_to: [community_id]` (≤2 extras, total ≤3 communities).
- `comments` — flat (parent_comment_id reserved but ignored in V1).
- `votes` — `target_type ∈ {post, comment, tool}`, `direction ∈ {1, -1}`. Unique per (user, target).
- (`tools_seed` gets a denormalized `vote_score` updated on tool-vote write — see F-COM-7.)

**Endpoints (all `/api/...`):**
- `GET /api/communities` — list active.
- `GET /api/communities/{slug}` — details.
- `GET /api/communities/{slug}/posts` — newest first.
- `POST /api/posts` — create post + optional cross-post.
- `GET /api/posts/{id}` — post + comments inline.
- `POST /api/comments` — flat comment.
- `POST /api/votes` — vote on post / comment / tool. Re-vote on same target with opposite direction = toggle off; same direction = no-op.
- `POST /api/communities/{slug}/join` and `.../leave`.

**Constraints (constitutional):**
- All write endpoints behind `require_role("user")`. Founders → 403.
- All reads open to authenticated users (founders included — they can browse).
- 10 hand-authored seed communities (names + slugs + descriptions); loaded by `python -m app.seed communities`, idempotent.

## Scope

**In:**
- 6 collections with indexes.
- 9 endpoints.
- Founder-write-block (constitutional invariant).
- Vote semantics: idempotent insert, toggle-on-resubmit, denormalized `vote_score` on the target.
- `cross_posted_to` validated: ≤2 extras, distinct from home, all communities exist.
- Tool-vote write updates `tools_seed.vote_score` (likes count on product page).
- 10 hand-authored seed communities + idempotent seed CLI.
- Test suite covering all 9 endpoints + role gating + vote toggle + cross-post limits.

**Out:**
- Threading (parent_comment_id stored as null, ignored).
- HN/hot ranking, gravity, sort params (newest-first only).
- Moderation queue / admin tools (flag bit stored only; no admin UI).
- Karma gates per community (schema reserved; not enforced in V1).
- Edit / delete posts or comments (V1.5).
- User-created communities (Mesh-staff-only).
- `kind=launch` post creation flow — that's cycle #8. The `attached_launch_id` field exists; nothing populates it in #7.
- `kind=tool_review` posts (dropped per cycle decision; tool voting covers the use case).
- Notifications fanout on reply / vote (cycle #11+).
- Frontend / React feed page (parallel Claude Design track).

## Risks

1. **Cross-post vote integrity.** A canonical post visible in 3 communities means one vote tally, not three. Trade-off accepted: ranking integrity > per-community vote signal. Documented in spec.
2. **Founder write-block breadth.** Easy to forget the role-gate on a new write endpoint and silently let a founder comment. Mitigation: every write endpoint added in this cycle has an explicit founder-403 test.
3. **Seed migration.** The seed CLI uses upsert-by-slug like cycle #3; new communities added later via the same CLI. No risk of clobbering user-side membership rows since memberships reference community_id, not slug.
4. **`vote_score` denormalization drift.** A future cycle that bulk-deletes votes (mod tools, V1.5) must reconcile `vote_score` on targets. Documented as a known wart in the spec.
5. **`attached_launch_id` orphan window.** Cycle #7 adds the field; #8 wires creation. Between now and #8 ship, the field is always null. Acceptable — it's a forward-compatible schema hook.
