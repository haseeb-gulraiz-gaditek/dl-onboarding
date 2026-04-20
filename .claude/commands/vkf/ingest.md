---
description: Classify and place external content into constitution and specs using a 9-point rubric with confidence scoring
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Source path or `--inline` for pasted content
  - Local file path: Google Doc export, PDF text, meeting notes, strategy docs
  - `--inline`: Ingest text from the conversation context (user pastes content directly)

## Actions

1. **Determine Source**
   - If `$ARGUMENTS` contains `--inline`: read content from the conversation context (user's pasted text)
   - If `$ARGUMENTS` is a file path: read from disk, verify file exists
   - If `$ARGUMENTS` is empty: ask user to provide a path or paste content with `--inline`

2. **Analyze Source**
   - Count words, detect format (markdown, plain text, structured data)
   - If >5000 words, chunk using heading boundaries (prefer `##` then `#` then paragraph breaks)
   - Record source metadata: filename, word count, chunk count, detected format

3. **Classify Content**
   - Apply the 9-point classification rubric (see `references/ingestion-rubric.md`)
   - For each chunk/section, map to one or more of the 9 targets:
     - 8 constitution files: `mission.md`, `pmf-thesis.md`, `personas.md`, `icps.md`, `positioning.md`, `principles.md`, `governance.md`, `index.md`
     - Feature specs: `specs/features/{feature}/spec.md`
   - Assign confidence level for each mapping:
     - **HIGH**: clear match to a specific section (e.g., competitor name + comparison = positioning)
     - **MEDIUM**: plausible match but ambiguous section (e.g., "users want..." could be personas or PMF)
     - **LOW**: tangential relevance, may not belong in constitution at all
   - Track unclassified content separately with excerpt

4. **Present Placement Plan**
   - Show user the full plan before any writes
   - HIGH confidence placements are auto-approved (user can still reject)
   - MEDIUM confidence placements require user confirmation for each
   - LOW confidence placements require user decision
   - Unclassified content: user assigns a target, creates a new spec, or discards

5. **Apply Placements**
   - For each approved placement:
     - If target is an active constitution file (no `[REQUIRED]` placeholders remaining):
       - Check if change is substantive (adding/changing meaning, not just appending notes)
       - If substantive: announce amendment tier and suggest `/vkf/amend`
     - If target is a draft constitution file (still has `[REQUIRED]` placeholders): append or replace directly
     - If target is a feature spec: create or update the spec file
   - Update `Last amended` or `Last reviewed` dates on all modified files

6. **Log Ingestion**
   - Append entry to `specs/ingestion-log.yaml`:
     ```yaml
     - id: ING-{sequential}
       timestamp: "YYYY-MM-DDTHH:MM:SS"
       source:
         type: file | inline
         path: "{file path or 'conversation'}"
         word_count: {N}
         format: "{detected format}"
       extractions:
         - target: "{file path}"
           section: "{section name}"
           confidence: high | medium | low
           excerpt: "{first 80 chars of placed content}"
           amendment_id: "{if routed through amend}"
       skipped:
         - excerpt: "{first 80 chars}"
           reason: "unclassified | user-discarded"
       files_modified:
         - "{list of files written}"
     ```

7. **Update State**
   - Update `.claude/state/vkf-state.yaml` with latest ingestion timestamp:
     ```yaml
     last_ingestion: "{current ISO timestamp}"
     last_ingestion_id: "ING-{N}"
     ```

8. **Commit**
   - Commit all changes: `[ingest] {source description}`

## Output Format

```
Ingestion Plan: board-deck-q1.txt
=================================
Source: local file | 2,450 words | 3 chunks

Placements:
  ✓ HIGH    positioning.md > Competitive Landscape     "Three key competitors identified..."
  ? MEDIUM  pmf-thesis.md > Evidence                   "Customer retention data shows..."
  ? LOW     personas.md > Pain Points                  "Users mentioned frustration with..."

Unclassified:
  ◯ "General industry statistics..." (assign / create spec / discard)

Apply HIGH confidence placements? Review MEDIUM/LOW individually? (y/n)
```

After applying:
```
Ingestion Complete: ING-007
===========================
Applied: 3 placements
  ✓ positioning.md > Competitive Landscape (direct)
  ✓ pmf-thesis.md > Evidence (direct)
  ✓ personas.md > Pain Points (routed to /vkf/amend — C2)
Skipped: 1 (user discarded)
Logged: specs/ingestion-log.yaml
```

## Error Handling

- **File not found**: Suggest checking path, offer `--inline` alternative
- **Empty source**: Report "no content to ingest"
- **No specs directory**: Suggest `/vkf/init`
- **Ingestion log doesn't exist**: Create it with header comment:
  ```yaml
  # Ingestion Log — STD-002 Venture Knowledge Foundation
  # Each entry records content classified and placed into constitution/specs
  ```
- **All content unclassified**: Suggest this may not be constitution-relevant content, offer to create a feature spec instead
- **State file missing**: Create `.claude/state/vkf-state.yaml` with ingestion fields
