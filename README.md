# Disrupt Labs — Engineer Onboarding Template

A fork-and-go template for onboarding engineers to the **Disrupt Labs way of building ventures**: grounded in [STD-002 Venture Knowledge Foundation (VKF)](docs/standards/std-002-venture-knowledge-foundation/standard.md) and [STD-001 Spec-Driven Development (SDD)](docs/standards/std-001-spec-driven-development/standard.md).

> The reference for these standards — the full curriculum, convictions, and tooling — lives in [`disrupt-gt/course-materials`](https://github.com/disrupt-gt/course-materials). **This repo is the hackathon template.** Fork it, build something small but real, and onboard yourself by shipping.

---

## Who this is for

1. **Existing Disrupt Labs engineers** — front-end, back-end, AI, data, full-stack — using this as a reference refresh.
2. **New engineers being onboarded** — running through the journey end-to-end, solo, in pairs, or in teams of ≤3.
3. **Any engineer** who wants to conform to how Disrupt Labs builds ventures: knowledge accumulation, cumulative learning, SDD, and VKF.

---

## What you get when you fork

- **The VKF toolchain** — `/vkf/init`, `/vkf/constitution`, `/vkf/amend`, `/vkf/ingest`, `/vkf/gaps`, `/vkf/freshness`, `/vkf/validate`, `/vkf/research`, `/vkf/transcript`, `/vkf/audit`, `/vkf/okrs`, `/vkf/workflow`
- **The SDD toolchain** — `/sdd:start`, `/sdd:explore`, `/sdd:implement`, `/sdd:complete`, `/sdd:status`, `/sdd:backlog`, `/sdd:run-all`
- **Supporting skills** — `disrupt-sdd`, `venture-foundation`, `loop-scaffold`, `dsrpt-knowhow`
- **The standards** themselves — STD-001 (SDD), STD-002 (VKF), STD-003 (Venture Metrics) — full source, CHANGELOGs, and references
- **An onboarding journey** — [`ONBOARDING.md`](ONBOARDING.md) — day-1 → first shipped feature via a proper SDD cycle
- **A self-assessment checklist** — [`CHECKLIST.md`](CHECKLIST.md) — the minimum bar you must clear to be considered "onboarded"

---

## Quickstart (≈10 minutes)

```bash
# 1. Fork this repo on GitHub, then clone your fork
git clone git@github.com:<your-username>/dl-onboarding.git my-venture
cd my-venture

# 2. Open it in Claude Code
claude

# 3. Get oriented
/lay-of-the-land

# 4. Start the onboarding journey
# Read: ONBOARDING.md
```

Then follow [ONBOARDING.md](ONBOARDING.md) step-by-step. You'll bootstrap a constitution, propose a first feature, ship it through a full SDD cycle, and score yourself against [CHECKLIST.md](CHECKLIST.md).

---

## Repository layout

```
dl-onboarding/
├── README.md                # You are here
├── CLAUDE.md                # Project conventions — SDD/VKF routing for Claude Code
├── ONBOARDING.md            # Day-1 → first shipped feature journey
├── CHECKLIST.md             # Self-assessment: are you onboarded?
├── .claude/                 # Commands, skills, agents, hooks, state
├── specs/
│   ├── constitution/        # Created by /vkf/init — who you are, what you build
│   └── features/            # Grown by /sdd:complete — current behavior
├── changes/                 # Active SDD cycles
├── archive/                 # Completed SDD cycles
├── backlog/                 # Lightweight work queue (optional)
├── docs/
│   ├── onboarding/          # Step-by-step onboarding modules
│   └── standards/           # STD-001, STD-002, STD-003 — full source
└── learnings.yaml           # Per-cycle insights surfaced by /sdd:complete
```

---

## Why this shape

- **Fork and build something real.** Reading about SDD/VKF teaches you nothing. Shipping one small feature through a full cycle teaches you everything. Solo is fine; pairs are better; teams of 3 max.
- **Template, not tutorial.** This repo is the real scaffold you'd use to start a venture. The onboarding journey walks you through *using it*, not a parallel toy.
- **Checklist-driven.** You're onboarded when the checklist passes. Not when you've read everything.
- **Cumulative, not one-shot.** Everything you learn ends up in `learnings.yaml`, the constitution, or a feature spec. No insight should leave your head without a home in the repo.

---

## Reference

- **Standards source of truth:** [`disrupt-gt/course-materials/content/standards/`](https://github.com/disrupt-gt/course-materials/tree/main/content/standards)
- **Full curriculum:** [`disrupt-gt/course-materials`](https://github.com/disrupt-gt/course-materials) (12 courses on Claude Code mastery, agentic frameworks, context engineering, SDD, and venture building)
- **This template's purpose:** Give engineers a fork-and-go starting point so the standards in course-materials can be *practiced*, not just read.

---

Questions? Ask in `#engineering` on Slack. Improvements to the template? Open a PR against this repo.
