# Mesh — Design Brief for V1 Screens

> A self-contained brief for designing the V1 screens of Mesh. No backend / engineering detail. Hand this to a designer (or Claude in design mode) and they should be able to mock up the full V1 surface from it.

---

## What is Mesh?

Mesh is a **launch platform built around an AI concierge for laypeople drowning in AI tools**. Two sides, one loop:

- **Users**: take a quick tap-to-answer questionnaire. The concierge learns your daily-life ops (role, current tools, frictions, wishes). It tells you which 2–5 AI tools are actually worth using *for you* — and which to skip. It also drops you into niche communities where peers in the same role/stack/problem live.
- **Founders**: launch a product to users whose profile is a *tight workflow-level fit* — not other founders scrolling Product Hunt. Get clicks, reviews, real engagement, in communities where the right users already are.

**Tone / personality**: smart, calm, opinionated, honest. Not hype-y. Closer to a thoughtful friend who knows the AI tool landscape than a marketing-driven launch site. Anti-Product-Hunt energy.

**Key UX principles**:
- **Tap, don't type** — most user input is one-tap option selection. Free-text is always optional, never the main path.
- **Profile compounds visibly** — users should *see* their profile sharpening their recommendations in real-time. Nothing happens "in the background" without showing the user.
- **Trust, not noise** — when Mesh tells the user about a tool, it should feel like a friend recommending, not an ad. Strict thresholds for nudges.
- **Mobile-responsive web app** — design for phone-first, but the layout has to scale to tablet/desktop too. No native mobile app in V1.

---

## V1 has 6 screens total — 3 for users, 3 for founders.

================================================================================

# USER SIDE — 3 screens

## 1. Onboarding (the magic moment)

**Route**: `/onboarding`

**Purpose**: take a brand-new user and turn them into someone with a meaningful profile + first set of recommendations in 3 minutes. This is the screen that decides whether Mesh feels delightful or boring.

**Layout**: **two-pane split**
- **Left pane (~50%)**: tap-to-answer question card. One question at a time. Big, clear options to tap. Below options, a small "type your own" link to free-text the answer.
- **Right pane (~50%)**: **a live, animated tool graph**. A force-directed cloud of tool nodes (each is a real AI tool from the catalog — show name + small logo). The graph mutates *every time the user answers a question*.

**The graph behavior** (this is the differentiator — get it right):
- Starts with ~20 candidate tool nodes scattered as a soft cloud.
- Each answer:
  - **Lights up / brightens** the tools that match (e.g., user picks "I'm a marketer" → marketing tools brighten).
  - **Dims / fades** the tools that don't fit (smaller, lower opacity, may drift to the edge).
  - **Floats in new candidate tools** as the profile sharpens.
- **Hard floor: minimum 5 bright/visible tools at all times.** The pool oscillates around 5–10 (e.g., 20 → 10 → 6 → 5 → 6 → 5 → 6). Never collapses to 1 — that would feel limiting.
- Edges (light lines) connect tools the user already uses to candidate tools that integrate or replace them.
- Hover/tap on any glowing tool node = quick tooltip with the tool's name + one-line description.
- Animation should feel *physical*, *responsive*, *alive*. Not a chart — a living thing.

**Question card details**:
- Show question count: "Question 4 of 12" in a thin bar or progress indicator.
- Each question has 3–6 option chips. User taps one → next question slides in. Smooth.
- "Type your own" link below the options. Clicking opens a small inline text input.
- Bottom of card: a small "skip this" link (shows once per session if used).

**End-of-onboarding state**:
- A celebration moment: "Here are 4–5 tools picked for you" — graph collapses into a clean grid of 4–5 tool cards with personalized reasoning under each ("this removes the 40-min Notion→Linear copy you mentioned"). One card explicitly labeled "skip this hyped tool — doesn't fit you" with a reason.
- Below that, a "join 3 communities we picked for you" block with one-tap join chips.
- CTA to enter the main app.

**Empty / edge states**:
- User refreshes mid-onboarding → resume from last unanswered question.
- User closes browser → graph + answers persist; come back later, pick up where they left off.
- "Type your own" answer that doesn't match the catalog → graph still updates (best-fit nodes brighten, no failure state).

================================================================================

## 2. Communities

**Routes**: `/c` (list), `/c/:slug` (single community), `/c/:slug/post/:id` (post detail)

**Purpose**: a place where users live and interact with peers in their niche. The visible "users live here" surface that differentiates Mesh from a tool directory.

**Community list page (`/c`)**:
- Sectioned: "Your communities" (joined) + "Suggested for you" (concierge-suggested) + "All communities" (browse).
- Each community card: name, brief description, member count, last-active indicator, join/leave button.
- Multi-dimensional axes shown as filter chips at top: **Role** | **Tool/Stack** | **Problem/Outcome**. Tapping filters the list.
- Empty "Your communities" state for new users: "concierge will suggest communities as your profile sharpens." (Should rarely show — concierge auto-suggests at end of onboarding.)

**Single community page (`/c/:slug`)**:
- Header: community name, description, member count, "Joined ✓" or "Join" button.
- Sub-tabs: "Hot" (HN-formula ranked), "New" (chronological), "Top" (all-time).
- Below: a feed of posts. Each post card shows: author avatar + name, post type badge (`launch` / `using-this-week` / `tool-review` / `discussion`), title, preview of body (2 lines), upvote count, comment count, time-ago.
- Sticky compose button: "+ Post" — opens a compose modal with post-kind picker.
- **For launch posts**: the post card has a slightly different visual — "Launch" badge in accent color, founder name beside the title, link to the canonical product page.

**Post detail page (`/c/:slug/post/:id`)**:
- Top: full post content (markdown-rendered).
- Voting on the post (up/down arrows + count).
- Below: **flat comments** (no threading in V1 — chronological). Each comment: avatar, name, body, upvote count, time-ago.
- Compose comment input at the bottom (sticky on mobile, inline on desktop).

**Empty states**:
- A community with 0 posts → friendly placeholder: "be the first to share what you're using."
- A community with no joined members yet (rare; staff-seeded) → seed state showing intended purpose.

**Compose modal** (post composition):
- Kind picker: Launch / Using This Week / Tool Review / Discussion (chips).
- Title input.
- Body markdown input (with simple toolbar — bold, italic, link, code).
- "Post to" picker: defaults to current community. User can add up to 2 more communities (max 3 total fan-out). Each shows as a chip with X to remove.
- Submit button.

================================================================================

## 3. Tools

**Route**: `/tools` with three sub-tabs: `/tools/mine`, `/tools/explore`, `/tools/new`

**Purpose**: the user's home base for their tool relationship. This is where they see what they have, what they could try, and what just launched.

### Tab 1: My Tools (`/tools/mine`)

- Grid or list of tool cards the user is already using or has saved.
- Each card: tool logo, name, one-line description, source badge ("from your profile" / "saved"), small action menu (remove, mark as not-using).
- Top of page: a search input (filter your own tools) + "+ Add a tool" button (manual add).
- Sub-section split (optional): "Currently using" / "Saved for later".
- Empty state: a friendly call to refine your profile or start saving recommendations.

### Tab 2: Explore (`/tools/explore`)

- The full curated catalog, filterable.
- Top: filter chips — Category (writing, scheduling, CRM, dev, etc.), Pricing tier, Integrations.
- Search input.
- Grid of tool cards, sortable (popular / newest / alphabetical).
- Each card: logo, name, tagline, category tag, pricing summary, "save" heart icon, like count.
- Tap card → goes to canonical product page (`/p/:slug`).

### Tab 3: New Tools (`/tools/new`)

- Chronological feed of recently-launched products on Mesh (founder launches only — not catalog updates).
- Default filter: "from your communities" (only launches in communities the user has joined).
- Toggle at top: "Your communities" / "All new launches".
- Each card: launch badge, founder name + avatar, product name + tagline, target communities listed, time-ago, like count, "see details" button.
- Tap card → canonical product page (`/p/:slug`).

**Cross-tab nav**: clean tab bar at top of `/tools`. Sticky on scroll.

**Empty states**:
- New user with empty My Tools → "as you take the questionnaire and save recommendations, this fills up."
- Empty New Tools (no launches in your communities yet) → fallback to "All new launches" view.

================================================================================

# FOUNDER SIDE — 3 screens

## 4. Product page (canonical, public)

**Route**: `/p/:slug`

**Purpose**: the permanent home for a launched product. One canonical URL the founder can share anywhere; all metrics, reviews, and likes aggregate here from across all communities.

**Layout**:
- **Header**: product logo, name, tagline, founder name + avatar, launch date, primary action button ("Visit site" — sends through Mesh redirect for tracking).
- **Metrics row** (visible to everyone): like count (heart), review count (with star), click count.
  - Like button is interactive for logged-in users (toggles vote on tool).
- **Description**: full product description, screenshots (if founder uploaded), pricing summary, integrations.
- **Launched into**: list of community badges with member counts — small chips showing where this product was surfaced.
- **Reviews / discussion**: feed of `kind=tool_review` posts attached to this tool, aggregated from all communities. Each review card: author avatar, name, body, time-ago, upvote count.
- **Compose review**: sticky CTA "Leave a review" for logged-in users (opens compose modal with kind=tool_review pre-set).

**Visual treatment**:
- Cleaner, more product-marketing-y than community pages. Full-bleed header, big hero image area for product screenshot. Feels closer to a Notion landing page than to a Reddit thread.
- Distinguishable from a regular post — this is "the product home," not "a launch post."

**Empty states**:
- A just-launched product with 0 reviews → encouraging placeholder: "be the first to share how this fits your workflow."

================================================================================

## 5. Communities (founder view, view-only)

**Route**: `/founders/launch/:id/communities` (during launch creation flow) and `/founders/launch/:id` (after publishing)

**Purpose**: when a founder is creating a launch, this screen helps them pick **5–6 target communities**. It also serves as a post-launch reference of where their product is showing.

**Pre-launch (picker mode)**:
- Heading: "Pick 5–6 communities for your launch."
- **Mesh-suggested communities at top** (auto-matched from the founder's product description and ICP). Show 8–10 candidates across the three axes:
  - **By Role** (e.g., r/growth-marketers, r/solo-founders).
  - **By Tool/Stack** (e.g., r/notion-power-users, r/cursor-builders).
  - **By Problem/Outcome** (e.g., r/email-time-killers, r/replacing-saas-with-ai).
  - Each axis labeled visually with a colored tag.
- Each community card: name, member count, last-week activity preview (3 sample post titles), match score (e.g., "92% match"), select button.
- **Selected counter**: "3 of 5–6 selected" prominent at top.
- "Browse all communities" link — opens the full directory in view-only mode.
- **View-only**: founder cannot post directly into a community here. Only via the launch flow.
- Bottom: "Continue to launch" button (enabled when 5–6 selected).

**Post-launch (view mode)**:
- Same screen layout, but selected communities are now in "Your launch is live in:" with click counts per community.
- Founder can see how launch is performing per-community without leaving this view.
- A "view in community" link per row that goes to the actual community feed (read-only for founders).

================================================================================

## 6. Analytics

**Route**: `/founders/dashboard` (overview), `/founders/launch/:id/analytics` (per-launch)

**Purpose**: founder sees how their launches are performing. The single screen that answers "is Mesh working for me?"

**Dashboard overview (`/founders/dashboard`)**:
- Header: founder name, total launches, total clicks-to-date.
- Launch list table:
  - Each row: product name + logo, launch date, status (pending / approved / live / paused), clicks, matched-user count, communities count, "view analytics" button.
- "+ New launch" CTA at top right.

**Per-launch analytics (`/founders/launch/:id/analytics`)**:
- Top: launch summary card (product name, launch date, target communities count, total clicks).
- **Click chart**: clicks over time (last 7d / 30d / all-time toggle). Simple line chart.
- **Dwell-time histogram**: how long users hovered on the redirect page before going through. Bar chart.
- **Matched-user count**: "your launch was surfaced to 47 users" (anonymized — no user names).
- **Per-community breakdown** table:
  - Community name | views | clicks | click-through-rate | comments
  - Sortable by clicks.
- **Concierge nudge stats**: how many users got a concierge nudge for this launch, how many tapped "tell me more" vs. skipped.

**Visual treatment**:
- Clean, data-dense, calming. Not flashy. Minimal but informative — closer to Linear or Plausible than to a heavy enterprise dashboard.
- Mobile-responsive: charts scroll horizontally; tables stack on narrow screens.

**Empty states**:
- Founder with 0 launches → onboarding card: "Submit your first launch to see analytics."
- Launch with 0 engagement yet → "Your launch just went live — check back in a few hours for first metrics."

================================================================================

# Cross-cutting design notes

## Brand / mood

- **Color palette**: calm but distinctive. Suggest: a soft neutral (off-white or warm gray) base; one strong accent for actions and identity (e.g., deep teal, warm orange, or quiet violet); muted secondary tones. Avoid the rainbow / "AI gradient" aesthetic that every AI tool uses — Mesh should feel grown-up.
- **Typography**: a clean sans for UI (Inter, Geist, or similar), and a slightly more characterful display face for headers (maybe a soft serif or geometric sans). Distinct from Linear / Notion / Vercel defaults if possible — Mesh is a *destination*, not a productivity tool.
- **Iconography**: minimal, line-based. Single weight throughout.
- **Density**: more whitespace than typical SaaS dashboards. Breathing room signals "we're not desperate for your attention."

## Tone of microcopy

- Direct, honest, slightly opinionated. Not corporate.
- Examples:
  - Empty My Tools: *"Nothing here yet. Tell the concierge what you use."* (Not: "You haven't added any tools.")
  - Bad-fit recommendation: *"Skip this one — it's hyped, but not for you."* (Not: "This tool may not be the best fit.")
  - Founder approval pending: *"We're reviewing your launch. Usually 24h. We'll email when it's live."*
  - Skip nudge follow-up: *"Surprised you skipped — what was off?"*

## Notification / nudge surface

- **Top banner on app open** (for high-priority concierge nudges only — top-5%-match threshold):
  - Slides in from top, soft entrance, dismissable with X.
  - Concierge avatar + one-line message + two buttons: "Tell me more" (primary) / "Skip" (secondary).
  - Auto-dismisses if user navigates away. Returns next session if not acted on (max 3 sessions).
- **Bell icon in top nav** (always visible):
  - Badge count for unread notifications.
  - Click → notification center page with all notifications listed (recommendations, replies, launch matches, system).

## Responsive notes

- Phone-first layout. The two-pane onboarding becomes single-column on mobile (graph stacks above questions, smaller; or graph available as a "see your matches" toggle).
- Communities feed: card view on phone, denser list on desktop.
- Tools tabs: bottom-nav-style on phone (My / Explore / New), tab-bar-top on desktop.
- Founder analytics: vertical stack on phone, multi-column on desktop.

## Accessibility

- All tap targets ≥ 44x44pt on mobile.
- Color contrast WCAG AA minimum.
- The narrowing graph must have a non-graph alternative for screen-reader users (a plain text "currently 6 tools match: A, B, C, D, E, F" updated live).
- Keyboard navigation through onboarding questions (Tab + Enter to advance).

## What NOT to design for V1 (deferred to later)

- Free-form chat with the concierge (V1.5)
- Threaded comments (V1.5)
- Direct messages between users / between founders and users (V1.5+)
- Email digests (V1.5)
- Founder DMs to matched users (V1.5+)
- User-created communities (V1.5+)
- Advanced filters/search inside communities (V1.5)
- Pricing / billing surfaces (deferred entirely)

---

## Deliverables expected from design

For each of the 6 screens above:
1. Mobile + desktop hi-fi mockup
2. Major empty states
3. One key interaction state (e.g., the graph mid-narrow, the compose modal open, the banner appearing)
4. A short style guide reference (color tokens, typography, spacing)

Plus: a single component sheet (buttons, inputs, cards, chips, tabs) used across the system.

---

*Brief is current as of 2026-04-28. Backing system architecture in `system_design.md`; product thesis in `basic_idea.md` (same `/scratch/` folder) — designer can ignore those unless they want backstory.*
