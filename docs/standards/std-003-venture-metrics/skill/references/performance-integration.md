# Performance Framework Integration Reference

How STD-003 metrics connect to the performance framework, OKR key results, and cross-venture benchmarking.

---

## OKR Key Results → Metric Mapping

STD-003 provides measurable data for OKR key results. The GTM lead + tech lead set monthly metric targets; engineers update weekly.

### Example Mappings

| OKR Key Result | STD-003 Metric | Target | Measurement |
|----------------|----------------|--------|-------------|
| "Reduce PR review cycle to <4h median" | PR Cycle Time | Median <4h | Monthly report |
| "Ship 20+ PRs per month" | PR Throughput | ≥20 PRs/month | Monthly report |
| "Zero failed deployments this quarter" | Deployment Failure Rate | 0% | Monthly report |
| "All features follow SDD workflow" | Spec Compliance | 100% | Monthly report (Extended) |
| "Keep specs current" | Freshness Score | >90% CURRENT | Monthly report (Extended) |
| "Deploy daily" | Deployment Frequency | ≥20/month | Monthly report |
| "First-pass approval on 70%+ PRs" | PR Approval Rate | ≥70% | Monthly report |

### Setting Metric Targets

1. **Start with baseline**: Run `/metrics/collect` for 1-2 months before setting targets
2. **Set realistic targets**: Use P50 (median) of baseline as starting target, improve 10-20% per quarter
3. **Avoid ceiling targets**: Don't set targets that encourage gaming (e.g., "0 review iterations" discourages thorough review)
4. **Review quarterly**: Adjust targets based on trends and team feedback

### Updating OKR Progress from Metrics

When STD-002 OKRs exist (`specs/okrs/current/`):

1. `/metrics/collect` computes metric values
2. Compare metric values against OKR key result targets
3. `/vkf/okrs update` reflects metric-based progress
4. Both commands update their respective state files

**STD-003 does NOT auto-update OKR scores.** It provides the data; the tech lead reviews and updates OKR progress manually or via `/vkf/okrs update`.

---

## Cross-Venture Benchmarking

### Normalization Rules

Raw metrics across ventures are not directly comparable. Cross-venture reports normalize:

| Factor | Method |
|--------|--------|
| **Team size** | Per-engineer metrics (PR Throughput / team size, Deployment Frequency / team size) |
| **Repo complexity** | Weight by lines of code or active file count (optional) |
| **Project phase** | Label: early (0-6 months), growth (6-18 months), mature (18+ months) — compare within phase |
| **Tech stack** | Annotate — don't normalize. A mobile app has different deployment patterns than a web API. |

### What's Compared Cross-Venture

| Metric | Cross-Venture? | Notes |
|--------|---------------|-------|
| PR Lead Time | Yes | Median, normalized by project phase |
| PR Cycle Time | Yes | Median, business hours |
| PR Throughput | Yes | Per-engineer normalized |
| Deployment Frequency | Yes | Per-engineer normalized |
| Deployment Failure Rate | Yes | Raw percentage (already normalized) |
| Review Iterations | Yes | Average (already normalized) |
| First Pass Approval | Yes | Raw percentage |
| Coding Time | No | Too dependent on project type |
| PR Size Distribution | No | Too dependent on codebase conventions |
| Time Between Deployments | No | Too dependent on deployment strategy |

---

## Safeguards Against Gaming

### Metrics That Can Be Gamed

| Metric | Gaming Risk | Safeguard |
|--------|------------|-----------|
| PR Size Distribution | Split PRs artificially to avoid XL | De-prioritized — collect but don't alert |
| PR Throughput | Many tiny PRs to inflate count | Report alongside PR Size Distribution for context |
| Review Iterations | Approve without reading | Track with Deployment Failure Rate as counterbalance |
| Deployment Frequency | Empty deploys | Require observable changes per deploy |
| Coding Time | Delay PR creation | Track Lead Time (which includes Coding Time) as primary |

### Structural Safeguards

1. **Team-level primary**: All reports and targets are at the venture/team level. Individual data is supplementary context, not the score.

2. **Multiple-metric context**: No single metric is used alone. The diagnostic patterns (Lead Time → Coding + Cycle, Approval Rate → Iterations + Size) ensure that gaming one metric surfaces in another.

3. **Trend over absolute**: Reports emphasize improvement trajectories. A team moving from 48h to 24h Lead Time is performing well, even if another team sits at 8h.

4. **Quarterly review of targets**: Targets are reviewed and adjusted each quarter. If a target is consistently gamed, it's either revised or replaced.

---

## Lead-Only Access Patterns

### What Leads See

| Data | Access Level | Purpose |
|------|-------------|---------|
| Venture-level reports | All team members | Transparency on team health |
| Per-engineer breakdowns | Tech lead + GTM lead | Context for 1:1s, workload balancing |
| Spec-to-code ratios | Tech lead only | Internal correlation research |
| Cross-venture individual data | Engineering leadership only | Cross-venture staffing and support decisions |

### Access Implementation

STD-003 uses structural separation (not access controls) to enforce visibility:

- `metrics/reports/` — venture-level, visible to all
- `metrics/internal/` — per-engineer, lead-only by convention
- `.gitignore` MAY exclude `metrics/internal/` from public repos (but SHOULD be committed in private repos for auditability)

### Per-Engineer Data in 1:1s

Per-engineer data is designed for coaching conversations, not performance reviews:

- "Your PR Cycle Time is higher this month — are you waiting on reviews?" (coaching)
- NOT: "Your PR Cycle Time is 2x the team average" (judgement)

The distinction: use data to ask questions, not to make statements.

---

## Integration Timeline

| Phase | Action | When |
|-------|--------|------|
| **Month 1** | Bootstrap STD-003, collect baseline | Immediately |
| **Month 2** | Second collection, first comparison report | +1 month |
| **Month 3** | Set initial targets based on baseline | +2 months |
| **Quarter 2** | Review targets, enable cross-venture | +3 months |
| **Ongoing** | Monthly collection, quarterly target review | Continuous |
