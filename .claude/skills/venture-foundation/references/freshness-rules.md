# Freshness Validation Rules

Rules for determining whether specs and constitution files are current, stale, or missing freshness metadata.

---

## Primary: Explicit Review Dates

Every spec and constitution file MUST include a date header:

- **Feature specs**: `Last reviewed: YYYY-MM-DD`
- **Constitution files**: `Last amended: YYYY-MM-DD`

These dates are the primary authority for freshness. Parse them from the first 20 lines of each file.

### Parsing Rules

1. Check both **YAML frontmatter** and **in-body metadata** for dates. Frontmatter fields like `updated` or `last_amended` count. In-body text like `Last reviewed:` or `Last amended:` (case-insensitive) in the first 20 lines also counts.
2. If both locations have dates, use the most recent one.
3. Accept ISO date format: `YYYY-MM-DD`
4. Accept informal formats: `February 26, 2026`, `Feb 2026` (normalize to YYYY-MM-DD)
5. If no date field exists in either location, status is `MISSING`

---

## Secondary: Git-Based Drift Detection

Cross-reference review dates with `git log` on corresponding code paths to detect drift.

### Path Mapping

| Spec Path | Code Path |
|-----------|-----------|
| `specs/features/auth/spec.md` | `src/features/auth/`, `src/auth/`, `app/auth/` |
| `specs/features/auth/decisions.md` | Same as parent feature (uses feature dir name) |
| `specs/features/billing/spec.md` | `src/features/billing/`, `src/billing/`, `app/billing/` |
| `specs/constitution/*.md` | N/A (constitution doesn't map to code) |
| `specs/*.md` (project-level) | N/A (assessed by date only, like constitution) |
| `specs/[custom-dir]/*.md` | N/A (assessed by date only, like constitution) |

**Multi-file features:** All `.md` files within a feature directory (and its sub-directories) are scanned for freshness -- not just `spec.md`. Companion files like `decisions.md` use the same code path mapping as the parent feature.

**Project-level specs:** Files at `specs/` root (e.g., `architecture.md`, `api-reference.md`) and files in custom spec directories (e.g., `specs/schemas/`) don't map to code paths. They follow the same date-only rules as constitution files.

### Drift Detection Algorithm

```
For each feature spec:
  1. Parse Last reviewed date
  2. Find corresponding code path(s)
  3. Run: git log --since="{review_date}" --oneline -- {code_path}
  4. If commits exist after review date → spec is STALE
  5. Count commits to gauge severity
```

### Git Commands

```bash
# Check if code changed since spec was reviewed
git log --since="2026-01-15" --oneline -- src/features/auth/

# Get last modification date of code path
git log -1 --format="%ai" -- src/features/auth/

# List all code paths that changed in last 90 days
git log --since="90 days ago" --name-only --pretty=format: -- src/ | sort -u
```

---

## Freshness Thresholds

| Status | Condition | Action |
|--------|-----------|--------|
| **CURRENT** | Review date within 90 days AND no code changes since review | None required |
| **STALE** | Code changed since review date, OR review date 30-90 days old with no code changes | Review recommended |
| **VERY_STALE** | Review date older than 90 days | Review required |
| **MISSING** | No `Last reviewed` / `Last amended` date found | Add date immediately |

### Priority Order for Fixes

1. `MISSING` -- add freshness dates first (quick fix, high impact)
2. `VERY_STALE` -- review and update these specs next
3. `STALE` -- schedule reviews for these

---

## Constitution Freshness

Constitution files follow different rules since they don't map to code:

| Status | Condition |
|--------|-----------|
| **CURRENT** | `Last amended` within 90 days |
| **REVIEW_DUE** | `Last amended` 90-180 days ago (quarterly review recommended) |
| **VERY_STALE** | `Last amended` over 180 days ago |
| **MISSING** | No `Last amended` date found |

Constitution files don't use git drift detection -- they change on their own cadence.

---

## Knowledge Type Freshness (when `knowledge_types` configured)

When `knowledge_types` is set in `vkf-state.yaml`, each type has its own freshness thresholds. The `freshness` value (in days) defines the CURRENT/REVIEW_DUE boundary; VERY_STALE is 2x that value.

| Type | Current | Review Due | Very Stale | Git Drift |
|------|---------|------------|------------|-----------|
| **constitution** | 90d | 90-180d | 180d+ | No |
| **architecture** | 180d | 180-365d | 365d+ | No |
| **features** | 90d | N/A | 90d+ | Yes — maps to code paths |
| **ux** | 90d | 90-180d | 180d+ | No |
| **reference** | 365d | 365-730d | 730d+ | No |

The `freshness` field in `knowledge_types` overrides these defaults. Types with `governance: none` still get freshness scanned but only produce INFO-level output (never WARN or FAIL).

---

## Project-Level and Custom Directory Freshness

Project-level specs (`specs/*.md`) and files in custom spec directories (`specs/schemas/`, `specs/apis/`, etc.) follow the same date-only rules as constitution files. They use `Last reviewed: YYYY-MM-DD` as the date header.

| Status | Condition |
|--------|-----------|
| **CURRENT** | `Last reviewed` within 90 days |
| **REVIEW_DUE** | `Last reviewed` 90-180 days ago |
| **VERY_STALE** | `Last reviewed` over 180 days ago |
| **MISSING** | No `Last reviewed` date found |

These files don't map to code paths, so no git drift detection is applied.

---

## Scanning Scope

The freshness scan covers all `.md` files in the `specs/` tree:

1. **Constitution files** — all `.md` in `specs/constitution/`
2. **Feature specs** — all `.md` files in each `specs/features/[feature]/` directory (including sub-directories), not just `spec.md`
3. **Project-level specs** — any `.md` files at `specs/` root (e.g., `architecture.md`, `api-reference.md`)
4. **Custom spec directories** — all `.md` files in any other directories under `specs/` (e.g., `specs/schemas/`, `specs/apis/`)

Files in `changes/` and `archive/` are excluded.

---

## Report Format

The freshness scan outputs a structured report:

```
Spec Freshness Report
=====================
Generated: 2026-02-26

Constitution Files (specs/constitution/):
  CURRENT    mission.md           (amended 2026-02-01)
  CURRENT    pmf-thesis.md        (amended 2026-01-20)
  REVIEW_DUE personas.md          (amended 2025-10-15, 134 days)
  MISSING    icps.md              (no date found)

Project-Level Specs (specs/):
  CURRENT    architecture.md      (reviewed 2026-02-15)
  STALE      api-reference.md     (reviewed 2025-12-01, 87 days)

Feature Specs (specs/features/):
  CURRENT    auth/spec.md         (reviewed 2026-02-10, no code changes)
  CURRENT    auth/decisions.md    (reviewed 2026-02-10, no code changes)
  STALE      billing/spec.md      (reviewed 2026-01-05, 3 commits since)
  VERY_STALE payments/spec.md     (reviewed 2025-08-20, 212 days)

Summary:
  Total files scanned: 10
  CURRENT: 5
  STALE: 2
  VERY_STALE: 1
  REVIEW_DUE: 1
  MISSING: 1

Action Items:
  1. Add Last amended date to icps.md
  2. Review payments/spec.md (212 days stale)
  3. Review api-reference.md (87 days stale)
  4. Review billing/spec.md (3 code commits since last review)
  5. Schedule quarterly review for personas.md
```

---

## Edge Cases

- **New files**: Files created within the last 7 days are automatically CURRENT even without a review date
- **Empty specs**: Files that exist but contain only placeholders (`[REQUIRED]`) are reported separately as INCOMPLETE, not assessed for freshness
- **Archived specs**: Files in `archive/` are excluded from freshness checks
- **Multiple code paths**: If a feature maps to multiple code directories, any change in any path triggers STALE
- **Multi-file features**: All `.md` files in a feature directory share the same code path mapping. Each file is assessed independently -- one file can be CURRENT while a sibling is STALE.
- **Non-markdown files**: Only `.md` files are scanned. Other files (images, JSON, YAML) in spec directories are ignored.
