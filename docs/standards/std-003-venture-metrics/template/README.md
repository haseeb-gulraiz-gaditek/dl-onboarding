# Metrics Command Template

Starter kit for projects adopting **STD-003 Venture Metrics**.

## Quick Setup

Copy the `.claude/` folder to your project root:

```bash
cp -r .claude/ /path/to/your-project/.claude/
```

Then run the init command:

```
/metrics/init
```

This creates all required directories, detects which standards are present, and configures available metric tiers.

## Directory Structure

After setup, your project should have:

```
your-project/
├── .claude/
│   ├── commands/
│   │   └── metrics/
│   │       ├── init.md           # Bootstrap structure
│   │       ├── collect.md        # Run metric collection
│   │       ├── report.md         # Generate/view reports
│   │       ├── status.md         # Show config and alerts
│   │       ├── define.md         # Add/modify custom metrics
│   │       └── correlate.md      # Spec-to-code correlation
│   └── state/
│       └── metrics-state.yaml    # Metrics tracking
├── metrics/
│   ├── definitions.yaml          # Metric definitions
│   ├── schedule.yaml             # Collection config
│   ├── reports/
│   │   ├── current/              # Current period reports
│   │   └── archive/              # Past period reports
│   └── internal/                 # Per-engineer data (lead-only)
│       ├── per-engineer.yaml
│       └── spec-code-ratios.yaml
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `/metrics/init` | Scaffold metrics structure, detect standards, configure tiers |
| `/metrics/collect` | Run metric collection for current or specified period |
| `/metrics/report` | Generate or view reports (current, comparison, trend, cross-venture) |
| `/metrics/status` | Show configuration, last collection, targets vs actuals |
| `/metrics/define` | Add or modify custom venture-specific metrics |
| `/metrics/correlate` | Run spec-to-code correlation analysis (requires STD-001) |

## Workflow

```
/metrics/init
    │
    ▼
Metrics structure created, standards auto-detected
    │
    ▼
/metrics/collect              # Collect metrics for current period
    │
    ▼
/metrics/report               # View the generated report
/metrics/report --compare     # Compare with previous period
/metrics/report --trend       # 3-month rolling trends
    │
    ▼
/metrics/status               # Check targets, alerts, and health
```

## Modes

STD-003 auto-detects which standards are present:

| Mode | Detection | Metrics Available |
|------|-----------|-------------------|
| **Standalone** | No `specs/constitution/` or `changes/` | 10 Core Delivery Speed metrics |
| **Enhanced** | STD-002 and/or STD-001 present | Core + Extended (spec compliance, freshness, OKRs) |

## No Hard Prerequisites

Unlike STD-001 (which requires STD-002), STD-003 works with any git repo that has GitHub API access. Adding STD-002/STD-001 later automatically unlocks Extended metrics.

## Reference

See [STD-003 Venture Metrics](../standard.md) for the full standard.
