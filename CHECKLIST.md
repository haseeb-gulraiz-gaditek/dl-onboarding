# Onboarding Checklist

The minimum bar for "onboarded to the Disrupt Labs way of building ventures." Everything below should be demonstrable in your fork — not just read.

Score yourself by ticking each box when it's actually true in your repo. Your onboarding buddy or manager should be able to verify every item by inspecting your fork.

---

## Tooling familiarity

You have personally run, at least once, and understood the output of:

- [ ] `/lay-of-the-land` — oriented yourself in this repo
- [ ] `/vkf/init` — bootstrapped your constitution directory
- [ ] `/vkf/constitution` — drafted a section interactively
- [ ] `/vkf/validate` — audited your foundation
- [ ] `/vkf/freshness` — checked at least one spec for staleness
- [ ] `/vkf/gaps` — surfaced at least one known unknown
- [ ] `/vkf/amend` — made a C1 or higher amendment on a filled-in constitution file
- [ ] `/vkf/ingest` — ingested at least one external input (doc, paste, link)
- [ ] `/sdd:backlog add` — added at least one backlog item
- [ ] `/sdd:start` — started a cycle (from backlog or directly)
- [ ] `/sdd:status` — read the state of an active cycle
- [ ] `/sdd:implement` — executed at least one task
- [ ] `/sdd:complete` — archived at least one cycle and merged its spec-delta

---

## VKF — Venture Knowledge Foundation (STD-002)

### Core tier (required — all of these)

- [ ] `specs/constitution/mission.md` is filled in (no `[REQUIRED]` placeholders), stating what your venture does and for whom in one sentence, plus the reason it exists
- [ ] `specs/constitution/pmf-thesis.md` is filled in with a named customer, problem, solution, and at least one honest evidence statement (or an explicit "we don't know yet")
- [ ] `specs/constitution/principles.md` has ≥ 3 product principles, each a deliberate choice (not generic "write good code" platitudes)
- [ ] `specs/constitution/index.md` links to all Core sections and shows their status
- [ ] `/vkf/validate` exits with `structure: PASS` and `constitution: PASS`

### Extended tier (adopt when relevant)

- [ ] If you have multiple user types → `personas.md` is filled in
- [ ] If you have a B2B motion → `icps.md` is filled in
- [ ] If you have identifiable competitors → `positioning.md` is filled in
- [ ] If > 1 person will amend the constitution → `governance.md` is filled in

### Discipline

- [ ] You have used `/vkf/amend` — not direct-edit — for at least one change to a filled-in constitution file
- [ ] You can state, without looking, what the four amendment tiers (C0 / C1 / C2 / C3) are and when each applies
- [ ] You have at least one entry in `specs/ingestion-log.yaml` from `/vkf/ingest`
- [ ] You have at least one known unknown tracked (or explicitly logged `gap_suppressions`)

---

## SDD — Spec-Driven Development (STD-001)

### Repository structure

- [ ] `specs/features/` has at least one feature directory with a canonical `spec.md`
- [ ] `archive/` has at least one completed cycle
- [ ] `changes/` is empty OR contains only work-in-progress cycles (no stale ones)

### Cycle discipline

- [ ] At least one cycle in `archive/` has:
  - [ ] A `proposal.md` with Problem / Solution / Scope / Alternatives / Risks / Rollback
  - [ ] A `spec-delta.md` with ADDED / MODIFIED / REMOVED sections using **Given / When / Then** scenarios — including error cases
  - [ ] A `tasks.md` with every box checked `[x]`
- [ ] The feature spec in `specs/features/` that came from that cycle is readable on its own — not a diff, an actual description of current behavior
- [ ] Your commit history on that cycle uses the conventions: `[spec]` for spec work, `[impl]` for code, `[archive]` for the archive commit
- [ ] You started the cycle with `/sdd:start` (not by mkdir-ing a folder manually)

### Judgement

- [ ] You can state, without looking, when a change does NOT need a cycle (bug fix restoring spec, pure refactor, config/deps/docs only)
- [ ] You've used `/sdd:explore` OR you can explain why you skipped it
- [ ] You've used the backlog (`/sdd:backlog`) OR you can explain why you went direct to `/sdd:start`

---

## Knowledge accumulation & cumulative learning

- [ ] `learnings.yaml` has ≥ 3 entries from your cycle(s), each with a concrete, non-generic insight
- [ ] You've captured at least one constitutional insight that emerged during implementation — something you didn't know when you wrote the constitution — and either amended the constitution or logged it as a known unknown
- [ ] Your repo has no "orphan knowledge": no pasted docs, meeting notes, or research-output sitting outside of either `specs/` or an ingestion log
- [ ] `CLAUDE.md` is customized for your venture (tech stack, tracker, any venture-specific routing) — not left at template defaults

---

## Mindset & Disrupt Labs standards

You can, without looking, answer:

- [ ] Why is STD-002 a prerequisite for STD-001? (Because SDD manages change against a specification, which doesn't exist until VKF is in place.)
- [ ] What is the litmus test for "this change needs a cycle" vs "this change doesn't"? (Does it alter observable behavior, per STD-001 §2?)
- [ ] What is the 5-type knowledge taxonomy in STD-002? (Constitution, Architecture, Features, UX, Reference.)
- [ ] What is the difference between "we don't know" suppression and a known unknown? (Suppression declares a heuristic inapplicable; a known unknown is a specific gap tracked for resurfacing.)
- [ ] Why is documentation code? (It's versioned, reviewed, lives next to the implementation, and is the authoritative input to both engineers and agents.)

---

## The bar

**You are onboarded when every box above is ticked and an onboarding buddy has walked your fork with you and agrees.**

Not when you've read everything. Not when it "feels like" you get it. When the fork itself demonstrates the discipline.

---

## After onboarding

Forks are artifacts, not deliverables — you aren't expected to keep maintaining your onboarding fork after you're onboarded. The point is that the discipline is now yours. Carry it into whichever venture you join next.
