# 01 — Welcome & orientation

Welcome to Disrupt Labs. This repo is the template we expect every engineer — new or existing — to run through once, so the way we build ventures is in your hands, not just your head.

**Time:** ~20 minutes of reading, before you touch any commands.

---

## Why this exists

Most onboarding looks like this: read some docs, watch some videos, get assigned a small ticket, ship it. The person doing the onboarding and the person being onboarded both walk away thinking it worked. Nothing transfers. Six months later the new engineer has quietly invented their own process, and the "Disrupt Labs way" is different for every team.

This onboarding is different. You will *do* the work — bootstrap a venture, write a constitution, ship a real feature through a real SDD cycle, score yourself against a real checklist. The repo itself is the evidence. If the discipline isn't visible in your fork, you haven't onboarded.

---

## The two standards

Everything you'll do in this repo is governed by two Disrupt Labs standards. You should know them by name and by purpose before touching any commands.

### STD-002 — Venture Knowledge Foundation (VKF)

> Every venture must have a constitution and an organized specs layout. That's the foundation the product is built on. Without it, there is no "source of truth" to manage change against.

- **Core files** (required): `mission`, `pmf-thesis`, `principles`, `index` in `specs/constitution/`
- **Extended files** (adopt when relevant): `personas`, `icps`, `positioning`, `governance`
- **Amendment tiers:** C0 cosmetic · C1 clarification · C2 substantive · C3 structural

Full spec: [`docs/standards/std-002-venture-knowledge-foundation/standard.md`](../standards/std-002-venture-knowledge-foundation/standard.md)

### STD-001 — Spec-Driven Development (SDD)

> Every change to observable behavior must be written as a spec *before* code is written. The spec is the source of truth; code is one implementation of the spec.

- **Cycle** = one change going through propose → implement → archive
- **Artifacts** (per cycle): `proposal.md`, `spec-delta.md`, `tasks.md`
- **On complete:** spec-delta merges into `specs/features/{feature}/spec.md`; cycle is archived; learnings captured

Full spec: [`docs/standards/std-001-spec-driven-development/standard.md`](../standards/std-001-spec-driven-development/standard.md)

### Why in this order?

**STD-002 first, then STD-001.** SDD manages change *against a specification*. If you don't have a constitution and a features layout, there is no spec — just chaos. You need foundation before you need process.

---

## The mental model

```
        ┌───────────────────────────────────────────┐
        │  VKF — The Foundation (who / what / why)  │
        │                                           │
        │    specs/constitution/                    │
        │    specs/features/  (current behavior)    │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │  SDD — The Engine of Change               │
        │                                           │
        │    changes/{slug}/  (active cycles)       │
        │    archive/  (completed cycles)           │
        │    learnings.yaml  (what we learned)      │
        └───────────────────────────────────────────┘
```

**Knowledge** lives in the constitution and feature specs. Change that knowledge through the appropriate command — `/vkf/amend` for constitution, `/sdd:start → /sdd:complete` for feature behavior. Never edit these files directly once they're live.

**Work** flows: backlog → cycle → implementation → archived cycle → updated spec. Every step has a command. Internalize the commands; they encode the discipline.

---

## The three things that make this work

1. **Repository-centric knowledge.** The docs live next to the code. They are code — versioned, reviewed, diffable. No Notion. No Google Docs. No tribal knowledge.
2. **Spec before code.** Always. If it changes observable behavior, the spec gets written first, reviewed first, committed first.
3. **Cumulative learning.** Every cycle surfaces something. That something goes into `learnings.yaml` or an amendment or a known unknown. Insight that leaves an engineer's head without going into the repo is insight lost.

---

## Before you continue

- **You don't need to understand every detail yet.** The primers (next two docs) give you just enough to start. You'll learn the rest by doing.
- **Pick a venture idea now.** Small. Completable in a day or two. Something you care about enough to care if it works. This is the feature your fork will ship. *Don't skip this step.*
- **Decide solo or pair.** Both work. Pairs tend to produce better constitutions (two perspectives force clearer thinking). Teams of 3 max — larger groups dilute the doing.

**Next:** [02 — SDD primer](02-sdd-primer.md)
