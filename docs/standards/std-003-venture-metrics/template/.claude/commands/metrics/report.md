---
description: Generate or view metric reports with options for comparison, trends, and cross-venture benchmarking
---

## Arguments

- **$ARGUMENTS** (optional):
  - `--period YYYY-MM` — view a specific period's report (default: latest)
  - `--compare` — period-over-period comparison (current vs previous)
  - `--trend` — 3-month rolling trend
  - `--cross-venture` — cross-venture benchmarking summary

## Actions

1. **Read State**
   - Parse `.claude/state/metrics-state.yaml` for last collection info
   - If no collection has been run, suggest `/metrics/collect` first

2. **Determine Report Type**
   - No flags → Show current period report
   - `--compare` → Period-over-period comparison
   - `--trend` → 3-month rolling trend
   - `--cross-venture` → Cross-venture benchmarking summary
   - `--period YYYY-MM` → Show specific period's report

3. **Generate Report**

   **Current Period Report:**
   - Read `metrics/reports/current/{YYYY}-{MM}.md`
   - Display the report contents
   - Highlight any metrics exceeding targets
   - Note any missing metrics (git-only mode)

   **Period-over-Period Comparison (`--compare`):**
   - Read current and previous period reports
   - Calculate deltas for all metrics
   - Classify trends: better/worse/flat (using the comparison template)
   - Highlight significant changes (>20% delta)

   **3-Month Rolling Trend (`--trend`):**
   - Read current + 2 previous period reports (from archive)
   - Calculate 3-month averages
   - Classify direction: improving/declining/stable
   - Generate key observations about trends

   **Cross-Venture Benchmarking (`--cross-venture`):**
   - Read reports from multiple venture repos (paths configured in schedule.yaml)
   - Normalize per-engineer metrics by team size
   - Generate comparison table
   - Note project phase for context

4. **Display Report**
   - Render the appropriate report template
   - Include trend indicators and target comparisons
   - Flag any alerts (targets missed, significant regressions)

## Output Format

### Current Period

```
Delivery Speed Report — {YYYY}-{MM}

  Summary:
  ┌─────────────────────────────┬────────┬───────┬──────────┐
  │ Metric                      │ Value  │ Trend │ Previous │
  ├─────────────────────────────┼────────┼───────┼──────────┤
  │ PR Lead Time (Median)       │ 18.5h  │  ↓ 3h │ 21.5h   │
  │ PR Cycle Time (Median)      │  4.2h  │  ↓ 1h │  5.2h   │
  │ PR Throughput               │  24    │  ↑ 4  │  20     │
  │ Deploy Frequency            │  15    │  ↑ 2  │  13     │
  │ Deploy Failure Rate         │  6.7%  │  → 0% │  6.7%   │
  └─────────────────────────────┴────────┴───────┴──────────┘

  Full report: metrics/reports/current/{YYYY}-{MM}.md
```

### Comparison

```
Period Comparison — {period_1} vs {period_2}

  Improving: PR Lead Time (-3h), PR Cycle Time (-1h), PR Throughput (+4)
  Declining: Deploy Failure Rate (+2%)
  Stable: Review Iterations, First Pass Approval

  Details: [full comparison table]
```

## Error Handling

- **No reports exist**: Suggest running `/metrics/collect` first
- **Missing periods for trend**: Show available data, note gaps
- **Cross-venture repos not configured**: Explain how to set up `schedule.yaml` with venture paths
- **Stale data**: Warn if latest report is >1 month old, suggest `/metrics/collect`
