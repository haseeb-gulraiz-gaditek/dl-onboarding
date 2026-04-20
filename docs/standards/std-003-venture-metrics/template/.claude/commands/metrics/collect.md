---
description: Run metric collection for current or specified period, computing all available tier metrics from git and GitHub data
---

## Arguments

- **$ARGUMENTS** (optional): `--period YYYY-MM` to collect for a specific month (default: previous month)

## Actions

1. **Read Configuration**
   - Parse `.claude/state/metrics-state.yaml` for initialization status
   - Parse `metrics/definitions.yaml` for enabled metrics
   - Parse `metrics/schedule.yaml` for GitHub API config, bot authors, working hours
   - If not initialized, suggest `/metrics/init` and stop

2. **Determine Period**
   - If `--period YYYY-MM` provided, use that month
   - Otherwise, use the previous calendar month
   - Check if a report already exists for this period — if yes, ask to overwrite or skip

3. **Re-Detect Standards**
   - Check for `specs/constitution/` → STD-002 present
   - Check for `changes/` and `.claude/state/sdd-state.yaml` → STD-001 present
   - Update tiers if detection changes since last run

4. **Collect Core Metrics**

   For each of the 10 Delivery Speed metrics:

   **a. PR data collection** (GitHub API)
   ```
   - Fetch all PRs merged in period
   - Filter out bot/automated PRs (by author match against schedule.yaml bot_authors)
   - For each human PR:
     - Get first commit timestamp (from /pulls/{n}/commits)
     - Get PR created_at, merged_at
     - Get additions, deletions, changed_files
     - Get reviews (from /pulls/{n}/reviews)
   ```

   **b. Compute per-PR values**
   ```
   - PR Lead Time = merged_at - first_commit_date
   - PR Cycle Time = merged_at - created_at (business hours only)
   - Coding Time = created_at - first_commit_date
   - Review Iterations = count of (CHANGES_REQUESTED → new commits) cycles
   - First Pass Approved = (first review state == "APPROVED")
   - PR Size = additions + deletions → categorize (Small/Medium/Large/XL)
   ```

   **c. Compute aggregate values**
   ```
   - Median + P90 for Lead Time, Cycle Time, Coding Time
   - Average + distribution for Review Iterations
   - Sum for PR Throughput, Deployment Frequency
   - Percentage for Approval Rate, Failure Rate, Size Distribution
   ```

   **d. Deployment data** (GitHub API or git fallback)
   ```
   - Fetch deployments to production in period
   - Count successful, failed, rollbacks
   - Calculate Time Between Deployments
   - If no Deployments API: fall back to merge-to-main count
   ```

5. **Collect Extended Metrics** (if tiers enabled)

   **Spec Compliance** (STD-001):
   - Count archived change cycles completed in period
   - Count merged PRs with observable behavior changes
   - Calculate compliance rate

   **Freshness Score** (STD-002):
   - Scan all specs for freshness dates
   - Classify: CURRENT, STALE, VERY_STALE, MISSING
   - Calculate percentage CURRENT

   **OKR Progress** (STD-002):
   - Read `specs/okrs/current/*.md`
   - Parse key result scores
   - Calculate average progress

6. **Write Venture-Level Report**
   - Generate `metrics/reports/current/{YYYY}-{MM}.md` using the monthly report template
   - Include all collected metrics with values, trends vs previous period, targets comparison
   - Archive previous period report to `metrics/reports/archive/` if exists

7. **Write Internal Data**
   - Write per-engineer breakdowns to `metrics/internal/per-engineer.yaml`
   - Write spec-to-code ratios to `metrics/internal/spec-code-ratios.yaml` (if STD-001 present)

8. **Update State**
   - Update `.claude/state/metrics-state.yaml`:
     ```yaml
     last_collection:
       period: "{YYYY}-{MM}"
       timestamp: "{ISO timestamp}"
       metrics_collected: {count}
       metrics_skipped: {count}
       mode: "{full | git-only}"
     ```

9. **Commit**
   - Stage: `metrics/reports/`, `metrics/internal/`, `.claude/state/metrics-state.yaml`
   - Commit with message: `[metrics] Collect {YYYY}-{MM} delivery speed metrics`

## Output

Display:
```
Collected metrics for {YYYY}-{MM}

  Mode: {Full (GitHub API) | Partial (git-only)}
  PRs analyzed: {N} human + {N} bot (excluded)

  Core Metrics:
    PR Lead Time:       {X}h median ({trend} from {prev}h)
    PR Cycle Time:      {X}h median ({trend} from {prev}h)
    Coding Time:        {X}h median ({trend} from {prev}h)
    Review Iterations:  {X} avg (target: 80% ≤2 → {MET/NOT MET})
    First Pass Approval:{X}%
    Deploy Frequency:   {N} deploys
    Time Between Deps:  {X}h avg
    PR Throughput:      {N} PRs merged
    PR Size (XL):       {X}% (target: <10% → {MET/NOT MET})
    Deploy Failure Rate:{X}%

  Extended Metrics:
    Spec Compliance:    {X}%
    Freshness Score:    {X}%
    OKR Progress:       {X} avg

  Report: metrics/reports/current/{YYYY}-{MM}.md
  Internal: metrics/internal/per-engineer.yaml

Next: /metrics/report to view full report
      /metrics/report --compare for period comparison
```

## Error Handling

- **Not initialized**: Suggest `/metrics/init` first
- **No GitHub API token**: Collect git-only metrics, list skipped metrics
- **No merged PRs in period**: Generate report with zero values, note "no activity"
- **API rate limit**: Report how many PRs were collected before limit, suggest retry
- **Existing report for period**: Ask to overwrite or skip
- **Git history not available**: Fail with message suggesting `git fetch --unshallow`
