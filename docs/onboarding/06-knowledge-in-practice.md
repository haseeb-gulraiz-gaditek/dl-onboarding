# 06 — Knowledge Management in Practice

You've shipped a feature. Now you use VKF the way you'd use it in a real venture, day after day. This module is about the habits, not just the commands.

**Time:** 30–60 minutes.

---

## The cycle that surfaced something unexpected

Almost always, shipping a feature teaches you something about the venture itself. Maybe a persona you hadn't considered showed up in the spec. Maybe a principle you wrote down turned out to be wrong in practice. Maybe a key assumption in your PMF thesis started to wobble.

**This is where cumulative learning happens.** Most engineers feel the surprise, ship the feature, and forget. At Disrupt Labs, the surprise goes somewhere — amendment, known unknown, ingestion, or at minimum a `learnings.yaml` entry.

Work through these three motions at least once each during onboarding.

---

## Motion 1 — Amendment from a learning

During your first cycle, something about your constitution probably felt off when it met reality. Name it, pick a tier, amend.

### Example

Your `principles.md` said: *"We prefer shipped v1 over polished v2."* During implementation you noticed you were tempted to polish before shipping — and it produced a *better* first feature. You want to nuance the principle.

Run:

```
/vkf/amend principles
```

Claude Code will:

1. Announce the amendment tier. Rewording a principle that changes emphasis but not direction = **C1 clarification**. Changing direction (e.g., "we prefer polish over speed") = **C2 substantive**. Removing the principle = **C3 structural**.
2. Walk you through the amendment — old text, new text, rationale, propagation check (does this affect any other constitution section?).
3. Commit with `[constitution] C1: clarify shipping-over-polish principle`.

**The lesson:** edits to the constitution always go through `/vkf/amend`. Not `vim`. Not Edit tool in Claude Code that bypasses the ritual. The ritual is how the amendment history stays useful six months later.

---

## Motion 2 — Track a known unknown

Something your cycle revealed you *don't* know. Mark it.

### Example

While implementing drift-check, you realized you have no idea how often PRs actually drift from linked issues in practice. Your PMF thesis implicitly assumed "often enough to matter" — but you don't have data. Don't fake it. Track it.

Run:

```
/vkf/gaps
```

Claude Code scans and lets you declare a new known unknown. Add:

```
KU-001: "Actual drift frequency in real teams' PRs is unknown. Assumed common enough to warrant a CLI in pmf-thesis.md. Resurface in 90 days to decide whether to gather data or retire the assumption."
```

On `/vkf/gaps` resurfacing dates, this reappears. Future-you (or your buddy) will get prompted to resolve it.

**The lesson:** "we don't know" is first-class knowledge. Writing it down beats assuming.

---

## Motion 3 — Ingest a piece of external input

Someone sent you a relevant article / thread / memo / interview transcript. Anything external. Instead of reading and internalizing it (which leaves no trace), route it through `/vkf/ingest`.

### Example

You read a Hacker News thread where engineers complain about PR scope creep. Two quotes feel relevant to your positioning.

Run:

```
/vkf/ingest --inline
```

Paste the content when prompted. Claude Code will:

1. Classify it against the 9-point rubric — probably mostly `positioning.md` (evidence of pain) with some `pmf-thesis.md` (evidence of problem prevalence).
2. Propose placements with confidence scores (HIGH / MEDIUM / LOW).
3. Ask you to confirm or adjust placements.
4. Update the relevant files and log the ingestion in `specs/ingestion-log.yaml`.

**The lesson:** nothing external should live in your head or your Slack. Either it belongs in the repo (routed via ingest) or it's not relevant enough to keep.

---

## The weekly habits

Once you're onboarded and working on a real venture, the habits compress into a short weekly loop:

| Day / cadence | Action | Why |
|---|---|---|
| Every cycle end | `/sdd:complete` → `learnings.yaml` update | Capture what the cycle taught |
| Weekly | `/vkf/freshness` | Catch stale specs before they drift |
| Weekly | `/vkf/gaps` resurfacing check | Old known unknowns may now be answerable |
| Monthly | `/vkf/validate` | Compliance check; catch process decay |
| Quarterly | `/vkf/okrs` update | Re-align activity with stated goals |

None of these are long. Each is under 10 minutes most of the time. Their power is cumulative — the venture that runs them loses less context, drifts less, ships straighter.

---

## The two anti-patterns to watch for

**1. "I'll amend later."**
The moment you hit the constitution in vim because the amendment feels like overhead, you've broken the discipline. Amendment is cheap. The cost of skipping it is a constitution that quietly diverges from what the team actually believes, and an amendment log that stops being a useful historical record.

**2. "I'll ingest the notes later."**
Everyone says this. Nobody does it. The memo sits in Slack; two weeks later it's forgotten; three months later someone re-derives the same insight from scratch. If it's worth ingesting, ingest it while the context is fresh.

---

## Customize CLAUDE.md for your venture

Open the repo's `CLAUDE.md`. Edit the **Tech Stack** and **Tracker Integration** sections to reflect your actual venture. If your venture introduces any venture-specific routing (e.g., "when the user asks about pricing, point them to `specs/pricing/`"), add it.

This is a C2 in spirit (substantive change to project conventions), but `CLAUDE.md` isn't a constitution file — edit it directly, commit with `[chore]` or `[foundation]` prefix. The discipline is lower here, but keeping `CLAUDE.md` fresh is still how Claude Code stays useful across the whole team.

---

**Next:** [Self-assessment: CHECKLIST.md](../../CHECKLIST.md)

Run through every box. Every ticked box should be demonstrable in your fork. If you tick a box you can't demonstrate, you haven't onboarded yet — go back and complete the work the box represents.

When you can tick every box: share your fork with your onboarding buddy or manager. They walk the checklist with you. If they agree on every item — you're onboarded.
