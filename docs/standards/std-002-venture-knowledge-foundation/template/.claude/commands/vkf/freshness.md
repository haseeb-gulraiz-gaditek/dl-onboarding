---
description: Scan all specs and constitution files for freshness, cross-reference with git history, report stale documents
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS** (optional): `--source-aware` to incorporate audit log data and detect source staleness

## Actions

1. **Scan Constitution Files**
   - Read all `.md` files in `specs/constitution/` (or the configured `constitution_root`)
   - Parse `Last amended` dates — check both YAML frontmatter and in-body text. Use the most recent date if both exist.
   - Classify each: CURRENT / REVIEW_DUE / VERY_STALE / MISSING

2. **Scan Project-Level Specs**
   - Read any `.md` files at `specs/` root (e.g., `architecture.md`, `api-reference.md`, `data-dictionary.md`)
   - Parse `Last reviewed: YYYY-MM-DD` from each file header
   - Classify by date only (no code path mapping): CURRENT / REVIEW_DUE / VERY_STALE / MISSING
   - Also scan any custom spec directories under `specs/` (e.g., `specs/schemas/`, `specs/apis/`) — same date-only rules

3. **Scan Feature Specs**
   - Read all `.md` files in each feature directory, including sub-directories — not just `spec.md`
   - Parse `Last reviewed` dates — check both YAML frontmatter and in-body text. Use the most recent date if both exist.
   - For each spec with a review date, run git drift detection:
     ```bash
     git log --since="{review_date}" --oneline -- {corresponding_code_path}
     ```
   - All `.md` files in a feature directory share the same code path mapping (derived from the feature directory name)
   - Classify each: CURRENT / STALE / VERY_STALE / MISSING

4. **Path Mapping for Git Detection**
   - Map feature spec paths to likely code paths:
     - `specs/features/auth/*.md` -> `src/features/auth/`, `src/auth/`, `app/auth/`, `lib/auth/`
     - Use the feature directory name as the search key
   - If no matching code path exists, skip git detection for that spec
   - Project-level specs and custom directory specs do not use git detection

5. **Generate Report**
   - List all files grouped by status
   - Show days since last review/amendment
   - For STALE specs, show the number of code commits since last review
   - For STALE specs, show the most recent relevant commit message
   - Calculate summary statistics

6. **Source-Aware Freshness** (only if `--source-aware` flag present)

   If `specs/ingestion-log.yaml` exists, enhance the freshness report with source provenance:

   - For each spec that has ingestion history, check if the original source may have been updated:
     - Compare source hash (if stored) with current source (if accessible)
     - Flag sources older than 90 days as potentially stale
   - Add `SOURCE_STALE` status for specs whose source data may be outdated
   - Show source age alongside the standard freshness status

   Additional output for source-aware mode:
   ```
   Source-Aware Freshness:
     ⚠ SOURCE_STALE  positioning.md    source "competitor-analysis.txt" is 95 days old
     ⚠ SOURCE_STALE  pmf-thesis.md     source "customer-survey.csv" is 120 days old
     ✓ SOURCE_OK     personas.md       source "user-interviews.txt" ingested 12 days ago

   Suggested: /vkf/research positioning (refresh competitive data)
   ```

7. **Update State**
   - Write freshness scan results to `.claude/state/vkf-state.yaml`:
     ```yaml
     last_freshness_scan: "{current ISO timestamp}"
     stale_specs:
       - path: "specs/features/billing/spec.md"
         status: STALE
         last_reviewed: "2026-01-05"
         commits_since: 3
     ```

## Output Format

```
Spec Freshness Report
=====================
Generated: 2026-02-26

Constitution (specs/constitution/):
  ✓ CURRENT     mission.md           amended 2026-02-01 (25 days)
  ✓ CURRENT     pmf-thesis.md        amended 2026-01-20 (37 days)
  ⚠ REVIEW_DUE  personas.md          amended 2025-10-15 (134 days)
  ✗ MISSING     icps.md              no date found
  ✓ CURRENT     positioning.md       amended 2026-02-10 (16 days)
  ✓ CURRENT     principles.md        amended 2026-02-10 (16 days)
  ✓ CURRENT     governance.md        amended 2026-01-15 (42 days)

Project-Level Specs (specs/):
  ✓ CURRENT     architecture.md      reviewed 2026-02-15 (11 days)
  ⚠ REVIEW_DUE  api-reference.md     reviewed 2025-11-01 (118 days)

Feature Specs (specs/features/):
  ✓ CURRENT     auth/spec.md         reviewed 2026-02-10 | no code changes
  ✓ CURRENT     auth/decisions.md    reviewed 2026-02-10 | no code changes
  ⚠ STALE       billing/spec.md      reviewed 2026-01-05 | 3 commits since
                  └─ most recent: "fix(billing): handle currency edge case"
  ✗ VERY_STALE  payments/spec.md     reviewed 2025-08-20 (190 days)
  ✗ MISSING     search/spec.md       no review date found

Summary: 12 files scanned
  ✓ CURRENT: 7  ⚠ STALE/REVIEW_DUE: 3  ✗ VERY_STALE/MISSING: 2

Action Items (priority order):
  1. [MISSING] Add Last reviewed date to search/spec.md
  2. [MISSING] Add Last amended date to icps.md
  3. [VERY_STALE] Review payments/spec.md (190 days)
  4. [REVIEW_DUE] Review api-reference.md (118 days)
  5. [STALE] Review billing/spec.md (3 commits since review)
  6. [REVIEW_DUE] Schedule quarterly review for personas.md
```

## Freshness Thresholds

### Feature Specs
| Status | Condition |
|--------|-----------|
| CURRENT | Review date within 90 days, no code changes since |
| STALE | Code changed since review date, OR 30-90 days old |
| VERY_STALE | Review date older than 90 days |
| MISSING | No review date found |

### Constitution Files
| Status | Condition |
|--------|-----------|
| CURRENT | Last amended within 90 days |
| REVIEW_DUE | Last amended 90-180 days ago |
| VERY_STALE | Last amended over 180 days ago |
| MISSING | No amendment date found |

### Source-Aware (with `--source-aware` flag)
| Status | Condition |
|--------|-----------|
| SOURCE_OK | Source ingested within 90 days, no hash mismatch |
| SOURCE_STALE | Source older than 90 days or hash mismatch detected |
| SOURCE_UNKNOWN | No ingestion history for this spec |

## Error Handling

- **No specs directory**: Suggest `/vkf/init`
- **Git not available**: Skip drift detection, note in report, assess by date only
- **No feature specs yet**: Report "No feature specs found" -- this is expected for new repos
- **No code paths match**: Skip git detection for that spec, note as "no code mapping"
