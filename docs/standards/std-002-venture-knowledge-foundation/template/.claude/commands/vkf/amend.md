---
description: Tiered amendment process (C0-C3) for constitution changes with propagation checking and history tracking
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Target constitution section or file path
  - Section name: `mission`, `pmf-thesis`, `personas`, `icps`, `positioning`, `principles`, `governance`
  - File path: `specs/constitution/positioning.md`

## Actions

1. **Identify Target**
   - Resolve `$ARGUMENTS` to a constitution file in `specs/constitution/` (or the configured `constitution_root`)
   - If a section name is given (e.g., `positioning`), map to `specs/constitution/positioning.md`
   - If a full path is given, verify it exists and is inside the constitution directory

2. **Check File State**
   - Scan the target file for `[REQUIRED]` placeholders
   - If any `[REQUIRED]` placeholders remain: redirect to `/vkf/constitution` — "This file still has placeholders. Use `/vkf/constitution {section}` for initial drafting."
   - If no placeholders: proceed with amendment process

3. **Auto-Detect Tier**
   - Examine the proposed change against the current content and classify:

   | Tier | Name | Detection | Process |
   |------|------|-----------|---------|
   | C0 | Cosmetic | Only whitespace, formatting, typos, date updates | Direct edit, no proposal needed |
   | C1 | Clarification | Rewording without changing meaning (same concepts, different words) | Note in amendment history |
   | C2 | Substantive | Adding, changing, or removing actual content/meaning | Full proposal + delta + propagation check |
   | C3 | Structural | Changing principles, invalidating PMF thesis, altering governance model | Full C2 + principle conflict analysis + rollback plan + impact analysis |

4. **Announce Tier**
   - Always announce: "This is a **C{N} ({name})** change because {reason}."
   - Never skip the announcement, even if the user says "just change it"

5. **Execute by Tier**

   **C0 (Cosmetic):**
   - Apply change directly
   - Update `Last amended: YYYY-MM-DD` date in file header
   - Commit: `[constitution] C0: {brief description}`

   **C1 (Clarification):**
   - Apply change
   - Update `Last amended: YYYY-MM-DD` date in file header
   - Add entry to `governance.md` Amendment History table
   - Commit: `[constitution] C1: {brief description}`

   **C2 (Substantive):**
   - Create amendment proposal showing:
     - **Current**: the existing content being changed (with line context)
     - **Proposed**: the new content
     - **Rationale**: why the change is being made (cite ingestion IDs or evidence if available)
   - Run propagation check:
     - Scan all constitution files for references to the changing content
     - Scan all feature specs for references to the changing content
     - Report each reference as: affected file, line number, relevant excerpt
   - Wait for user approval
   - Apply change, update `Last amended` date, add Amendment History entry
   - Commit: `[constitution] C2: {brief description}`

   **C3 (Structural):**
   - Everything from C2, plus:
   - **Principle conflict analysis**: does this change contradict any principle in `principles.md`? List each principle and whether it conflicts, is neutral, or is reinforced.
   - **Rollback plan**: what would reverting this change require? List files and sections that would need to be restored.
   - **Impact analysis**: what decisions, feature specs, or downstream documents depend on the content being changed?
   - Present full impact assessment
   - Wait for user approval
   - Apply change, update `Last amended` date, add Amendment History entry
   - Commit: `[constitution] C3: {brief description}`

6. **Update Audit Log**
   - If the amendment was triggered by an ingestion (`/vkf/ingest`), record the amendment ID in the corresponding ingestion log entry
   - Link format in `specs/ingestion-log.yaml`: `amendment_id: "AMD-{N}"`

7. **Update State**
   - Record amendment in `.claude/state/vkf-state.yaml`:
     ```yaml
     last_amendment: "{current ISO timestamp}"
     last_amendment_id: "AMD-{N}"
     last_amendment_tier: "C{N}"
     last_amendment_target: "{file path}"
     ```

## Output Format

### C0/C1 (minimal output):
```
Amendment: positioning.md
=========================
Tier: C0 (Cosmetic) — formatting and typo fixes only

Applied: Fixed typo in Competitive Landscape section
Updated: Last amended → 2026-03-04
Committed: [constitution] C0: Fix typo in positioning competitive landscape
```

### C2 (full proposal):
```
Amendment Proposal: positioning.md
==================================
Tier: C2 (Substantive) — content meaning changes

Current:
  > For startup CTOs who need deployment automation...

Proposed:
  > For engineering leaders who need deployment orchestration...

Rationale: Broadening target from CTOs to engineering leaders based on
           customer call evidence (ING-005, Acme transcript)

Propagation Check:
  ⚠ personas.md references "startup CTOs" (line 23) — may need update
  ⚠ features/deploy/spec.md references "CTO workflow" (line 8)
  ✓ pmf-thesis.md — no references to changing content
  ✓ principles.md — no conflicts

Approve this amendment? (y/n)
```

### C3 (full impact assessment):
```
Amendment Proposal: principles.md
=================================
Tier: C3 (Structural) — changing a core principle

Current:
  > Principle 3: Speed over completeness — ship fast, iterate

Proposed:
  > Principle 3: Correctness over speed — validate before shipping

Rationale: Post-mortem from Acme deployment failure (2026-02-28)

Propagation Check:
  ⚠ governance.md references "speed over completeness" in decision framework
  ⚠ features/deploy/spec.md built around rapid deployment assumption

Principle Conflict Analysis:
  ✓ Principle 1 (User trust first) — reinforced by correctness focus
  ⚠ Principle 4 (Bias toward action) — potential tension with validation step
  ✓ Principle 5 (Measure everything) — neutral

Rollback Plan:
  - Revert principles.md to previous Principle 3 text
  - Re-review governance.md decision framework
  - Re-review features/deploy/spec.md assumptions

Impact Analysis:
  - Deploy feature spec assumes rapid iteration (may need redesign)
  - CI/CD pipeline decisions based on speed-first principle
  - 2 pending feature specs reference this principle

Approve this amendment? (y/n)
```

## Amendment History Entry Format

Added to the Amendment History table in `governance.md`:

```markdown
| 2026-03-04 | positioning.md | C2: Broadened target persona from CTOs to engineering leaders | @founder |
```

## Error Handling

- **File not found**: List available constitution files:
  ```
  File not found: "pricing". Available sections:
    mission, pmf-thesis, personas, icps, positioning, principles, governance
  ```
- **File still in draft**: Redirect to `/vkf/constitution {section}` for initial drafting
- **No governance.md**: Create it with just the Amendment History table so the entry can be recorded
- **User says "just change it"**: Still announce tier, explain briefly why governance matters ("Tracking changes prevents knowledge drift"), then proceed with the proper process for that tier
- **No specs directory**: Suggest `/vkf/init`
- **State file missing**: Create `.claude/state/vkf-state.yaml` with amendment fields
