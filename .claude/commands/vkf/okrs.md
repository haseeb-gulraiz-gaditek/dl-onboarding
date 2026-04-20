---
description: Manage quarterly objectives and key results linked to constitution sections and feature specs
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Subcommand
  - `draft {quarter}` (e.g., `draft 2026-Q2`) — interactive OKR creation
  - `update` — progress update for current quarter
  - `review` — end-of-quarter scoring
  - `archive` — archive current quarter, create next quarter stub
  - No args — show current quarter OKRs

## Actions

### `draft {quarter}`

1. **Ensure Directory Structure**
   - Create `specs/okrs/current/` and `specs/okrs/archive/` if they do not exist

2. **Check for Existing Quarter**
   - If `specs/okrs/current/{YYYY}-Q{N}.md` already exists, ask whether to overwrite or edit the existing file
   - If editing, load current content as the starting point

3. **Read Constitution Context**
   - Read all files in `specs/constitution/` to understand current product direction
   - Identify sections with known gaps (empty placeholders, stale content)
   - Read `specs/gaps/` if it exists to find unresolved unknowns

4. **Suggest Objectives**
   - Based on constitution content and gaps, suggest 2-4 objectives
   - Each suggestion includes: objective description, relevant constitution section, rationale
   - Present suggestions and ask the user to select, modify, or add their own

5. **Define Key Results**
   - For each accepted objective, walk through key result definition:
     - KR description
     - Metric (what is measured)
     - Baseline (current value)
     - Target (end-of-quarter goal)
     - Link to constitution section or feature spec
   - Suggest 2-4 KRs per objective based on the linked constitution content

6. **Write OKR File**
   - Create `specs/okrs/current/{YYYY}-Q{N}.md` using the structured format below
   - Include the initial Progress Log entry with "Quarter started, baselines set"

7. **Commit**: `[okr] Draft {quarter} objectives`

### `update`

1. **Load Current Quarter**
   - Find the current quarter OKR file in `specs/okrs/current/`
   - If multiple files exist, use the one with the latest quarter designation

2. **Collect Progress**
   - For each key result, display current value and ask for the updated value
   - Accept numeric values, percentages, or "Done"/"Not started"

3. **Auto-Calculate Status**
   - Determine elapsed fraction of the quarter (days elapsed / total days)
   - Calculate target pace: expected progress = elapsed fraction * target
   - Score each KR:
     - **On Track**: current >= 70% of target pace
     - **At Risk**: current >= 40% and < 70% of target pace
     - **Behind**: current < 40% of target pace
     - **Done**: KR completed (score = 1.0)

4. **Check Constitution Changes**
   - For each linked constitution section, check if the file was modified since the last OKR update
   - If changes detected, note them in the progress log entry

5. **Update File**
   - Update current values and statuses in the OKR file
   - Update the `Last updated` date
   - Add a new entry to the Progress Log section with date and notes

6. **Commit**: `[okr] Update {quarter} progress`

### `review`

1. **Load Current Quarter**
   - Read the current quarter OKR file

2. **Collect Final Values**
   - For each key result, ask for the final value if not already at target
   - Auto-score: `score = min(actual / target, 1.0)` rounded to one decimal

3. **Calculate Objective Scores**
   - Each objective score = average of its KR scores
   - Overall score = average of all objective scores

4. **Flag Constitution Implications**
   - KR scored < 0.3: Flag linked constitution section — "Evidence may need revision, assumptions may be invalidated"
   - KR scored 0.3 - 0.6: Flag as "Partial progress — consider adjusting targets or approach"
   - KR scored > 0.9: Flag as "Exceeded — consider raising ambition or documenting what worked"

5. **Update File**
   - Fill in all score columns
   - Add review summary at the bottom of the file
   - Update status to "Reviewed"

6. **Commit**: `[okr] Review {quarter} — overall score {X.X}`

### `archive`

1. **Identify Current Quarter**
   - Find the current quarter file in `specs/okrs/current/`

2. **Validate Review Complete**
   - Check that the file has status "Reviewed" — if not, warn and suggest running `review` first
   - If user confirms archive without review, proceed

3. **Archive**
   - Move the file to `specs/okrs/archive/{YYYY}-Q{N}.md`

4. **Create Next Quarter Stub**
   - Determine next quarter (Q1->Q2, Q2->Q3, Q3->Q4, Q4->Q1 of next year)
   - Carry over unmet KRs (score < 0.7) as suggested objectives for the new quarter
   - Create `specs/okrs/current/{next-YYYY}-Q{N}.md` with stub content

5. **Commit**: `[okr] Archive {quarter}, create {next quarter} stub`

### No args

1. **Load Current Quarter**
   - Read the current quarter OKR file in `specs/okrs/current/`

2. **Display Summary**
   - Show each objective with its status and constitution link
   - Show each KR with metric, current value, target, and status
   - Show next suggested actions

## OKR File Format

File: `specs/okrs/current/{YYYY}-Q{N}.md`

```markdown
# Q2 2026 Objectives & Key Results

**Quarter:** 2026-Q2 (Apr 1 - Jun 30)
**Last updated:** 2026-04-15
**Status:** Active

---

## Objective 1: [Objective description]

**Constitution link:** pmf-thesis.md > Evidence
**Status:** On Track

| # | Key Result | Metric | Baseline | Target | Current | Score | Status |
|---|-----------|--------|----------|--------|---------|-------|--------|
| 1.1 | [KR description] | [metric] | [start] | [goal] | [now] | — | On Track |
| 1.2 | [KR description] | [metric] | [start] | [goal] | [now] | — | At Risk |

**Feature spec links:** specs/features/retention/spec.md

---

## Objective 2: [Objective description]

[...]

---

## Progress Log

| Date | Notes |
|------|-------|
| 2026-04-15 | KR 1.1 updated: acquired 3 of 5 target customers |
| 2026-04-01 | Quarter started, baselines set |
```

## Output Format

**No args / status display:**
```
Current OKRs: 2026-Q2
======================
Last updated: 2026-04-15

Objective 1: Demonstrate product-market fit with enterprise customers
  Status: On Track | Constitution: pmf-thesis.md
  KR 1.1: Acquire 5 enterprise customers        3/5    On Track
  KR 1.2: Achieve 90% monthly retention         82%    At Risk
  KR 1.3: Get 3 customer referrals              1/3    Behind

Objective 2: Establish competitive positioning
  Status: At Risk | Constitution: positioning.md
  KR 2.1: Complete competitive analysis          Done   ✓
  KR 2.2: Publish differentiation content        0/3    Behind

Next: /vkf/okrs update (record progress)
      /vkf/okrs review (end-of-quarter scoring)
```

**After `review`:**
```
OKR Review: 2026-Q2
====================
Overall Score: 0.6

Objective 1: Demonstrate product-market fit (0.7)
  KR 1.1: Acquire 5 enterprise customers        4/5    0.8
  KR 1.2: Achieve 90% monthly retention         88%    0.7
  KR 1.3: Get 3 customer referrals              2/3    0.7

Objective 2: Establish competitive positioning (0.5)
  KR 2.1: Complete competitive analysis          Done   1.0
  KR 2.2: Publish differentiation content        0/3    0.0

Constitution Implications:
  ⚠ KR 2.2 scored 0.0 — review positioning.md differentiation strategy
  ✓ KR 1.1 scored 0.8 — pmf-thesis.md evidence is strengthening

Next: /vkf/okrs archive (archive and start next quarter)
```

## Error Handling

- **No OKRs directory**: Create `specs/okrs/current/` and `specs/okrs/archive/` automatically
- **No current quarter**: Report "No current quarter OKRs found. Use `/vkf/okrs draft {quarter}` to create one (e.g., `/vkf/okrs draft 2026-Q2`)."
- **Quarter already exists**: Ask whether to overwrite or edit the existing file
- **No constitution files to link**: Warn "No constitution files found — OKRs will be created without constitution links. Run `/vkf/init` first for full integration."
- **Invalid quarter format**: Report expected format `YYYY-QN` (e.g., `2026-Q2`)
- **Archive without review**: Warn "Quarter has not been reviewed. Run `/vkf/okrs review` first, or confirm to archive without scoring."
- **Multiple files in current/**: Use the latest quarter, note the others exist
