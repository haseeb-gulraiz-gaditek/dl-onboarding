# Catalog Research Prompt — Mesh AI Tool Catalog

> **How to use:** copy everything below the `---` (start of the prompt section) and paste it into another AI assistant (ChatGPT, Claude, Gemini, Perplexity). The agent should return a single JSON array of 300 tool entries. Save the agent's output verbatim as `app/seed/catalog.json` in this repo, then run `python -m app.seed catalog`.
>
> **Reference date:** when this prompt is run, the agent should treat "today" as the current real date. The current intended reference is **2026-05-01**.
>
> **If the response is too long for one reply:** the agent should output the array in numbered chunks ("Part 1 of N"). Concatenate the inner arrays into a single JSON array before saving.

---

You are an AI tool researcher producing a curated discovery catalog. Your output will be loaded into a recommendation engine that matches tools to users based on their workflow profile. Output 300 high-quality, real, currently-available AI tools.

## Output

Produce a single JSON array. **No surrounding markdown, no explanatory prose, no code fences. Just the array.** If the response is too long, split into numbered parts (`Part 1 of N`) where each part is itself a valid JSON array; the array contents will be concatenated.

## Distribution (must hit these counts as closely as possible)

- **150 entries** with `labels: ["all_time_best"]` — established, widely-adopted tools that have been notable for ≥ 12 months.
- **100 entries** with `labels: ["gaining_traction"]` — tools that have meaningfully grown in adoption or buzz over the last ~6 months.
- **50 entries** with `labels: ["new"]` — tools launched within the last ~30 days from the reference date.

A single tool may carry multiple labels if all genuinely apply (e.g., a tool launched in the last 30 days that has already gained meaningful traction can have both `new` and `gaining_traction`).

## Required fields per entry (no other fields, no extras)

| Field | Type | Description |
|---|---|---|
| `slug` | string, lowercase, hyphen-separated | Stable identifier. Derive from product name. Examples: `chatgpt`, `midjourney`, `perplexity-ai`. |
| `name` | string | Official product name as the company writes it. |
| `tagline` | string ≤ 120 chars | One-sentence summary of what the tool does. |
| `description` | string, 2–4 sentences | Explain WHAT the tool does and WHO it's for. Wirecutter-listing tone, not press release. |
| `url` | string | Official product URL. Must be a real URL the company controls — not an affiliate or aggregator link. |
| `pricing_summary` | string | Short pricing summary. Examples: `"Free"`, `"Free + $20/mo Pro"`, `"$10–$50/mo by tier"`, `"Enterprise pricing only"`, `"$0.002 per 1K tokens"`, or `"See website"` if unknown. **Never invent a number.** |
| `category` | string (single value, from the closed enum below) | One category per tool. |
| `labels` | array of strings | Subset of `["all_time_best", "gaining_traction", "new"]`. At least one. |

## Category enum (closed list — pick exactly one)

- `productivity` — task management, notes, project tracking
- `writing` — text generation, editing, long-form content
- `design` — visual design, UI, graphics
- `engineering` — code editors, debugging, dev assistants
- `research_browsing` — search, web research, summarization
- `meetings` — recording, transcription, meeting AI
- `marketing` — campaigns, copy, social, audience tools
- `sales` — outreach, CRM AI, prospecting
- `analytics_data` — data analysis, BI, dashboards
- `finance` — accounting, budgeting, financial analysis
- `education` — learning, tutoring, study tools
- `creative_video` — image, video, audio, music generation
- `automation_agents` — workflow automation, agent platforms, MCP servers

If a tool spans multiple categories, pick the single most representative one.

## Quality requirements

1. **All entries must be real, currently-available tools.** Do not invent tools. If uncertain about a specific tool, omit it rather than guess.
2. **URLs must be the actual official URL.** Not affiliate links, not "best-of" articles.
3. **Pricing must reflect what the company publishes today.** If pricing is unknown or hard to verify, use `"See website"` — never fabricate a number.
4. **Descriptions say what the tool does**, not why it's "revolutionary". Avoid superlatives.
5. **No duplicates.** Every `slug` is unique within the array.
6. **Slugs are stable.** A tool's slug should not depend on its tagline or pricing — it's the canonical identifier.

## Two complete example entries (for reference; do not include these in your output unless they are genuinely real)

```json
[
  {
    "slug": "chatgpt",
    "name": "ChatGPT",
    "tagline": "OpenAI's general-purpose conversational assistant.",
    "description": "Chat-based interface to OpenAI's GPT family of models. Used for writing, brainstorming, coding help, summarization, and ad-hoc research. Free tier available; paid plans add access to newer models, longer context, and image generation.",
    "url": "https://chat.openai.com",
    "pricing_summary": "Free + $20/mo Plus + Team & Enterprise tiers",
    "category": "productivity",
    "labels": ["all_time_best"]
  },
  {
    "slug": "granola",
    "name": "Granola",
    "tagline": "AI meeting note-taker that listens and writes notes you would have written.",
    "description": "Records meetings with consent, transcribes them, and produces structured notes mapped to your meeting agenda. Designed for product, sales, and exec workflows where meeting follow-through is the bottleneck. Mac-only as of the reference date.",
    "url": "https://www.granola.ai",
    "pricing_summary": "Free + $18/mo Pro",
    "category": "meetings",
    "labels": ["gaining_traction"]
  }
]
```

## Final output instruction

Return a single JSON array containing 300 entries matching the distribution and schema above. Nothing else.
