---
description: Execute task(s) from the active SDD cycle following the spec-delta
version: "1.3"
---

## Arguments

- **$ARGUMENTS** (optional): Task description or number
  - If omitted, selects next unchecked task
  - Can be task number (e.g., "1", "2")
  - Can be partial description match

## Actions

1. **Validate State**
   - Read `.claude/state/sdd-state.yaml`
   - Refuse if no active cycle
   - Get cycle slug

2. **Check Spec Readiness**
   - Read ALL files in `changes/{slug}/`: proposal.md, spec-delta.md, tasks.md
   - Refuse if any `[REQUIRED]` placeholders remain in ANY file
   - List which files still have unfilled placeholders
   - Parse specification details from spec-delta.md

3. **Select Task**
   - Read `changes/{slug}/tasks.md`
   - Find target task (specified or next unchecked)
   - Display task context

4. **Implement**
   - Follow spec-delta exactly
   - Make minimal changes needed
   - Write tests if specified in tasks

5. **Update Progress**
   - Mark task `[x]` in tasks.md
   - Update phase to "implementation" if was "proposal"

6. **Commit**
   - Stage implementation changes
   - Commit with message: `[impl] {task description}`

## Output

### Initial Display
```
═══════════════════════════════════════════════════════════════
  IMPLEMENTING: {Task Name}
  Cycle — {slug}
═══════════════════════════════════════════════════════════════

Task: {Task description}

Spec Guidance:
  • Add localStorage key "theme-preference"
  • Values: "light" | "dark" | "system"
  • Read on app init, apply before render

═══════════════════════════════════════════════════════════════
Starting implementation...
═══════════════════════════════════════════════════════════════
```

### Completion Display
```
═══════════════════════════════════════════════════════════════
  IMPLEMENTATION COMPLETE
═══════════════════════════════════════════════════════════════

Changes made:
  • src/lib/theme.ts - Added persistence logic
  • src/app.tsx - Load theme on init

Committed: [impl] {task description}

Progress: 3/4 tasks complete
Next task: Update all pages

═══════════════════════════════════════════════════════════════
Run /sdd/implement for next task, or /sdd/complete to finish.
═══════════════════════════════════════════════════════════════
```

## Guardrails

- **No active cycle**: Refuse, suggest `/sdd/start`
- **Unfilled [REQUIRED]**: Refuse, list all files and sections with remaining placeholders
- **All tasks done**: Suggest `/sdd/complete`
- **Deviation detected**: Warn if implementation differs from spec

## Deviation Warning

```
⚠ Potential deviation from spec:

Spec says:
  "Store in localStorage"

Implementation uses:
  sessionStorage

Proceed anyway? This will be flagged for review.
```

## Multi-Task Mode

If multiple tasks are specified or `--all` flag:

```
/sdd/implement --all
```

Implements all remaining tasks sequentially, committing after each.
