---
id: "STD-003"
title: "Venture Metrics"
description: "Every venture repository can track delivery speed metrics from git/GitHub data, with optional enhanced metrics when STD-002/STD-001 are present. Metrics live in the repo as markdown — the metrics app is a viewer, not a source of truth."
status: "Draft"
version: "0.1"
effective: "2026-03-24"
enhances: "STD-002"
---

# STD-003: Venture Metrics

**Status:** Draft | **Version:** 0.1 | **Effective:** March 2026

---

## Summary

Every venture repository SHOULD track delivery speed and engineering health metrics. Metrics are collected from git history and GitHub API data, stored as markdown reports in the repository, and never require a separate stateful application. The metrics app becomes a viewer of markdown with no state of its own.

STD-003 has **no hard prerequisite** on STD-002 or STD-001. It works standalone for any git repo with GitHub. When STD-002/STD-001 are present, additional metrics become available (spec compliance, freshness scores, OKR progress).

---

## Requirements

### 1. Repository Structure

Every venture repository adopting STD-003 MUST have:

```
project/
├── metrics/
│   ├── definitions.yaml          # Metric definitions (Core + Extended + custom)
│   ├── schedule.yaml             # Collection frequency, sources, GitHub API config
│   ├── reports/
│   │   ├── current/              # Current period reports
│   │   │   └── {YYYY}-{MM}.md   # Monthly markdown report (primary)
│   │   └── archive/              # Past period reports
│   └── internal/                 # NEVER exposed in venture-level reports
│       ├── per-engineer.yaml     # Per-engineer breakdowns
│       └── spec-code-ratios.yaml # Spec-to-code tracking (when STD-001 present)
└── .claude/
    ├── commands/metrics/         # Metrics commands (copied from template)
    │   ├── init.md
    │   ├── collect.md
    │   ├── report.md
    │   ├── status.md
    │   ├── define.md
    │   └── correlate.md
    └── state/
        └── metrics-state.yaml    # Metrics tracking state
```

### 2. Metric Definitions

STD-003 uses a three-tier model. Each tier builds on the previous one.

#### Core Tier — Delivery Speed Metrics (any git repo + GitHub)

These 10 metrics are derived from the Delivery Speed Metrics Framework agreed upon by engineering leadership for cross-venture benchmarking. They require only git history and GitHub API access.

| # | Metric | Measures | Formula | Reporting |
|---|--------|----------|---------|-----------|
| 1 | **PR Lead Time** | First Commit → Merge | Merge Timestamp – First Commit Timestamp | Median + P90/month, 3-month rolling |
| 2 | **PR Cycle Time** | PR Created → Merge | Merge Timestamp – PR Created Timestamp | Median + P90/month |
| 3 | **Coding Time** | First Commit → PR Created | PR Created Timestamp – First Commit Timestamp | Median + P90/month |
| 4 | **Review Iterations** | Review cycles per PR | Count of (feedback + author update) cycles | Average + distribution/month |
| 5 | **PR Approval Rate (First Pass)** | % PRs approved on first review | (First-pass approvals / Total PRs) x 100 | Monthly percentage |
| 6 | **Deployment Frequency** | Successful production deploys/month | Count of successful prod deployments | Total + per-engineer/month |
| 7 | **Time Between Deployments** | Avg interval between deploys | Sum of intervals / (deploys - 1) | Average + median/month |
| 8 | **PR Throughput** | PRs merged/month | Count of merged PRs | Total + per-engineer/month |
| 9 | **PR Size Distribution** | Distribution of PR sizes (lines + files) | Small <100, Medium 100-400, Large 400-1000, XL >1000 | Monthly % per category |
| 10 | **Deployment Failure Rate** | % deploys that fail/rollback | (Failed + Rollbacks + Hotfixes) / Total x 100 | Monthly percentage |

**Key relationship:** PR Lead Time = Coding Time + PR Cycle Time. When Lead Time spikes, decompose into Coding Time and Cycle Time to identify the bottleneck (slow development vs slow review/merge).

**Defined targets:**

| Metric | Target | Source |
|--------|--------|--------|
| Review Iterations | 80% of PRs approved within 2 iterations | Delivery Speed Metrics Framework |
| PR Size Distribution | <10% XL PRs (>1000 lines) | Delivery Speed Metrics Framework |

**Reporting conventions:**
- Time metrics (Lead Time, Cycle Time, Coding Time, Time Between Deployments): report Median + P90
- PR Cycle Time: exclude weekends and non-working hours from elapsed time
- Bot/automated PRs (Dependabot, Renovate, CI-generated): separate from human PRs in all metrics
- PR Size Distribution: de-prioritized metric — collect but do not alert on

#### Extended Tier — Standard-Enhanced Metrics (requires STD-001/STD-002)

When STD-002 and/or STD-001 are present, these additional metrics become available:

| Metric | Measures | Source | Reporting |
|--------|----------|--------|-----------|
| **Spec Compliance** | % of changes that follow the SDD workflow | `changes/` and `archive/` directories | Monthly percentage |
| **Proposal Velocity** | Time from proposal creation to implementation start | SDD state files | Median/month |
| **Freshness Score** | % of specs that are CURRENT | `/vkf/freshness` scan | Monthly percentage |
| **OKR Progress** | Key result completion vs targets | `specs/okrs/current/` | Monthly snapshot |

#### Advanced Tier — Performance Framework Integration

| Metric | Measures | Source | Reporting |
|--------|----------|--------|-----------|
| **Cross-Venture Benchmarking** | Normalized metrics across ventures | All venture reports | Quarterly summary |
| **Spec-to-Code Correlation** | Ratio of spec changes to code changes per PR | PR file diffs | Per-PR ratio, monthly average |
| **Performance Framework Alignment** | Metric alignment with OKR key results | Performance framework config | Quarterly review |

#### Internal-Only Metrics

The following metrics are collected but MUST NOT appear in venture-level reports. They are stored in `metrics/internal/` and accessible only to leads:

| Metric | Purpose | Storage |
|--------|---------|---------|
| **Per-Engineer Breakdowns** | Individual contribution data for all 10 Core metrics | `metrics/internal/per-engineer.yaml` |
| **Spec-to-Code Ratio** | Per-PR ratio (until correlation with quality is proven) | `metrics/internal/spec-code-ratios.yaml` |
| **Individual Contribution Scoring** | Weighted scoring across metrics | `metrics/internal/per-engineer.yaml` |

#### Custom Metrics

Ventures MAY define custom metrics in `metrics/definitions.yaml` beyond the standard tiers. Custom metrics MUST include:
- Name, description, and formula
- Data source and collection method
- Reporting format and cadence
- Whether venture-level or internal-only

### 3. Collection Schedule

| Cadence | What | Method |
|---------|------|--------|
| **Monthly** (primary) | All Core metrics, Extended metrics (if available), custom metrics | Automated via `/metrics/collect` or CI |
| **Weekly** (optional) | Subset of high-signal metrics (PR Throughput, Deployment Frequency) | Manual or automated |

**Data sources:**

| Source | Metrics | Access |
|--------|---------|--------|
| `git log` | Coding Time, PR Throughput (partial), commit history | Local — always available |
| GitHub API | PR Lead Time, PR Cycle Time, Review Iterations, PR Approval Rate, PR Size, Deployment data | Requires GitHub API token |
| VKF state (`vkf-state.yaml`) | Freshness Score, OKR Progress | Requires STD-002 |
| SDD state (`sdd-state.yaml`) | Spec Compliance, Proposal Velocity | Requires STD-001 |

**Partial data handling:** If GitHub API access is unavailable, degrade to git-only metrics (Coding Time proxy, commit counts, file change distributions). Report which metrics were collected and which were skipped.

### 4. Report Format

Monthly reports MUST be written to `metrics/reports/current/{YYYY}-{MM}.md` in markdown. Reports are venture-level and MUST NOT contain per-engineer data.

**Report requirements:**
- All collected Core metrics with values
- Median + P90 for all time-based metrics
- Trend indicators vs previous period (up/down/flat with delta)
- 3-month rolling averages for key metrics
- Exclude weekends and non-working hours from PR Cycle Time
- Bot/automated PRs reported separately
- Target comparison where targets are defined
- Extended and custom metrics in separate sections (when available)

**Archival:** When a new month's report is generated, the previous month's report MUST be moved to `metrics/reports/archive/`.

### 5. Performance Framework Integration

STD-003 provides the measurement layer for venture OKRs and performance tracking:

- **OKR key results** SHOULD map to measurable metrics defined in STD-003
- GTM lead + tech lead set monthly metrics targets (aligned with `/vkf/okrs` if STD-002 present)
- Progress updates: weekly (manual or automated)
- STD-003 does NOT replace `/vkf/okrs` — it provides the data that feeds into OKR key results
- Metric targets from the performance framework are stored in `metrics/definitions.yaml` alongside metric definitions

### 6. Venture Compatibility

STD-003 operates in two modes, auto-detected during initialization:

| Mode | Detection | Metrics Available |
|------|-----------|-------------------|
| **Standalone** | No `specs/constitution/` or `changes/` | Core tier only (10 Delivery Speed metrics) |
| **Enhanced** | `specs/constitution/` present (STD-002) and/or `changes/` present (STD-001) | Core + Extended + Advanced tiers |

**Auto-detection rules:**
1. Check for `specs/constitution/` → STD-002 present
2. Check for `changes/` and `.claude/state/sdd-state.yaml` → STD-001 present
3. Configure `metrics/definitions.yaml` with available tiers
4. Re-detect on each `/metrics/collect` run (ventures may adopt standards over time)

### 7. Internal-Only Metrics

Per-engineer data and spec-to-code ratios MUST be treated as internal-only:

1. **Storage**: Always in `metrics/internal/`, never in `metrics/reports/`
2. **Access**: Lead-only — per-engineer data is for context, not evaluation
3. **Reports**: Venture-level reports aggregate to team level. Individual data never appears.
4. **Cross-venture**: Per-engineer data (Deployment Frequency, PR Throughput) is normalized and anonymized for cross-venture benchmarking only
5. **Spec-to-code ratio**: Collected when STD-001 is present, stored internally until correlation with quality metrics is established

### 8. Automated Collection

Three collection methods are supported:

| Method | When | How |
|--------|------|-----|
| **GitHub Actions cron** | Repos with CI/CD | Monthly cron job running `/metrics/collect` |
| **Claude Code command** | Manual or on-demand | User runs `/metrics/collect` |
| **External cron** | Centralized collection | Script calls GitHub API + git for multiple repos |

Automated collection MUST:
- Write results to `metrics/reports/current/` (venture-level) and `metrics/internal/` (per-engineer)
- Commit with `[metrics]` prefix
- Update `.claude/state/metrics-state.yaml` with collection timestamp
- Never overwrite internal data from a previous period (archive first)

### 9. Incentive Safeguards

Metrics are powerful but dangerous if misused. STD-003 enforces safeguards:

1. **Venture-level primary**: All reports default to team/venture aggregates. Individual data requires explicit access.
2. **No sole-basis metrics**: No single metric should be used as the sole basis for performance evaluation. Metrics provide context, not verdicts.
3. **Gameable metrics excluded from targets**: PR Size Distribution is collected but de-prioritized — it's too easy to game by splitting PRs artificially.
4. **Per-engineer normalization**: Cross-venture comparisons normalize per-engineer data by team size, repo complexity, and project phase. Raw counts are not compared across ventures.
5. **Trend over absolute**: Reports emphasize period-over-period trends over absolute values. A team improving from bad to acceptable is performing better than a team plateauing at good.
6. **Internal-only enforcement**: The `metrics/internal/` directory is structurally separated. Report generation commands never read from it.

---

## Why

Most ventures lack visibility into engineering velocity — the data exists in git and GitHub but nobody collects or presents it. Meanwhile, a separate metrics app would add infrastructure overhead and become yet another tool to maintain. STD-003 solves this by making the repo the source of truth:

- **Repo-centric**: Metrics live where the code lives. No separate database, no sync issues, no app to maintain.
- **Markdown reports**: The metrics app becomes a viewer of markdown. It renders what the repo contains, with no state of its own.
- **Incremental adoption**: Works standalone for any git repo. Adding STD-002/STD-001 unlocks more metrics without changing the collection workflow.
- **Thoughtful incentives**: Team-level by default, individual data internal-only, gameable metrics deprioritized. Metrics should illuminate, not punish.

---

## Relationship to STD-002 and STD-001

STD-003 **enhances** but does not require STD-002:

| Concern | STD-002 | STD-001 | STD-003 |
|---------|---------|---------|---------|
| Knowledge | Creates specs, constitution | Manages changes to specs | N/A |
| Metrics | N/A | N/A | Collects, reports, tracks |
| OKRs | `/vkf/okrs` authors OKRs | N/A | Provides metric data for OKR key results |
| Freshness | Establishes review dates | Maintains them | Reports freshness scores as a metric |
| Compliance | N/A | Enforces spec-before-code | Reports compliance rate as a metric |

**STD-002 OKRs remain canonical.** `/vkf/okrs` is the authoring tool. STD-003 adds a measurement and reporting layer that feeds data into OKR key results.

---

## Resources

- [Metrics Command Template](/resources/std-003-venture-metrics-template) — starter kit with `/metrics/init`, `/metrics/collect`, `/metrics/report`, `/metrics/status`, `/metrics/define`, `/metrics/correlate` commands
- [CLAUDE.md Intelligence Layer](/resources/std-003-claude-md-template) — routing table, auto-detection, passive enforcement rules for Claude Code
