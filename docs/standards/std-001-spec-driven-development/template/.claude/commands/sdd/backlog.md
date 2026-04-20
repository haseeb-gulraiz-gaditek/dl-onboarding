---
description: Add a new item to the development backlog
version: "1.3"
---

## Arguments

- **$ARGUMENTS** (optional): Item summary. If empty, prompt interactively.

Examples:
- `/sdd/backlog Fix mobile nav overflow on /pricing`
- `/sdd/backlog Add dark mode toggle to dashboard`
- `/sdd/backlog` (interactive — will prompt for details)

## Actions

1. **Detect Tracker**
   - Check if an external issue tracker MCP is available (e.g., `linear_*` or `github_*` tools)
   - Read `.claude/state/sdd-state.yaml` for `tracker_preference`:
     - `"linear"` → use Linear
     - `"github"` → use GitHub Issues
     - `"local"` → use local backlog
     - `null` → auto-detect (see below)
   - If preference is `null` and a tracker MCP is detected:
     - Ask user: "I detected {tracker} integration. Use it as your SDD backlog? (yes/no/always)"
     - If "always": set `tracker_preference` in state file, use tracker
     - If "yes": use tracker this time, don't persist
     - If "no": use local backlog
   - If no tracker MCP detected: use local backlog

2. **Read Current Backlog** (if using local backlog)
   - Read `backlog/items.yaml`
   - If file doesn't exist, create it with `items: []`

3. **Parse Input**
   - If `$ARGUMENTS` provided: use as the item summary
   - If empty: ask the user what they want to add

4. **Gather Details**
   - **summary**: Short title (from arguments or user input)
   - **priority**: `critical | high | medium | low` — default to `medium`. Infer urgency from keywords ("fix", "broken", "crash" → `high`). Ask if unclear.
   - **description**: 1-3 sentence expansion. Generate from summary if straightforward; ask if the task is ambiguous.

5. **Add Item**
   - **If using tracker:**
     - Create issue via MCP with:
       - Title = summary
       - Description/body = description
       - Priority mapping: `critical` → Urgent, `high` → High, `medium` → Medium, `low` → Low
       - Label: `sdd` (for filtering SDD items vs. other issues)
     - Note the issue ID and URL from the response
   - **If using local backlog:**
     - Append to the end of the `items:` list in `backlog/items.yaml`:
       ```yaml
       - summary: "Short title"
         priority: medium
         status: queued
         added: YYYY-MM-DD
         description: |
           Detailed description.
       ```

6. **Display Confirmation**

   **If tracker was used:**
   ```
   ═══════════════════════════════════════════════════════════════
     BACKLOG ITEM ADDED
   ═══════════════════════════════════════════════════════════════

   Summary:  {summary}
   Priority: {priority}
   Tracker:  {issue-id} ({issue-url})

   Description:
     {description}

   ═══════════════════════════════════════════════════════════════
   Item created in {tracker}. Use --from {issue-id} with /sdd/start.
   ═══════════════════════════════════════════════════════════════
   ```

   **If local backlog was used:**
   ```
   ═══════════════════════════════════════════════════════════════
     BACKLOG ITEM ADDED
   ═══════════════════════════════════════════════════════════════

   Summary:  {summary}
   Priority: {priority}
   Status:   queued
   Added:    {date}

   Description:
     {description}

   ═══════════════════════════════════════════════════════════════
   Backlog now has {N} queued items.
   Run /sdd/start to begin a cycle, or /sdd/run-all to process.
   ═══════════════════════════════════════════════════════════════
   ```

## Notes

- Do NOT modify existing items — only append new ones
- Always set `status: queued` for new items (local) or add the `sdd` label (tracker)
- If the user says "backlog this" during a conversation about a specific issue, capture the full context as the description
- The `sdd` label is how other commands filter for SDD-managed items vs. regular issues in the tracker
