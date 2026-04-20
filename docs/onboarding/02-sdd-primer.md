# 02 — SDD Primer

Just enough SDD to start a cycle without embarrassing yourself. For the full spec see [`docs/standards/std-001-spec-driven-development/standard.md`](../standards/std-001-spec-driven-development/standard.md).

**Time:** ~15 minutes.

---

## The one-sentence version

> Every change that alters observable behavior is preceded by a written spec, reviewed like code, that lives in the repo and is the source of truth.

Everything else in STD-001 is machinery for making this work smoothly — commands, templates, state tracking, archival.

---

## What counts as "observable behavior"

Ask: *could a user, operator, caller, or consumer of this system notice the difference?* If yes, it's observable. If no, it isn't.

| Scenario | Observable? | Needs a cycle? |
|---|---|---|
| Add a new API endpoint | Yes | Yes |
| Change the shape of an existing API response | Yes | Yes |
| Swap an internal sorting algorithm (same output) | No | No |
| Rename a private helper function | No | No |
| Change how errors are presented in the UI | Yes | Yes |
| Bump a dependency version (no behavior change) | No | No |
| Fix a bug to restore specified behavior | — (restoring) | No (reference the spec in commit) |
| Fix a bug that exposes unspecified behavior | Yes (implicit spec) | Often yes — write the spec |
| Change database schema | Yes | Yes |
| Add a CI check | No (behavior) but … | No cycle, but update dev docs |

The honest call: *when in doubt, start a cycle.* The overhead is low. Spec-deltas don't have to be long.

---

## Anatomy of a cycle

A cycle lives under `changes/{slug}/` while active:

```
changes/add-csv-export/
├── proposal.md      # Problem / Solution / Scope / Alternatives / Risks / Rollback
├── spec-delta.md    # ADDED / MODIFIED / REMOVED  (with Given/When/Then)
└── tasks.md         # Implementation checklist
```

On `/sdd:complete`:

1. `spec-delta.md` is merged into `specs/features/{feature}/spec.md` (canonical)
2. `changes/{slug}/` is moved to `archive/{slug}/`
3. Insights flow into `learnings.yaml`
4. A PR is opened against `main`

---

## The canonical spec format: Given / When / Then

Every requirement — including error cases — uses this shape.

```gherkin
Given [precondition]
When [action]
Then [expected outcome]
```

Example:

```gherkin
Given a user has at least one saved query
When they request CSV export from the Results page
Then they receive a CSV file named "{query-title}-{YYYYMMDD}.csv" containing all current result rows

Given a user has zero saved queries
When they attempt CSV export
Then they see the inline message "No queries to export" and no file is downloaded
```

Notice: both the happy path *and* the error case are specified. That's required. An unspecified error case is a bug waiting to happen — and the next cycle's author won't know what "correct" looks like.

---

## When you start a cycle

```
/sdd:start add-csv-export
```

- Creates `changes/add-csv-export/` with the three templates pre-filled with prompts.
- Creates a cycle branch, e.g. `001-add-csv-export`, off your current HEAD.
- Updates `.claude/state/sdd-state.yaml` with the new `current_cycle`.
- Surfaces *tensions* — constitutional conflicts, spec conflicts, hidden scope — so you address them in the proposal before you write code.

If you've been exploring first:

```
/sdd:explore add-csv-export        # creates wip/add-csv-export/ with investigation notes
/sdd:start add-csv-export          # pre-fills proposal from the investigation
```

If you've queued the work on the backlog:

```
/sdd:backlog add "Export results as CSV"    # → backlog:3
/sdd:start --from backlog:3
```

---

## When you implement

```
/sdd:status       # shows phase, unchecked tasks, recent commits
/sdd:implement    # executes the next unchecked task, marks it [x]
```

Rules:

- The spec-delta is the contract. Implementation must satisfy every Given/When/Then scenario.
- If you discover the spec is wrong mid-implementation, **don't silently change the code** — update the spec-delta first, *then* the code. The spec is the source of truth.
- Commit with `[impl]` prefix: `git commit -m "[impl] csv export: happy path"`.

---

## When you complete

```
/sdd:complete
```

This:

1. Verifies all tasks are `[x]`.
2. Verifies each Given/When/Then holds in the implementation (prompts you to confirm, and — when feasible — runs tests).
3. Merges `spec-delta.md` into `specs/features/{feature}/spec.md`. Commits with `[spec]`.
4. Moves `changes/{slug}/` to `archive/{slug}/`. Commits with `[archive]`.
5. Extracts insights to `learnings.yaml`.
6. Pushes the branch and opens a PR.

If you tried to run `/sdd:complete` on an incomplete cycle, it will refuse and tell you what's missing. That's the point.

---

## Commit conventions

```
[spec]    …   changes to specs/ (the spec-delta merge on complete, or a standalone spec edit)
[impl]    …   implementation commits inside a cycle
[archive] …   the archive commit on /sdd:complete
[fix]     …   bug fix that restores specified behavior
[chore]   …   config, deps, docs — no cycle needed
```

---

## Common mistakes

1. **Skipping the spec-delta because "it's obvious".** If it's obvious, writing it takes 90 seconds. If it's not obvious, skipping it means you're about to ship something you don't fully understand.
2. **Writing the spec-delta in the past tense after you've coded it.** This defeats the point. The spec-delta is how you *think through* the change, not how you document what happened.
3. **Cycling for refactors.** If a refactor genuinely has no behavioral change, no cycle is needed. Don't burn the ceremony where it adds no value.
4. **Letting `changes/` accumulate stale cycles.** If a cycle is abandoned, close it — move it to archive with a `[archive] abandoned: {reason}` commit, or delete the directory. Don't leave orphans.
5. **Editing `archive/` after the fact.** Archives are history. If you need to change behavior, start a new cycle.

---

**Next:** [03 — VKF primer](03-vkf-primer.md)
