# Metric Definitions Reference

Full definitions for all STD-003 metrics with exact formulas, data sources, reporting formats, and targets.

---

## Core Tier — Delivery Speed Metrics

### 1. PR Lead Time

| Attribute | Value |
|-----------|-------|
| **Measures** | Total time from first commit to merge |
| **Formula** | `Merge Timestamp - First Commit Timestamp` |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/pulls/{number}/commits` (first commit date), PR `merged_at` field |
| **Reporting** | Median + P90 per month, 3-month rolling average |
| **Target** | None defined (venture-specific) |
| **Key Relationship** | PR Lead Time = Coding Time + PR Cycle Time |

**Decomposition guidance:** When Lead Time spikes, break down into Coding Time and PR Cycle Time. If Coding Time is high, the bottleneck is development (scope, complexity, blocked work). If Cycle Time is high, the bottleneck is review/merge.

### 2. PR Cycle Time

| Attribute | Value |
|-----------|-------|
| **Measures** | Time from PR creation to merge |
| **Formula** | `Merge Timestamp - PR Created Timestamp` |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/pulls/{number}` — `created_at` and `merged_at` fields |
| **Reporting** | Median + P90 per month |
| **Target** | None defined (venture-specific) |
| **Adjustments** | Exclude weekends (Sat-Sun) and non-working hours (before 9am, after 6pm local) from elapsed time |

**Weekend exclusion:** Calculate business hours only. A PR created Friday 5pm and merged Monday 9am = 1 business hour, not 64 calendar hours.

### 3. Coding Time

| Attribute | Value |
|-----------|-------|
| **Measures** | Time from first commit to PR creation |
| **Formula** | `PR Created Timestamp - First Commit Timestamp` |
| **Data Source** | GitHub API: PR `created_at` and first commit `date` from `/pulls/{number}/commits` |
| **Reporting** | Median + P90 per month |
| **Target** | None defined (venture-specific) |

### 4. Review Iterations

| Attribute | Value |
|-----------|-------|
| **Measures** | Number of review cycles per PR |
| **Formula** | Count of (reviewer feedback + author update) cycles. A cycle = one review comment/request-changes event followed by author pushing new commits. |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/pulls/{number}/reviews` + `GET /repos/{owner}/{repo}/pulls/{number}/commits` (timestamps to correlate review → push cycles) |
| **Reporting** | Average per month + distribution (1 iteration, 2 iterations, 3+ iterations) |
| **Target** | **80% of PRs approved within 2 iterations** (Delivery Speed Metrics Framework) |

**Counting rules:**
- Initial review request does not count as an iteration
- Each "request changes" → "push commits" → "re-review" sequence = 1 iteration
- Approved on first review = 0 iterations (ideal)
- Comments without "request changes" do not count as iterations unless followed by author commits

### 5. PR Approval Rate (First Pass)

| Attribute | Value |
|-----------|-------|
| **Measures** | Percentage of PRs approved on first review without changes requested |
| **Formula** | `(PRs with first review = "approved") / (Total PRs with reviews) x 100` |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/pulls/{number}/reviews` — first review event per PR |
| **Reporting** | Monthly percentage |
| **Target** | None defined (venture-specific) |

### 6. Deployment Frequency

| Attribute | Value |
|-----------|-------|
| **Measures** | Number of successful production deployments per month |
| **Formula** | Count of successful production deployments in period |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/deployments` with `environment=production` and `status=success`. Fallback: count merges to main/production branch. |
| **Reporting** | Total per month + per-engineer per month |
| **Target** | None defined (venture-specific) |

**Detection heuristic:** If GitHub Deployments API is not configured, fall back to counting merges to the default branch (assuming CI/CD deploys on merge).

### 7. Time Between Deployments

| Attribute | Value |
|-----------|-------|
| **Measures** | Average time interval between consecutive deployments |
| **Formula** | `Sum of (deploy[n+1] timestamp - deploy[n] timestamp) / (total deploys - 1)` |
| **Data Source** | Same as Deployment Frequency |
| **Reporting** | Average + Median per month |
| **Target** | None defined (venture-specific) |

### 8. PR Throughput

| Attribute | Value |
|-----------|-------|
| **Measures** | Number of PRs merged per month |
| **Formula** | Count of merged PRs in period |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/pulls?state=closed&sort=updated` — filter by `merged_at` in period |
| **Reporting** | Total per month + per-engineer per month |
| **Target** | None defined (venture-specific) |

### 9. PR Size Distribution

| Attribute | Value |
|-----------|-------|
| **Measures** | Distribution of PR sizes by lines changed |
| **Formula** | Categorize each PR: Small (<100 lines), Medium (100-400), Large (400-1000), XL (>1000) |
| **Data Source** | GitHub API: `GET /repos/{owner}/{repo}/pulls/{number}` — `additions + deletions` fields |
| **Reporting** | Monthly percentage per category |
| **Target** | **<10% XL PRs** (Delivery Speed Metrics Framework) — informational only, de-prioritized |

**Line counting:** `additions + deletions` from the PR. Excludes generated files (lock files, compiled output) if `.gitattributes` marks them as generated.

**De-prioritized:** This metric is collected but not alerted on. It's too easy to game by splitting PRs artificially. Use as contextual data, not a KPI.

### 10. Deployment Failure Rate

| Attribute | Value |
|-----------|-------|
| **Measures** | Percentage of deployments that fail, are rolled back, or require hotfixes |
| **Formula** | `(Failed deploys + Rollbacks + Hotfixes) / Total deploys x 100` |
| **Data Source** | GitHub API: Deployments with `status=failure`. Rollbacks detected by deploy → revert commit → deploy pattern. Hotfixes detected by PRs with "hotfix" label or branch prefix merged within 24h of a deploy. |
| **Reporting** | Monthly percentage |
| **Target** | None defined (venture-specific) |

---

## Extended Tier — Standard-Enhanced Metrics

### Spec Compliance

| Attribute | Value |
|-----------|-------|
| **Measures** | Percentage of changes that follow the SDD workflow |
| **Formula** | `(Changes with proposal + spec-delta) / (Total merged PRs with observable behavior change) x 100` |
| **Data Source** | `changes/` and `archive/` directories, `.claude/state/sdd-state.yaml` |
| **Reporting** | Monthly percentage |
| **Requires** | STD-001 |

### Proposal Velocity

| Attribute | Value |
|-----------|-------|
| **Measures** | Time from proposal creation to implementation start |
| **Formula** | `Implementation started_at - Proposal created_at` |
| **Data Source** | `.claude/state/sdd-state.yaml` (cycle history) |
| **Reporting** | Median per month |
| **Requires** | STD-001 |

### Freshness Score

| Attribute | Value |
|-----------|-------|
| **Measures** | Percentage of specs in CURRENT status |
| **Formula** | `(Specs with CURRENT status) / (Total specs) x 100` |
| **Data Source** | `/vkf/freshness` scan output, `.claude/state/vkf-state.yaml` |
| **Reporting** | Monthly percentage |
| **Requires** | STD-002 |

### OKR Progress

| Attribute | Value |
|-----------|-------|
| **Measures** | Key result completion across active OKRs |
| **Formula** | Average key result score (0.0-1.0) across all active objectives |
| **Data Source** | `specs/okrs/current/` files |
| **Reporting** | Monthly snapshot |
| **Requires** | STD-002 with OKRs adopted |

---

## Internal-Only Metrics

### Per-Engineer Breakdowns

All 10 Core metrics broken down by individual contributor. Stored in `metrics/internal/per-engineer.yaml`.

**Schema:**
```yaml
period: "2026-03"
engineers:
  - name: "engineer-handle"
    pr_lead_time_median: 18.5  # hours
    pr_cycle_time_median: 4.2
    coding_time_median: 14.3
    review_iterations_avg: 1.2
    first_pass_approval_rate: 75.0
    deployment_count: 8
    pr_throughput: 12
    pr_size_distribution:
      small: 60
      medium: 30
      large: 10
      xl: 0
```

### Spec-to-Code Ratio

Per-PR ratio of spec file changes to code file changes. Stored in `metrics/internal/spec-code-ratios.yaml`.

**Schema:**
```yaml
period: "2026-03"
prs:
  - number: 42
    spec_files_changed: 2
    code_files_changed: 8
    ratio: 0.25
    has_proposal: true
monthly_average_ratio: 0.18
```

**Status:** Internal-only until correlation with code quality metrics (deployment failure rate, review iterations) is established. Minimum 20 PRs with spec changes required before correlation analysis is meaningful.

---

## Key Relationship Diagram

```
PR Lead Time = Coding Time + PR Cycle Time

Timeline:
  ├─── Coding Time ───┤├───── PR Cycle Time ─────┤
  │                    ││                          │
  First              PR                         PR
  Commit           Created                    Merged

Diagnostic decomposition:
  Lead Time ↑
  ├── Coding Time ↑ → Development bottleneck
  │   └── Check: scope, blocked dependencies, context switching
  └── Cycle Time ↑ → Review bottleneck
      ├── Review Iterations ↑ → PR quality issues
      │   └── PR Size large? → Split PRs
      └── Review Iterations normal → Reviewer availability
```
