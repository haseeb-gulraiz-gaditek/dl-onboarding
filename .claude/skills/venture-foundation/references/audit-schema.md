# Audit Log Schema & Query Patterns

Full provenance traceability for the Venture Knowledge Foundation. Every piece of information is traceable from source to placement and back -- no content exists in the knowledge base without a recorded origin.

---

## Primary Log Location

```
specs/ingestion-log.yaml
```

All ingestion events are recorded here. The log is append-only (see Log Immutability section).

---

## Entry Schema

Each ingestion event creates one entry:

```yaml
- id: "ING-001"                      # Sequential ingestion ID
  timestamp: "2026-03-04T10:30:00Z"  # ISO 8601 UTC
  source:
    type: "google-doc"               # Source type (see Source Types below)
    identifier: "board-deck-q1.txt"  # Human-readable source name
    url: null                        # Optional: original URL if applicable
    word_count: 2450                 # Word count of source content
    hash: "sha256:abc123..."         # Content hash for duplicate/staleness detection
  extractions:
    - target: "specs/constitution/positioning.md"
      section: "Competitive Landscape"   # H2 section within the target file
      action: "append"                   # How content was placed
      confidence: "high"                 # Classification confidence
      excerpt: "First 100 chars of placed content..."
    - target: "specs/features/export/spec.md"
      section: null                      # null when creating a new file
      action: "create"
      confidence: "medium"
      excerpt: "Feature request for CSV export..."
  skipped:
    - reason: "unclassified"             # Why content was not placed
      excerpt: "Content that wasn't placed..."
  modified_files:                        # All files touched by this ingestion
    - "specs/constitution/positioning.md"
    - "specs/features/export/spec.md"
  amendment_ids: ["AMEND-003"]           # If changes routed through /vkf/amend
```

### Source Types

| Type | Description | Example identifier |
|------|-------------|-------------------|
| `google-doc` | Google Docs export (txt/md) | `board-deck-q1.txt` |
| `google-sheet` | Google Sheets export | `customer-feedback-march.csv` |
| `webpage` | Web page content | `blog-post-launch-announcement` |
| `local-file` | File from local filesystem | `notes/investor-meeting.md` |
| `inline` | Content pasted directly into chat | `inline-2026-03-04-001` |
| `transcript` | Meeting/call transcript | `weekly-standup-2026-03-04` |

### Extraction Actions

| Action | Description | When used |
|--------|-------------|-----------|
| `append` | Content added to the end of an existing section | New information extends existing content |
| `replace` | Content replaces an existing section | Updated data supersedes previous content |
| `create` | New file or section created | No prior content existed for this target |

### Skip Reasons

| Reason | Description |
|--------|-------------|
| `unclassified` | Content could not be confidently classified to any target |
| `duplicate` | Content hash matches a previously ingested source |
| `irrelevant` | Content is out of scope for the knowledge base |
| `user-discarded` | User explicitly chose to discard this content |
| `code-snippet` | Source contained code that is not constitution/spec content |
| `too-short` | Source had fewer than 50 words of substantive content |

---

## Transcript-Specific Fields

Transcript ingestions include additional fields for speaker attribution and structured extraction:

```yaml
- id: "ING-015"
  timestamp: "2026-03-04T14:00:00Z"
  source:
    type: "transcript"
    identifier: "product-review-2026-03-04"
    url: null
    word_count: 8200
    hash: "sha256:def456..."
  meeting_brief: "specs/meetings/2026-03-04-product-review.md"  # Intermediary analysis artifact
  transcript_metadata:
    speakers:
      - name: "Alice Chen"
        role: "CEO"
      - name: "Bob Park"
        role: "Head of Product"
    duration_minutes: 45
    extraction_template: "product-review"  # Template used for structured extraction
    raw_speaker_segments: 127             # Number of speaker turns in the transcript
  extractions:
    - target: "specs/constitution/pmf-thesis.md"
      section: "Evidence"
      action: "append"
      confidence: "high"
      excerpt: "Q1 retention numbers discussed..."
      speaker_attribution: "Alice Chen"    # Who said this content
    - target: "specs/features/reporting/spec.md"
      section: null
      action: "create"
      confidence: "medium"
      excerpt: "Request for weekly email reports..."
      speaker_attribution: "Bob Park"
  skipped:
    - reason: "irrelevant"
      excerpt: "Discussion about office lunch plans..."
  modified_files:
    - "specs/constitution/pmf-thesis.md"
    - "specs/features/reporting/spec.md"
  amendment_ids: []
```

### Transcript-Only Fields

| Field | Location | Description |
|-------|----------|-------------|
| `meeting_brief` | Entry level | Path to the intermediary meeting brief document — the analysis artifact connecting the raw transcript to document modifications |
| `transcript_metadata.speakers` | Entry level | List of speakers with names and roles |
| `transcript_metadata.duration_minutes` | Entry level | Meeting duration |
| `transcript_metadata.extraction_template` | Entry level | Which extraction template was used (e.g., `product-review`, `customer-interview`, `board-meeting`) |
| `transcript_metadata.raw_speaker_segments` | Entry level | Total speaker turns for completeness tracking |
| `speaker_attribution` | Extraction level | Which speaker contributed this specific extraction |

---

## Query Modes

### 1. Trace: `--trace <section>`

Reverse lookup -- "What sources contributed to this section?"

Scan all entries where any `extractions[].target` matches the given section path.

```
/vkf/audit --trace specs/constitution/positioning.md

Trace: specs/constitution/positioning.md
=========================================
3 sources contributed to this section:

ING-001  2026-01-15  board-deck-q1.txt (google-doc)
  → Competitive Landscape (append, high confidence)
  → "Unlike Terraform, we handle state..."

ING-007  2026-02-20  market-analysis.md (local-file)
  → Moat / Defensibility (replace, high confidence)
  → "Network effects from shared config..."

ING-012  2026-03-01  competitor-update.txt (inline)
  → Competitive Landscape (append, medium confidence)
  → "New entrant: CloudDeploy raised..."
```

### 2. Source: `--source <id>`

Forward lookup -- "Where did this ingestion's content go?"

Show all extractions and skipped content for a specific ingestion ID.

```
/vkf/audit --source ING-007

Source: ING-007
===============
market-analysis.md (local-file)
Ingested: 2026-02-20  |  2450 words  |  hash: sha256:abc123...

Extractions (3):
  → specs/constitution/positioning.md ## Moat / Defensibility
    Action: replace  |  Confidence: high
    "Network effects from shared config..."

  → specs/constitution/positioning.md ## Competitive Landscape
    Action: append  |  Confidence: high
    "Market growing at 34% CAGR..."

  → specs/features/integrations/spec.md
    Action: create  |  Confidence: medium
    "Integration requirements extracted..."

Skipped (1):
  → "Author bio and publication info..." (irrelevant)

Modified files:
  specs/constitution/positioning.md
  specs/features/integrations/spec.md
```

### 3. Stale: `--stale`

Staleness check -- "Which placements might be outdated?"

Compare each extraction's source timestamp and hash against current data. Flag entries where the source may have been updated since placement.

```
/vkf/audit --stale

Stale Placement Report
=======================
Generated: 2026-03-04

2 potentially stale placements found:

ING-003  competitor-landscape.txt → positioning.md ## Competitive Landscape
  Source ingested: 2025-11-15 (110 days ago)
  ⚠ Source age exceeds 90-day threshold

ING-008  customer-survey-q3.csv → pmf-thesis.md ## Evidence
  Source ingested: 2025-12-01 (94 days ago)
  ⚠ Source age exceeds 90-day threshold
  ⚠ Source type "google-sheet" may have been updated since export
```

### 4. Contradictions: `--contradictions`

Conflict detection -- "Any conflicting content placed in the same section from different sources?"

Find entries where multiple sources contributed to the same target section. Flag potential contradictions for human review.

```
/vkf/audit --contradictions

Contradiction Report
====================
Generated: 2026-03-04

1 potential contradiction found:

specs/constitution/pmf-thesis.md ## Evidence
  ING-005 (2026-01-20): "Month-2 retention is 68%"
  ING-011 (2026-02-28): "Retention dropped to 52% in February"
  → Same section, conflicting data points. Review recommended.
```

### 5. Summary (no args)

Overview statistics when `/vkf/audit` is run without arguments.

```
/vkf/audit

Ingestion Audit Summary
========================
Generated: 2026-03-04

Total ingestions: 15
Date range: 2026-01-10 to 2026-03-04
Total extractions: 38
Total skipped: 7

Coverage by constitution section:
  mission.md          2 extractions from 2 sources
  pmf-thesis.md       8 extractions from 5 sources
  personas.md         4 extractions from 3 sources
  icps.md             1 extraction  from 1 source
  positioning.md      6 extractions from 4 sources
  principles.md       3 extractions from 2 sources
  governance.md       1 extraction  from 1 source
  index.md            0 extractions

Coverage by feature specs:
  specs/features/export/spec.md        3 extractions
  specs/features/reporting/spec.md     2 extractions
  specs/features/integrations/spec.md  1 extraction

Source type breakdown:
  google-doc:  5 ingestions
  local-file:  4 ingestions
  transcript:  3 ingestions
  inline:      2 ingestions
  webpage:     1 ingestion

Gaps (sections with 0 extractions):
  index.md — no content ingested (expected; rarely targeted)
```

---

## Archiving

Entries older than 6 months can be moved to a separate archive file for performance:

```
specs/ingestion-log-archive.yaml
```

### Archiving Rules

1. Only entries older than 180 days are eligible for archiving
2. Move the full entry (including all extractions and skipped content) to the archive file
3. The archive file follows the same schema as the primary log
4. Query commands automatically search both the primary log and the archive
5. Archive entries are read-only -- they follow the same immutability rules as the primary log

### Archiving Command

Archiving is triggered manually, never automatically:

```
/vkf/audit --archive
```

This moves eligible entries, reports what was archived, and confirms the primary log was trimmed.

---

## Integration with Freshness

The `/vkf/freshness` command accepts a `--source-aware` flag that cross-references freshness status with the ingestion log.

### SOURCE_STALE Status

When `--source-aware` is active, an additional freshness status is available:

| Status | Condition |
|--------|-----------|
| **SOURCE_STALE** | A source that contributed to this section was ingested more than 90 days ago, or the source's content hash no longer matches (indicating the source was updated since ingestion) |

### How It Works

```
For each constitution section:
  1. Run standard freshness check (see freshness-rules.md)
  2. Look up all ingestion entries targeting this section
  3. For each source:
     a. Check if source timestamp is older than 90 days
     b. If source URL exists, optionally re-fetch and compare hash
  4. If any source is stale, add SOURCE_STALE alongside the existing status
```

### Example Output

```
Spec Freshness Report (source-aware)
=====================================
Generated: 2026-03-04

Constitution Files:
  CURRENT       mission.md           (amended 2026-02-01)
  CURRENT       pmf-thesis.md        (amended 2026-01-20)
  SOURCE_STALE  positioning.md       (amended 2026-02-15, but source ING-003 is 110 days old)
  MISSING       icps.md              (no date found)
```

---

## Log Immutability

The ingestion log is append-only. This ensures full provenance traceability.

### Rules

1. **Never delete entries.** Even if the placed content was later removed, the ingestion record remains.
2. **Never modify entries.** If an entry contains an error, create a correction entry.
3. **Corrections use `supersedes`.** A correction entry includes a `supersedes` field pointing to the original entry ID:

```yaml
- id: "ING-016"
  timestamp: "2026-03-04T16:00:00Z"
  supersedes: "ING-003"              # This entry corrects ING-003
  source:
    type: "local-file"
    identifier: "competitor-landscape-v2.txt"
    url: null
    word_count: 1800
    hash: "sha256:ghi789..."
  extractions:
    - target: "specs/constitution/positioning.md"
      section: "Competitive Landscape"
      action: "replace"
      confidence: "high"
      excerpt: "Updated competitor analysis..."
  skipped: []
  modified_files:
    - "specs/constitution/positioning.md"
  amendment_ids: ["AMEND-008"]
```

4. **Superseded entries remain in the log.** They are not deleted or marked as inactive. Query commands should note when an entry has been superseded:

```
ING-003  2025-11-15  competitor-landscape.txt
  ⚠ Superseded by ING-016 (2026-03-04)
```

5. **Hash integrity.** The `source.hash` field allows verification that a source hasn't been tampered with. If a source is re-ingested and the hash differs, it's a new ingestion (not a modification of the old one).

---

## Edge Cases

- **Failed ingestions**: If an ingestion fails partway through (e.g., classification succeeds but file write fails), log the entry with extractions marked as `action: "failed"` and include error details. Do not leave partial state unlogged.
- **Bulk ingestions**: When multiple files are ingested in a single session, each file gets its own entry with its own ID. They share the same timestamp (session start time).
- **Re-ingestion of same source**: If the same source is ingested again (same hash), flag as duplicate in the `skipped` array unless the user explicitly requests re-ingestion. If the user confirms, create a new entry -- do not modify the original.
- **Empty extractions**: If a source is ingested but all content is skipped (nothing placed), still create a log entry. The `extractions` array will be empty and all content appears under `skipped`. This documents that the source was reviewed.
- **Amendment routing**: When an extraction targets an active constitution file, the change routes through `/vkf/amend`. The resulting amendment ID is recorded in `amendment_ids`. The ingestion log and amendment log are cross-referenced but maintained separately.
- **Concurrent ingestions**: If two ingestion sessions run simultaneously, IDs are assigned sequentially based on write order. There is no locking mechanism -- the YAML file handles this via append-only semantics.
