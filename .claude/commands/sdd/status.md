---
description: Show current SDD cycle state, task progress, and recent commits
version: "1.5"
---

## Actions

1. **Read State**
   - Parse `.claude/state/sdd-state.yaml`

2. **Check Standard Version**
   - Read `installed_standard_version` from state file
   - Compare against the `version` field in this command's frontmatter (represents the current standard version)
   - If installed version is missing or older than current version, flag for upgrade

3. **Check Tracker Status**
   - Read `tracker_preference` from state file
   - If a preference is set, check if the corresponding MCP tools are available
   - Determine connection status: connected, preference set but MCP unavailable, or not configured

4. **If Active Cycle**
   - Display cycle info (slug, phase, started date)
   - Display branch info: `Branch: {current_cycle.branch_name} (from {current_cycle.base_branch})` (v1.5). If `branch_name` is null (pre-v1.5 cycle), omit the Branch line.
   - If `current_cycle.tracker_ref` exists, display it with link
   - Parse `changes/{slug}/tasks.md` for checkbox progress
   - Check for unfilled `[REQUIRED]` placeholders
   - List recent commits with `[spec]` or `[impl]` prefixes

5. **If No Active Cycle**
   - Check for orphaned `changes/` folders
   - If tracker is connected, show count of queued SDD items in tracker
   - Suggest `/sdd/start` to begin new cycle

## Output Format

### Active Cycle

```
═══════════════════════════════════════════════════════════════
  SDD STATUS
═══════════════════════════════════════════════════════════════

Standard: STD-001 v1.5 (installed {date})
Tracker:  Linear (connected) | Local backlog | Not configured

Cycle:   add-dark-mode
Phase:   implementation
Started: 2026-02-12
Branch:  add-dark-mode (from main)
Tracker: TEND-42 (linear.app/tendemo/TEND-42)

Tasks: 2/4 complete
  - [x] Define color tokens
  - [x] Create toggle component
  - [ ] Persist preference
  - [ ] Update all pages

Recent Commits:
  • [impl] Add color tokens
  • [impl] Create ThemeToggle

═══════════════════════════════════════════════════════════════
Next: /sdd/implement to continue
═══════════════════════════════════════════════════════════════
```

### With Warnings

```
═══════════════════════════════════════════════════════════════
  SDD STATUS
═══════════════════════════════════════════════════════════════

Cycle:   add-dark-mode
Phase:   proposal

⚠ Unfilled [REQUIRED] sections:
  - proposal.md: Problem, Solution
  - spec-delta.md: ADDED section

═══════════════════════════════════════════════════════════════
Fill required sections before implementing.
═══════════════════════════════════════════════════════════════
```

### No Active Cycle

```
═══════════════════════════════════════════════════════════════
  SDD STATUS
═══════════════════════════════════════════════════════════════

Standard: STD-001 v1.5 (installed {date})
Tracker:  Linear (connected) — 3 items queued

No active cycle

Recent Archives:
  • fix-auth-bug (2026-02-10)
  • add-user-roles (2026-02-08)

═══════════════════════════════════════════════════════════════
Run /sdd/start [slug] to begin a new cycle.
═══════════════════════════════════════════════════════════════
```

## Checks Performed

- State file exists and is valid
- Standard version is current (compare `installed_standard_version` with command `version` frontmatter)
- Change directory exists for active cycle
- All `[REQUIRED]` placeholders filled
- Tasks.md has valid checkbox format
- Phase matches actual progress

## Version Staleness

If `installed_standard_version` is null or older than this command's `version` frontmatter, append after the Standard line:

```
Standard: STD-001 v1.4 (installed 2026-04-06)
  ⚠ v1.5 available — re-run adoption prompt to upgrade
```

If version is missing (pre-versioning install):

```
Standard: STD-001 (version unknown — pre-versioning install)
  ⚠ v1.5 available — re-run adoption prompt to upgrade
```
