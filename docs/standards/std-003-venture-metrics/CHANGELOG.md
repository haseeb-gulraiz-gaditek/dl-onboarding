# STD-003 Changelog

All changes to the Venture Metrics standard are documented here. Standard changes are held to a higher bar than regular code — each entry records the rationale and what was evaluated but rejected.

---

## 2026-03-24 — v0.1: Initial Draft

**Origin:** Meeting between Ilian, Salman, and Mobeen on 2026-03-24. Key motivations: repo-centric metrics (pull contribution stats from repos instead of a separate app), OKR tracking in repos (engineering OKRs committed to repos, GTM lead + tech lead set monthly, update weekly), and careful incentive design. Additionally incorporates the Delivery Speed Metrics Framework document, which defines 10 metrics agreed upon by engineering leadership (Akip) for cross-venture benchmarking.

### Decisions Made

#### 1. No hard prerequisite on STD-002

Unlike STD-001 (which requires STD-002), STD-003 works standalone. Two modes: Standalone (Core delivery speed metrics from git/GitHub) and Enhanced (adds spec compliance, OKR progress, freshness scores when STD-002/STD-001 present). **Why:** All ventures need visibility, including those not yet following STD-002/STD-001. A hard prerequisite would exclude the ventures that need metrics visibility most.

#### 2. STD-002 OKRs remain canonical

STD-003 does NOT replace `/vkf/okrs`. It adds a measurement and reporting layer that feeds data into OKR key results. `/vkf/okrs` stays the authoring tool. **Why:** Separation of concerns — one tool writes OKRs, another tool measures progress against them.

#### 3. Built-in metrics from Delivery Speed Metrics Framework

The standard adopts the existing 10-metric framework as its Core tier. These are the metrics Akip prioritized for cross-venture benchmarking. Includes the key relationship: PR Lead Time = Coding Time + PR Cycle Time. **Why:** These metrics were already agreed upon by engineering leadership. Building on existing consensus rather than inventing new metrics.

#### 4. Tiered model matching STD-002 pattern

Core (any git repo), Extended (STD-001/STD-002 present), Advanced (performance framework integration). **Why:** Consistent with STD-002's tiered approach. Allows incremental adoption without requiring the full stack.

#### 5. Exposed vs internal-only separation

Venture-level aggregates are public. Per-engineer breakdowns and spec-to-code ratios are internal-only. **Why:** Meeting consensus — track metrics but be thoughtful about what's exposed. Avoid vanity metrics. Individual data stays internal to prevent gaming and maintain trust.

### Evaluated and Deferred

| Capability | Status | Reason |
|---|---|---|
| **Spec-to-code ratio as exposed metric** | Deferred | Mobeen wants to track it internally first. Expose only after correlation with quality metrics is established. Currently stored in `metrics/internal/spec-code-ratios.yaml`. |
| **Cross-venture aggregation repo** | Deferred | Considered creating a central repo that pulls from all venture reports. Deferred until at least 3 ventures are collecting metrics and patterns emerge. |
| **Real-time dashboards** | Deferred | Monthly collection cadence is sufficient for v0.1. Real-time adds infrastructure complexity that contradicts the "repo as source of truth" principle. |
| **PR Size Distribution as a target** | De-prioritized | Collected but not alerted on. Per the framework document: too easy to game by splitting PRs artificially. The <10% XL target is informational only. |
| **Automated PR labeling** | Deferred | Considered auto-labeling PRs with size category. Adds complexity to the PR workflow without clear value at this stage. |
| **Historical backfill** | Deferred | Considered collecting metrics retroactively from git history. Deferred to v0.2 — current focus is forward-looking collection. |

### Files Created

- `standard.md` — Full standard definition with 9 requirements
- `CHANGELOG.md` — This file
- `skill/SKILL.md` — Skill definition for `venture-metrics`
- `skill/references/metric-definitions.md` — Full metric definitions with formulas and data sources
- `skill/references/collection-schedule.md` — Collection methods, git commands, GitHub API calls
- `skill/references/report-templates.md` — Report templates for monthly, cross-venture, and trend reports
- `skill/references/performance-integration.md` — Performance framework integration guide
- `template/README.md` — Quick setup guide
- `template/CLAUDE.md` — Command routing and passive enforcement
- `template/.claude/commands/metrics/init.md` — Bootstrap metrics structure
- `template/.claude/commands/metrics/collect.md` — Run metric collection
- `template/.claude/commands/metrics/report.md` — Generate/view reports
- `template/.claude/commands/metrics/status.md` — Show configuration and alerts
- `template/.claude/commands/metrics/define.md` — Add/modify custom metrics
- `template/.claude/commands/metrics/correlate.md` — Spec-to-code correlation analysis
- `template/.claude/state/metrics-state.yaml` — State tracking template
