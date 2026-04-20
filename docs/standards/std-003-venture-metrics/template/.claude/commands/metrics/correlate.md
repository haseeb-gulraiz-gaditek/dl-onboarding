---
description: Run spec-to-code correlation analysis between spec changes and code changes in PRs (requires STD-001, minimum 20 PRs)
---

## Arguments

- **$ARGUMENTS** (optional):
  - `--period YYYY-MM` — analyze a specific month (default: all available data)
  - `--min-prs N` — minimum PRs required (default: 20)

## Actions

1. **Check Prerequisites**
   - Verify STD-001 is detected (check for `changes/` and `sdd-state.yaml`)
   - If STD-001 not present, explain requirement and stop
   - Read `metrics/internal/spec-code-ratios.yaml` for existing data

2. **Check Data Sufficiency**
   - Count PRs with spec file changes in the analysis period
   - If below minimum threshold (default 20), report insufficient data and stop
   - Show current count and how many more are needed

3. **Collect PR Data**
   - Fetch merged PRs in period
   - For each PR, categorize changed files:
     - **Spec files**: files in `specs/`, `changes/`, `*.spec.md`, `*.spec.yaml`
     - **Code files**: all other tracked files (excluding config, docs, generated)
   - Calculate per-PR ratio: `spec_files_changed / code_files_changed`
   - Record whether PR had an associated SDD proposal

4. **Run Correlation Analysis**

   Analyze relationships between spec-to-code ratio and quality indicators:

   **Correlation 1: Spec Ratio vs Review Iterations**
   - Do PRs with higher spec coverage need fewer review cycles?
   - Group PRs by spec ratio quartile, compare average review iterations

   **Correlation 2: Spec Ratio vs Deployment Failure Rate**
   - Do PRs with specs have lower deployment failure rates?
   - Compare failure rates: PRs with specs vs PRs without

   **Correlation 3: Spec Ratio vs PR Size**
   - Do spec-driven PRs tend to be smaller (more focused)?
   - Compare size distributions: with specs vs without

   **Correlation 4: Proposal Presence vs Lead Time**
   - Do PRs with SDD proposals have different lead times?
   - Compare lead time distributions: with proposal vs without

5. **Generate Internal Report**
   - Write analysis results to `metrics/internal/spec-code-ratios.yaml`
   - Include:
     - Per-PR ratios
     - Monthly average ratio
     - Correlation coefficients
     - Statistical significance (if sufficient data)
     - Key findings and caveats

6. **Update State**
   - Record correlation analysis timestamp in metrics-state.yaml

7. **Do NOT Commit Automatically**
   - Show results to the user
   - Ask if they want to commit the analysis

## Output

Display:
```
Spec-to-Code Correlation Analysis
Period: {period or "all data"}
PRs analyzed: {N} (with spec changes: {N}, without: {N})

  Average spec-to-code ratio: {X}
  PRs with SDD proposals: {N} ({X}%)

  Correlation Findings:

  1. Spec Ratio vs Review Iterations:
     High spec ratio (>{X}):  {X} avg iterations
     Low spec ratio (<{X}):   {X} avg iterations
     → {Positive correlation / No significant correlation / Insufficient data}

  2. Spec Ratio vs Deployment Failures:
     PRs with specs:    {X}% failure rate
     PRs without specs: {X}% failure rate
     → {Positive correlation / No significant correlation / Insufficient data}

  3. Spec Ratio vs PR Size:
     With specs:    {X} avg lines | {X}% XL
     Without specs: {X} avg lines | {X}% XL
     → {Specs correlate with smaller PRs / No significant difference}

  4. Proposal vs Lead Time:
     With proposal:    {X}h median lead time
     Without proposal: {X}h median lead time
     → {Proposals add time / No significant difference}

  ⚠ This analysis is INTERNAL ONLY per STD-003 §7.
  Results are stored in metrics/internal/spec-code-ratios.yaml.

  Commit this analysis? (y/n)
```

## Error Handling

- **STD-001 not detected**: Explain that correlation analysis requires spec-driven development workflow
- **Insufficient PRs**: Report current count, calculate how many more months of data are needed at current velocity
- **No spec file changes found**: Note that no PRs modified spec files, suggest checking SDD adoption
- **GitHub API unavailable**: Explain that file-level PR data requires GitHub API access
