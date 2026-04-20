# 05 — Your First SDD Cycle

The main event. You'll pick the smallest feature that makes your venture real, propose it, implement it, and ship it through `/sdd:complete`.

**Time:** 3 hours to 2 days, depending on scope. Smaller is better.

---

## Step 1 — Pick the first feature

This is the single hardest decision in the onboarding. Not because the answer is hard to find, but because the temptation to pick something more impressive is strong.

**Rules for the first feature:**

- **It must be observable end-to-end.** Not internal plumbing. A user (or a caller, or an operator) can tell whether it works.
- **It must be shippable in < 1 day of work.** If you think it's 1 day, it's probably 2. If you think 2, it's probably 4. Scope *ruthlessly*.
- **It must be real.** Not a "hello world" that proves you can run a build. A real slice of the product's value.

**Good examples (using the "PR drift CLI" venture idea):**

- *"Given a local git repo with an open PR that links to an issue, when the user runs `drift check`, then the CLI prints the linked issue's acceptance criteria and the PR's current diff summary side-by-side."*
- Observable? Yes — the user sees output.
- < 1 day? Yes — GitHub API read + format.
- Real? Yes — this is the core read path of the product.

**Bad examples:**

- *"Set up the CLI framework and add `--help`."* — Not observable as product value. Plumbing.
- *"Full drift detection with AI-powered comparison."* — Not < 1 day. Two or three cycles worth.
- *"Dark mode."* — Not real product value on day one.

If you're paired up, discuss the candidate feature for 10 minutes. If you both still like it after 10 minutes, it's probably OK. If one of you is already hedging, scope it smaller.

---

## Step 2 — Backlog (optional but recommended)

```
/sdd:backlog add "CLI: drift check command — prints issue ACs and PR diff summary"
```

This gives you an ID (e.g. `backlog:1`) you can reference in `/sdd:start`. Even for a one-cycle project, using the backlog practices the flow. Later, when you're working on a real venture with multiple queued features, the same motion scales.

---

## Step 3 — (Optional) Explore

If the feature has real ambiguity — how do we handle repos without a linked issue? what if the issue has no ACs? — run `/sdd:explore` first:

```
/sdd:explore drift-check
```

This creates `wip/drift-check/` with investigation notes. Use it to think through corner cases, API shapes, trade-offs. Then:

```
/sdd:start drift-check
```

`/sdd:start` will pre-fill the proposal from your investigation.

If the feature is genuinely simple and you already know how you'll build it, skip exploration and go straight to `/sdd:start`.

---

## Step 4 — Start the cycle

```
/sdd:start drift-check
```

or if you backlogged it:

```
/sdd:start --from backlog:1
```

Claude Code will:

1. Check git state is clean, create a cycle branch (e.g. `001-drift-check`).
2. Create `changes/drift-check/` with `proposal.md`, `spec-delta.md`, `tasks.md` — all pre-populated with prompts.
3. Update `.claude/state/sdd-state.yaml` with the active cycle.
4. Surface tensions — e.g., "this feature implies a new feature directory `cli-commands/` which doesn't exist yet; that's fine, but confirm."

---

## Step 5 — Fill in proposal.md

Key sections:

- **Problem** — What is broken / missing / painful *from the perspective of a user of your venture*. Not from the perspective of your codebase.
- **Solution** — The proposed change, in outcome terms. Not implementation detail.
- **Scope** — What's in, what's out. Be explicit about both.
- **Alternatives** — At least one other approach considered and why it was rejected. "None considered" is almost always wrong and signals insufficient thought.
- **Risks** — What could go wrong. What dependencies might break. What constitutional principles this might strain.
- **Rollback** — How do you undo this if it's a bad call.
- **Dependencies** — External libraries, services, auth flows.

**Tension check:** Before finishing the proposal, re-read your constitution. Does this feature conflict with any principle? If yes, either the feature needs to change, or the principle does (C3 amendment). Don't proceed until you've resolved the tension. Sweeping conflicts under the rug is how ventures drift.

---

## Step 6 — Fill in spec-delta.md

Three sections: **ADDED**, **MODIFIED**, **REMOVED**. For a first feature, everything is ADDED. Use Given/When/Then for every requirement. Include error cases.

Example skeleton:

```markdown
## ADDED

### Feature: drift check

#### Scenario: successful drift report
Given the current working directory is inside a git repository with an open PR
And the PR body contains an issue link in the form "closes #123" or "fixes #123"
When the user runs `drift check`
Then the CLI prints two sections:
    - "Issue #123 — Acceptance Criteria": the bulleted AC block from the linked issue
    - "PR Diff Summary": a one-line-per-file summary of the PR's current changes

#### Scenario: no linked issue
Given the current PR body contains no issue link
When the user runs `drift check`
Then the CLI exits with code 1 and prints "No issue link found in PR body. Expected 'closes #N' or 'fixes #N'."

#### Scenario: linked issue has no AC block
Given the PR links to an issue whose body has no discernible AC block
When the user runs `drift check`
Then the CLI prints the PR diff summary and a warning: "Linked issue #123 has no recognizable acceptance criteria."
And exits with code 0
```

Two markers of a good spec-delta:

1. Every happy path has a matching error path.
2. A second engineer, reading only the spec-delta, could reproduce the intended behavior.

---

## Step 7 — Fill in tasks.md

A checklist of concrete implementation tasks. Keep each task small enough that `/sdd:implement` can do one in one session.

```markdown
- [ ] Set up CLI scaffolding (argument parsing, help text)
- [ ] Implement git repo detection (`git rev-parse --show-toplevel`)
- [ ] Implement current PR detection (`gh pr view --json`)
- [ ] Parse issue link from PR body (regex: closes/fixes #N)
- [ ] Fetch issue body via `gh issue view`
- [ ] Extract AC block (heading-based parse)
- [ ] Format diff summary (`gh pr diff --name-only` + grouped counts)
- [ ] Print combined report
- [ ] Handle no-link case with exit code 1
- [ ] Handle no-AC-block case with warning
```

---

## Step 8 — Commit the spec before coding

```
git add changes/drift-check/
git commit -m "[spec] drift-check: propose, spec-delta, tasks"
```

**This is the critical discipline.** The spec exists, reviewed, before code exists. Even if you're solo. Especially if you're solo.

---

## Step 9 — Implement

Loop:

```
/sdd:status       # see what's next
/sdd:implement    # work the next unchecked task
```

Rules:

- One task per `/sdd:implement` invocation, in most cases. Larger tasks can be split mid-flight.
- After each task, commit with `[impl]` prefix: `git commit -m "[impl] drift-check: parse issue link from PR body"`.
- If you discover the spec is wrong, **stop.** Update `spec-delta.md` first (commit with `[spec]`), then continue implementation.
- If you discover a scope creep opportunity, resist. Add it to the backlog for a future cycle; don't smuggle it into this one.

---

## Step 10 — Verify

Before running `/sdd:complete`, manually walk through each Given/When/Then scenario in your spec-delta. Confirm the implementation actually does what the scenario says. Run tests if you have them.

This is where the discipline pays off. If any scenario doesn't hold, you have a bug — or your spec-delta was wrong. Either way, fix it *now*, not after archival.

---

## Step 11 — Complete

```
/sdd:complete
```

This will:

1. Confirm all tasks `[x]`.
2. Ask you to confirm each scenario holds.
3. Merge `spec-delta.md` into `specs/features/drift-check/spec.md`. Commit `[spec]`.
4. Move `changes/drift-check/` → `archive/drift-check/`. Commit `[archive]`.
5. Prompt for learnings to add to `learnings.yaml`.
6. Push the branch and open a PR via `gh`.

If step 1 or 2 fails, `/sdd:complete` refuses to proceed. Fix what's flagged and re-run.

---

## Step 12 — Reflect in learnings.yaml

Don't skip this. What surprised you? What was harder than expected? Easier? What would you tell the next engineer onboarding?

```yaml
learnings:
  - date: 2026-04-22
    cycle: "drift-check"
    insight: "The hardest part of the first cycle wasn't implementation — it was scoping the spec-delta tightly. First draft had 7 scenarios; shipping version had 3 happy + 3 error. The cut scenarios were backlog material, not first-cycle material."
    category: "process"
```

A good learning is specific, non-obvious, and something you'd actually say to a teammate in a hallway. Not "writing specs is useful" (generic). Yes, "spec-deltas drift during implementation more than you'd expect — plan to edit them mid-cycle" (specific, non-obvious).

---

**Next:** [06 — Knowledge management in practice](06-knowledge-in-practice.md)
