---
id: "STD-001"
title: "Spec-Driven Development"
description: "Every feature that changes observable behavior must have a specification before implementation begins."
status: "Adopted"
version: "1.5"
effective: "2026-01-01"
reference: "/reference/spec-driven-development"
---

# STD-001: Spec-Driven Development

**Status:** Adopted | **Version:** 1.5 | **Effective:** January 2026 | **Last Updated:** 17/Apr/26

---

## Summary

All code that changes observable behavior MUST be preceded by a written specification. Specs live in the repository, are reviewed like code, and are the source of truth for what the system does.

---

## Requirements

### 1. Repository Structure

Every project MUST have:

```
project/
├── specs/
│   ├── constitution.md        # Immutable project principles
│   └── features/
│       └── [feature]/
│           └── spec.md        # Current behavior specification
├── changes/
│   └── [change-name]/
│       ├── proposal.md        # What and why
│       ├── spec-delta.md      # ADDED / MODIFIED / REMOVED
│       └── tasks.md           # Implementation checklist
└── archive/                   # Completed changes
```

### 2. When a Proposal is Required

A change proposal MUST be created when the change:

- Adds new features or functionality
- Modifies observable behavior
- Introduces breaking API changes
- Changes architecture or security patterns
- Alters database schemas

A change proposal MAY be skipped when the change:

- Fixes a bug to restore behavior already described in the spec
- Is a refactor with no behavior change
- Updates config, dependencies, or documentation only

### 2.1 Backlog Tier (Optional)

For rapid iteration, teams MAY use a lightweight backlog as a work queue.

**Backend options:**
- **External issue tracker** (e.g., Linear, GitHub Issues) via MCP integration.
  When configured, the tracker is the single source of truth — no local duplicate
  is maintained. Items are tagged with an `sdd` label for filtering.
- **Local YAML file** (`backlog/items.yaml`) — the default when no tracker is
  available.

Both backends support the same status flow and promotion workflow.

**Tracker integration:** When an external tracker is available via MCP, the
`/sdd/backlog` command routes items there instead of `backlog/items.yaml`. The
`/sdd/start` command can reference tracker issues via `--from {issue-id}`.
Status updates (in-progress, done) are propagated to the tracker automatically
by `/sdd/start` and `/sdd/complete`.

**Local YAML format:**

```
backlog/
  items.yaml
```

```yaml
# backlog/items.yaml
items:
  - summary: "Short description"
    priority: high | medium | low
    status: queued | in_progress | done | cut
    added: 2026-02-12  # serves as natural ordering
```

**No explicit IDs** - items are identified by summary + added date. List order = priority order within same status. This avoids merge conflicts when multiple branches add items.

**Status flow:** `queued` → `in_progress` → `done` (or `cut` if deprioritized)

**When picked up:** Create `changes/[slug]/` from item (or tracker issue), then follow standard workflow.

Backlog suits quick ideas, design polish, bug reports, and tech debt notes. Full `changes/` proposals remain required for new features, breaking changes, and security modifications.

### 2.2 Deep Investigation (Optional)

For complex changes, teams MAY investigate in a `wip/{slug}/` folder before starting a cycle. The investigation produces focused analysis files (gap analyses, architecture options, trade-off matrices, corner cases, recommendations). When ready, `/sdd/start` reads the investigation and pre-fills the proposal.

### 2.3 Ambiguity Resolution

The proposal phase SHOULD include review of existing specs and project principles for tensions with the proposed change. Conflicts with existing specified behavior MUST be acknowledged as MODIFIED sections in the spec-delta, not silently overridden.

### 3. Proposal-Before-Code

Change proposals (proposal.md, spec-delta.md, tasks.md) MUST be committed before implementation changes in the same PR. The proposal commit SHOULD use the `[spec]` prefix, followed by `[impl]` for the implementation. The canonical `specs/` files are updated during archival (see requirement 6).

```
[spec] Add SSO support specification
[impl] Implement SSO support
[archive] Archive add-sso-support
```

### 4. Spec Format

Feature specs MUST use Given/When/Then scenarios for all requirements:

```gherkin
Given [precondition]
When [action]
Then [expected outcome]
```

Each requirement MUST have at least one scenario. Error cases MUST be specified explicitly.

### 5. PR Gates

Every PR that requires a proposal MUST include:

- `changes/[name]/proposal.md` describing what and why
- `changes/[name]/spec-delta.md` with explicit ADDED/MODIFIED/REMOVED sections
- `changes/[name]/tasks.md` with implementation checklist
- Proposal artifacts committed before code changes

### 6. Archive on Merge

When a PR merges, the change directory MUST be moved from `changes/` to `archive/` and the spec-delta MUST be merged into the canonical `specs/features/` files.

### 7. Naming Convention

Code and spec locations MUST mirror each other:

| Code | Spec |
|------|------|
| `src/features/auth/` | `specs/features/auth/spec.md` |
| `src/features/billing/` | `specs/features/billing/spec.md` |

### 8. Spec Size

A single spec file SHOULD NOT exceed 500 lines. If it does, the feature SHOULD be split into smaller, focused specifications.

### 9. Spec Verification

Spec scenarios MUST be verified before a cycle is marked complete. The verification method is project-specific — code inspection, unit tests, integration tests, E2E tests, or manual verification are all valid. What matters is that every scenario in the spec-delta has been confirmed to hold in the implementation.

### 10. Cycle Branching

Every SDD cycle MUST execute on a dedicated branch created from the contributor's current `HEAD` at `/sdd:start` time. The branch name MUST be the cycle slug, or `{NNN}-{slug}` on collision (where `NNN` is the smallest zero-padded integer in `[001, 999]` that yields a name not present on any local or remote ref).

`/sdd:start` MUST refuse on a dirty working tree and MUST capture the current HEAD as `base_branch` (the branch name, or the short SHA if HEAD is detached) so that Work Forest worktrees and feature-branch workflows are preserved.

`/sdd:complete` MUST clear `current_cycle` — including `base_branch` and `branch_name` — as a committed step before PR creation, so the base branch never carries non-null active-cycle state. After state is cleared and archived, `/sdd:complete` SHOULD push the cycle branch and open a PR using the platform CLI (`gh` for GitHub, `glab` for GitLab), falling back to a printed compare URL when the CLI is unavailable. Cycles started pre-v1.5 (no `base_branch` recorded) complete without PR automation and warn the user to push manually.

---

## Why

Documentation drift is a systems problem, not a discipline problem. When specs live outside the development workflow, they go stale within weeks. This standard ensures specs are co-located with code, reviewed in PRs, and kept current by making updates the path of least resistance.

---

## Learn More

- [Full SDD Reference Guide](/reference/spec-driven-development) -- complete methodology with templates, workflows, anti-patterns, and AI/agent integration
- [SDD Context Engineering Course](/courses/sdd-context-engineering) -- hands-on training

## Resources

- [SDD Command Template](/resources/std-001-spec-driven-development-template) -- starter kit with `/sdd/start`, `/sdd/status`, `/sdd/implement`, `/sdd/complete` commands

---

## Component Registry

| Component | Type | Last Updated |
|-----------|------|--------------|
| [`disrupt-sdd`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/skill/SKILL.md) | Skill | 17/Apr/26 |
| [`skill/references/templates.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/skill/references/templates.md) | Skill Reference | 2/Feb/26 |
| [`/sdd/start`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/start.md) | Command | 17/Apr/26 |
| [`/sdd/implement`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/implement.md) | Command | 06/Apr/26 |
| [`/sdd/status`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/status.md) | Command | 17/Apr/26 |
| [`/sdd/complete`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/complete.md) | Command | 17/Apr/26 |
| [`/sdd/explore`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/explore.md) | Command | 06/Apr/26 |
| [`/sdd/backlog`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/backlog.md) | Command | 06/Apr/26 |
| [`/sdd/run-all`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/commands/sdd/run-all.md) | Command | 06/Apr/26 |
| [`sdd-state.yaml`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/template/.claude/state/sdd-state.yaml) | State | 17/Apr/26 |
| [`CHANGELOG.md`](https://github.com/disrupt-gt/course-materials/blob/main/content/standards/std-001-spec-driven-development/CHANGELOG.md) | Changelog | 17/Apr/26 |
