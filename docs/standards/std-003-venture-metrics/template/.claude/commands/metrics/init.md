---
description: Bootstrap STD-003 metrics structure, auto-detect standards, and configure available metric tiers
---

## Arguments

- **$ARGUMENTS** (optional): `--github-token` to configure GitHub API access during setup

## Actions

1. **Check Current State**
   - Read `.claude/state/metrics-state.yaml` if it exists
   - If already initialized, show current state and ask user if they want to re-initialize

2. **Auto-Detect Standards**
   - Check for `specs/constitution/` → STD-002 present
   - Check for `changes/` and `.claude/state/sdd-state.yaml` → STD-001 present
   - Record detected standards for tier configuration

3. **Create Directory Structure**
   - Create `metrics/` (if not exists)
   - Create `metrics/reports/current/` (if not exists)
   - Create `metrics/reports/archive/` (if not exists)
   - Create `metrics/internal/` (if not exists)
   - Create `.claude/commands/metrics/` (if not exists)
   - Create `.claude/state/` (if not exists)

4. **Create Files from SKILL.md Templates**

   Create each file using the canonical templates defined in SKILL.md § Initialization Templates:
   - `metrics/definitions.yaml` — from SKILL.md template, update `standards_detected` based on step 2
   - `metrics/schedule.yaml` — from SKILL.md template, populate `github.owner` and `github.repo` from git remote if available
   - `metrics/internal/per-engineer.yaml` — from SKILL.md template
   - `metrics/internal/spec-code-ratios.yaml` — from SKILL.md template
   - `.claude/state/metrics-state.yaml` — from SKILL.md template, set `initialized_at` to current timestamp

5. **Configure Extended Metrics** (if standards detected)
   - If STD-002 detected: uncomment and add `freshness_score` and `okr_progress` to `extended_metrics` in `definitions.yaml`
   - If STD-001 detected: uncomment and add `spec_compliance` and `proposal_velocity` to `extended_metrics` in `definitions.yaml`
   - Update `metrics-state.yaml` with `tiers_enabled.extended: true`

6. **Commit**
   - Stage all new files
   - Commit with message: `[metrics] Bootstrap STD-003 metrics structure`

7. **Run Verification**
   - Execute the verification checklist from SKILL.md § Verification
   - Report results (expected: all PASS except collection freshness which will be VERY_STALE since no collection has run)

## Output

Display:
```
Initialized Venture Metrics (STD-003)

  metrics/
  ├── definitions.yaml          # 10 Core Delivery Speed metrics
  ├── schedule.yaml             # Collection config
  ├── reports/
  │   ├── current/              # Monthly reports go here
  │   └── archive/              # Past reports
  └── internal/                 # Per-engineer data (lead-only)
      ├── per-engineer.yaml
      └── spec-code-ratios.yaml

Standards detected:
  STD-002: {YES/NO}
  STD-001: {YES/NO}

Mode: {Standalone | Enhanced}
Tiers: Core {+ Extended} {+ Advanced}

Verification: {PASS/WARN summary from § Verification}

Next steps:
1. Configure GitHub API: set GITHUB_TOKEN env var, update metrics/schedule.yaml
2. Run /metrics/collect to gather first month's data
3. Run /metrics/report to view results
4. Run /metrics/status to check configuration
```

## Error Handling

- **Already initialized**: Run § Verification, show results, ask to re-initialize or skip
- **Partial structure exists**: Create only missing pieces, run § Verification to report gaps
- **No GitHub API token**: Initialize with git-only mode, § Verification will WARN on GitHub API
- **No git history**: Warn that historical data is needed, suggest initial collection after first month of activity
