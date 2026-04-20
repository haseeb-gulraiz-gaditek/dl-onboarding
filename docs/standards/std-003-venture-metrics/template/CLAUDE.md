# Venture Metrics (STD-003)

This repository follows the Venture Metrics standard. The sections below guide Claude Code on when and how to use each metrics command.

## Metrics Operations

### Command Routing Table

When the user asks about or attempts something, consult this table and suggest the right command:

| User says / situation | Command | What it does |
|----------------------|---------|-------------|
| "How are we doing?" / "Show metrics" | `/metrics/report` | View current period report |
| "Collect metrics" / "Run metrics" | `/metrics/collect` | Collect all available metrics |
| "Compare to last month" | `/metrics/report --compare` | Period-over-period comparison |
| "Show trends" / "How are we trending?" | `/metrics/report --trend` | 3-month rolling trend |
| "How do we compare to other ventures?" | `/metrics/report --cross-venture` | Cross-venture benchmarking |
| "Set up metrics" / "Initialize metrics" | `/metrics/init` | Bootstrap metrics structure |
| "What's our PR lead time?" | `/metrics/status` | Show current values and targets |
| "Add a custom metric" | `/metrics/define` | Add venture-specific metric |
| "What's the spec-to-code ratio?" | `/metrics/correlate` | Run correlation analysis |
| "Are we meeting our targets?" | `/metrics/status` | Show targets vs actuals |
| "When was the last collection?" | `/metrics/status` | Show collection history |

### Before Generating Reports

Before generating or sharing any metrics report, evaluate:

1. **Is this venture-level or per-engineer data?**
   - Venture-level → Include in report (from `metrics/reports/`)
   - Per-engineer → Internal only (from `metrics/internal/`). Announce: "Per-engineer data is internal-only per STD-003. I'll show venture-level aggregates."

2. **Is the data current?**
   - Last collection within current month → Use directly
   - Last collection is stale → Suggest: "The latest report is from {date}. Want me to run `/metrics/collect` first?"

3. **Is the user asking for cross-venture data?**
   - Yes → Ensure normalization is applied (per-engineer, by team size)
   - Announce: "Cross-venture data is normalized per active engineer."

### Passive Behaviors

Things to do automatically without being asked:

- **After any collection:** Highlight metrics that exceed targets or show significant trend changes
- **When reports are stale (>1 month old):** Suggest running `/metrics/collect`
- **When PR Lead Time spikes:** Automatically decompose into Coding Time + Cycle Time and suggest where the bottleneck is
- **When per-engineer data is requested:** Remind that individual data is internal-only per STD-003
- **When OKRs exist and metrics change significantly:** Note: "This metric relates to OKR key result [X]. Consider updating progress via `/vkf/okrs update`."
- **When STD-002/STD-001 are adopted after initial setup:** Note: "Extended metrics are now available. Run `/metrics/collect` to include spec compliance and freshness scores."

### Always

- Store venture-level reports in `metrics/reports/` and per-engineer data in `metrics/internal/`
- Report Median + P90 for all time-based metrics
- Exclude weekends and non-working hours from PR Cycle Time
- Separate bot/automated PRs from human PRs in all metrics
- Use `[metrics]` commit prefix for all changes
- Update `.claude/state/metrics-state.yaml` after every operation

### Ask First

- Running collection that calls GitHub API (confirm scope and period)
- Overwriting an existing report for a period that already has data
- Exposing per-engineer data in any context
- Changing metric definitions that affect historical comparability

### Never

- Never include per-engineer data in venture-level reports
- Never expose spec-to-code ratios outside `metrics/internal/`
- Never compare raw per-engineer counts across ventures without normalization
- Never overwrite internal data from a previous period without archiving
- Never fabricate metrics when data is unavailable — report what was collected and what was skipped
