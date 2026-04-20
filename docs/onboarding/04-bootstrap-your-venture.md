# 04 — Bootstrap Your Venture

Time to actually do the thing. You'll run `/vkf/init`, fill in the Core constitution for your chosen venture idea, and validate.

**Time:** 1–2 hours. Less if you already know exactly what you're building. More if your venture idea needs refinement — that's fine, refining the idea *is* the work.

---

## Before you start

You should have:

- **A venture idea.** Small. One-sentence describable. Completable in a day or two.
- **Your fork** of this repo, cloned locally, open in Claude Code.
- **Some willingness to commit to the idea.** You can change your mind, but the constitution process is much better when you're aiming at a specific thing. *"Some kind of AI tool for engineers"* is too vague. *"A CLI that watches a git repo and warns when PRs drift from the linked issue's acceptance criteria"* is concrete enough.

---

## Step 1 — Initialize the foundation

In Claude Code, run:

```
/vkf/init
```

This creates:

- `specs/constitution/` with 8 scaffolded files (Core + Extended), each with `[REQUIRED]` placeholders
- `specs/features/` (empty)
- `changes/` and `archive/` (empty)
- Updates `.claude/state/vkf-state.yaml` with `initialized_at` timestamp

Open the files it created. Read through the `[REQUIRED]` prompts in each.

> If you're a team of 2–3, assign different sections to different people for first draft. Reconvene for review. Two sets of eyes catch placeholder-prose much faster than one.

---

## Step 2 — Draft the Core constitution

Run, for each Core file:

```
/vkf/constitution mission
/vkf/constitution pmf-thesis
/vkf/constitution principles
```

`/vkf/constitution` is interactive. Claude Code will ask you questions — answer them honestly, not aspirationally. The goal is clarity, not marketing copy.

### mission.md — tips

- One sentence. One. If you can't do it in one, you don't yet know what you're building.
- Use active voice: "We build X for Y so that Z." Not "Our platform enables users to…"
- Vision vs. mission: mission is today's verb, vision is the end state. Keep them distinct.

**Bad:** *"Our mission is to leverage cutting-edge AI to empower engineers with transformative productivity."*
**Better:** *"We build a CLI that warns when pull requests drift from their linked issue's acceptance criteria, so that teams catch scope creep before review."*

### pmf-thesis.md — tips

- **Customer:** specific enough that you could name three. Not "developers" — that's a market, not a customer.
- **Problem:** stated as an experience the customer has, not as a feature you could build. "PRs get merged that don't do what the issue asked for" (problem). Not "there's no automated drift detection" (feature).
- **Solution:** describe the outcome, not the mechanism. "Drift is caught at PR review time with a single comment" (outcome). Not "A GitHub App that diffs descriptions" (mechanism).
- **Evidence:** cite what you actually have. Two interviews, a log of your own frustrations, a thread on Hacker News. "We don't have evidence yet" is a legitimate answer — mark it as a known unknown via `/vkf/gaps` later.

### principles.md — tips

- 3 to 8 principles. More than 8 means you haven't decided what matters most.
- Each principle should be **a decision** — something where the opposite is a real alternative you're rejecting. Not a platitude.
- Format: short title + one paragraph explaining the decision and why.

**Bad:** *"We value quality code."* (Nobody values bad code. This is not a decision.)
**Better:** *"We prefer one shipping feature to three half-finished ones. When forced to choose between scope and shipping, we cut scope — even if it means an ugly v1 — because learning requires users, and users require a shipped thing."*

### index.md

Usually filled in automatically by `/vkf/init`, but review it after drafting to make sure each section link is correct and the status matches reality.

---

## Step 3 — Decide on Extended sections

Ask yourself, for each:

- **personas.md** — Do I have >1 distinct type of user with different goals / workflows / pain points? If yes, draft it. If not (e.g., your tool has exactly one user role), skip it.
- **icps.md** — Am I selling to companies? If yes, draft it. If not, skip it.
- **positioning.md** — Can I name 2+ real competitors? If yes, draft it. If not, skip — you'll fabricate positioning without real context.
- **governance.md** — Is there more than one person on this venture? If yes, at minimum note who amends what. If solo, skip.

For the ones you skip, *delete the file* so `/vkf/validate` doesn't flag it as unfilled. You can always re-create it when you need it.

For the ones you adopt, run `/vkf/constitution {section}` for each and fill them in.

---

## Step 4 — Validate

```
/vkf/validate
```

Expected output on a well-bootstrapped foundation:

```
structure:    PASS
constitution: PASS
freshness:    PASS (all docs fresh — just created)
workflows:    PASS
std001_ready: true
```

If you see `FAIL` or `WARN`, fix what it tells you. Common issues:

- `[REQUIRED]` placeholders still in a filled-in file → go finish it
- Missing Core file → run `/vkf/init` again or create by hand
- Invalid path in `vkf-state.yaml` → check `constitution_root` setting

---

## Step 5 — Commit

```
git add specs/ .claude/state/vkf-state.yaml
git commit -m "[foundation] Initial constitution for {your-venture-name}"
```

Use the `[foundation]` prefix for the initial bootstrap. Future changes to the constitution use `[constitution]` (for amendments) or `[ingest]` (for ingested content).

---

## Reflection before moving on

Before you start shipping features, pause and ask:

- **Would someone reading only my `mission.md` know what I'm building?** If no, go back.
- **Is my `pmf-thesis.md` honest about what I don't know?** Guessing is worse than explicitly acknowledging the gap.
- **Do my principles encode actual decisions?** If any principle could be uttered by any engineer at any company, it's a platitude — replace it.

This isn't gold-plating. The constitution is the specification your first feature cycle will be measured against. Weak constitution, weak spec, weak feature.

---

**Next:** [05 — Your first SDD cycle](05-first-sdd-cycle.md)
