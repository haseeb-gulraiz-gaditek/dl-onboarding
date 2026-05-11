---
name: Hackathon retrospective
description: Post-demo reflection on what worked and what fought back when building Mesh under STD-001 (SDD) + STD-002 (VKF).
type: reference
last_reviewed: 2026-05-11
---

# Hackathon retrospective

> 5 days · 16 SDD cycles · 13 feature specs · 321 backend tests · 1 cinematic demo. Written the day after demo-day while it's still fresh.

The structured per-cycle insights live in `learnings.yaml`. This file is the human-scale story: where the discipline earned its keep, and where it fought back.

---

## Frictions (where SDD + VKF fought back)

**Task explosion on small backlog items.** A basic feature sometimes spawns more spec-delta tasks than the change deserves. The discipline's overhead is roughly fixed — proposal + spec-delta + tasks + commit conventions + archive — so it amortizes badly across small items. Future-me should be quicker to apply the STD-001 §2 exceptions (bug fix, refactor, config, docs) and skip the full cycle when the change genuinely doesn't alter observable behavior. Tracking-everything-as-a-cycle feels safer; it isn't.

**VKF tangents.** Question prompts inside `/vkf/constitution` and `/vkf/research` drill into adjacent questions you didn't come in for. Useful for exploration, costly when you have a specific decision to make and a clock. The fix: bound the session — set a target outcome *before* invoking the command — and capture the side-quest as a known-unknown via `/vkf/gaps` rather than letting it derail the current draft.

**No parallel cycles.** Independent backlog features still queue serially through `.claude/state/sdd-state.yaml`'s single `current_cycle` slot. Can't fan two cycles out across different agents and merge their archives later. For a hackathon solo this is fine; for a team it would be a real bottleneck. Candidate STD-001 v1.6 improvement: support multiple parallel cycles keyed by branch.

---

## Where it helped (where SDD + VKF earned their keep)

**VKF sharpens fuzzy thinking.** "Mesh should recommend tools" became a clear written direction — mission + pmf-thesis + personas + principles + positioning + icps + governance, ~250 lines of decisions across eight files. The structure forces you to answer questions you'd otherwise skip: who exactly is this for, what do we never compromise on, how do we behave when revenue and principles conflict. That clarity persists across cycles, and it's the thing every implementation gets aligned against without re-discovering.

**SDD removes architecture surprises.** Every ambiguity in a feature is forced out into the spec-delta (ADDED / MODIFIED / REMOVED with Given/When/Then scenarios) before code is written. The cost is up-front clarity; the payoff is that implementation became mechanical execution of decisions already made on paper. Almost every late-cycle "surprise" turned out to be something the spec-delta didn't pin down — meaning the spec was the lesson, not the code.

**Repo as the thinking trail.** Every spec, every navigated direction, every amendment, every learning lives in-repo as versioned markdown. Nothing was lost to chat. Future contributors (and future-me) can reconstruct *why* a decision was made by reading `archive/{slug}/proposal.md` alongside the spec it merged into `specs/features/`. Knowledge is not in someone's head, not in Notion, not in Slack — it's in the source tree next to the code it constrains.

---

## In numbers

| | |
|---|---|
| SDD cycles started → archived | 16 → 16 (zero abandoned, zero stale) |
| Feature specs landed | 13 (each readable as current behavior, not a diff) |
| `learnings.yaml` entries | 57 (CHECKLIST bar is ≥3) |
| Constitution files filled | 8 / 8 — zero `[REQUIRED]` placeholders |
| C2 amendments recorded | 1 (cycle #8 launch-in-recs slot) |
| Ingestion-log entries | 2 (ING-001 idea docs · ING-002 scratch migration) |
| Backend tests | 321 passing |
| Frontend routes | 18 compiling clean |

---

## What I'd carry into the next venture

1. **Cycle granularity tuned by change size.** Three small cycles beat one mega-cycle for review fidelity. Don't conflate "one user story" with "one cycle."
2. **Bound the VKF tangent.** Decide what you came in for before invoking the command; bank everything else as a gap.
3. **The repo IS the deliverable.** Slides and demos are downstream artifacts; the spec + the test suite + `learnings.yaml` are what carry forward.
