---
name: venture-metrics
description: "Collect, report, and track delivery speed and engineering health metrics for venture repositories (Disrupt STD-003). Works standalone or enhanced with STD-002/STD-001."
user-invocable: true
invocation: "/venture-metrics"
arguments: "[init|collect|report|status|define|correlate] [args]"
---

# Venture Metrics (STD-003)

## Purpose

Every venture repository SHOULD track delivery speed metrics from git/GitHub data. This skill bootstraps metrics collection, generates reports, and integrates with the performance framework. It works standalone for any git repo and unlocks additional metrics when STD-002/STD-001 are present.

## Three-Tier Model

STD-003 uses a tiered metric model. Each tier builds on the previous one.

| Tier | Name | Audience | What's Available |
|------|------|----------|------------------|
| **Core** | Delivery Speed | Any git repo + GitHub | 10 Delivery Speed metrics (PR Lead Time, Cycle Time, Coding Time, Review Iterations, Approval Rate, Deployment Frequency, Time Between Deployments, PR Throughput, PR Size Distribution, Deployment Failure Rate) |
| **Extended** | Standard-Enhanced | Ventures with STD-001/STD-002 | Spec Compliance, Proposal Velocity, Freshness Score, OKR Progress |
| **Advanced** | Performance Framework | Ventures with performance config | Cross-venture benchmarking, spec-to-code correlation, performance alignment |

**Auto-detection:** On each collection run, check for `specs/constitution/` (STD-002) and `changes/` + `sdd-state.yaml` (STD-001) to determine available tiers.

## Invocation

| Command | Behavior |
|---------|----------|
| `/venture-metrics` | Auto-detect: status if initialized, else init |
| `/venture-metrics init` | Bootstrap metrics structure, auto-detect standards, configure GitHub API access |
| `/venture-metrics collect` | Run metric collection for current period |
| `/venture-metrics collect --period YYYY-MM` | Collect for a specific month |
| `/venture-metrics report` | Generate/view current period report |
| `/venture-metrics report --compare` | Period-over-period comparison |
| `/venture-metrics report --trend` | 3-month rolling trend |
| `/venture-metrics report --cross-venture` | Cross-venture benchmarking summary |
| `/venture-metrics status` | Show configuration, last collection, alerts, targets vs actuals |
| `/venture-metrics define` | Add a new custom venture-specific metric |
| `/venture-metrics define --edit <name>` | Modify an existing custom metric |
| `/venture-metrics correlate` | Run spec-to-code correlation analysis (requires STD-001, min 20 PRs) |

## Always

1. Store venture-level reports in `metrics/reports/current/` and archive previous periods to `metrics/reports/archive/`.
2. Store per-engineer data exclusively in `metrics/internal/` — never in venture-level reports.
3. Report Median + P90 for all time-based metrics (Lead Time, Cycle Time, Coding Time, Time Between Deployments).
4. Exclude weekends and non-working hours from PR Cycle Time calculations.
5. Separate bot/automated PRs (Dependabot, Renovate, CI-generated) from human PRs in all metrics.
6. Auto-detect STD-002/STD-001 presence on each collection run and configure available tiers accordingly.
7. Use commit conventions: `[metrics]` prefix for all metrics-related commits.
8. Update `.claude/state/metrics-state.yaml` after every collection, report generation, or configuration change.

## Ask First

1. Running collection that calls GitHub API — confirm scope and period.
2. Overwriting an existing report for a period that already has data — confirm intent.
3. Exposing per-engineer data in any cross-venture context — confirm normalization approach.
4. Changing metric definitions that affect historical comparability — warn about trend breaks.

## Never

1. Never include per-engineer data in venture-level reports. Individual breakdowns stay in `metrics/internal/`.
2. Never expose spec-to-code ratios outside `metrics/internal/` until correlation with quality is established.
3. Never use a single metric as the sole basis for performance evaluation — metrics provide context, not verdicts.
4. Never compare raw per-engineer counts across ventures without normalization (team size, repo complexity, project phase).
5. Never overwrite internal data from a previous period without archiving first.
6. Never fabricate or estimate metrics when data is unavailable — report which metrics were collected and which were skipped.

## Decision Tree

```
Is metrics/ directory present?
├── NO  → Run `init` to bootstrap
└── YES → Is metrics-state.yaml initialized?
    ├── NO  → Run `init` to complete setup
    └── YES → What does the user want?
        ├── Collect data → Run `collect`
        │   ├── GitHub API configured? → Full Core metrics
        │   └── No GitHub API? → Git-only subset, warn about missing metrics
        ├── View results → Run `report`
        │   ├── Current period has data? → Show report
        │   └── No data? → Suggest `collect` first
        ├── Check health → Run `status`
        │   ├── Targets defined? → Show targets vs actuals with alerts
        │   └── No targets? → Show config and last collection
        ├── Add metrics → Run `define`
        ├── Analyze correlation → Run `correlate`
        │   ├── STD-001 present + ≥20 PRs? → Run analysis
        │   └── Missing prerequisites? → Explain requirements
        └── Unknown → Show available commands
```

## Commit Convention

| Prefix | Usage |
|--------|-------|
| `[metrics]` | All metrics-related changes (collection, reports, config, definitions) |

Examples:
```
[metrics] Bootstrap STD-003 metrics structure
[metrics] Collect 2026-03 delivery speed metrics
[metrics] Generate monthly report with trend analysis
[metrics] Add custom metric: feature-adoption-rate
[metrics] Run spec-to-code correlation analysis
```

## Required Structure

```
project/
  metrics/
    definitions.yaml              # Metric definitions (Core + Extended + custom)
    schedule.yaml                 # Collection frequency, sources, GitHub API config
    reports/
      current/                    # Current period reports
        {YYYY}-{MM}.md            # Monthly venture-level report
      archive/                    # Past period reports
    internal/                     # NEVER exposed in reports
      per-engineer.yaml           # Per-engineer breakdowns
      spec-code-ratios.yaml       # Spec-to-code tracking
  .claude/
    commands/metrics/
      init.md                     # Bootstrap structure
      collect.md                  # Run collection
      report.md                   # Generate/view reports
      status.md                   # Show config and alerts
      define.md                   # Add/modify custom metrics
      correlate.md                # Spec-to-code correlation
    state/
      metrics-state.yaml          # Metrics tracking state
```

## Initialization Templates

These are the canonical templates created by `/venture-metrics init`. Commands reference these templates — any changes to template structure happen here first.

### metrics/definitions.yaml

```yaml
# STD-003 Venture Metrics — Metric Definitions
# Generated by /metrics/init

version: "0.1"
standards_detected:
  std_002: false  # Updated by auto-detection
  std_001: false  # Updated by auto-detection

core_metrics:
  - name: pr_lead_time
    display: "PR Lead Time"
    formula: "Merge Timestamp - First Commit Timestamp"
    unit: hours
    reporting: "Median + P90/month, 3-month rolling"
    source: github_api
  - name: pr_cycle_time
    display: "PR Cycle Time"
    formula: "Merge Timestamp - PR Created Timestamp"
    unit: hours
    reporting: "Median + P90/month"
    source: github_api
    adjustments: "Exclude weekends and non-working hours"
  - name: coding_time
    display: "Coding Time"
    formula: "PR Created Timestamp - First Commit Timestamp"
    unit: hours
    reporting: "Median + P90/month"
    source: github_api
  - name: review_iterations
    display: "Review Iterations"
    formula: "Count of (feedback + author update) cycles"
    unit: count
    reporting: "Average + distribution/month"
    source: github_api
    target: "80% of PRs within 2 iterations"
  - name: pr_approval_rate
    display: "PR Approval Rate (First Pass)"
    formula: "(First-pass approvals / Total PRs) x 100"
    unit: percent
    reporting: "Monthly percentage"
    source: github_api
  - name: deployment_frequency
    display: "Deployment Frequency"
    formula: "Count of successful prod deployments"
    unit: count
    reporting: "Total + per-engineer/month"
    source: github_api
  - name: time_between_deployments
    display: "Time Between Deployments"
    formula: "Sum of intervals / (deploys - 1)"
    unit: hours
    reporting: "Average + median/month"
    source: github_api
  - name: pr_throughput
    display: "PR Throughput"
    formula: "Count of merged PRs"
    unit: count
    reporting: "Total + per-engineer/month"
    source: github_api
  - name: pr_size_distribution
    display: "PR Size Distribution"
    formula: "Small <100, Medium 100-400, Large 400-1000, XL >1000"
    unit: distribution
    reporting: "Monthly % per category"
    source: github_api
    target: "<10% XL PRs"
    priority: deprioritized
  - name: deployment_failure_rate
    display: "Deployment Failure Rate"
    formula: "(Failed + Rollbacks + Hotfixes) / Total x 100"
    unit: percent
    reporting: "Monthly percentage"
    source: github_api

extended_metrics: []
  # Populated when STD-001/STD-002 detected:
  # - name: spec_compliance
  #   display: "Spec Compliance"
  #   formula: "(Changes with proposal + spec-delta) / Total behavior-changing PRs x 100"
  #   unit: percent
  #   source: sdd_state
  #   requires: std_001
  # - name: proposal_velocity
  #   display: "Proposal Velocity"
  #   formula: "Implementation started_at - Proposal created_at"
  #   unit: hours
  #   source: sdd_state
  #   requires: std_001
  # - name: freshness_score
  #   display: "Freshness Score"
  #   formula: "(Specs with CURRENT status) / Total specs x 100"
  #   unit: percent
  #   source: vkf_state
  #   requires: std_002
  # - name: okr_progress
  #   display: "OKR Progress"
  #   formula: "Average key result score (0.0-1.0)"
  #   unit: score
  #   source: okr_files
  #   requires: std_002

custom_metrics: []
  # Add venture-specific metrics via /metrics/define
  # - name: feature_adoption_rate
  #   display: "Feature Adoption Rate"
  #   description: "Percentage of users who adopt a new feature within 30 days"
  #   formula: "(Users using feature at day 30 / Total users) x 100"
  #   unit: percent
  #   source: external
  #   reporting: "Monthly percentage"
  #   cadence: monthly
  #   target: ">50%"
  #   visibility: venture
  #   added: "YYYY-MM-DD"
```

### metrics/schedule.yaml

```yaml
# STD-003 Venture Metrics — Collection Schedule
# Generated by /metrics/init

primary_cadence: monthly  # 1st of each month
optional_cadence: weekly  # Monday (PR Throughput, Deployment Frequency only)

github:
  api_configured: false
  # token: set via GITHUB_TOKEN env var
  owner: ""    # GitHub org or user
  repo: ""     # Repository name

collection_methods:
  - github_actions  # Preferred: automated cron
  - claude_command   # Manual: /metrics/collect
  - external_cron    # Centralized: script-based

bot_authors:
  - "dependabot[bot]"
  - "renovate[bot]"
  - "github-actions[bot]"

working_hours:
  start: "09:00"
  end: "18:00"
  timezone: "UTC"
  exclude_days: ["Saturday", "Sunday"]
```

### metrics/internal/per-engineer.yaml

```yaml
# Per-engineer metric breakdowns — INTERNAL ONLY
# This file MUST NOT be referenced in venture-level reports.
# Access: tech lead + GTM lead only.

periods: []
  # - period: "YYYY-MM"
  #   engineers:
  #     - name: "engineer-handle"
  #       pr_lead_time_median: 18.5
  #       pr_cycle_time_median: 4.2
  #       coding_time_median: 14.3
  #       review_iterations_avg: 1.2
  #       first_pass_approval_rate: 75.0
  #       deployment_count: 8
  #       pr_throughput: 12
  #       pr_size_distribution:
  #         small: 60
  #         medium: 30
  #         large: 10
  #         xl: 0
```

### metrics/internal/spec-code-ratios.yaml

```yaml
# Spec-to-code ratios per PR — INTERNAL ONLY
# Collected when STD-001 is present.
# Do not expose until correlation with quality metrics is established.

periods: []
  # - period: "YYYY-MM"
  #   prs:
  #     - number: 42
  #       spec_files_changed: 2
  #       code_files_changed: 8
  #       ratio: 0.25
  #       has_proposal: true
  #   monthly_average_ratio: 0.18
```

### .claude/state/metrics-state.yaml

```yaml
# STD-003 Venture Metrics — State Tracking
# Managed by /metrics/* commands. Do not edit manually.

initialized_at: null
standards_detected:
  std_002: false
  std_001: false
last_collection: null
  # period: "YYYY-MM"
  # timestamp: "ISO timestamp"
  # metrics_collected: 0
  # metrics_skipped: 0
  # mode: "full | git-only"
last_report: null
  # period: "YYYY-MM"
  # timestamp: "ISO timestamp"
  # type: "current | compare | trend | cross-venture"
github_api_configured: false
tiers_enabled:
  core: false
  extended: false
  advanced: false
collection_history: []
correlation_analysis:
  last_run: null
  prs_analyzed: 0
  sufficient_data: false
```

## Verification

When `/venture-metrics` is invoked with no arguments (or via `/venture-metrics status`), verify the setup is correct. This is the canonical checklist — commands reference these rules.

### 1. Structure Check

| Path | Required | Check |
|------|----------|-------|
| `metrics/` | Yes | Directory exists |
| `metrics/definitions.yaml` | Yes | File exists, valid YAML, has `core_metrics` with 10 entries |
| `metrics/schedule.yaml` | Yes | File exists, valid YAML, has `github` and `working_hours` sections |
| `metrics/reports/current/` | Yes | Directory exists |
| `metrics/reports/archive/` | Yes | Directory exists |
| `metrics/internal/` | Yes | Directory exists |
| `metrics/internal/per-engineer.yaml` | Yes | File exists |
| `metrics/internal/spec-code-ratios.yaml` | Yes | File exists (even if STD-001 not present) |
| `.claude/commands/metrics/` | Yes | Directory exists with at least `init.md`, `collect.md`, `report.md`, `status.md` |
| `.claude/state/metrics-state.yaml` | Yes | File exists, `initialized_at` is set |

Score: **PASS** (all present), **WARN** (optional items missing), **FAIL** (required items missing)

### 2. Configuration Check

| Item | Check | Score |
|------|-------|-------|
| `metrics-state.yaml` has `initialized_at` set | Initialization completed | FAIL if null |
| `definitions.yaml` has all 10 Core metrics | No metrics removed | FAIL if <10 |
| `schedule.yaml` has `github.owner` and `github.repo` set | GitHub API configured | WARN if empty |
| `GITHUB_TOKEN` env var or `github.api_configured: true` | API access available | WARN if missing (git-only mode) |
| `standards_detected` matches actual repo state | Auto-detection current | WARN if stale |

### 3. Standards Auto-Detection

Re-detect on every verification run:

| Standard | Detection Method | Action if Changed |
|----------|-----------------|-------------------|
| STD-002 | `specs/constitution/` directory exists | Enable/disable `freshness_score`, `okr_progress` in extended_metrics |
| STD-001 | `changes/` dir AND `.claude/state/sdd-state.yaml` exist | Enable/disable `spec_compliance`, `proposal_velocity` in extended_metrics |

If detection changes since last run, update `metrics/definitions.yaml` extended_metrics and `metrics-state.yaml` tiers_enabled. Announce: "Standards detection changed — {STD-002/STD-001} is now {detected/no longer detected}. Extended metrics updated."

### 4. Collection Freshness

| Status | Condition | Action |
|--------|-----------|--------|
| **CURRENT** | Last collection is within current or previous month | None |
| **STALE** | Last collection is 2 months old | WARN: suggest `/metrics/collect` |
| **VERY_STALE** | Last collection is 3+ months old or never run | FAIL: require `/metrics/collect` |

### 5. Internal-Only Enforcement

Verify that per-engineer data has not leaked into reports:

- Scan `metrics/reports/current/*.md` for engineer handles listed in `metrics/internal/per-engineer.yaml`
- Scan `metrics/reports/current/*.md` for the string "spec-code-ratio" or contents from `spec-code-ratios.yaml`
- Score: PASS (no leaks), FAIL (internal data found in reports)

### 6. Target Compliance

For metrics with defined targets, compare latest values:

| Metric | Target | Check |
|--------|--------|-------|
| Review Iterations | 80% of PRs within 2 iterations | Parse latest report |
| PR Size Distribution | <10% XL PRs | Parse latest report |
| Custom metrics with targets | Per `definitions.yaml` | Parse latest report |

Report: MET / NOT MET / NO DATA for each target.

### Verification Output

```
╔═══════════════════════════════════════════════════╗
║  STD-003 Verification Report                      ║
║  Generated: {date}                                ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  1. Structure                      [PASS]         ║
║     ✓ metrics/definitions.yaml (10 Core metrics)  ║
║     ✓ metrics/schedule.yaml                       ║
║     ✓ metrics/reports/current/                    ║
║     ✓ metrics/reports/archive/                    ║
║     ✓ metrics/internal/                           ║
║     ✓ .claude/commands/metrics/ (6 commands)      ║
║     ✓ .claude/state/metrics-state.yaml            ║
║                                                   ║
║  2. Configuration                  [WARN]         ║
║     ✓ Initialized: 2026-03-24                    ║
║     ✓ 10 Core metrics defined                    ║
║     ⚠ GitHub API not configured (git-only mode)  ║
║                                                   ║
║  3. Standards Detection            [Enhanced]     ║
║     ✓ STD-002 detected (specs/constitution/)     ║
║     ✓ STD-001 detected (changes/ + sdd-state)    ║
║     ✓ Extended metrics enabled (4 metrics)       ║
║                                                   ║
║  4. Collection Freshness           [CURRENT]      ║
║     Last collection: 2026-03 (2026-04-01)        ║
║                                                   ║
║  5. Internal-Only Enforcement      [PASS]         ║
║     ✓ No per-engineer data in reports            ║
║     ✓ No spec-code ratios in reports             ║
║                                                   ║
║  6. Targets                        [1/2 MET]      ║
║     ✓ Review Iterations: 85% ≤2 (target: 80%)   ║
║     ⚠ XL PRs: 12% (target: <10%)                ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║  Overall: 4 PASS | 2 WARN | 0 FAIL              ║
╚═══════════════════════════════════════════════════╝
```

## Key Metric Relationships

```
PR Lead Time = Coding Time + PR Cycle Time

When Lead Time spikes:
├── Coding Time high? → Development bottleneck (scope, complexity, blocked PRs)
└── Cycle Time high? → Review bottleneck (reviewer availability, iteration count)
    └── Review Iterations high? → PR quality issue (unclear changes, missing context)
        └── PR Size large? → PRs too big (suggest splitting)
```

## Cross-Metric Diagnostic Patterns

| Symptom | Check | Likely Cause |
|---------|-------|-------------|
| Lead Time spike | Decompose into Coding + Cycle | Identifies bottleneck stage |
| Low Approval Rate | Review Iterations + PR Size | Large PRs or unclear changes |
| High Deployment Failure Rate | PR Size Distribution + Review Iterations | Insufficient review or oversized changes |
| Low Throughput | Lead Time + Deployment Frequency | Slow pipeline or blocked PRs |

## Freshness Thresholds (for reports)

| Status | Condition |
|--------|-----------|
| **CURRENT** | Report generated within current month |
| **STALE** | Report is 1 month old (previous period, not yet refreshed) |
| **VERY_STALE** | Report is 2+ months old |
| **MISSING** | No report exists for the expected period |

## CLAUDE.md Intelligence Layer

Adopting repos SHOULD include the `CLAUDE.md` template (shipped with the standard) to enable:

1. **Command routing** — maps user intents ("how are we doing?", "collect metrics", "show trends") to the right `/metrics/*` command
2. **Auto-detection** — checks for STD-002/STD-001 presence and configures available metric tiers
3. **Passive enforcement** — automatic behaviors like suggesting collection when reports are stale, warning about internal-only data, and noting OKR relevance when metrics change
