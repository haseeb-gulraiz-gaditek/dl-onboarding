---
description: Process meeting transcripts through extraction templates, classify insights, and route to ingestion pipeline
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Source and optional template flag
  - Source: file path or `--inline` for pasted transcript
  - Template flag: `--template general|customer-call|strategy-session|{custom-name}`
  - Examples:
    - `transcripts/acme-call.txt`
    - `--inline --template customer-call`
    - `meeting-notes.md` (auto-detects template)

## Actions

1. **Determine Source**
   - If `$ARGUMENTS` contains `--inline`: read transcript from conversation context
   - If `$ARGUMENTS` contains a file path: read from disk, verify file exists
   - If no source provided: ask user to paste or provide a path

2. **Detect/Select Template**
   - If `--template` is specified in `$ARGUMENTS`: use that template
   - Otherwise auto-detect based on content analysis:
     - Contains customer/company names + pain points + feature mentions → `customer-call`
     - Contains strategic keywords (positioning, roadmap, OKR, vision, strategy, pivot) → `strategy-session`
     - Default → `general`
   - Check `specs/transcripts/templates/` for custom templates matching any `--template` name
   - Announce detected template: "Auto-detected template: **{name}** because {reason}"

3. **Store Raw Transcript**
   - Save to `specs/transcripts/{date}-{title}.md` with metadata header:
     ```markdown
     # Transcript: {title}

     **Date:** YYYY-MM-DD
     **Participants:** [names if identifiable from content]
     **Duration:** [if known or estimable from content length]
     **Source:** [file path or inline]
     **Template:** {template used}
     **Processed:** false

     ---

     [raw transcript content]
     ```
   - Title is derived from filename (if file path) or first meaningful line (if inline)

4. **Extract Insights**
   - Apply the selected template to extract structured insights:

   **`general` template extracts:**
   - **Decisions made**: what was decided, context, participants involved
   - **Action items**: task description, owner (if identifiable), deadline (if mentioned)
   - **Product insights**: user feedback, feature ideas, usability observations
   - **Strategic statements**: direction changes, priority shifts, goal articulations
   - **Open questions**: unresolved topics, deferred decisions, things to research

   **`customer-call` template extracts:**
   - **Pain points**: problem description, severity signal (blocking/frustrating/minor), speaker
   - **Feature requests**: requested capability, use case context, speaker
   - **Competitive mentions**: competitor name, context of mention, sentiment (positive/negative/neutral)
   - **Buying/churn signals**: positive signals (renewal, expansion, referral) or negative signals (evaluation, complaints, timeline pressure)
   - **PMF evidence**: retention signals, satisfaction indicators, referral mentions, "can't live without" statements

   **`strategy-session` template extracts:**
   - **Positioning decisions**: target market, differentiation, category changes
   - **Persona refinements**: new personas identified, existing persona updates
   - **Principle discussions**: new principles proposed, existing principles challenged
   - **OKR proposals**: objectives, key results, timeline
   - **Governance decisions**: process changes, role assignments, decision rights

5. **Generate Meeting Brief**
   - Create `specs/meetings/{date}-{title}.md` with the following structure:
     ```markdown
     # Meeting Brief: {title}

     **Date:** YYYY-MM-DD
     **Participants:** [names if identifiable]
     **Duration:** [if known]
     **Template:** {template used}
     **Transcript:** specs/transcripts/{date}-{title}.md
     **Ingestion ID:** ING-{N}

     ---

     ## Executive Summary

     [2-3 sentence synopsis of what happened and what matters most.
      This is the paragraph someone reads who missed the meeting.]

     ## Key Decisions

     | Decision | Context | Participants |
     |----------|---------|-------------|
     | [what was decided] | [why / what prompted it] | [who was involved] |

     ## Action Items

     | Action | Owner | Deadline | Status |
     |--------|-------|----------|--------|
     | [task] | [person] | [date if mentioned] | open |

     ## Learnings

     Insights extracted from this meeting that inform product direction,
     process, or strategy.

     | Learning | Category | Placement |
     |----------|----------|-----------|
     | "Export takes 20 minutes for large datasets" | Pain point | personas.md > Pain Points |
     | "Retention at 68% in Q1" | PMF evidence | pmf-thesis.md > Evidence |

     ## Open Questions

     - [questions raised but not answered — track for follow-up]

     ## Document Modifications

     Changes made to knowledge base documents as a result of this meeting:

     | Document | Section | Change | Confidence |
     |----------|---------|--------|------------|
     | positioning.md | Competitive Landscape | Appended competitor mention | HIGH |
     | features/export/spec.md | (created) | New feature spec from request | MEDIUM |
     ```
   - The meeting brief is the **canonical record** of what the meeting produced. It connects the raw transcript (source) to the document changes (outcome) through the analysis layer (learnings).
   - If a meeting references a previous meeting's decision, link to the earlier brief: `See [Meeting Brief: {title}](specs/meetings/{date}-{title}.md)`

6. **Route to Ingestion**
   - Classify extracted insights via the same 9-point rubric used by `/vkf/ingest`
   - For each extraction:
     - Assign a target constitution file or feature spec
     - Assign confidence level (high/medium/low)
     - Include excerpt with speaker attribution
   - Present unified placement plan to user (same format as `/vkf/ingest`)

7. **Apply Placements**
   - Same rules as `/vkf/ingest`:
     - Active constitution files with substantive changes → route through `/vkf/amend`
     - Draft constitution files → append or replace directly
     - Feature specs → create or update
   - Update `Last amended` or `Last reviewed` dates on modified files

8. **Log Everything**
   - Append to `specs/ingestion-log.yaml` with transcript-specific fields:
     ```yaml
     - id: ING-{sequential}
       timestamp: "YYYY-MM-DDTHH:MM:SS"
       source:
         type: transcript
         path: "specs/transcripts/{date}-{title}.md"
         word_count: {N}
         format: transcript
         template: "{template name}"
       meeting_brief: "specs/meetings/{date}-{title}.md"
       extractions:
         - target: "{file path}"
           section: "{section name}"
           confidence: high | medium | low
           excerpt: "{first 80 chars}"
           speaker: "{name if known}"
           amendment_id: "{if routed through amend}"
       skipped:
         - excerpt: "{first 80 chars}"
           reason: "unclassified | user-discarded"
       files_modified:
         - "{list of files written}"
     ```

9. **Update Transcript**
   - Mark the stored raw transcript as `Processed: true`
   - Append extraction summary to the end of the transcript file:
     ```markdown
     ---

     ## Extraction Summary

     **Template:** {template}
     **Processed:** YYYY-MM-DD
     **Ingestion ID:** ING-{N}
     **Meeting Brief:** specs/meetings/{date}-{title}.md
     **Placements:** {count applied} applied, {count skipped} skipped
     ```

10. **Update Meeting Register**
    - Append entry to `specs/meetings/INDEX.md`:
      ```markdown
      | {date} | {title} | {template} | {participants} | {one-line key outcome} | [brief]({date}-{title}.md) | ING-{N} |
      ```
    - Create `specs/meetings/INDEX.md` if it doesn't exist, with header:
      ```markdown
      # Meeting Register

      All meetings processed through `/vkf/transcript`, with key outcomes and document modifications.

      | Date | Title | Template | Participants | Key Outcome | Brief | Ingestion |
      |------|-------|----------|-------------|-------------|-------|-----------|
      ```

11. **Commit**
    - `[transcript] Process {title} with {template} template`

## Output Format

```
Transcript Processing: acme-weekly-call
=======================================
Template: customer-call (auto-detected)
Stored: specs/transcripts/2026-03-04-acme-weekly-call.md

Extractions:
  Pain Points:
    HIGH   "Export takes 20 minutes for large datasets" (Acme CTO)
    MED    "Can't filter by date range in reports" (Acme PM)

  Feature Requests:
    "CSV export with custom column selection" (Acme CTO)

  Competitive Mentions:
    "They also evaluated CompetitorX" (Acme PM, neutral tone)

  PMF Evidence:
    "We renewed because nothing else handles our volume" (Acme CTO)

  Buying Signals:
    (+) "Planning to expand to the analytics team next quarter" (Acme CTO)

Placement Plan:
  ✓ HIGH    personas.md > Pain Points          "Export performance..."
  ✓ HIGH    pmf-thesis.md > Evidence            "Acme renewed for volume..."
  ? MEDIUM  positioning.md > Competitive        "CompetitorX evaluation..."
  ? MEDIUM  features/export/spec.md (create)    "CSV export request..."

Apply placements? (y/n)
```

After applying:
```
Transcript Complete: acme-weekly-call
=====================================
Ingestion ID: ING-012
Meeting Brief: specs/meetings/2026-03-04-acme-weekly-call.md
Applied: 3 placements
  ✓ personas.md > Pain Points (direct)
  ✓ pmf-thesis.md > Evidence (direct)
  ✓ features/export/spec.md (created)
Skipped: 1 (user discarded)
Transcript marked as processed
Meeting register updated
```

## Custom Template Format

Custom templates are stored in `specs/transcripts/templates/{name}.yaml`:

```yaml
name: investor-update
description: Extract investor-relevant information
extractions:
  - name: metrics_discussed
    signal_words: ["revenue", "ARR", "MRR", "churn", "growth", "runway"]
    target: pmf-thesis.md
  - name: strategic_pivots
    signal_words: ["pivot", "strategy change", "new direction", "repositioning"]
    target: positioning.md
  - name: hiring_plans
    signal_words: ["hire", "team", "headcount", "role"]
    target: governance.md
```

## Error Handling

- **No transcripts directory**: Create `specs/transcripts/` and `specs/transcripts/templates/` automatically
- **No meetings directory**: Create `specs/meetings/` and `specs/meetings/INDEX.md` automatically
- **Empty transcript**: Report "no content to process"
- **Template not found**: List available templates:
  ```
  Template "weekly-sync" not found. Available templates:
    Built-in: general, customer-call, strategy-session
    Custom: investor-update (specs/transcripts/templates/investor-update.yaml)
  ```
- **No extractable content**: Report honestly ("no structured insights found"), suggest a different template or manual review
- **File not found**: Suggest checking path, offer `--inline` alternative
- **No specs directory**: Suggest `/vkf/init`
- **Ingestion log doesn't exist**: Create it with header comment
