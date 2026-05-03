// Mesh — value-to-tag map for the live ToolGraph.
// Per spec-delta frontend-core F-FE-6.
//
// Strategy: when an onboarding answer's `value` is a tool slug, the
// tags come from the baked MESH_TOOLS table inside ToolGraph.tsx.
// For role / friction questions the values are free-form labels;
// this module hand-maintains the lookup mirroring the design's
// hardcoded data.
//
// Drift risk: if the seed question bank changes option values,
// these maps go stale. Tests would not catch it (frontend has no
// tests in cycle #13). V1.5 considers a backend `tags: []` field on
// QuestionOption.

import { MESH_TOOLS } from "@/components/ToolGraph";

const TOOL_SLUG_TO_TAGS: Record<string, string[]> = Object.fromEntries(
  MESH_TOOLS.map((t) => [t.id, t.tags]),
);

// Hand-maintained — mirrors scratch/mesh-app/src/app/onboarding/page.tsx.
const VALUE_TO_TAGS: Record<string, string[]> = {
  // role.primary_function answer values
  marketing_ops: ["sales", "crm", "email"],
  design: ["design"],
  engineering: ["dev", "ai"],
  other: ["productivity"],

  // role/day-shape labels (in case backend uses these as values)
  "Writing & docs": ["writing", "docs"],
  "Shipping product": ["pm", "meetings"],
  "Code & building": ["dev", "ai"],
  "Design work": ["design"],
  "Sales & outreach": ["sales", "crm", "email"],
  "Bit of everything": ["productivity", "ai"],

  // friction labels
  "Switching between apps": ["productivity"],
  "Meetings & note-taking": ["meetings", "ai"],
  "Email triage": ["email"],
  "Manual research": ["research", "ai"],
  "Status updates": ["pm", "meetings"],
  "Drafting & rewriting": ["writing", "ai"],

  // attitude
  "I try everything": ["ai"],
  "Curious, overwhelmed": ["ai", "productivity"],
  "Tired of the hype": ["productivity"],
  "Strict — only if it sticks": ["productivity"],
};

export function tagsForOptionValue(value: string): string[] {
  if (!value) return [];
  // 1) Tool slug (cycle #10 F-TOOL-7 contract: multi_select tool
  // questions use slugs as option values).
  if (TOOL_SLUG_TO_TAGS[value]) return TOOL_SLUG_TO_TAGS[value];
  // 2) Hand-maintained label map.
  if (VALUE_TO_TAGS[value]) return VALUE_TO_TAGS[value];
  // 3) Fallback: lowercase the value as a single tag for the graph
  // (best-effort; better than empty).
  return [value.toLowerCase().replace(/[^a-z0-9]+/g, "-")];
}

export function tagsForAnswerValue(value: string | string[]): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((v) => tagsForOptionValue(v));
  }
  return tagsForOptionValue(value);
}
