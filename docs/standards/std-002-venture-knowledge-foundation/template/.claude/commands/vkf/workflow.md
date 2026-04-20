---
description: Documentation lifecycle management — track states, evaluate triggers, orchestrate review cycles across all documents
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Subcommand
  - `status` — show lifecycle state for all documents with pending actions
  - `check` — evaluate all triggers, report pending transitions
  - `transition <path> <state>` — manual state transition
  - No args — same as `status`

## Actions

### `status`

1. **Load Workflow State**
   - Read `.claude/state/vkf-state.yaml` for document lifecycle states (stored under `workflow.documents`)
   - If file does not exist or has no `workflow` key, proceed to initialization

2. **Initialize If Needed**
   - Scan all documents in `specs/constitution/` and `specs/features/*/`
   - For each document, set initial state based on content and freshness:
     - File has only template placeholders: **Draft**
     - File modified within the last 90 days and has substantive content: **Active**
     - File not modified in 90+ days: **Review Due**
   - Write initial state to `.claude/state/vkf-state.yaml`

3. **Display Status**
   - Group documents by lifecycle state
   - For each document show: path, state, date entered state, trigger (if Review Due)
   - For Review Due documents, show the pending action description
   - Show count of pending actions at the bottom

### `check`

1. **Load Current State**
   - Read `.claude/state/vkf-state.yaml`
   - If no state exists, run initialization (same as `status` step 2)

2. **Evaluate Schedule-Based Triggers**
   - **Quarterly constitution review**: Flag any constitution file not reviewed (state unchanged) in 90+ days
   - **Monthly OKR check**: If `specs/okrs/current/` exists, flag if the current quarter OKR file was not updated in 30+ days
   - **Annual governance review**: Flag `specs/constitution/governance.md` if not amended in 365+ days

3. **Evaluate Event-Based Triggers**
   - **Post-ingestion review**: Read `specs/ingestion-log.yaml`, find ingestions from the last 7 days. Flag target files that were modified by ingestion but have not been manually reviewed since (state is still Active, not transitioned through Review)
   - **Post-amendment propagation**: Read `.claude/state/vkf-state.yaml` for recent amendments. Flag files listed in amendment propagation checks that have not been reviewed
   - **Gap resolution follow-up**: If `specs/gaps/` contains resolved gaps, flag if the corresponding constitution section has not been reviewed since resolution

4. **Evaluate Custom Triggers**
   - Check if `specs/workflows.yaml` exists
   - If yes, read custom trigger definitions and evaluate each:
     - Schedule triggers: check if the target file's last review exceeds the defined interval
     - Event triggers: check if the named event has occurred (based on state file or recent commits)
   - If no `specs/workflows.yaml`, skip and note "No custom triggers defined"

5. **Apply State Transitions**
   - For each triggered document currently in Active state, transition to **Review Due**
   - Record the trigger name and suggested action in `pending_actions`
   - Update `.claude/state/vkf-state.yaml` with new states and pending actions

6. **Display Results**
   - Show all triggers that fired with details
   - Show documents with no triggers (OK status)
   - Show custom trigger results if applicable

### `transition <path> <state>`

1. **Validate Path**
   - Check that the specified file path exists
   - Accept full paths (`specs/constitution/positioning.md`) or short names (`positioning.md`)
   - If short name, resolve to full path by searching `specs/constitution/` and `specs/features/*/`

2. **Validate State**
   - Valid states: `Draft`, `Review`, `Active`, `Review Due`, `Archived`
   - Case-insensitive matching (e.g., `active` matches `Active`)

3. **Apply Transition**
   - Update the document's entry in `.claude/state/vkf-state.yaml`:
     - Set `state` to the new value
     - Set `since` to today's date
     - Clear `last_trigger` if transitioning to Active or Draft
   - If transitioning to Active, remove any pending actions for this document

4. **Log Transition**
   - Add entry to `workflow.transition_log` in `vkf-state.yaml`:
     ```yaml
     transition_log:
       - path: "specs/constitution/positioning.md"
         from: "Review Due"
         to: "Active"
         date: "2026-03-04"
         reason: "Manual transition after review"
     ```

5. **Commit**: `[workflow] Transition {filename} to {state}`

## Lifecycle States

| State | Meaning | Entry Condition |
|-------|---------|-----------------|
| **Draft** | New or heavily revised, not yet authoritative | Created or major rewrite |
| **Review** | Under active review for accuracy/completeness | Submitted for review |
| **Active** | Current, authoritative, ready for use | Review approved |
| **Review Due** | Trigger fired, needs re-review | Schedule or event trigger |
| **Archived** | Superseded or deprecated, kept for history | Manual archival |

## State Storage Format

File: `.claude/state/vkf-state.yaml` under the `workflow` key:

```yaml
workflow:
  documents:
    "specs/constitution/mission.md":
      state: "Active"
      since: "2026-02-15"
      last_trigger: null
    "specs/constitution/positioning.md":
      state: "Review Due"
      since: "2026-03-04"
      last_trigger: "post-ingestion-review"
  pending_actions:
    - path: "specs/constitution/positioning.md"
      action: "Review after ingestion ING-005 modified competitive landscape"
      triggered: "2026-03-04"
  transition_log:
    - path: "specs/constitution/positioning.md"
      from: "Active"
      to: "Review Due"
      date: "2026-03-04"
      reason: "Trigger: post-ingestion-review (ING-005)"
```

## Custom Triggers Format

File: `specs/workflows.yaml` (optional):

```yaml
triggers:
  - name: "Monthly competitive review"
    target: "specs/constitution/positioning.md"
    schedule: "30d"
    action: "Review competitive landscape is current"
  - name: "Post-release spec review"
    event: "release"
    targets: ["specs/features/*/spec.md"]
    action: "Review affected feature specs"
```

## Output Format

**`status` (or no args):**
```
Documentation Lifecycle Status
==============================
Generated: 2026-03-04

Active (5):
  ✓ specs/constitution/mission.md          since 2026-02-15
  ✓ specs/constitution/pmf-thesis.md       since 2026-02-01
  ✓ specs/constitution/principles.md       since 2026-02-10
  ✓ specs/features/auth/spec.md            since 2026-02-20
  ✓ specs/features/billing/spec.md         since 2026-01-15

Review Due (2):
  ⚠ specs/constitution/positioning.md      trigger: post-ingestion-review
    Action: Review after ingestion ING-005 modified competitive landscape
  ⚠ specs/constitution/personas.md         trigger: quarterly-review
    Action: Quarterly review overdue (last: 2025-12-01, 94 days ago)

Draft (1):
  ◯ specs/constitution/icps.md             since 2026-02-26

Archived (0):
  (none)

Pending Actions: 2 documents need attention
Next: /vkf/workflow check (evaluate all triggers)
      /vkf/workflow transition <path> <state> (manual transition)
```

**`check`:**
```
Workflow Trigger Evaluation
===========================
Generated: 2026-03-04

Triggers Fired:
  🔔 POST-INGESTION REVIEW
     positioning.md — modified by ING-005 (today)
     Suggested: Review competitive landscape additions

  🔔 QUARTERLY REVIEW
     personas.md — last amended 2025-12-01 (94 days ago)
     Suggested: Schedule persona review, consider /vkf/gaps personas

  🔔 MONTHLY OKR CHECK
     2026-Q1 OKRs — last updated 2026-02-01 (31 days ago)
     Suggested: /vkf/okrs update

No Triggers (OK):
  ✓ mission.md, pmf-thesis.md, principles.md — all recently reviewed
  ✓ Feature specs — no post-release triggers pending

Custom Triggers (from specs/workflows.yaml):
  ✓ Monthly competitive review — not due (last: 2026-02-20)
```

**`transition`:**
```
State Transition
================
  specs/constitution/positioning.md
  Review Due → Active (2026-03-04)

  Pending action cleared: "Review after ingestion ING-005..."
  Logged to transition history.
```

## Error Handling

- **No workflow state file**: Initialize automatically by scanning all documents and inferring states from content freshness. Report "Initialized workflow state for {N} documents."
- **Invalid state**: Report "Invalid state `{input}`. Valid states: Draft, Review, Active, Review Due, Archived."
- **File not found**: Check path, search `specs/constitution/` and `specs/features/*/` for partial matches. If no match: "File not found: `{path}`. Check the path and try again."
- **No workflows.yaml**: Skip custom triggers and note "No custom triggers defined — create `specs/workflows.yaml` to add schedule or event-based triggers."
- **No ingestion log for event triggers**: Skip post-ingestion triggers and note "No ingestion log found — post-ingestion triggers skipped."
- **State file corrupted**: Back up the corrupted file to `vkf-state.yaml.bak`, reinitialize, and warn "Workflow state was corrupted and has been reinitialized. Backup saved."
