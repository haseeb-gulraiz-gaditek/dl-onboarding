# Mesh — System Design (v0.1)

> Source: implements `basic_idea.md` v0.2. Read that first for the product thesis. This doc is the architecture-level companion — what gets built, in what shape, with what dependencies.

## Overview

Mesh V1 is a single web app (mobile-responsive) where laypeople take a tap-to-answer questionnaire that builds a living profile, get 2–3 personalized AI-tool recommendations per week, and live in Reddit-style niche communities. Founders submit lightweight-verified launches that surface (a) as posts in matched communities and (b) as private concierge nudges to the tightest-fit subset of users. V1 is free for founders; tracking is redirect-only; pricing is deferred.

## Tech stack (locked)

| Layer | Choice |
|---|---|
| Backend | **FastAPI (Python)** |
| Database | **MongoDB** (single DB, monolithic schema) |
| Vector DB | **Weaviate** (separate service, not co-located in Mongo) |
| Frontend | **React** (web, mobile-responsive) |
| Auth | **Custom Python email + password** (JWT/session, bcrypt, password reset) |
| LLM | **Anthropic Claude** — Sonnet for reasoning-heavy steps, Haiku for high-volume cheap calls |
| Async / queues | **Celery + Redis** |
| Architecture | **Monolith** (single FastAPI app, single Mongo, single React build) |
| Deployment | TBD (user to specify) |

================================================================================

## Data model — MongoDB collections

### `users`
- `_id`, `email`, `password_hash`, `created_at`, `last_active_at`
- `role_type`: `user` | `founder` (non-transferable; one account = one role)
- `display_name`, `avatar_url`
- `invite_tree`: `{invited_by_user_id, invite_code_used, depth}` — public, used for anti-spam
- `email_verified`, `verification_token`, `password_reset_token`

### `profiles` (one per user-role account)
- `_id`, `user_id` (ref)
- `role` (e.g., "growth-marketer", "solo-founder", "designer", "ops") — auto-detected from first answers
- `current_tools`: `[{tool_id, source: "self_reported"|"oauth_verified", added_at}]`
- `workflows`: `[{description, frequency, friction_score, captured_at}]`
- `tools_tried_bounced`: `[{tool_id, reason, captured_at}]`
- `counterfactual_wishes`: `[{description, captured_at}]` — "I wish a tool existed that did X"
- `budget_tier`: enum (none, indie, sub-$100/mo, sub-$1k/mo, enterprise)
- `embedding_vector_id`: foreign reference into Weaviate (the actual vector lives there)
- `last_recompute_at`, `last_invalidated_at`
- `exportable: true` — locked: users own and can export this whole document

### `questions` (the questionnaire bank)
- `_id`, `key` (stable identifier), `text`, `kind`: `single_select` | `multi_select` | `free_text`
- `options`: `[{value, label}]` (empty for free-text)
- `next_logic`: branching rule (which question fires next based on answer)
- `is_core`: bool — core questions are always asked; non-core triggered by LLM follow-up logic
- `category`: `role` | `stack` | `workflow` | `friction` | `wishlist` | `budget`
- `version`, `active`

### `answers`
- `_id`, `user_id`, `question_id`, `value` (string or array), `is_typed_other`, `captured_at`
- Append-only — answer history is the audit trail for profile evolution.

### `tools` (the catalog + founder-launched products)
- `_id`, `slug`, `name`, `tagline`, `description`, `url`, `pricing_summary`, `categories: []`, `integrations: []`
- `embedding_vector_id`: Weaviate ref
- `source`: `taaft` | `producthunt` | `futuretools` | `manual` | `founder_launch`
- `curation_status`: `pending` | `approved` | `rejected`
- `last_reviewed_at`, `reviewed_by`
- `metadata`: pricing, last-changelog-seen, sentiment-summary (for V1.5 enrichment)
- **Product-page fields** (used when canonical product page renders at `/p/:slug`):
  - `like_count` (denormalized; source of truth = `votes` with `target_type=tool`)
  - `review_count` (denormalized; source of truth = `posts` with `kind=tool_review` and `tool_id=this`)
  - `is_founder_launched`: bool — if true, additionally renders launch metadata + founder link on the product page
  - `launched_via_id`: ref to `launches._id` if founder-launched

### `recommendations`
- `_id`, `user_id`, `tool_id`, `score`, `reasoning` (LLM-generated string), `generated_at`
- `cache_expires_at` (7 days from generation, per locked rec-engine policy)
- `surface_type`: `concierge` | `community_post`
- `user_action`: `null` | `tell_me_more` | `skip` | `clicked_through`
- `action_at`

### `communities`
- `_id`, `slug`, `name`, `description`, `category`, `created_at`
- `mod_user_ids`: `[]` (V1: Mesh-staff; community-elected mods deferred)
- `member_count`, `is_active`
- `formed_by`: `manual` (V1) | `concierge_cluster` (V1.5+)

### `community_memberships`
- `_id`, `user_id`, `community_id`, `joined_at`, `joined_via`: `signup_pick` | `concierge_suggestion` | `manual`

### `user_tools` (My Tools page backing collection)
- `_id`, `user_id`, `tool_id`
- `source`: `auto_from_profile` | `explicit_save` | `manual_add`
- `status`: `using` (default for `auto_from_profile`) | `saved` (for `explicit_save`) | `tried_bounced` | `want_to_try` — V1 only sets `using` and `saved`; finer status is V1.5
- `added_at`, `last_updated_at`
- Auto-populates: when a user mentions a tool during onboarding answers (matched against catalog), an entry is created with `source=auto_from_profile`. Explicit bookmarks add with `source=explicit_save`.

### `posts` (community feed; founder launches are a kind of post)
- `_id`, `community_id`, `author_user_id`, `kind`: `launch` | `using_this_week` | `discussion` | `tool_review`
- `title`, `body_md`, `attached_launch_id` (if `kind=launch`)
- `created_at`, `last_activity_at`
- `vote_score`, `comment_count`
- `flagged`: bool, `flag_reasons: []`

### `comments`
- `_id`, `post_id`, `parent_comment_id` (nullable; threading), `author_user_id`, `body_md`
- `created_at`, `vote_score`, `flagged`

### `votes`
- `_id`, `user_id`, `target_type`: `post` | `comment` | `tool`, `target_id`, `direction`: `1` | `-1`, `cast_at`
- `target_type=tool` powers the product-page like count.

### `launches` (founder side)
- `_id`, `founder_user_id`, `tool_id` (created at launch submission)
- `product_url`, `icp_description`, `problem_statement`, `existing_presence_links: []`
- `verification_status`: `pending` | `approved` | `rejected`, `reviewed_by`, `reviewed_at`
- `target_communities: [community_id]` (founder-picked or Mesh-suggested)
- `concierge_match_count`: int (how many user profiles tightly matched)
- `created_at`, `published_at`

### `engagements` (CPA-shaped event log even though billing is off in V1)
- `_id`, `launch_id`, `user_id` (anonymized to founder), `event_type`: `view` | `click` | `dwell` | `tell_me_more` | `redirect_through`
- `dwell_seconds` (for redirect events), `referrer_surface`: `community_feed` | `concierge_nudge`
- `captured_at`
- Schema is CPA-ready so V1.5 billing can attach without migration.

### `notifications`
- `_id`, `user_id`, `kind`: `new_recommendation` | `community_reply` | `concierge_nudge` | `launch_match` | `system`
- `payload`, `created_at`, `read_at`
- V1: in-app only (no email/push fanout).

================================================================================

## Subsystem 1 — Concierge / questionnaire engine

**Surface**: `/onboarding`, `/profile/refine`. **Two-pane layout**: tap-to-answer cards on one side + **live interactive narrowing graph** on the other. The graph IS the magic moment.

**Onboarding graph (V1 differentiator)**:
- Layout: a force-directed cloud of tool nodes. Initial state shows ~20 candidate tools (sampled across categories).
- Each answer mutates the graph live: nodes light up (matched), dim (excluded), or float in (new candidates as profile sharpens). Edges connect tools the user already uses to candidates that integrate or replace them.
- **Floor: minimum 5 tools always visible.** Pool oscillates around 5–10 (e.g., 20 → 10 → 6 → 5 → 6 → 5 → 6) — never collapses to 1. User feels the profile *refining*, not *constraining*.
- Implementation: React + a force-graph lib (e.g., react-force-graph, vis-network, or D3 force-layout). Tool nodes carry tool_id; edges from `tools.metadata` (integration/replacement signals).
- The graph is decorative-but-honest: it shows the actual recommender's current top-K. Nothing fake.

**Flow**:
1. New user lands on `/onboarding`. FastAPI fetches the next core question (where `is_core=true` and unanswered) via `next_logic`.
2. User taps an option (or types own). `POST /api/answers` writes to `answers`, updates `profiles` via aggregation (e.g., role classification, tools list).
3. **After every answer**, a *fast* match call hits Weaviate with the partial profile and returns top 5–10 candidates → graph re-renders. (No LLM in this fast path; pure vector + filter for sub-200ms response.)
4. After every N core answers (e.g., N=5), Celery enqueues an **LLM follow-up job**: Claude Haiku reads recent answers, generates 1–3 contextual follow-up questions, writes them to `questions` with `is_core=false` and queues them for that user.
5. Profile embedding regenerated whenever profile mutates (debounced — Celery task, runs after 30s of inactivity). Embedding written to Weaviate; `profiles.embedding_vector_id` updated.
6. **End of onboarding**: full LLM-ranked recommendation pass produces **4–5 starter recommendations** with reasoning (vs. 2–3 weekly afterward). Higher count gives the user variety to react to on first visit.
7. **End of onboarding**: concierge surfaces 3 community auto-suggestions based on profile (no directory browsing in V1 — concierge does the discovery).
8. User can revisit `/profile/refine` anytime to add new answers, refresh tool stack, log a new "wish."

**Question schema specifics** (locked): hybrid — 10–15 hand-authored core questions seed every profile (role, stack, daily ops, primary friction, budget); LLM-generated follow-ups deepen the profile in `is_core=false` slots. LLM follow-ups are saved into `questions` with provenance so the bank grows over time.

**Build cost**: moderate-to-high. The hardest parts are (a) writing the 10–15 core questions well (product work), and (b) the live narrowing graph — needs a fast Weaviate match path and a smooth React force-graph re-render.

## Subsystem 2 — Recommendation engine

**Locked policy**: on-demand with caching. Cache TTL = 7 days OR until profile mutates (`last_invalidated_at` bumped). **Cadence**: 4–5 recs at end-of-onboarding (variety to react to); 2–3 recs weekly thereafter.

**Pipeline**:
1. User opens `/recommendations`. FastAPI checks `recommendations` collection for fresh entries (cache_expires_at > now AND profile.last_invalidated_at < generated_at).
2. If fresh → return cached.
3. If stale → enqueue Celery `generate_recommendations` task; return a "generating, refresh in 30s" UI shell.
4. Inside the task:
    - **a. LLM clarifier (pre-query)**: Claude Sonnet reads the user's profile + last 10 answers + current request context. Outputs a structured query: `{intent: "looking for X", filters: {pricing, integrations, role-fit}, exclude_tools: [...]}`. This is the "LLM in the loop *before* DB" mechanic the user specified.
    - **b. Weaviate hybrid search**: BM25 over tool descriptions + vector similarity (profile embedding ↔ tool embeddings) + structured filters from clarifier. Returns top 20–30 candidates.
    - **c. LLM ranker (post-query)**: Claude Sonnet receives the 20–30 candidates + user profile, picks N (4–5 onboarding, 2–3 weekly), writes the personalized reasoning string ("this removes the 40-min Notion→Linear copy you mentioned Thursday"). Includes "don't bother with X" notes when a hyped match is a poor fit.
    - **d. Persist**: write `recommendations` rows with score, reasoning, cache_expires_at = now + 7 days.
5. UI re-fetches; user sees recs with reasoning.

**Fast onboarding match path** (separate from main pipeline): the live graph during onboarding hits a lightweight endpoint that does *only* Weaviate filter+vector search (no LLM) and returns top 5–10 candidates in <200ms. This is a different code path from the full pipeline above — fast, cheap, runs on every answer.

**Future direction (deferred)**: graph-DB-based recommendation (research item user flagged). The vector→LLM pipeline is the V1 substrate; graph layer slots in as a richer candidate generator post-V1.

**Cost model**: Sonnet calls (clarifier + ranker) per recommendation. Caching to 7 days bounds spend. Estimated <$0.05 per fresh rec generation.

## Subsystem 3 — Catalog ingestion

**Locked policy**: one-time scrape + manual curation; refresh manually monthly in V1.

**V1 flow**:
1. **Scrape job (Celery, run-once)**: scrapers for theresanaiforthat, Product Hunt, Futuretools dump candidate tools into `tools` with `curation_status=pending`. Expected: ~1000–2000 candidates.
2. **Manual curation surface** (admin-only React page `/admin/catalog`): Mesh staff (you) reviews, edits metadata, sets `curation_status=approved` for ~300 trusted tools. Rest stay pending or get rejected.
3. **Embedding job**: on `curation_status=approved` transition, Celery generates an embedding (Claude or sentence-transformers — pick one) and writes it to Weaviate; tool gets `embedding_vector_id`.
4. **Monthly refresh**: re-run scrapers, surface new candidates and changed-pricing alerts to admin queue.

**V1.5 path**: replace manual curation with AI-agent enrichment (Babel-style); add automated change-detection for tool pricing/sunsetting.

## Subsystem 4 — Community surface

**Locked UX**: Reddit-style threaded feed.

**Components**:
- `GET /communities` — list of joinable communities + user's joined ones.
- `GET /c/:slug` — community feed (posts ranked by HN-formula: `(votes-1)/(time+2)^G` with G=1.8 default, tunable per community).
- `GET /c/:slug/post/:id` — post page with **flat comments (V1)**.
- `POST /api/posts` — create a post (kind: `launch`, `using_this_week`, `discussion`, `tool_review`).
- `POST /api/comments` — flat reply (V1: `parent_comment_id` always null; threading deferred to V1.5).
- `POST /api/votes` — upvote/downvote post, comment, or tool.
- `POST /api/communities/:id/join` and `/leave`.

**MVP scoping note**: V1 ships with **flat comments (no threading)**. The `comments` collection still has the `parent_comment_id` field schema for forward-compat, but the API ignores it and renders chronologically. Threading enabled in V1.5. Cuts ~30% of UI complexity (no nested rendering, no collapse logic, no thread permalinks) for the V1 cycle.

**Formation policy** (locked):
- **Multi-dimensional axes.** Communities exist along three axes simultaneously: **role/job-function** (e.g., r/growth-marketers), **tool/stack** (e.g., r/notion-power-users, r/cursor-builders), and **problem/outcome** (e.g., r/email-time-killers, r/replacing-saas-with-ai). A user typically belongs to one of each.
- **Discovery via concierge auto-suggestion.** No directory browsing in V1. At end of onboarding, concierge surfaces 3 best-fit communities (one per axis where possible) — one-tap join. Concierge can suggest more later as profile sharpens.
- **Activity shape**: tool reviews + "using this week" posts + tool comparisons + Q&A. Founder launches drop into the same feed naturally as `kind=launch` posts. Reddit-style threading on every post.
- **Cross-posting policy**: posts default to **one community** (user picks the home community when posting). User can optionally select up to 3 communities to fan out to. UI: "post to r/notion-power-users (home) + r/solo-founders + r/replacing-saas-with-ai".
- **Communities spawned by Mesh staff in V1.** Catalog of ~30–60 communities seeded across the three axes. User-created communities deferred to V1.5+.

**Moderation in V1**: Mesh staff are mods on every community. Flagging surface (`flagged` bool on posts/comments) feeds an admin queue. Community-elected mods is V1.5+.

**Anti-spam mechanics** (per basic_idea.md locks):
- Founder accounts (`role_type=founder`) **cannot post** in community feeds. They can only submit launches via the founder pipeline. This is the role-split that prevents the Product Hunt founder-gravity problem.
- Public invite tree visible on user profiles.
- Per-community karma stored in `community_memberships` (V1.5: gates flag/post privileges).

## Subsystem 5 — Founder launch flow

**Founder onboarding** (locked: lightweight verification):
1. Founder signs up with `role_type=founder` (separate signup path: `/founders/signup`). Cannot be flipped to `user` later.
2. Submits launch via `/founders/launch`:
    - product URL
    - 1-line problem statement
    - ICP description (target user — role, scale, current stack)
    - links to existing presence (X, LinkedIn, personal site, GitHub)
3. Saves to `launches` with `verification_status=pending`. Admin queue.
4. Mesh staff reviews within 24h. Approve → `verification_status=approved`, founder gets email (note: in V1 we said in-app-only, but founder verification email is a transactional necessity — flagged below).
5. Founder picks target communities (auto-suggested via tool→community matching) → **target: 5–6 communities** to spread the launch (vs. 2–3 for users posting). Founder picks across the three axes (role / tool-stack / problem) — Mesh suggests defaults across axes; founder accepts/swaps. Launch publishes.

**Dual-fire publish flow**:
- **Canonical product page**: launch creates a `tools` row (or links to existing) with `is_founder_launched=true`, `launched_via_id=launch._id`. Reachable at `/p/:slug` — permanent home for the product. Aggregates: total likes (`votes` where `target_type=tool`), review count (`posts` where `kind=tool_review` and `tool_id=this`), launch metadata (founder, ICP, problem statement), engagement metrics (clicks, dwell from `engagements`).
- **Public side**: a `posts` row with `kind=launch`, `attached_launch_id`, in each of the founder's 5–6 target communities. Each community-post links to the canonical `/p/:slug` page for "see full details / leave a review."
- **Concierge side**: a Celery task scans `profiles` for tightest-fit users (via Weaviate query against the founder's ICP description embedding). **Match-quality threshold gate (locked)**: only users in the **top 5% of match scores** (or hard floor: cosine similarity > 0.85) get a `concierge_nudge`. Most launches will nudge 0–30 users, not 30–50. Strict threshold = trust ("if Mesh nudges me, it's signal, not spam").
- The nudge surfaces as a **top banner on app open** (non-blocking, dismissable) plus a notification in the concierge tab: *"a new launch matches your [Tuesday Notion friction] — want to look?"*
- User responds skip / tell-me-more. Each response writes an `engagements` row.
- **Skip feedback (locked)**: silent inference by default — Mesh downweights the matched-tool's category/tag cluster in future matches for that user. For high-signal skips (where match score was top 1% but user skipped), a one-tap follow-up: *"surprised you skipped — was it: wrong category / already use one / pricey / just not now?"* Optional. Trains the matcher.
- Click-through goes via `/r/:launch_id?u=:user_id_hash` redirect (dwell logged), then forwards to product URL.

**Founder dashboard** (locked scope): bare-min + matched-user count + community spread.
- Launch list with status.
- Per-launch: clicks, dwell-time histogram, matched-user count (anonymized), community-by-community click breakdown.
- *Not* in V1: decline reasons, DM-with-users, retention-cohort. (V1.5+.)

## Subsystem 6 — Tracking / engagement (V1: free, redirect-only)

**Mechanism**: `/r/:launch_id?u=:user_token&s=:surface` (surface = `community` or `concierge`). On hit:
1. FastAPI logs `engagements` row (`event_type=redirect_through`, dwell_seconds=0 initially).
2. 302 redirect to launch's product_url with founder-supplied UTMs preserved.
3. Optional client-side beacon on the redirect intermediate page captures dwell-time before redirect (debounce ~1.5s).

**No founder-side instrumentation in V1.** No JS pixel, no webhook. Schema is CPA-ready; V1.5 can add the pixel without migration.

**No billing in V1.** Founders get the dashboard free.

## Subsystem 7 — Notifications

**V1: in-app only.** Bell icon, badge count, notification center page. **Plus: top banner on app open** specifically for high-priority concierge nudges (launch matches above the 5% threshold).

**Notification triggers**:
- new_recommendation — concierge generated fresh recs (bell only)
- launch_match — a launch matched your profile above threshold (top banner + bell)
- community_reply — someone replied to your post/comment (bell only)
- system — admin announcements, profile-import status, etc. (bell only)

**Storage**: `notifications` collection. Read state stored per-user. Top banner shows the most recent unread `launch_match` notification on app open; dismissable to bell-only.

**Out of scope V1**: email digest, browser push. The one exception: founder verification approval email (transactional; can't avoid). Implementation: simple SMTP or Postmark/Resend, single-use.

================================================================================

## Async jobs (Celery)

| Job | Trigger | Cadence |
|---|---|---|
| `generate_recommendations` | Profile change OR cache miss on `/recommendations` | On-demand |
| `regenerate_profile_embedding` | Answer write (debounced 30s) | On-demand |
| `llm_followup_questions` | After every 5 core answers | On-demand |
| `scan_launch_for_concierge_matches` | Launch publish | On-demand |
| `scrape_catalog_sources` | Manual trigger (V1); cron monthly (V1.5) | Manual / monthly |
| `embed_approved_tool` | Tool curation_status flips to approved | On-demand |
| `expire_recommendation_cache` | Cron daily | Daily 03:00 UTC |
| `process_flagged_content` | Flag write | On-demand → admin queue |

Redis = broker + result backend. Single-worker fleet to start; scale horizontally as needed.

## Auth (custom Python)

- `POST /api/auth/signup` → email, password, role_type. Sends verification email (single transactional exception per Subsystem 7). bcrypt hash stored.
- `POST /api/auth/login` → returns JWT (HS256, 7-day expiry, refresh token in httpOnly cookie).
- `POST /api/auth/forgot-password`, `/reset-password` → token-based, 1h expiry.
- Middleware: `current_user` dependency on every authed endpoint; role-aware (founder endpoints reject `role_type=user` and vice versa).
- Anti-abuse: rate limit signup (5/hr/IP), login (10/min/IP) via slowapi or redis-based.

## Frontend (React)

- Mobile-responsive single SPA.
- State: TanStack Query for server state, light Zustand for ephemeral UI. No Redux.
- UI library: Tailwind + shadcn/ui-style primitives (decision deferred to implementation).

**V1 user-side screens (3)**:

| Screen | Route | Purpose |
|---|---|---|
| **Onboarding** | `/onboarding` | Two-pane: tap-to-answer questions + live narrowing graph (Subsystem 1). |
| **Communities** | `/c`, `/c/:slug`, `/c/:slug/post/:id` | Multi-dimensional community list + per-community flat-comment feed (Subsystem 4). |
| **Tools** | `/tools` (with three tabs: `/tools/mine`, `/tools/explore`, `/tools/new`) | The user's tool home base. **My Tools** = auto-populated from profile + explicit saves (`user_tools` collection). **Explore** = full curated catalog browse, filterable by category/tag/pricing. **New Tools** = founder launches only, default-filtered to communities the user has joined. |

**V1 founder-side screens (3)**:

| Screen | Route | Purpose |
|---|---|---|
| **Product page** | `/p/:slug` | Canonical public page per product. Likes (votes), reviews (`posts` where `kind=tool_review`), launch metadata, founder link, engagement metrics. Reachable from every community-post launch fan-out. |
| **Communities (relevant, view-only)** | `/founders/launch/:id/communities` | Mesh-suggested 5–6 communities for a launch + preview of each (member count, recent activity). Founder picks 5–6 to fan-out to. View-only — founders cannot post directly into communities outside the launch flow. |
| **Analytics** | `/founders/dashboard`, `/founders/launch/:id/analytics` | Click counts, dwell-time histogram, matched-user count (anonymized), per-community click breakdown (Subsystem 5). |

**Other V1 routes**:
- `/recommendations` — 4–5 starter recs at end of onboarding; 2–3 weekly thereafter.
- `/profile`, `/profile/refine`
- `/notifications`
- `/founders/signup`, `/founders/launch`
- `/admin/*` — Mesh-staff curation, founder verification, flag queue.

================================================================================

## Open implementation questions (for during build, not before)

1. **Embedding model** — Claude embeddings vs. open-source (BGE, sentence-transformers). Cost vs. quality test on the curated 300 tools.
2. **HN-formula gravity tuning per community** — start with G=1.8, monitor.
3. **Per-community karma rules** — when does it gate posting? Flagging? V1.5 work.
4. **Admin tooling depth** — how rich is the curation UI vs. raw Mongo edits? Iterative.
5. **Profile export format** — JSON, Markdown, both? Defaults to JSON for V1.
6. **Question-set authoring tooling** — direct Mongo writes vs. an admin form. Probably admin form by V1.5; raw Mongo + seed-script for V1.
7. **Deployment target** — user to specify.
8. **Pricing model** — deferred per `basic_idea.md` lock.

## What's deferred to V1.5+

- Email digests + browser push notifications
- AI-agent continuous catalog crawling (Babel-style)
- LLM-generated dynamic question paths beyond follow-ups
- Founder JS pixel for conversion tracking
- Community-elected mods + moderation tooling depth
- DM-between-founder-and-user surface
- Decline-reason aggregation in founder dashboard
- Graph-DB recommendation layer (research)
- Free-form chat concierge (replacing tap-to-answer)
- Per-community karma gates
- Multi-language support

================================================================================

## Build sequence (suggested)

1. **Auth + user/founder split** (foundation)
2. **Question bank + answer capture + profile aggregation** (concierge skeleton)
3. **Catalog scrape + admin curation page** (data substrate)
4. **Weaviate integration + embedding pipeline** (matching substrate)
5. **Recommendation engine pipeline** (the user-side magic moment)
6. **Communities + posts + threaded comments + voting** (community substrate)
7. **Founder launch flow + verification + dual-fire publish** (the founder side)
8. **Founder dashboard with click + dwell + matched-user count**
9. **Notifications (in-app)**
10. **Polish + manual user-test loop** per `basic_idea.md` cheapest-test plan

Steps 1–5 are the user-side V1; founder side (6–8) layers on top. Manual validation should run between step 5 and step 6.

---

*Status: v0.1 system design, build-ready. Open implementation questions are normal-course-of-development items, not blockers. Recommended next step: pick a build target (deployment + first-week scope) and convert step 1 into an SDD spec cycle.*
