---
description: Execute an approved integration plan to update course materials
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Execute an approved integration plan, implementing all specified changes across reference docs, course modules, resources, templates, and flagging slides for regeneration.

## Input Parsing

Parse the user input for:
- **Plan Path** (required): Path to the integration plan file
  - Expected format: `WIP/ingestions/{slug}/integration-plan.md`

## Workflow Phases

### Phase 1: Plan Validation

**Actions:**
1. Read the integration plan file
2. Verify it exists and has expected structure
3. Parse all action items into a structured list
4. Verify referenced files exist (for updates)
5. Check that new file paths don't already exist

**Output:** Validated action item list

### Phase 2: Load Source Knowledge

**Actions:**
1. Extract the slug from plan path
2. Read the corresponding extraction report: `WIP/ingestions/{slug}/extraction-report.md`
3. Parse key knowledge elements for reference during implementation

**Output:** Source knowledge loaded

### Phase 3: Execute Integration

Execute in the order specified in the plan:

#### Phase 3a: Reference Documentation

For each reference doc action:

1. **New Document:**
   ```
   - Create file at specified path
   - Use knowledge from extraction report
   - Follow existing doc patterns in content/reference/engineering/
   - Include proper frontmatter and structure
   ```

2. **Update Existing:**
   ```
   - Read the existing file
   - Locate the specified section
   - Apply the change (add/update/expand)
   - Maintain consistent formatting
   ```

**Output:** Reference docs updated

#### Phase 3b: Course Modules

For each course module action:

1. **New Section:**
   ```
   - Read the existing module
   - Locate insertion point (after specified section)
   - Add new section with proper heading level
   - Include content from extraction report
   - Maintain module formatting patterns
   ```

2. **Update Content:**
   ```
   - Read the existing module
   - Locate the section to update
   - Apply changes while preserving structure
   - Update any related cross-references
   ```

3. **New Example:**
   ```
   - Read existing module
   - Find appropriate example section
   - Add new example with context
   - Include code blocks if applicable
   ```

**Output:** Course modules updated

#### Phase 3c: Resources and Templates

For each resource/template action:

1. **New Resource:**
   ```
   - Create file at specified path
   - Follow patterns from existing resources in same course
   - Include proper structure and formatting
   ```

2. **Update Resource/Template:**
   ```
   - Read existing file
   - Apply specified changes
   - Maintain existing patterns
   ```

**Output:** Resources and templates updated

#### Phase 3d: Slides Flagging

For each slide regeneration needed:

1. Create/update a file: `WIP/ingestions/{slug}/slides-to-regenerate.md`
2. List all modules whose slides need regeneration
3. Include the reason for each

**Output:** Slides flagged for regeneration

### Phase 4: Implementation Log

**Actions:**
1. Create implementation log: `WIP/ingestions/{slug}/implementation-log.md`
2. Record all changes made:
   - Files created
   - Files modified (with diff summary)
   - Any issues encountered
3. Update integration plan checklist (mark items complete)

### Phase 4b: Changelog Entry

**Actions:**
1. Create a changelog entry file: `content/changelog/YYYY-MM-DD-{source-slug}-integration.md`
2. Use the following frontmatter template:
   ```yaml
   ---
   title: "{Source Name} — Knowledge Integration"
   date: YYYY-MM-DD
   type: integration
   courses:
     - {affected-course-slug-1}
     - {affected-course-slug-2}
   standards: []
   source: "{source URL or reference if available}"
   ---
   ```
3. Write two required sections:
   - `## What changed` — summarize what knowledge was integrated and which modules were updated
   - `## What it means` — explain how the new knowledge improves or extends the curriculum

**Output:** Changelog entry created

## Implementation Approach

### Content Generation Guidelines

When adding content from the extraction report:

1. **Adapt, don't copy** - Rewrite in our course style
2. **Add context** - Explain why this matters
3. **Include examples** - Concrete illustrations
4. **Link appropriately** - Cross-reference related content
5. **Match voice** - Follow existing content tone

### File Modification Safety

1. Always read files before modifying
2. Use Edit tool for targeted changes
3. Preserve existing formatting
4. Don't remove unrelated content
5. Test that markdown renders correctly

### Terminology Alignment

Follow the conflict resolution from the integration plan:
- Use existing terms when specified
- Introduce new terms with definition if adopting
- Note both terms if keeping both

## Output Format

### Implementation Log Template

```markdown
# Implementation Log: {source-slug}

## Execution Summary

| Metric | Value |
|--------|-------|
| Execution Date | {YYYY-MM-DD HH:MM} |
| Integration Plan | {plan-path} |
| Status | Complete/Partial |

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| {path} | {purpose} | {n} |

## Files Modified

| File | Section | Change Type | Summary |
|------|---------|-------------|---------|
| {path} | {section} | Added/Updated | {brief description} |

## Slides Flagged

| Course | Module | Reason |
|--------|--------|--------|
| {course} | {module} | Content updated |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| {if any} | {how handled} |

## Next Steps

1. Review changes for accuracy
2. Run `/slides:generate-module-slides` for flagged modules
3. Consider running related tests
```

## Completion

Report to user:

```markdown
## Integration Complete

### Summary
- Files created: {n}
- Files modified: {n}
- Slides flagged: {n}

### Changes Made
{List top 5 most significant changes}

### Implementation Log
`WIP/ingestions/{slug}/implementation-log.md`

### Next Steps
1. Review the changes made
2. Regenerate slides for affected modules:
   {list commands for each flagged module}
3. Run any relevant tests
4. Commit changes if satisfied
```

## Error Handling

### File Not Found
- Skip the action
- Log the error
- Continue with remaining actions
- Report in summary

### Content Conflict
- Log the conflict
- Skip the specific change
- Note in implementation log
- User can resolve manually

### Write Failure
- Log the error
- Attempt rollback if partial
- Report what succeeded and what failed
