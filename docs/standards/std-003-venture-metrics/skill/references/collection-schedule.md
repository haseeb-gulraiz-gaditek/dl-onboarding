# Collection Schedule Reference

Methods, commands, and workflows for collecting STD-003 metrics.

---

## Collection Cadence

| Cadence | Metrics | Trigger |
|---------|---------|---------|
| **Monthly** (primary) | All Core + Extended + custom | 1st of each month (collects previous month) |
| **Weekly** (optional) | PR Throughput, Deployment Frequency | Monday (collects previous week) |

---

## GitHub Actions Workflow Template

```yaml
name: Collect Metrics
on:
  schedule:
    - cron: '0 9 1 * *'  # 9am UTC on the 1st of each month
  workflow_dispatch:       # Manual trigger

permissions:
  contents: write
  pull-requests: read

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git log

      - name: Collect metrics
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Calculate previous month
          PERIOD=$(date -d "last month" +%Y-%m 2>/dev/null || date -v-1m +%Y-%m)

          # Collection script placeholder
          # In practice, this calls the /metrics/collect command logic
          echo "Collecting metrics for $PERIOD"

      - name: Commit results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add metrics/
          git diff --staged --quiet || git commit -m "[metrics] Collect $(date -d 'last month' +%Y-%m 2>/dev/null || date -v-1m +%Y-%m) delivery speed metrics"
          git push
```

---

## Git Commands for Each Metric

### PR Throughput (git-only proxy)

```bash
# Count merged PRs via merge commits in period
git log --merges --after="2026-03-01" --before="2026-04-01" --oneline | wc -l

# Per-engineer merge count
git log --merges --after="2026-03-01" --before="2026-04-01" --format="%an" | sort | uniq -c | sort -rn
```

### Coding Time (git-only proxy)

```bash
# For a specific branch, time from first commit to branch creation
# (Approximation: first commit on branch to last commit before merge)
git log --format="%H %ai" main..feature-branch | tail -1  # First commit
git log --format="%H %ai" main..feature-branch | head -1   # Last commit
```

### Deployment Frequency (git-only fallback)

```bash
# Count merges to main (proxy for deploys when CI/CD deploys on merge)
git log --merges --first-parent main --after="2026-03-01" --before="2026-04-01" --oneline | wc -l
```

### PR Size (git-only proxy)

```bash
# Lines changed per merge commit
git log --merges --after="2026-03-01" --before="2026-04-01" --format="%H" | while read hash; do
  git diff --shortstat "${hash}^..${hash}"
done
```

### Commit Activity by Engineer

```bash
# Commits per engineer in period
git log --after="2026-03-01" --before="2026-04-01" --format="%an" | sort | uniq -c | sort -rn

# Lines changed per engineer
git log --after="2026-03-01" --before="2026-04-01" --format="%an" --shortstat | awk '...'
```

---

## GitHub API Calls

### PR Data (Core metrics: Lead Time, Cycle Time, Coding Time, Size, Throughput)

```bash
# List merged PRs in period
gh api repos/{owner}/{repo}/pulls \
  --paginate \
  -q '.[] | select(.merged_at >= "2026-03-01T00:00:00Z" and .merged_at < "2026-04-01T00:00:00Z")' \
  -f state=closed -f sort=updated -f direction=desc

# For each PR, get commits (for first commit timestamp)
gh api repos/{owner}/{repo}/pulls/{number}/commits \
  -q '.[0].commit.author.date'  # First commit date

# PR size
gh api repos/{owner}/{repo}/pulls/{number} \
  -q '{additions: .additions, deletions: .deletions, changed_files: .changed_files}'
```

### Review Data (Review Iterations, Approval Rate)

```bash
# Get reviews for a PR
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  -q '.[] | {user: .user.login, state: .state, submitted_at: .submitted_at}'

# Count iterations: sequence of CHANGES_REQUESTED followed by new commits
# Logic: for each CHANGES_REQUESTED review, check if commits exist after that timestamp
```

### Deployment Data (Deployment Frequency, Failure Rate, Time Between Deployments)

```bash
# List deployments
gh api repos/{owner}/{repo}/deployments \
  -q '.[] | select(.environment == "production")' \
  --paginate

# Get deployment statuses
gh api repos/{owner}/{repo}/deployments/{id}/statuses \
  -q '.[0].state'  # success, failure, error
```

### Bot/Automated PR Detection

```bash
# Filter out bot PRs by author
gh api repos/{owner}/{repo}/pulls \
  --paginate \
  -q '.[] | select(.user.login | test("bot$|\\[bot\\]|dependabot|renovate|github-actions") | not)'
```

---

## Weekend Exclusion for Cycle Time

Business hours calculation for PR Cycle Time:

```
Working hours: Monday-Friday, 09:00-18:00 (local timezone)
Hours per working day: 9

Algorithm:
1. Parse PR created_at and merged_at timestamps
2. For each day in the range:
   a. Skip Saturday and Sunday
   b. On start day: count hours from max(created_at, 09:00) to 18:00
   c. On end day: count hours from 09:00 to min(merged_at, 18:00)
   d. On full working days: count 9 hours
3. Sum business hours
```

---

## Partial Data Handling

When GitHub API access is unavailable, degrade gracefully:

| Full (GitHub API) | Git-only Fallback | Notes |
|-------------------|-------------------|-------|
| PR Lead Time | N/A (no PR data) | Skip, note in report |
| PR Cycle Time | N/A | Skip |
| Coding Time | Approximate from branch duration | Less accurate |
| Review Iterations | N/A | Skip |
| PR Approval Rate | N/A | Skip |
| Deployment Frequency | Merge count to main | Proxy, assumes CI/CD on merge |
| Time Between Deployments | Time between merges to main | Proxy |
| PR Throughput | Merge commit count | Proxy |
| PR Size Distribution | Diff stats per merge | Less accurate (includes merge artifacts) |
| Deployment Failure Rate | N/A | Skip |

**Report header when degraded:**
```markdown
> **Note:** This report was collected with git-only data (no GitHub API access).
> Metrics marked with * are proxies. PR-specific metrics (Lead Time, Cycle Time,
> Review Iterations, Approval Rate) are unavailable.
```

---

## Extended Tier Collection

### Spec Compliance (requires STD-001)

```bash
# Count archived change cycles (completed SDD workflows)
ls archive/ | wc -l

# Count merged PRs that should have had proposals
# (PRs touching src/ or app/ — observable behavior changes)
gh api repos/{owner}/{repo}/pulls \
  --paginate \
  -q '.[] | select(.merged_at >= "2026-03-01" and .merged_at < "2026-04-01") | select(.changed_files > 0)'
```

### Freshness Score (requires STD-002)

```bash
# Parse Last reviewed / Last amended dates from all spec files
grep -r "Last reviewed:\|Last amended:" specs/ | while read line; do
  # Parse date, compare to today, classify as CURRENT/STALE/VERY_STALE/MISSING
  echo "$line"
done
```

### OKR Progress (requires STD-002 with OKRs)

```bash
# Read current quarter OKR file
cat specs/okrs/current/*.md
# Parse key result scores (0.0-1.0)
```
