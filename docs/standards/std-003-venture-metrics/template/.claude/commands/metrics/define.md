---
description: Add or modify custom venture-specific metric definitions
---

## Arguments

- **$ARGUMENTS** (optional):
  - No args → Interactive: prompt for metric details
  - `--edit <name>` → Modify an existing custom metric

## Actions

1. **Read Current Definitions**
   - Parse `metrics/definitions.yaml`
   - List existing custom metrics if any

2. **Add New Metric** (no `--edit` flag)

   Prompt the user for:
   - **Name**: Machine-readable identifier (e.g., `feature_adoption_rate`)
   - **Display name**: Human-readable label (e.g., "Feature Adoption Rate")
   - **Description**: What it measures
   - **Formula**: How to calculate it
   - **Data source**: Where the data comes from (git, GitHub API, manual, external)
   - **Unit**: hours, count, percent, distribution, or custom
   - **Reporting format**: How to display (median, average, total, percentage, distribution)
   - **Cadence**: monthly, weekly, or custom
   - **Target** (optional): Target value or range
   - **Visibility**: `venture` (in reports) or `internal` (metrics/internal/ only)

3. **Edit Existing Metric** (`--edit <name>`)
   - Find the metric in `metrics/definitions.yaml`
   - Show current definition
   - Prompt for changes (leave blank to keep current value)
   - Warn if changes affect historical comparability

4. **Validate Definition**
   - Name is unique (no collision with Core/Extended metrics)
   - Formula is documented
   - Data source is specified
   - Visibility is explicitly set

5. **Update Definitions**
   - Add or update the metric in `metrics/definitions.yaml` under `custom_metrics`
   - Format:
     ```yaml
     custom_metrics:
       - name: feature_adoption_rate
         display: "Feature Adoption Rate"
         description: "Percentage of users who adopt a new feature within 30 days"
         formula: "(Users using feature at day 30 / Total users) x 100"
         unit: percent
         source: external
         reporting: "Monthly percentage"
         cadence: monthly
         target: ">50%"
         visibility: venture
         added: "2026-03-24"
     ```

6. **Commit**
   - Stage `metrics/definitions.yaml`
   - Commit with message: `[metrics] Add custom metric: {display_name}` or `[metrics] Update metric: {display_name}`

## Output

Display:
```
Added custom metric: Feature Adoption Rate

  Name:       feature_adoption_rate
  Formula:    (Users using feature at day 30 / Total users) x 100
  Source:     external
  Reporting:  Monthly percentage
  Target:     >50%
  Visibility: venture (included in reports)

This metric will be included in the next /metrics/collect run.
Note: External data sources require manual input during collection.
```

## Error Handling

- **Metric name collision**: Suggest a different name
- **Missing required fields**: Prompt for each missing field
- **Editing non-existent metric**: List available custom metrics
- **Editing Core/Extended metric**: Refuse — these are defined by the standard
