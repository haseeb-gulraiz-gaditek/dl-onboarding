---
description: Interactive constitution drafting -- walk through each section, fill placeholders, optionally research with exa.ai
version: "2.0-rc"
---

## Arguments

- **$ARGUMENTS** (optional): Target a specific section
  - No argument: walk through all sections with `[REQUIRED]` placeholders
  - Section name: `personas`, `icps`, `positioning`, `mission`, `pmf-thesis`, `principles`, `governance`

## Actions

1. **Assess Current State**
   - Read all files in `specs/constitution/` (or the configured `constitution_root`)
   - For each file, check for `[REQUIRED]` placeholders
   - If targeting a specific section, focus on that file only
   - If no argument, prioritize files with the most placeholders

2. **Interactive Drafting (per section)**

   For each constitution file that needs work:

   a. **Show Context**
      - Display the file's current content
      - Highlight `[REQUIRED]` placeholders
      - Show the section's purpose from the constitution guide

   b. **Gather Input**
      - Ask the user targeted questions for each `[REQUIRED]` field
      - Offer to use exa.ai research for market-facing sections (positioning, ICPs, personas)
      - Accept freeform input and help structure it into the template format

   c. **Draft Content**
      - Replace `[REQUIRED]` placeholders with user-provided content
      - Format according to the template structure
      - Show draft for user review before saving

   d. **Save and Commit**
      - Write updated file
      - Update `Last amended` date to today
      - Commit with message: `[constitution] Draft {section name}`

3. **Update Index**
   - After drafting, update `specs/constitution/index.md`:
     - Update one-line summary for the completed section
     - Change status from "Draft" to "Active"
   - Commit: `[constitution] Update constitution index`

4. **Update State**
   - Record constitution review timestamp in `.claude/state/vkf-state.yaml`

## Section-Specific Guidance

### mission
Questions to ask:
- "What does your product do in one sentence?"
- "Who is it for?"
- "Where do you see this in 3-5 years?"
- "Why does this matter right now?"

### pmf-thesis
Questions to ask:
- "Who is your primary customer? (job title, company type)"
- "What problem are they trying to solve?"
- "How does your product solve it differently?"
- "What's your strongest evidence of product-market fit?"
- "What stage would you say you're at: Pre-PMF, Approaching, or Post-PMF?"

Offer: "Want me to research market evidence with exa.ai?"

### personas
Questions to ask:
- "Who are the 2-3 main types of users?"
- For each: "What's their role? Goals? Biggest frustration?"
- "How do they solve this problem today without your product?"
- "How often would they use it?"

Offer: "Want me to research typical workflows for this role?"

### icps
Questions to ask:
- "What size companies are the best fit?"
- "What industries?"
- "What triggers them to look for a solution like yours?"
- "Who signs the check? Who champions it internally?"
- "What's a red flag that a company is NOT a good fit?"

Offer: "Want me to research companies in this segment?"

### positioning
Questions to ask:
- "Who are your top 2-3 competitors (direct or indirect)?"
- "What do you do better than them?"
- "What category does your product belong to?"
- "What's your primary defensibility / moat?"

Offer: "Want me to research your competitive landscape?"

### principles
Questions to ask:
- "What will your product ALWAYS do, no matter what?"
- "What will it NEVER do?"
- "When two good things conflict, which wins?" (give examples)
- "What are your top 3 design tenets?"

### governance
Questions to ask:
- "Who makes decisions about new features?"
- "Who decides on breaking changes or deprecations?"
- "How should constitution amendments be proposed and approved?"
- "Is there existing decision-making structure to document?"

## Output

After completing a section:
```
Updated: specs/constitution/personas.md
  - Filled 7 [REQUIRED] sections
  - Added 2 personas: "Startup CTO" and "Enterprise Dev Lead"
  - Last amended: 2026-02-26

Committed: [constitution] Draft personas

Remaining [REQUIRED] sections across constitution:
  - icps.md: 8 placeholders
  - positioning.md: 6 placeholders

Next: /vkf/constitution icps
```

## Error Handling

- **No constitution directory**: Suggest running `/vkf/init` first
- **File not found**: Offer to create it from template
- **No placeholders remaining**: Report section is complete, offer to review and refine
- **Exa.ai not available**: Skip research offers, guide manual input instead
