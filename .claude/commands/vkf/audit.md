---
description: Query audit logs for content provenance — trace sections to sources, track placements, detect staleness and contradictions
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Query mode
  - `--trace <section-path>` — reverse: show all sources that contributed to a section
  - `--source <ingestion-id>` — forward: show where content from a source was placed
  - `--stale` — find placements whose source may have been updated since placement
  - `--contradictions` — find potentially contradictory placements in the same section
  - No args — summary statistics

## Actions

1. **Load Audit Log**
   - Read `specs/ingestion-log.yaml`
   - If `specs/ingestion-log-archive.yaml` exists, read it as well and merge entries
   - Parse all ingestion entries into a working dataset

2. **Parse Query Mode**
   - Check `$ARGUMENTS` for `--trace`, `--source`, `--stale`, `--contradictions`
   - If none matched and arguments are non-empty, report unrecognized flag
   - If empty, default to summary mode

3. **Execute Query**

   **`--trace <section-path>`:**
   - Scan all log entries for `extractions[].target` matching the section path
   - Accept partial matches (e.g., `positioning` matches `specs/constitution/positioning.md`)
   - Group results by source
   - For each source, show: source type, identifier, date, confidence, excerpt
   - Sort by recency (newest first)
   - Calculate age of each source and flag sources older than 90 days

   **`--source <ingestion-id>`:**
   - Find the log entry with matching `id` field (e.g., `ING-003`)
   - Show all extractions: target, action, confidence, excerpt
   - Show any skipped content and reasons from the `skipped` field
   - Show any amendment IDs triggered by this ingestion
   - If the ingestion has a `speaker` field (transcript), include it

   **`--stale`:**
   - For each log entry with a `source_hash` field:
     - Check if the source file still exists (for local files)
     - Compare current hash against stored hash
   - For entries without hash:
     - Flag any source with ingestion date older than 90 days
   - Collect all potentially stale placements
   - Report: source, original ingestion date, age, affected sections

   **`--contradictions`:**
   - Group all extractions by target section
   - Within each section, collect excerpts from different sources
   - Compare excerpts that address the same topic area:
     - Different numeric claims (market size, percentages)
     - Different categorical claims (positioning, competitor status)
     - Different temporal claims (timelines, dates)
   - Flag potential contradictions for human review
   - Note: this is heuristic, not definitive — always present as "potential" contradictions

   **No args (summary):**
   - Count total ingestions
   - Determine date range (first to last ingestion)
   - Calculate coverage: which constitution sections have been populated by ingestion vs manual
   - Per-section breakdown: number of contributing sources, last ingestion date
   - Count feature specs populated by ingestion
   - Count potential issues: stale sources, sections with no ingestion history

4. **Display Results** — formatted output per the mode-specific format below

## Output Format

**`--trace <section-path>`:**
```
Audit Trace: specs/constitution/positioning.md
=============================================
3 sources contributed to this section

Source 1: board-deck-q1.txt (ING-003)
  Type: local-file | Ingested: 2026-02-15 (17 days ago)
  Section: Competitive Landscape | Action: append | Confidence: high
  Excerpt: "Three key competitors in the deployment automation..."

Source 2: acme-call transcript (ING-005)
  Type: transcript | Ingested: 2026-03-04 (today)
  Section: Competitive Landscape | Action: append | Confidence: medium
  Excerpt: "Acme CTO mentioned evaluating CompetitorX..."
  Speaker: Acme CTO

Source 3: exa.ai research (ING-001)
  Type: webpage | Ingested: 2026-01-20 (43 days ago)
  Section: Category | Action: replace | Confidence: high
  Excerpt: "The deployment orchestration category is growing..."

⚠ Source 3 is 43 days old — consider /vkf/research positioning to refresh
```

**`--source <ingestion-id>`:**
```
Audit Source: ING-003 (board-deck-q1.txt)
=========================================
Type: local-file | Ingested: 2026-02-15

Extractions (4):
  1. specs/constitution/positioning.md > Competitive Landscape
     Action: append | Confidence: high
     Excerpt: "Three key competitors in the deployment automation..."

  2. specs/constitution/pmf-thesis.md > Evidence
     Action: append | Confidence: medium
     Excerpt: "Revenue grew 40% QoQ suggesting strong pull..."

  3. specs/features/billing/spec.md > Requirements
     Action: append | Confidence: low
     Excerpt: "Enterprise customers requesting annual billing..."

  4. specs/constitution/icps.md > Buying Trigger
     Action: append | Confidence: medium
     Excerpt: "Typically triggered by a failed deployment..."

Skipped (1):
  - Page 12 (appendix): Financial projections — not relevant to constitution

Amendments triggered: AMD-007 (positioning competitive update)
```

**`--stale`:**
```
Stale Source Analysis
=====================
2 potentially stale sources found

ING-001: exa.ai research (webpage)
  Ingested: 2026-01-20 (43 days ago)
  Affected sections: positioning.md (Category)
  Recommendation: /vkf/research positioning

ING-002: competitor-analysis.pdf (local-file)
  Ingested: 2025-12-15 (79 days ago)
  Hash changed: YES (file was modified 2026-02-01)
  Affected sections: positioning.md (Competitive Landscape)
  Recommendation: /vkf/ingest competitor-analysis.pdf
```

**`--contradictions`:**
```
Potential Contradictions
========================
2 potential contradictions detected (for human review)

1. specs/constitution/positioning.md > Competitive Landscape
   ING-003 (2026-02-15): "Three key competitors..."
   ING-005 (2026-03-04): "Five main competitors including two new entrants..."
   ⚠ Conflict: different competitor counts — may need reconciliation

2. specs/constitution/pmf-thesis.md > Market Size
   ING-001 (2026-01-20): "TAM estimated at $2.1B..."
   ING-004 (2026-02-28): "Total addressable market around $3.5B..."
   ⚠ Conflict: different TAM figures — verify sources and methodology
```

**No args (summary):**
```
Audit Summary
=============
Total ingestions: 9 | Date range: 2026-01-05 to 2026-03-04

Constitution Coverage:
  Section              Sources  Last Ingested   Status
  ─────────────────────────────────────────────────────
  mission.md              2     2026-02-01      ✓ Recent
  pmf-thesis.md           4     2026-03-04      ✓ Recent
  personas.md             1     2026-01-15      ⚠ 48 days
  icps.md                 0     —               ◯ No data
  positioning.md          3     2026-03-04      ✓ Recent
  principles.md           1     2026-02-10      ✓ Recent
  governance.md           0     —               ◯ No data

Feature Specs: 3 specs populated by ingestion

Potential Issues:
  ⚠ 2 sources older than 90 days
  ⚠ icps.md and governance.md have no ingestion history
```

Commit: None — audit is read-only.

## Error Handling

- **No ingestion log**: Report "No ingestion log found at `specs/ingestion-log.yaml`. Run `/vkf/ingest` to start building provenance."
- **Invalid ingestion ID**: Report the ID was not found and list the 5 most recent ingestion IDs for reference
- **Section not found in log**: Report "No ingestion history for `<section-path>`. This section may have been populated manually."
- **Malformed log entries**: Skip malformed entries, note count of skipped entries in output
- **Empty log**: Report "Ingestion log exists but contains no entries."
