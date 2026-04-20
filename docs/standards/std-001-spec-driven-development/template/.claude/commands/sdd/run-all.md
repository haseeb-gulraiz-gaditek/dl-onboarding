---
description: Process all queued backlog items end-to-end through the full SDD lifecycle
version: "1.3"
---

## Arguments

- **$ARGUMENTS** (optional): Maximum number of items to process. Default: all queued items.

## Actions

### Phase 1: Plan

1. **Read State**
   - `.claude/state/sdd-state.yaml` — must have no active cycle
   - **If tracker available and preferred** (per `tracker_preference` or auto-detect):
     - Query tracker for issues with `sdd` label in open/queued/todo status
     - Map to work queue format: summary, priority, description, tracker_ref
   - **If using local backlog:**
     - `backlog/items.yaml` — collect all items with `status: queued`

2. **Validate**
   - If an active cycle exists: abort with "Active cycle found. Run `/sdd/complete` first."
   - If no queued items: "Backlog is empty. Nothing to do."

3. **Build Work Queue**
   - Collect all `status: queued` items
   - If `$ARGUMENTS` is a number N, take only the first N items
   - Order by priority: `critical` > `high` > `medium` > `low`
   - Within same priority, preserve YAML order

4. **Display Plan**
   ```
   ═══════════════════════════════════════════════════════════════
     SDD RUN-ALL — {N} items queued
   ═══════════════════════════════════════════════════════════════

   Work Queue (by priority):
     1. [{priority}] {summary}
     2. [{priority}] {summary}
     ...

   Strategy: For each item → start → implement → verify →
   complete → commit → next item

   ═══════════════════════════════════════════════════════════════
   Starting...
   ═══════════════════════════════════════════════════════════════
   ```

### Phase 2: Process Each Item

For each item (or batch of related items) in the queue:

#### Step A — Group Related Items

Check if the next few queued items are related — same area of the codebase, same feature, or closely connected work. If so, batch them into a single cycle (max 6 items). Generate a descriptive slug from the batch.

If items span different areas, keep them as separate cycles.

#### Step B — Start Cycle

Follow `/sdd/start` logic:
- Generate slug from item summary (or batch description)
- Create `changes/{slug}/` with proposal.md, spec-delta.md, tasks.md
- Pre-fill proposal from tracker issue details if available
- Update `.claude/state/sdd-state.yaml` with `tracker_ref` if applicable
- If using tracker: update issue status to In Progress
- If using local backlog: mark items as `status: in_progress`

#### Step C — Implement

Follow `/sdd/implement` logic:
- Analyze items, identify files to create/modify
- Create subtasks, execute each one
- Run build/test verification after implementation

#### Step D — Complete Cycle

Follow `/sdd/complete` logic:
- Verify tasks are done and spec scenarios hold
- Merge spec-delta to canonical specs
- Archive `changes/{slug}/` to `archive/{slug}/`
- If using tracker: issue gets marked Done automatically (via `/sdd/complete` tracker update)
- If using local backlog: mark items as `status: done`
- Clear state (including `tracker_ref`), add to history
- Extract learnings if anything notable happened

#### Step E — Commit

- Stage changed files (specific files, not `git add -A`)
- Commit with descriptive message referencing the cycle
- Do NOT push — leave that to the user

#### Step F — Next

- Display progress: `[{completed}/{total}] items done`
- Loop back to Step A for the next batch

### Phase 3: Summary

```
═══════════════════════════════════════════════════════════════
  SDD RUN-ALL COMPLETE
═══════════════════════════════════════════════════════════════

Cycles Completed: {N}
Items Processed:  {total}
Commits Created:  {count}

Remaining queued: {M} (run /sdd/run-all again if needed)

═══════════════════════════════════════════════════════════════
All done. Run /sdd/status to view updated state.
═══════════════════════════════════════════════════════════════
```

## Error Handling

- **Build failure**: Fix the error, rebuild, continue
- **Blocker found**: Log it, mark item as `queued` again (not done), continue with remaining items
- **Context running low**: Complete the current cycle, commit, display progress. User can run `/sdd/run-all` again to continue.

## Notes

- Each cycle gets its own commit — do not batch all cycles into one commit
- Do NOT push to remote — leave that to the user
- Prefer quality over speed — do each cycle properly
- Follow all patterns from `/sdd/start`, `/sdd/implement`, and `/sdd/complete`
