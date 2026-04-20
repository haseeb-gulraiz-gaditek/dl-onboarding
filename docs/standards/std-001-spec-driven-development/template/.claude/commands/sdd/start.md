---
description: Begin a new SDD change cycle by scaffolding changes/{slug}/ with proposal, spec-delta, and tasks
version: "1.5"
---

## Arguments

- **$ARGUMENTS**: Change slug, optionally with source reference
  - `add-dark-mode` — manual start
  - `add-dark-mode --from TEND-42` — start from tracker issue
  - `add-dark-mode --from backlog:3` — start from local backlog item

## Actions

1. **Check State**
   - Read `.claude/state/sdd-state.yaml`
   - If active cycle exists, prompt to complete or abandon it first

2. **Branch Setup** (v1.5)
   - Verify git repository: `git rev-parse --git-dir` must succeed. If not, refuse with "Not a git repository. /sdd:start requires git."
   - Verify clean working tree: `git status --porcelain` must return empty. If dirty, refuse with the list of uncommitted paths and the message "Working tree has uncommitted changes. Commit, stash, or clean before starting a cycle." Do NOT modify state or create any branch.
   - Capture base branch: `base_branch = git symbolic-ref --short HEAD`. If HEAD is detached, capture `base_branch = git rev-parse HEAD` (store the short SHA; document in state comment).
   - Resolve branch name (collision-safe):
     - Candidate 1: `{slug}`
     - For each candidate, check both refs: `git show-ref --verify --quiet refs/heads/{candidate}` AND `git ls-remote --heads --exit-code origin {candidate}`. If either returns a match, the candidate is taken.
     - On collision, try `001-{slug}`, `002-{slug}`, ... `999-{slug}` in order.
     - If all 1000 candidates are taken, refuse with "All {slug} variants 001-999 are taken. Rename the slug."
   - Create and switch: `git switch -c {branch_name}`.
   - Hold `base_branch` and `branch_name` for step 6.

3. **Surface Tensions**
   - Read relevant codebase context: files in the affected area, existing patterns for similar work
   - Read `specs/constitution/` if present — especially `principles.md`, `personas.md`, and any section relevant to the proposed change
   - Read existing specs in `specs/features/` for the affected area
   - Flag any of the following if found:
     - **Constitutional tensions**: the proposed change is in tension with principles, personas, or positioning the team has defined. Quote the specific principle and explain the tension.
     - **Spec conflicts**: the proposed change would modify or contradict behavior already defined in existing feature specs. Identify the specific scenario affected.
     - **Technology forks**: the proposed change involves a technology with multiple valid integration patterns that have meaningfully different trade-offs. Present concrete alternatives.
     - **Hidden scope**: the codebase reveals the proposed change implies significant prerequisite work (new infrastructure, missing abstractions, data migration) not mentioned in the description.
   - If nothing to flag: proceed directly to step 4
   - If flagging: present findings, let the user respond, incorporate decisions into the scaffold

4. **Resolve Source**
   - **Check for WIP investigation**: if `wip/{slug}/` exists (from a prior `/sdd/explore` session), read `00-overview.md` and all numbered files. Use the investigation to pre-fill the scaffold (Problem, Solution, Scope, Risks, spec-delta). Surface Tensions step may skip tensions already resolved in the WIP.
   - **If `--from {tracker-ref}`** (e.g., `TEND-42`, `#123`):
     - Fetch issue details from tracker via MCP
     - Extract: title, description, comments, priority
     - Store in context for pre-filling templates
   - **If `--from backlog:{N}`**:
     - Read item N from `backlog/items.yaml`
     - Store in context for pre-filling templates
   - **If no `--from` and tracker is available** (per `tracker_preference` or auto-detect):
     - After scaffolding, auto-create a tracker issue for this cycle
   - Store source reference for state tracking

5. **Create Change Directory**
   - Create `changes/{slug}/` with three files:

   **proposal.md** — If WIP investigation, tension resolution, or source context provided content, pre-fill relevant sections and mark them `[REVIEW]` instead of `[REQUIRED]`. Otherwise use `[REQUIRED]` placeholders.

   ```markdown
   # Proposal: {slug}

   ## Problem
   [REQUIRED: What problem does this solve?]

   ## Solution
   [REQUIRED: How will we solve it?]

   ## Scope
   [REQUIRED: What's in/out of scope?]

   ## Risks
   [REQUIRED: What could go wrong?]
   ```

   **spec-delta.md**
   ```markdown
   # Spec Delta: {slug}

   ## ADDED

   ### [Section Name]
   [REQUIRED: New specification content]

   ## MODIFIED

   ### [Section Name]
   **Before:** [Current state]
   **After:** [New state]

   ## REMOVED

   (None)
   ```

   **tasks.md**
   ```markdown
   # Tasks: {slug}

   ## Implementation Checklist

   - [ ] [REQUIRED: First task]
   - [ ] [REQUIRED: Second task]

   ## Validation

   - [ ] All tasks complete
   - [ ] Tests pass
   - [ ] Spec-delta reviewed
   ```

6. **Update State**
   - Set `current_cycle.slug` to the slug
   - Set `current_cycle.phase` to "proposal"
   - Set `current_cycle.started_at` to current timestamp
   - Set `current_cycle.tracker_ref` to source reference (e.g., `"linear:TEND-42"`, `"github:#123"`) or `null`
   - Set `current_cycle.base_branch` to the value captured in step 2 (v1.5)
   - Set `current_cycle.branch_name` to the value captured in step 2 (v1.5)

7. **Update Tracker** (if applicable)
   - If starting from a tracker issue (`--from {tracker-ref}`):
     - Update tracker issue status to "In Progress"
   - If no `--from` and tracker is available:
     - Create a new tracker issue referencing this cycle
     - Add `sdd` label
     - Set `current_cycle.tracker_ref` to the new issue reference

8. **Commit**
   - Stage all changes (on the new branch created in step 2)
   - Commit with message: `[spec] Start change cycle: {slug}`

## Output

Display:
```
═══════════════════════════════════════════════════════════════
  CYCLE STARTED — {slug}
═══════════════════════════════════════════════════════════════

Branch:  {branch_name} (from {base_branch})

changes/{slug}/
  ├── proposal.md      # Define problem & solution
  ├── spec-delta.md    # Specify changes to make
  └── tasks.md         # Implementation checklist

Tracker: {issue-id} ({issue-url})        ← only if tracker is active
Source:  --from {ref}                     ← only if started from a reference

Next steps:
  1. Fill out [REQUIRED] sections in all files
  2. Run /sdd/status to check progress
  3. Run /sdd/implement when ready

═══════════════════════════════════════════════════════════════
Ready to begin. Fill [REQUIRED] sections, then /sdd/implement
═══════════════════════════════════════════════════════════════
```

If the branch name collided with an existing ref, note the prefix in the output:
```
Branch:  001-{slug} (from {base_branch}) — original slug was taken, prefixed with 001-
```

If tensions were surfaced, show them before the scaffold output:
```
═══════════════════════════════════════════════════════════════
  TENSIONS FOUND — {N} items to address
═══════════════════════════════════════════════════════════════

  1. CONSTITUTIONAL: {principle} — {tension description}
  2. SPEC CONFLICT: {spec path} — {conflict description}
  ...

═══════════════════════════════════════════════════════════════
```

If WIP investigation was found, note it:
```
  WIP investigation found: wip/{slug}/ ({N} documents)
  Pre-filled proposal and spec-delta from investigation.
  Sections marked [REVIEW] — verify before proceeding.
```

## Error Handling

- **No slug provided**: Ask user for slug
- **Active cycle exists**: Show current cycle, ask to complete or abandon first
- **Invalid slug**: Reject slugs with spaces or special characters
- **Tracker issue not found**: Warn and continue without pre-fill — "Could not fetch {ref} from tracker. Starting without source context."
- **Not a git repository** (v1.5): Refuse with "Not a git repository. /sdd:start requires git."
- **Dirty working tree** (v1.5): Refuse, list uncommitted paths, and say "Commit, stash, or clean the working tree before starting a cycle." Do NOT modify state or create a branch.
- **Branch collision exhausted** (v1.5): When all candidates from `{slug}` through `999-{slug}` are taken, refuse with "All {slug} variants 001-999 are taken. Rename the slug."
