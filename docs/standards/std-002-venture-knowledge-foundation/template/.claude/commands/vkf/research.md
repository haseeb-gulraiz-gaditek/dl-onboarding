---
description: Research market data for constitution sections -- competitors, personas, positioning, PMF validation. Uses exa.ai when available, falls back to WebSearch/WebFetch.
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS**: Research topic or constitution section
  - Section names: `positioning`, `icps`, `personas`, `pmf-thesis`, `competitors`
  - Freeform: any research topic (e.g., "developer tools market 2026", "B2B SaaS pricing")

## Actions

1. **Select Research Backend**
   - Check if `EXA_API_KEY` is set in the environment (check `.env` file if env var is not directly available)
   - If key found: use **exa.ai** as the research backend (higher quality neural search)
   - If key NOT found: use the **AskUserQuestion** tool to ask:
     - "No EXA_API_KEY found. Would you like to set up exa.ai for higher-quality research, or continue with standard web search?"
     - Options: "Continue with web search" / "Set up exa.ai"
   - If user chooses "Set up exa.ai", display setup instructions and pause:
     ```
     To set up exa.ai:
     1. Get an API key at https://exa.ai
     2. Add to .env: EXA_API_KEY=your-key
     3. Run this command again
     ```
   - If user chooses "Continue with web search": proceed using **WebSearch** and **WebFetch** tools as the research backend

2. **Read Constitution Context**
   - Read relevant constitution file(s) to understand existing content
   - Identify gaps that research could fill

3. **Present Query Plan**
   - Before executing any searches, show the user what will be searched:
     ```
     Research Plan: Competitive Landscape
     =====================================
     I'll search for:
       1. "[product category] competitors 2026" (search + contents)
       2. "[competitor name] vs alternatives" (search + contents)
       3. "[product category] market landscape" (search + contents)

     Estimated: 3 API calls

     Proceed? (y/n)
     ```
   - Wait for user confirmation before executing

4. **Execute Research**

   **If using exa.ai:**
   - Use exa.ai search endpoint for discovery:
     ```
     POST https://api.exa.ai/search
     {
       "query": "{search query}",
       "numResults": 5,
       "type": "neural",
       "useAutoprompt": true
     }
     ```
   - Use exa.ai contents endpoint for detail:
     ```
     POST https://api.exa.ai/contents
     {
       "ids": ["{result_ids}"],
       "text": { "maxCharacters": 2000 }
     }
     ```

   **If using web search:**
   - Use the **WebSearch** tool with the same queries from the query plan
   - For each promising result, use **WebFetch** to extract detailed content
   - Aim for the same depth: 3-5 sources per query, extract key data points

5. **Synthesize Findings**
   - Organize findings by relevance to the constitution section
   - Extract key data points: names, numbers, quotes, patterns
   - Format as suggestions that map to constitution template fields

6. **Present Results**
   - Show synthesized findings with source attribution
   - Suggest specific content for constitution placeholders
   - Offer to apply findings directly to constitution files

## Section-Specific Research

### positioning
Searches:
- "[product category] competitors [year]"
- "[product name] alternatives"
- "[product category] market size"
- "[competitor] strengths weaknesses"

Output maps to: Competitive Landscape table, Moat/Defensibility, Category

### icps
Searches:
- "[product category] ideal customer"
- "[industry] [product category] adoption"
- "[product category] buyer persona B2B"

Output maps to: Company Size, Industry, Buying Trigger, Decision Maker

### personas
Searches:
- "[job title] workflow [product category]"
- "[job title] pain points [domain]"
- "[job title] tools stack [year]"

Output maps to: Role, Goals, Pain Points, Current Workflow

### pmf-thesis
Searches:
- "[product category] product market fit signals"
- "[problem domain] market validation"
- "[customer segment] buying behavior"

Output maps to: Evidence, Key Assumptions, Invalidation Criteria

### competitors (standalone)
Searches:
- "[product name] vs [competitor]"
- "[product category] comparison [year]"
- "[product category] market leader"

Output: Competitive analysis brief

## Output Format

```
Research Results: Competitive Landscape
=======================================
Sources: 5 articles analyzed

Key Findings:

1. Direct Competitors:
   - CompetitorA: [summary] (source: url)
   - CompetitorB: [summary] (source: url)

2. Market Positioning Insights:
   - [Finding with source attribution]

3. Suggested Constitution Updates:

   For positioning.md > Competitive Landscape:
   | Competitor | Category | Strengths | Weaknesses | Our Advantage |
   |-----------|----------|-----------|------------|---------------|
   | CompetitorA | [Cat] | [Str] | [Weak] | [Suggested] |

   For positioning.md > Category:
   "[Suggested category positioning based on research]"

Apply these suggestions to specs/constitution/positioning.md? (y/n)
```

## Error Handling

- **No API key**: Ask user via AskUserQuestion whether to set up exa.ai or continue with web search (see step 1)
- **Exa API rate limit**: Wait and retry once, then fall back to web search
- **Exa API error**: Fall back to web search, note the fallback in output
- **No results**: Suggest alternative search terms, try the other backend if available
- **User declines plan**: Exit without making any calls
- **Partial results**: Present what was found, note gaps
