---
description: Audit repository against all STD-002 Venture Knowledge Foundation requirements
version: "2.1"
---

## Actions

1. **Check Structure** (Requirement 1)
   - Verify `specs/constitution/` exists — REQUIRED (or the configured `constitution_root`)
   - Verify `specs/features/` exists — REQUIRED (or the configured `features_root`)
   - Verify `changes/` exists
   - Verify `archive/` exists
   - Verify `.claude/commands/` exists with at least one command
   - Report any project-level specs found at `specs/` root (e.g., `architecture.md`, `api-reference.md`) — informational, not scored
   - Report any custom spec directories found (e.g., `specs/schemas/`, `specs/apis/`) — informational, not scored
   - Score: PASS (all present), WARN (some missing), FAIL (constitution/ or features/ missing)

2. **Check Constitution Completeness** (Requirement 2)

   The constitution uses a tiered model. Core files are required; Extended files are recommended.

   **Core Tier** (FAIL if missing):
     - `index.md`
     - `mission.md`
     - `pmf-thesis.md`
     - `principles.md`

   **Extended Tier** (WARN if missing, with adoption guidance):
     - `personas.md` -- adopt when you have distinct user types
     - `icps.md` -- adopt when selling to companies (B2B) or segmenting users
     - `positioning.md` -- adopt when competitors exist and differentiation matters
     - `governance.md` -- adopt when more than one person makes product decisions

   - Scan each existing file for remaining `[REQUIRED]` placeholders
   - Score: PASS (all Core complete, no placeholders), WARN (Core complete but has placeholders, or Extended missing), FAIL (Core files missing)

3. **Check Spec Freshness** (Requirement 3)
   - Parse freshness dates from all spec files — check both YAML frontmatter and in-body `Last reviewed:` / `Last amended:` text. Use the most recent date if both exist.
   - For feature specs: scan all `.md` files in each feature directory (not just `spec.md`), cross-reference review dates with `git log` on corresponding code paths
   - For constitution files: check if `Last amended` date is present (frontmatter or in-body)
   - For project-level specs (`specs/*.md`): check if `Last reviewed` date is present, assess by date only
   - For custom spec directories: scan all `.md` files, assess by date only
   - Classify each file: CURRENT / STALE / VERY_STALE / MISSING / REVIEW_DUE
   - Score: PASS (all current), WARN (some stale), FAIL (any missing dates)

4. **Check Planning Workflows** (Requirement 4)
   - Verify `.claude/commands/` has at least one command file
   - Check for VKF commands specifically (`vkf/` subdirectory)
   - Score: PASS (commands present), WARN (commands dir exists but empty), FAIL (no commands dir)

5. **Check Advanced Tier** (INFO-level, non-blocking)

   If `advanced_tier: true` in `.claude/state/vkf-state.yaml`, check for Advanced capabilities. These are reported as INFO (present) or silently skipped (absent). They NEVER produce WARN or FAIL.

   - **Ingestion**: Check if `specs/ingestion-log.yaml` exists → INFO if present with entry count
   - **Gaps**: Check if `specs/gaps/` exists with reports → INFO if present with report count
   - **Amendments**: Check `governance.md` Amendment History for entries → INFO if entries exist
   - **Transcripts**: Check if `specs/transcripts/` exists with files → INFO if present with count
   - **Audit**: Check if `specs/ingestion-log.yaml` has queryable entries → INFO (same as ingestion check)
   - **OKRs**: Check if `specs/okrs/current/` exists with quarter files → INFO if present
   - **Workflow**: Check if workflow state exists in `vkf-state.yaml` → INFO if configured

   If `advanced_tier` is false or absent, skip this step entirely (no output).

6. **Check Knowledge Base Health** (INFO-level, non-blocking)

   If `knowledge_types` is configured in `.claude/state/vkf-state.yaml`, scan the full knowledge base. This is purely informational — it never produces WARN or FAIL.

   - **Type coverage**: Which configured knowledge types have documents? Which are empty?
   - **Frontmatter coverage**: What percentage of docs have structured frontmatter (`title`, `type`, `status`, date field)?
   - **Stub detection**: Flag documents under 50 words as potential stubs
   - **Cross-references**: Do feature specs reference constitution principles? Do architecture docs reference the technical constitution?
   - **Type freshness**: Per-type freshness summary using the configured thresholds

   If `knowledge_types` is not configured, skip this step entirely.

7. **Generate Report**
   - Compile results across all requirements (4 core + optional advanced + optional knowledge base health)
   - Calculate overall score
   - List specific issues with fix suggestions

8. **Update State**
   - Write validation timestamp and results to `.claude/state/vkf-state.yaml`
   - Include advanced tier results (INFO/null) in `validation_result.advanced` when `advanced_tier: true`

## Output Format

```
╔═══════════════════════════════════════════════════╗
║  STD-002 Validation Report                        ║
║  Generated: 2026-02-26                            ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  1. Repository Structure         [PASS]           ║
║     ✓ specs/constitution/                         ║
║     ✓ specs/features/                             ║
║     ✓ changes/                                    ║
║     ✓ archive/                                    ║
║     ✓ .claude/commands/ (3 commands)              ║
║     ℹ specs/architecture.md (project-level)       ║
║     ℹ specs/api-reference.md (project-level)      ║
║                                                   ║
║  2. Constitution Completeness    [PASS]           ║
║     Core:                                         ║
║     ✓ index.md                                    ║
║     ✓ mission.md                                  ║
║     ✓ pmf-thesis.md                               ║
║     ✓ principles.md                               ║
║     Extended:                                     ║
║     ⚠ personas.md (2 [REQUIRED] remaining)        ║
║     − icps.md (not yet needed — no B2B sales)     ║
║     ✓ positioning.md                              ║
║     − governance.md (not yet needed — solo)       ║
║                                                   ║
║  3. Spec Freshness               [WARN]           ║
║     ✓ constitution/mission.md    CURRENT           ║
║     ✓ architecture.md            CURRENT           ║
║     ⚠ features/auth/spec.md     STALE (14 days)   ║
║     ✓ features/auth/decisions.md CURRENT           ║
║     ✗ features/billing/spec.md  MISSING date       ║
║                                                   ║
║  4. Planning Workflows           [PASS]           ║
║     ✓ .claude/commands/vkf/ (5 commands)          ║
║                                                   ║
║  5. Advanced Tier (INFO)        [7/7 active]      ║
║     ℹ Ingestion: 9 entries in audit log           ║
║     ℹ Gaps: 3 reports in specs/gaps/              ║
║     ℹ Amendments: 5 entries in history            ║
║     ℹ Transcripts: 4 files processed              ║
║     ℹ Audit: queryable (9 entries)                ║
║     ℹ OKRs: 2026-Q1 active                       ║
║     ℹ Workflow: 7 documents tracked               ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║  Overall: 4 PASS | 0 WARN | 0 FAIL | 7 INFO    ║
║  STD-001 Ready: YES (Core complete)               ║
╚═══════════════════════════════════════════════════╝

Action Items:
  1. Fill [REQUIRED] sections in personas.md (run /vkf/constitution personas)
  2. Add Last reviewed date to features/billing/spec.md
  3. Review features/auth/spec.md (code changed since last review)

Extended tier suggestions:
  • Consider icps.md when you begin B2B sales or user segmentation
  • Consider governance.md when a second person joins product decisions
```

## Scoring Rules

| Category | PASS | WARN | FAIL |
|----------|------|------|------|
| Structure | All dirs present | Some non-critical dirs missing | `specs/constitution/` or `specs/features/` missing |
| Constitution | Core complete, no `[REQUIRED]` | Core complete but placeholders remain, or Extended missing | Core files missing |
| Freshness | All CURRENT | Some STALE | Any MISSING dates |
| Workflows | Commands present | Dir exists but empty | No commands dir |

**STD-001 Ready:** Only YES when all 4 categories are PASS.

## Error Handling

- **Not initialized**: Suggest running `/vkf/init` first
- **Git not available**: Skip git-based freshness checks, note in report
- **No feature specs yet**: Score freshness as PASS with note "no specs to check"
