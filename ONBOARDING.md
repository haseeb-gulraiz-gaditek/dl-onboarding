# Onboarding: Day 1 → First Shipped Feature

A hands-on, hackathon-style walkthrough. Solo, pair, or team of up to 3.

**Target:** 1–3 days of focused work. Ship one small but real feature through a full SDD cycle, against a constitution you wrote yourself. Finish by passing [`CHECKLIST.md`](CHECKLIST.md).

**What you're building:** You choose. Pick a venture idea simple enough to scope in a day — a CLI tool, a small web service, a Claude Code skill, a focused agent, a data pipeline. The *point* is the process, not the product.

---

## The path

1. **[01 — Welcome & orientation](docs/onboarding/01-welcome.md)** — why SDD + VKF exist, the mental model
2. **[02 — SDD primer](docs/onboarding/02-sdd-primer.md)** — what a cycle looks like, when to use it, when to skip
3. **[03 — VKF primer](docs/onboarding/03-vkf-primer.md)** — the 5-type knowledge architecture, amendment tiers
4. **[04 — Bootstrap your venture](docs/onboarding/04-bootstrap-your-venture.md)** — `/vkf/init`, draft the Core constitution
5. **[05 — Your first SDD cycle](docs/onboarding/05-first-sdd-cycle.md)** — propose, implement, ship
6. **[06 — Knowledge management in practice](docs/onboarding/06-knowledge-in-practice.md)** — ingestion, gaps, freshness, amendments
7. **[07 — Self-assessment](CHECKLIST.md)** — score yourself against the checklist

---

## Rules of engagement

- **Do it in the repo, not in your head.** Every insight goes to `learnings.yaml`, the constitution, or a feature spec.
- **Use the commands, don't work around them.** The point of `/vkf/amend` and `/sdd:start` is to internalize the discipline. Editing files by hand defeats the onboarding.
- **Small scope is better than impressive scope.** You will learn more from one shipped cycle on a tiny feature than from three half-finished cycles on a big one.
- **Ship to `main`.** Complete the SDD cycle to the point where `/sdd:complete` runs cleanly and the feature spec lands in `specs/features/`.
- **Reflect at the end.** The final `learnings.yaml` entries are the real deliverable. They're what you'd tell the next engineer onboarding.

---

## If you get stuck

- **The command doesn't do what you expect?** Read the command's file in `.claude/commands/` — they are human-readable.
- **VKF vs SDD confusion?** VKF governs *who you are and what you build* (constitution, feature-spec layout). SDD governs *how you change what you build* (cycles, proposals, spec-deltas). Knowledge → VKF. Change → SDD.
- **Constitution question you can't answer?** Mark it as a known unknown via `/vkf/gaps`. Don't fabricate.
- **Feature change feels too small for a cycle?** It probably is — apply the "bug fix / refactor / config-only" exceptions in STD-001 §2.
- **Still stuck?** Ask in `#engineering` on Slack. Tag what you tried.

---

## When you finish

You're done when:

- [`CHECKLIST.md`](CHECKLIST.md) passes end-to-end.
- Your fork's `main` has at least one feature spec in `specs/features/` landed via `/sdd:complete`.
- Your `learnings.yaml` has ≥ 3 entries with genuine insights (not rote platitudes).
- You can explain, without looking, when to use `/vkf/amend` vs `/vkf/ingest` vs `/vkf/constitution`, and when to start a cycle vs not.

Then share your fork URL with your onboarding buddy or manager. They'll walk the checklist with you and either ratify you as onboarded or point at what's missing.
