---
description: Extract knowledge from a URL and create an integration plan for course materials
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Take a URL, extract structured knowledge from it, and create a comprehensive integration plan specifying where and how the knowledge should be incorporated across the course materials ecosystem (reference docs, courses, modules, slides, templates).

## Input Parsing

Parse the user input for:
- **URL** (required): The URL to ingest
- **--focus** (optional): Specific topic focus to prioritize
- **--scope** (optional): Limit to specific course(s)

Examples:
- `https://example.com/article`
- `https://example.com/article --focus="workflow automation"`
- `https://example.com/article --scope=claude-code`

## Workflow Phases

### Phase 1: Setup and Validation

**Actions:**
1. Parse input to extract URL and options
2. Validate URL format
3. Generate a slug from the URL for output directory:
   - Use domain + path, sanitized (e.g., `example-com-article-name`)
   - Truncate to reasonable length (50 chars max)
4. Create output directory: `WIP/ingestions/{slug}/`

**Output:** Slug and output path confirmed

### Phase 2: Knowledge Extraction

**Actions:**
1. Use Task tool to spawn `url-knowledge-extractor` agent:

```
Task: Extract structured knowledge from URL

Agent: url-knowledge-extractor

URL: {url}
Focus: {focus if provided, otherwise "general"}

Instructions:
1. Fetch the URL content using WebFetch
2. Identify the content type (article, docs, tutorial, research, repo)
3. Extract all knowledge components following your output format
4. Assess relevance to each course domain
5. Cross-reference with existing content in the repository
6. Return the complete extraction report

If the URL fails to fetch, try:
- WebSearch to find cached/alternative versions
- Return partial report with note about access issues
```

2. Receive extraction report from agent
3. Save to `WIP/ingestions/{slug}/extraction-report.md`

**Output:** Extraction report saved

### Phase 3: Integration Planning

**Actions:**
1. Use Task tool to spawn `integration-planner` agent:

```
Task: Create integration plan for extracted knowledge

Agent: integration-planner

Extraction Report Path: WIP/ingestions/{slug}/extraction-report.md

Instructions:
1. Read the extraction report thoroughly
2. For each high/medium relevance domain:
   - Search existing reference docs for related content
   - Search course modules for integration points
   - Check resources and templates
3. Identify all integration opportunities
4. Flag any conflicts or terminology issues
5. Create prioritized action items
6. Define implementation order
7. Return the complete integration plan

Focus on:
- Specific file paths and section locations
- Clear action descriptions
- Realistic scope per item
```

2. Receive integration plan from agent
3. Save to `WIP/ingestions/{slug}/integration-plan.md`

**Output:** Integration plan saved

### Phase 4: Summary and Next Steps

**Actions:**
1. Read both generated files
2. Create summary for user including:
   - Source summary
   - Top integration opportunities
   - Estimated scope
   - Next steps

## Output Structure

```
WIP/ingestions/{slug}/
├── extraction-report.md    # Structured knowledge from URL
└── integration-plan.md     # Where/how to integrate
```

## Agent Delegation Summary

| Phase | Agent | Effort | Purpose |
|-------|-------|--------|---------|
| 2 | url-knowledge-extractor | high | Fetch URL and extract structured knowledge |
| 3 | integration-planner | high | Analyze ecosystem and create integration plan |

## Completion

Report to user:

```markdown
## Knowledge Ingestion Complete

### Source
- **URL:** {url}
- **Type:** {content type from extraction}
- **Confidence:** {extraction confidence}

### Summary
{2-3 sentence summary from extraction report}

### Top Integration Opportunities
1. {highest priority integration point}
2. {second priority}
3. {third priority}

### Scope
- New files to create: {n}
- Existing files to update: {n}
- Slides to regenerate: {n}

### Output Files
- Extraction Report: `WIP/ingestions/{slug}/extraction-report.md`
- Integration Plan: `WIP/ingestions/{slug}/integration-plan.md`

### Next Steps
1. Review the integration plan
2. Approve or modify priorities
3. Run: `/knowledge:apply-integration WIP/ingestions/{slug}/integration-plan.md`
```

## Error Handling

### URL Fetch Failure
- Report the error clearly
- Suggest checking URL accessibility
- Offer to try WebSearch for alternatives

### Empty/Minimal Content
- Report low extraction confidence
- Still generate reports with available content
- Note limitations in summary

### No Relevant Integration Points
- Generate extraction report normally
- Create minimal integration plan
- Report that content may not be applicable to current courses
