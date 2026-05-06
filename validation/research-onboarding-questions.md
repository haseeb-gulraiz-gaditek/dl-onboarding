# Onboarding Question Flows for Granular User-Needs Profiles

_Research brief for Mesh — 2026-05-04_

Goal: design 12 V1 onboarding questions that yield workflow-granular signal (not "likes productivity tools" but "copies from Notion to Linear weekly"), while keeping completion high.

---

## 1. Sources (one-line takeaways)

- **Descope, "Progressive Profiling 101" (2025)** — Ask one or two segmentation questions upfront; defer the rest until contextual moments; field-level drop-off is the primary diagnostic. ([source](https://www.descope.com/learn/post/progressive-profiling))
- **Eleken, "Fintech onboarding: 6 UX practices" (2025)** — Each extra field costs ~5–7% completion; 70% abandon if onboarding > 20 minutes; split long flows into micro-steps to preserve momentum. ([source](https://www.eleken.co/blog-posts/fintech-onboarding-simplification))
- **Ravi Mehta, "Confidence engineering: Why your onboarding is probably too short" (2024)** — Counterintuitive: longer flows with the *right* questions outperform shorter ones because each step builds commitment ("Sesame's 25-step checkout converts 40% better"). ([source](https://blog.ravi-mehta.com/p/onboarding-optimization))
- **RevenueCat, "Inside Noom's web-to-app funnel" (2024)** — Mix tap-chip questions with 1–2 slider/scale items; pre-frame sensitive questions with rationale; reflect answers back ("we'll personalize X") to make effort feel rewarded. ([source](https://www.revenuecat.com/blog/growth/web-to-app-onboarding-funnel/))
- **Juno School, "The Duolingo Onboarding Experience" (2024)** — 4 questions only, all chip-based, ordered: target → motivation → skill level → daily commitment. Branches to placement test if "already know some". ([source](https://www.junoschool.org/article/duolingo-onboarding-experience/))
- **Tony Ulwick / Strategyn, "Jobs-to-be-Done & ODI"** — Customers can articulate up to 100+ "desired outcomes" per job; ask about *measurable success metrics* (speed, accuracy, effort) not solutions. ([source](https://strategyn.com/jobs-to-be-done/))
- **June.so, "How to run a JTBD interview" (Bob Moesta)** — The Switch Interview elicits the *Four Forces*: Push (current pain), Pull (new attraction), Anxiety (unknown), Habit (status quo). All four together explain tool adoption. ([source](https://www.june.so/blog/how-to-run-a-jtbd-interview-like-the-co-creator-of-the-framework))
- **Qualaroo, "Skip Logic: Why Surveys Get Abandoned" (2025)** — Branching reduces effective length 20–40% and lifts completion; respondents "satisfice" (give junk answers) when irrelevant questions appear. ([source](https://qualaroo.com/blog/skip-logic-survey/))

---

## 2. Principles synthesis (for Mesh)

1. **Reflect-back > extract-only.** Every 2–3 questions, surface a short personalized echo ("So you're a solo founder who lives in Linear and resents context-switching..."). Effort feels paid back, completion holds.
2. **Tap-first, free-text strategically.** Chips/multi-select for ~10 of 12; reserve free-text for 1–2 slots where granularity is otherwise impossible (the "what tool did you abandon and why" type).
3. **Workflow-anchored, not category-anchored.** Ask about *actions* ("the last thing I copy-pasted between two apps was…") not *categories* ("I like AI writing tools").
4. **Surface friction via the past, not the future.** "Tell me about the last time you…" outperforms "would you like…" for signal quality (Moesta/JTBD).
5. **Branch early, deepen late.** Q1–4 broad and universal; Q5–7 branch on role/workflow type; Q8–12 drill into the specific paradigm the user revealed.
6. **One commitment moment.** Borrow Duolingo: ask a daily-use commitment ("how many minutes/week do you want to save?") — humans have completion-bias, and it sets expectations for recommendations.
7. **Exclusion is a first-class signal.** Tools tried-and-bounced are as informative as tools loved. Make at least one question explicit about this — ChatGPT churn for tone, Notion churn for bloat, etc.

---

## 3. Concrete 12-question proposal (V1)

Format key: **C** = single-tap chip, **MC** = multi-select chips, **S** = slider, **FT** = short free-text (≤140 chars). Signal slots: `friction`, `capability`, `exclusion`, `paradigm`, `workflow_edge`, `counterfactual`.

| # | Question | Format | Signal | Branch |
|---|----------|--------|--------|--------|
| 1 | "What best describes you right now?" → Solo founder / Operator at small co / IC at bigger co / Creator / Student / Other | C | `paradigm` | Routes Q5–7 templates |
| 2 | "Pick up to 3 things you spend the most time on this week." → Writing / Research / Coding / Design / Meetings / Ops & admin / Customer/sales / Learning | MC (max 3) | `capability` | Top pick chosen ⇒ Q5 specific |
| 3 | "Which AI tools do you actually use weekly?" → ChatGPT / Claude / Gemini / Perplexity / Cursor / Copilot / Midjourney / None yet / Other | MC | `capability`, `paradigm` | "None yet" ⇒ skip Q4, jump to Q6 |
| 4 | "Of those, which one frustrated you most recently — and why in 5 words?" → [chip of selected tools] + tiny FT | C+FT | `friction`, `exclusion` | Free-text classifier feeds Q8 |
| 5 | "Where does your work *actually* live?" → Notion / Google Docs / Obsidian / Linear / Jira / Slack / Email / Figma / VS Code / Sheets / Other | MC | `workflow_edge` | Top 2 selected become "App A → App B" placeholders in Q7 |
| 6 | "What slows you down the most?" → Repetitive copy-paste between apps / Searching for info I already wrote / Writing the same thing twice / Formatting & cleanup / Deciding which tool to even open / Not knowing what's possible | C | `friction` | Picks the deepening track for Q9–10 |
| 7 | "Last time you copied something from {App A} to {App B}, what was it?" (uses Q5 picks) | FT | `workflow_edge` | The single richest free-text — ungated |
| 8 | "Have you tried & abandoned any of these in the last year?" → ChatGPT / Notion AI / Zapier / Make / Reflect / Mem / Granola / Otter / Fathom / Custom GPTs / None | MC + optional FT "why" per pick | `exclusion`, `friction` | Each pick triggers a follow-up reason chip set in Q9 |
| 9 | _Adaptive_: For each Q8 pick, "Why did it not stick?" → Too generic / Too clunky / Hallucinated / Privacy worry / Forgot it existed / Cost / Couldn't fit my workflow | MC per tool | `exclusion`, `friction` | If "Couldn't fit my workflow" ⇒ Q11 prioritizes integration paradigm |
| 10 | "How do you prefer AI to show up?" → Chat I open on purpose / In the app I'm already in / Background automation / Voice / I don't know yet | C | `paradigm` | Drives surface-mode of recs |
| 11 | "If a tool could do ONE thing for you this month, what would it be?" | FT (≤140) | `counterfactual` | Embedding-classified into ~20 known JTBD buckets |
| 12 | "How many minutes per day are you willing to spend setting up new tools?" → <2 / 5 / 15 / 30+ | C | `paradigm` (tolerance) | Sets recommender's setup-cost ceiling |

---

## 4. Adaptive deepening strategy

**Principle: questions 1–4 are universal; 5–7 branch on persona/workflow; 8–12 drill into the paradigm revealed.**

Concrete branches:

- **Branch A — "Solo founder + lives in Notion + frustrated by ChatGPT" (Q1+Q5+Q4):** Q9 prioritizes "context-switching" reasons; Q11 prompt rewrites to "If a tool lived inside Notion and could do ONE thing…". Post-V1: add Q13 "Do you re-paste your roadmap into ChatGPT each time?" (Y/N).
- **Branch B — "IC at bigger co + Jira + Slack" (Q1+Q5):** Q6 chips re-order to lead with "searching for info I already wrote"; Q10 chips emphasize "in the app I'm already in" since Slack/Jira-native is the wedge.
- **Branch C — "None yet" on Q3:** Q4 skipped; Q8 reframed to non-AI exclusions ("tried & abandoned: Notion templates, Zapier, Trello…"); Q11 free-text becomes more important — it's the only `counterfactual` we'll get.
- **Branch D — "Couldn't fit my workflow" dominant in Q9:** Recommender weights integration depth > raw capability; Q12 cap of "<2 min" becomes a hard filter.
- **Post-V1 deepening (Q13–18, contextual, post-first-recommendation):** trigger when user dismisses 3 recs in a row → "What's missing?" chip set; trigger when user clicks a rec but doesn't install → micro Switch Interview ("what made you hesitate?" anxiety chips).

**Reflect-back checkpoints** at Q4, Q7, Q11: render a 1-line synthesis using their own words ("Sounds like Notion is your home base and ChatGPT keeps losing context — got it"). This is the commitment-building beat that lets us extend to 12 questions without bleeding completion.

---

## 5. Estimated friction budget

12 chip-dominant questions, 2 short free-text, 3 reflect-backs ≈ 90–120 seconds median. Stays well under the 20-minute abandonment cliff and within the "5–7% per field" envelope because 10 of 12 are taps. The two FT slots (Q7, Q11) are the highest-signal items; protect them by placing them *after* a reflect-back so users feel investment.
