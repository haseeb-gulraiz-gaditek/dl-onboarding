---
description: Merge spec-delta to canonical specs, archive the completed change, push the branch, and open a PR
version: "1.5"
---

## Actions

1. **Verify Completion**
   - Read `changes/{slug}/tasks.md`
   - All tasks must be checked `[x]`
   - If incomplete, show remaining tasks and refuse

2. **Verify Spec Scenarios**
   - Read `changes/{slug}/spec-delta.md`
   - For each Given/When/Then scenario in ADDED and MODIFIED sections, confirm the implementation satisfies it
   - Verification method is project-specific: code inspection, running tests, manual check — whatever fits
   - If any scenario does not hold, list failures and refuse (unless `--force`)

3. **Read Spec Delta**
   - Parse `changes/{slug}/spec-delta.md`
   - Extract ADDED, MODIFIED, REMOVED sections

4. **Merge to Canonical Specs**
   - For each ADDED section:
     - Append to appropriate `specs/features/{feature}/spec.md`
     - Create new spec file if feature doesn't exist
   - For each MODIFIED section:
     - Find and update the target section
     - Preserve surrounding content
   - For each REMOVED section:
     - Delete the specified content
     - Leave note if significant

5. **Commit Spec Merge**
   - Stage spec changes
   - Commit: `[spec] Merge {slug} to canonical specs`

6. **Archive Change and Capture Locals** (MODIFIED in v1.5)
   - Move `changes/{slug}/` to `archive/{slug}/` (filesystem only — commit happens in step 10).
   - Capture into local variables from `current_cycle` for use in later steps (they'll be cleared in step 10):
     - `_tracker_ref` ← `current_cycle.tracker_ref`
     - `_base_branch` ← `current_cycle.base_branch` (v1.5)
     - `_branch_name` ← `current_cycle.branch_name` (v1.5)

7. **Extract Learnings** (optional, skip for trivial cycles)
   - Review the cycle for anything surprising or worth remembering:
     - Patterns that worked well or caused problems
     - Decisions that should inform future cycles
     - Mistakes to avoid next time
   - Append to `learnings.yaml` (or project-specific location):
     ```yaml
     - date: YYYY-MM-DD
       cycle: "{slug}"
       insight: "What was learned"
       category: "architecture | testing | performance | tooling | process"
     ```

8. **Update Backlog** (if item came from local backlog)
   - Set backlog item status to `done` in `backlog/items.yaml`

9. **Update Tracker** (if applicable)
   - If `_tracker_ref` (captured in step 6) is non-null:
     - If tracker MCP is available:
       - Mark issue as Done/Completed
       - Add comment: "Completed via SDD cycle `{slug}`. Archive: `archive/{slug}/`"
     - If tracker MCP is not available:
       - Warn: "Could not update tracker — {_tracker_ref} not reachable. Update manually."
   - If no tracker ref and no backlog item: skip

10. **Clear State and Commit Archive** (MODIFIED in v1.5)
    - Clear `current_cycle` fields to null: `slug`, `phase`, `started_at`, `tracker_ref`, `base_branch`, `branch_name`.
    - Append the cycle to the `history` array with `slug`, `completed` (today's date), and a short `summary`.
    - Stage the archive move AND the state file AND `backlog/items.yaml` (if modified in step 8) AND `learnings.yaml` (if modified in step 7), so state-clear lands atomically with archival.
    - Commit: `[archive] Archive {slug} and clear cycle state`

11. **Push and PR** (NEW in v1.5)
    - If `_base_branch` or `_branch_name` is null (pre-v1.5 cycle): print "Pre-v1.5 cycle — base branch unknown. Push and open the PR manually." and exit successfully. Skip the rest of this step.
    - Push: `git push -u origin {_branch_name}`. If push fails, print the git error and exit nonzero (user must fix auth or remote before retrying — state is already cleared so `/sdd:complete` does not need to re-run).
    - Detect platform from `git remote get-url origin`:
      - Host matches `github.com` → tool = `gh`
      - Host matches `gitlab.com` or contains `gitlab` → tool = `glab`
      - Otherwise → skip PR creation; print the branch name and say "Unrecognized host. Push succeeded. Open a PR manually."
    - Check CLI availability: `command -v {tool}` AND `{tool} auth status` must both exit 0. If either fails, fall back to the compare-URL path below.
    - On success: run `{tool} pr create --base {_base_branch} --head {_branch_name} --title "[SDD] {slug}" --body "{body}"` where `{body}` summarizes the spec-delta (ADDED/MODIFIED/REMOVED sections) and links to `archive/{slug}/`. Capture the returned PR URL.
    - **Compare-URL fallback** (when tool unavailable, auth expired, or `pr create` returns nonzero):
      - Parse `{owner}/{repo}` from the origin URL.
      - For GitHub: `https://github.com/{owner}/{repo}/compare/{_base_branch}...{_branch_name}`
      - For GitLab: `https://gitlab.com/{owner}/{repo}/-/compare/{_base_branch}...{_branch_name}` (or the configured host)
      - Print the compare URL with a warning that the cycle completed but the PR must be opened manually. The cycle still counts as completed.

## Output

```
═══════════════════════════════════════════════════════════════
  CYCLE COMPLETED — add-dark-mode
═══════════════════════════════════════════════════════════════

Merging spec-delta:
  ADDED:
    • specs/features/theming/spec.md - Dark mode section
  MODIFIED:
    • specs/features/settings/spec.md - Theme preference
  REMOVED:
    (none)

Committed: [spec] Merge add-dark-mode to canonical specs

Archived: changes/add-dark-mode → archive/add-dark-mode
Committed: [archive] Archive add-dark-mode and clear cycle state

Pushed:   add-dark-mode → origin
PR:       https://github.com/disrupt-gt/example/pull/42

Duration: 3 days
Tasks:    4/4
Commits:  6

═══════════════════════════════════════════════════════════════
Cycle archived. Run /sdd/start [slug] to begin next cycle.
═══════════════════════════════════════════════════════════════
```

### Compare-URL fallback (v1.5)

When `gh`/`glab` is unavailable or auth has expired, the cycle still completes but the PR must be opened manually:

```
Pushed:   add-dark-mode → origin
⚠ PR tool unavailable — open manually:
  https://github.com/disrupt-gt/example/compare/main...add-dark-mode
```

### Pre-v1.5 cycle (v1.5)

Cycles started before v1.5 have no `base_branch`/`branch_name` recorded. Push and PR steps are skipped with a warning:

```
⚠ Pre-v1.5 cycle — base branch unknown.
  Push and open the PR manually.
```

## Error Cases

### Incomplete Tasks

```
═══════════════════════════════════════════════════════════════
  CANNOT COMPLETE — 2 tasks remaining
═══════════════════════════════════════════════════════════════

  - [ ] Persist preference
  - [ ] Update all pages

═══════════════════════════════════════════════════════════════
Run /sdd/implement to finish, or
/sdd/complete --force to complete anyway.
═══════════════════════════════════════════════════════════════
```

### Unverified Scenarios

```
═══════════════════════════════════════════════════════════════
  CANNOT COMPLETE — 2 spec scenarios not verified
═══════════════════════════════════════════════════════════════

ADDED > Dark mode toggle
  Given the user is on the settings page
  When they toggle dark mode
  Then the UI switches to dark theme
  └─ Status: NOT VERIFIED

MODIFIED > Theme persistence
  Given the user selects a theme
  When they close and reopen the app
  Then the selected theme is preserved
  └─ Status: NOT VERIFIED

═══════════════════════════════════════════════════════════════
Verify these scenarios, or
/sdd/complete --force to skip verification.
═══════════════════════════════════════════════════════════════
```

### Merge Conflict

```
═══════════════════════════════════════════════════════════════
  ⚠ MERGE CONFLICT — specs/features/settings/spec.md
═══════════════════════════════════════════════════════════════

The MODIFIED section targets content that has changed
since the spec-delta was written.

Current spec:
  "Theme is stored in user preferences"

Spec-delta expects:
  "Theme is stored in cookies"

Options:
  1. Update spec-delta to match current spec
  2. Force overwrite (--force)
  3. Abort and resolve manually

═══════════════════════════════════════════════════════════════
```

## Force Complete

```
/sdd/complete --force
```

Completes even with:
- Unchecked tasks (marks as skipped)
- Unverified spec scenarios (marks as unverified)
- Minor merge conflicts (uses spec-delta version)

Does NOT force through:
- Missing spec-delta file
- Invalid state
