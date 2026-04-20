---
description: Run the full STD-003 verification checklist and show configuration, collection freshness, and target compliance
---

## Actions

1. **Read State**
   - Parse `.claude/state/metrics-state.yaml`
   - If not initialized, suggest `/metrics/init` and stop

2. **Run Verification Checklist**

   Execute all 6 checks from SKILL.md § Verification:

   - **§1 Structure Check** — verify all required files and directories exist
   - **§2 Configuration Check** — verify initialization, metric count, GitHub API, standards detection
   - **§3 Standards Auto-Detection** — re-detect STD-002/STD-001, update if changed
   - **§4 Collection Freshness** — check last collection age (CURRENT/STALE/VERY_STALE)
   - **§5 Internal-Only Enforcement** — scan reports for leaked per-engineer data
   - **§6 Target Compliance** — compare latest metric values against defined targets

3. **Display Verification Report**
   - Use the output format defined in SKILL.md § Verification Output

## Output Format

### Initialized (per SKILL.md § Verification Output)

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

Next: /metrics/collect to refresh data
      /metrics/report --compare for trends
```

### Not Initialized

```
╔══════════════════════════════════════╗
║  STD-003 Metrics Status              ║
╠══════════════════════════════════════╣
║  Not initialized                     ║
╚══════════════════════════════════════╝

Run /metrics/init to bootstrap metrics structure.
```

## Error Handling

- **Not initialized**: Suggest `/metrics/init`
- **Standards detection changed**: Update state, announce change, re-run verification
- **Internal data leak detected**: FAIL with specific file and line where leak was found
