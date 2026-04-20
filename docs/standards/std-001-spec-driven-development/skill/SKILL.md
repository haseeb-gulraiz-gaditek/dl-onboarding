---
name: disrupt-sdd
description: "Enforce Spec-Driven Development (Disrupt STD-001). Ensures every behavior-changing feature has a specification before implementation begins."
user-invocable: false
---

# Spec-Driven Development (STD-001)

## Purpose

Every code change that modifies observable behavior MUST have a written specification committed before implementation. Specs live in the repository, are reviewed like code, and are the single source of truth for what the system does.

## Always

1. Maintain the required directory structure (see Required Structure below).
2. Create a change proposal (`proposal.md`, `spec-delta.md`, `tasks.md`) BEFORE writing implementation code.
3. Commit proposal artifacts with the `[spec]` prefix before any `[impl]` commits in the same PR.
4. Write specs using Given/When/Then scenarios for every requirement.
5. Include at least one scenario per requirement; specify error cases explicitly.
6. Keep spec files under 500 lines. Split large features into focused specs.
7. Mirror code paths in spec paths (`src/features/auth/` -> `specs/features/auth/spec.md`).
8. On PR merge, move the change directory from `changes/` to `archive/` and merge the spec-delta into canonical `specs/features/` files.
9. Verify every scenario in the spec-delta holds in the implementation before marking a cycle complete. The verification method is project-specific.
10. Before scaffolding a change cycle, read the relevant codebase context, existing specs, and constitution (if present). If the proposed change has tensions with constitutional principles, conflicts with existing specs, technology forks with meaningful trade-offs, or hidden scope implications — surface them before scaffolding and let the user decide.
11. `/sdd:start` MUST create the cycle's branch from the current HEAD and refuse on a dirty working tree. Never commit cycle artifacts to the base branch directly. On slug collision, prefix with `{NNN}-` up to `999-{slug}`.
12. `/sdd:complete` MUST clear `current_cycle` (including `base_branch` and `branch_name`) in a committed step BEFORE pushing or opening a PR. The base branch must never carry non-null active-cycle state.

## Ask First

1. Skipping a proposal for a change that arguably modifies observable behavior -- confirm with the team lead.
2. Splitting or merging spec files -- confirm the new structure with the team.
3. Modifying `specs/constitution.md` -- requires explicit team approval.

## Never

1. Never merge implementation code without the corresponding spec artifacts in the same PR.
2. Never modify canonical `specs/features/` files directly during implementation; use `spec-delta.md` in `changes/`.
3. Never delete or overwrite `specs/constitution.md` without team approval.
4. Never skip error-case scenarios in specifications.

## Red Flag Rationalizations

If you catch yourself thinking any of these, STOP — the proposal is required:

- "This is a simple change, no spec needed"
- "I'll add the spec after I implement"
- "The user said 'just do it' — they don't want a spec"
- "This is just a bug fix" (but it changes observable behavior)
- "I already know what to build, the spec is overhead"
- "The change is so small it doesn't need Given/When/Then"

These are the exact rationalizations that cause spec drift. The standard's core rule is spec-before-code — these rationalizations are how that rule gets eroded in practice.

## Decision: Do I Need a Proposal?

```
Is the change:
  - Adding new features or functionality?          -> YES, proposal required
  - Modifying observable behavior?                 -> YES, proposal required
  - Introducing breaking API changes?              -> YES, proposal required
  - Changing architecture or security patterns?    -> YES, proposal required
  - Altering database schemas?                     -> YES, proposal required
  - Fixing a bug to restore already-specified behavior? -> NO
  - Refactoring with no behavior change?           -> NO
  - Updating config, deps, or docs only?           -> NO
  - Quick idea, design tweak, or bug report?       -> ADD TO backlog (tracker or local)
  - Ready to implement a backlog item?             -> PROMOTE to changes/[slug]/
```

## Backlog Tier (Optional)

For quick ideas, design polish, bug reports, or tech debt—use the lightweight backlog instead of a full proposal.

### Backend

The backlog can use either:
- **External tracker** (Linear, GitHub Issues) via MCP — preferred when available.
  The tracker becomes the single source of truth. No local copy is maintained.
  Items are tagged with an `sdd` label for filtering.
- **Local YAML** (`backlog/items.yaml`) — fallback when no tracker is configured.

When an external tracker is detected, the agent will ask on first use whether to
adopt it as the backlog backend. Use `/sdd/backlog` to add items regardless of
backend — the command routes automatically.

### When to Use

When the user says "backlog this", "add to backlog", or describes a quick fix/tweak that doesn't need a full spec, use `/sdd/backlog` to add items.

### Local Format

```yaml
# backlog/items.yaml
items:
  - summary: "Short description of the work"
    priority: critical | high | medium | low
    status: queued
    added: 2026-02-12
    description: |
      Optional longer description with context.
```

### Status Flow

`queued` → `in_progress` → `done` (or `cut` if deprioritized)

This flow applies to both backends. For external trackers, SDD commands update the issue status automatically.

### Promoting to Full Workflow

When ready to implement a backlog item:
1. Run `/sdd/start {slug} --from {issue-id}` (tracker) or `/sdd/start {slug} --from backlog:{N}` (local)
2. Proposal is pre-filled from the issue/item details
3. Follow standard SDD workflow
4. `/sdd/complete` marks the tracker issue as Done (or local item as `done`)

### Deep Investigation (Optional)

For complex features, architecture migrations, or new product directions — use `/sdd/explore {slug}` to investigate before starting a cycle. This creates a `wip/{slug}/` folder with an `00-overview.md` index and focused analysis files that emerge organically during the investigation (gap analyses, architecture options, trade-off matrices, corner cases, strategic recommendations).

When ready, `/sdd/start {slug}` detects the WIP folder and pre-fills the proposal and spec-delta from the investigation.

## Commands

### Core Lifecycle

| Command | Purpose |
|---------|---------|
| `/sdd/start {slug} [--from ref]` | Begin a new change cycle — scaffolds `changes/{slug}/`, optionally pre-filling from a tracker issue or backlog item |
| `/sdd/implement [task]` | Execute the next task (or a specific one) from the current cycle's tasks.md |
| `/sdd/status` | Show current cycle state, task progress, recent commits |
| `/sdd/complete` | Verify scenarios, merge spec-delta to canonical specs, archive, extract learnings |

### Backlog & Batch

| Command | Purpose |
|---------|---------|
| `/sdd/explore {slug}` | Start or continue a deep investigation in `wip/{slug}/` before committing to a cycle |
| `/sdd/backlog [description]` | Add an item to the backlog (tracker or local YAML) with priority and status tracking |
| `/sdd/run-all [N]` | Process queued backlog items end-to-end — groups related items into cycles, runs the full start→implement→complete→commit lifecycle for each |

### Cycle Flow

```
                 /sdd/explore (optional)
                      │
                 deep investigation
                 wip/{slug}/ folder
                      │
Backlog item ──→ /sdd/start ──→ /sdd/implement ──→ /sdd/complete
(tracker or       │                │                   │
 local YAML)  reads context     executes           merges specs
    │         surfaces tensions  tasks from          archives change
    │         scaffolds          spec-delta           extracts learnings
    │         changes/{slug}/                          updates tracker/backlog
    │
    └── or: /sdd/run-all (automates the full loop for batch processing)
```

### Learning Extraction

`/sdd/complete` optionally extracts learnings — patterns, mistakes, decisions worth remembering — and appends them to `learnings.yaml`. Skip for trivial cycles. Use when something surprising happened.

## Required Structure

```
project/
  backlog/
    items.yaml                   # Lightweight work queue (if using local backlog)
  specs/
    constitution.md              # Immutable project principles
    features/
      [feature]/
        spec.md                  # Current behavior specification
  changes/
    [change-name]/
      proposal.md                # What and why
      spec-delta.md              # ADDED / MODIFIED / REMOVED sections
      tasks.md                   # Implementation checklist
  archive/                       # Completed changes (moved on merge)
  wip/                           # Deep investigations before cycles (optional)
  learnings.yaml                 # Accumulated learnings from cycles (optional)
```

## Cycle State

Cycle state lives in `.claude/state/sdd-state.yaml`. Managed by `/sdd/*` commands — do not edit by hand.

```yaml
installed_standard_version: "1.5"   # set during adoption
installed_at: 2026-04-17T00:00:00Z
tracker_preference: "linear" | "github" | "local" | null
current_cycle:
  slug: null                        # e.g., "add-dark-mode"
  phase: null                       # proposal | implementation | ready-to-merge
  started_at: null
  tracker_ref: null                 # e.g., "linear:TEND-42"
  base_branch: null                 # v1.5: branch /sdd:start was invoked from
  branch_name: null                 # v1.5: actual cycle branch (slug, or {NNN}-{slug})
history: []                         # completed cycles with slug, completed date, summary
```

`base_branch` and `branch_name` are new in v1.5. Commands MUST treat missing fields on older installs as `null` (no deserialization crash) so pre-v1.5 cycles complete gracefully without PR automation.

## Commit Convention

| Prefix      | Usage                                    |
|-------------|------------------------------------------|
| `[spec]`    | Proposal and spec artifacts              |
| `[impl]`    | Implementation code                      |
| `[archive]` | Moving completed changes to archive      |
| `[fix]`     | Bug fix restoring specified behavior     |
| `[refactor]`| Refactor with no behavior change         |

Examples:
```
[spec] Add SSO support specification
[impl] Implement SSO support
[archive] Archive add-sso-support
[fix] Restore correct session timeout behavior
```

## Templates

### proposal.md (minimal)

```markdown
# Proposal: [Change Name]

## Problem
[What is broken or missing]

## Solution
[What we will do]

## Scope
[Which features/specs are affected]

## Risks
[What could go wrong]
```

### spec-delta.md (minimal)

```markdown
# Spec Delta: [Change Name]

## ADDED
- [New behavior with Given/When/Then]

## MODIFIED
- [Changed behavior with before/after scenarios]

## REMOVED
- [Deleted behavior and rationale]
```

### tasks.md (minimal)

```markdown
# Tasks: [Change Name]

- [ ] Create proposal and spec-delta
- [ ] Review with team
- [ ] Implement changes
- [ ] Update tests
- [ ] Archive change on merge
```

Full templates with detailed guidance: see `references/templates.md`
