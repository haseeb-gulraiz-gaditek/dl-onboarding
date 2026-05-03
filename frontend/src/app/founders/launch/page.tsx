"use client";

// Mesh — Founder launch flow.
// Per spec-delta frontend-core F-FE-8.
//
// 6-step form serializes onto cycle #8's POST /api/founders/launch:
//   product_url            → required, http(s)
//   problem_statement      ← pitch (or oneliner if pitch empty)
//   icp_description        ← concat of category + audience + pricing + replaces
//   existing_presence_links ← parsed CSV from a single text input
//   target_community_slugs ← clicked nodes on the live CommunityGraph (1..6)

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import {
  CommunityGraph,
  COMMUNITIES as MESH_COMMUNITIES,
} from "@/components/CommunityGraph";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { LaunchResponse, LaunchSubmitRequest } from "@/lib/api-types";

interface Opt { l: string; tags: string[] }
interface Field { id: string; kind: "text" | "longtext" | "pick" | "pick-multi"; label: string; placeholder?: string; opts?: Opt[]; required?: boolean }
interface Step { id: string; title: string; sub?: string; fields: Field[] }

const STEPS: Step[] = [
  {
    id: "product",
    title: "What are you building?",
    sub: "We need the URL — it's how the rest of Mesh links to you.",
    fields: [
      { id: "name", kind: "text", label: "Product name (display)", placeholder: "Granola, Linear, Reflect" },
      { id: "product_url", kind: "text", label: "Product URL (required)", placeholder: "https://example.com", required: true },
      { id: "oneliner", kind: "text", label: "One-liner", placeholder: "AI meeting notes that live next to your calendar" },
      { id: "presence", kind: "text", label: "Existing presence (CSV — X / LinkedIn / GitHub)", placeholder: "https://x.com/yours, https://github.com/yours" },
    ],
  },
  {
    id: "category",
    title: "Where does it fit?",
    fields: [
      {
        id: "category",
        kind: "pick",
        label: "Category",
        opts: [
          { l: "AI / agent", tags: ["ai"] },
          { l: "Writing & docs", tags: ["writing", "docs"] },
          { l: "PM / collaboration", tags: ["pm", "meetings"] },
          { l: "Dev tooling", tags: ["dev", "ai"] },
          { l: "Design tooling", tags: ["design"] },
          { l: "Sales / CRM / outreach", tags: ["sales", "crm", "email"] },
          { l: "Browser / productivity", tags: ["browser", "productivity"] },
        ],
      },
    ],
  },
  {
    id: "replaces",
    title: "What does it replace or sit next to?",
    fields: [
      {
        id: "replaces",
        kind: "pick-multi",
        label: "Tools (multi-pick)",
        opts: [
          { l: "Notion", tags: ["writing", "pm", "docs"] },
          { l: "Linear", tags: ["pm", "dev"] },
          { l: "Figma", tags: ["design"] },
          { l: "Cursor", tags: ["dev", "ai"] },
          { l: "ChatGPT", tags: ["ai"] },
          { l: "Gmail", tags: ["email"] },
          { l: "Slack", tags: ["messaging"] },
          { l: "Spreadsheets", tags: ["data"] },
        ],
      },
    ],
  },
  {
    id: "audience",
    title: "Who is it for, really?",
    fields: [
      {
        id: "audience",
        kind: "pick-multi",
        label: "Roles",
        opts: [
          { l: "Solo founders", tags: ["founders", "productivity"] },
          { l: "Staff PMs", tags: ["pm", "docs"] },
          { l: "Eng leads", tags: ["dev", "pm"] },
          { l: "Design leads", tags: ["design", "pm"] },
          { l: "Growth / marketers", tags: ["sales", "crm", "email"] },
          { l: "Researchers", tags: ["research", "ai"] },
        ],
      },
    ],
  },
  {
    id: "pricing",
    title: "How does it work, money-wise?",
    fields: [
      {
        id: "pricing",
        kind: "pick",
        label: "Pricing",
        opts: [
          { l: "Free / open source", tags: ["productivity"] },
          { l: "Freemium", tags: ["productivity"] },
          { l: "Per-seat SaaS", tags: ["pm"] },
          { l: "One-time / lifetime", tags: ["productivity"] },
          { l: "Usage-based", tags: ["ai", "dev"] },
        ],
      },
    ],
  },
  {
    id: "pitch",
    title: "What's your hook?",
    sub: "Becomes problem_statement. Skip if you'd rather we use the one-liner.",
    fields: [
      {
        id: "pitch",
        kind: "longtext",
        label: "Hook (optional)",
        placeholder: "Replaces the 40 minutes you lose every week to copy-pasting between Notion and Linear.",
      },
    ],
  },
];

type FieldValue = string | Opt | Opt[] | undefined;

export default function FoundersLaunchPage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  useEffect(() => {
    if (!isAuthenticated()) router.replace("/onboarding");
    else setAuthChecked(true);
  }, [router]);

  const [step, setStep] = useState(0);
  const [data, setData] = useState<Record<string, FieldValue>>({});
  const [pickedSlugs, setPickedSlugs] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<LaunchResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const tags = useMemo(() => {
    const t: string[] = [];
    Object.values(data).forEach((v) => {
      if (Array.isArray(v)) v.forEach((o) => o?.tags && t.push(...o.tags));
      else if (v && typeof v !== "string" && v.tags) t.push(...v.tags);
    });
    return t;
  }, [data]);

  const setFieldValue = (fieldId: string, val: FieldValue) =>
    setData((prev) => ({ ...prev, [fieldId]: val }));

  const toggleMulti = (fieldId: string, opt: Opt) => {
    setData((prev) => {
      const cur = Array.isArray(prev[fieldId]) ? (prev[fieldId] as Opt[]) : [];
      const exists = cur.find((o) => o.l === opt.l);
      const next = exists ? cur.filter((o) => o.l !== opt.l) : [...cur, opt];
      return { ...prev, [fieldId]: next };
    });
  };

  const total = STEPS.length;
  const cur = STEPS[step];

  const submit = async () => {
    const product_url = ((data.product_url as string) || "").trim();
    if (!product_url.startsWith("http")) {
      setErr("Product URL must start with http:// or https://.");
      return;
    }
    if (pickedSlugs.length === 0) {
      setErr("Pick at least one community by tapping nodes on the graph.");
      return;
    }
    if (pickedSlugs.length > 6) {
      setErr("Pick at most 6 communities.");
      return;
    }

    const oneliner = ((data.oneliner as string) || "").trim();
    const pitch = ((data.pitch as string) || "").trim();
    const problem_statement = pitch || oneliner || "Founder launch on Mesh.";

    const category = (data.category as Opt | undefined)?.l;
    const pricing = (data.pricing as Opt | undefined)?.l;
    const audience = ((data.audience as Opt[]) || []).map((o) => o.l);
    const replaces = ((data.replaces as Opt[]) || []).map((o) => o.l);

    const icp_description = [
      category && `Category: ${category}`,
      audience.length && `Audience: ${audience.join(", ")}`,
      pricing && `Pricing: ${pricing}`,
      replaces.length && `Replaces / sits next to: ${replaces.join(", ")}`,
    ]
      .filter(Boolean)
      .join("\n\n");

    const presenceCsv = ((data.presence as string) || "")
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.startsWith("http"));

    const payload: LaunchSubmitRequest = {
      product_url,
      problem_statement,
      icp_description: icp_description || "(see problem statement)",
      existing_presence_links: presenceCsv,
      target_community_slugs: pickedSlugs,
    };

    setErr(null);
    setSubmitting(true);
    try {
      const resp = await api.post<LaunchResponse>("/api/founders/launch", payload);
      setSubmitted(resp);
    } catch (e) {
      const msg = e instanceof ApiError
        ? typeof e.body === "object" && e.body && "detail" in e.body
          ? JSON.stringify((e.body as { detail: unknown }).detail)
          : "Submission failed."
        : "Submission failed.";
      setErr(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (!authChecked) return null;

  if (submitted) {
    return <PendingScreen launch={submitted} pickedSlugs={pickedSlugs} />;
  }

  return (
    <div className="onb-root founders-root">
      <div className="onb-graph-pane founders-graph-pane">
        <div className="onb-graph-canvas">
          <CommunityGraph tags={tags} gridSlots={6} scale={1.3} />
        </div>
        <div className="onb-graph-meta mono">
          <div className="onb-graph-meta-row">
            <span className="onb-graph-dot" />
            <span>
              {pickedSlugs.length === 0
                ? `tap nodes to pick target communities (1..6)`
                : `${pickedSlugs.length} community${pickedSlugs.length === 1 ? "" : " ies"} picked`}
            </span>
          </div>
          <CommunityPicker
            tags={tags}
            picked={pickedSlugs}
            onToggle={(slug) =>
              setPickedSlugs((prev) =>
                prev.includes(slug)
                  ? prev.filter((s) => s !== slug)
                  : prev.length < 6
                  ? [...prev, slug]
                  : prev,
              )
            }
          />
        </div>
      </div>

      <div className="onb-content-pane founders-content-pane">
        <header className="onb-header">
          <Link href="/" className="onb-brand">
            <MeshMark size={20} />
            <span>Mesh</span>
            <span className="founders-brand-tag mono">/ founders</span>
          </Link>
          <Link href="/home" className="onb-exit mono">
            save & exit
          </Link>
        </header>

        <div className="onb-q-wrap founders-step">
          <div className="onb-q-meta">
            <button
              className="onb-q-back mono"
              disabled={step === 0}
              onClick={() => setStep((s) => Math.max(0, s - 1))}
            >
              ← back
            </button>
            <span className="mono onb-q-count">
              Step {step + 1} of {total}
            </span>
            <div className="onb-q-bars">
              {Array.from({ length: total }).map((_, i) => (
                <span
                  key={i}
                  className={`onb-q-bar ${i < step ? "done" : i === step ? "on" : ""}`}
                />
              ))}
            </div>
          </div>

          <div className="onb-q-card founders-card">
            <h1 className="onb-q-title">{cur.title}</h1>
            {cur.sub && <p className="onb-q-sub">{cur.sub}</p>}

            <div className="founders-fields">
              {cur.fields.map((f) => (
                <FieldRow
                  key={f.id}
                  field={f}
                  value={data[f.id]}
                  onText={(v) => setFieldValue(f.id, v)}
                  onPick={(opt) => setFieldValue(f.id, opt)}
                  onToggle={(opt) => toggleMulti(f.id, opt)}
                />
              ))}
            </div>

            {err && (
              <div className="mono" style={{ color: "var(--warn)", marginTop: 16 }}>
                {err}
              </div>
            )}

            <div className="onb-q-multi-foot">
              <span className="mono onb-q-skip">your data stays — refine anytime ↘</span>
              {step < total - 1 ? (
                <MButton onClick={() => setStep((s) => s + 1)}>
                  Continue →
                </MButton>
              ) : (
                <MButton onClick={submit} variant="primary">
                  {submitting ? "Submitting…" : `Submit launch (${pickedSlugs.length}) →`}
                </MButton>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FieldRow({
  field,
  value,
  onText,
  onPick,
  onToggle,
}: {
  field: Field;
  value: FieldValue;
  onText: (v: string) => void;
  onPick: (opt: Opt) => void;
  onToggle: (opt: Opt) => void;
}) {
  if (field.kind === "text") {
    return (
      <div className="founders-field">
        <label className="founders-label mono">
          {field.label}
          {field.required && (
            <span className="founders-label-hint" style={{ color: "var(--accent)" }}>
              *
            </span>
          )}
        </label>
        <input
          className="m-input founders-input"
          placeholder={field.placeholder}
          value={(value as string) || ""}
          onChange={(e) => onText(e.target.value)}
        />
      </div>
    );
  }
  if (field.kind === "longtext") {
    return (
      <div className="founders-field">
        <label className="founders-label mono">{field.label}</label>
        <textarea
          className="m-input founders-input founders-textarea"
          placeholder={field.placeholder}
          value={(value as string) || ""}
          rows={3}
          onChange={(e) => onText(e.target.value)}
        />
      </div>
    );
  }
  if (field.kind === "pick") {
    const v = value as Opt | undefined;
    return (
      <div className="founders-field">
        <label className="founders-label mono">{field.label}</label>
        <div className="onb-q-opts">
          {field.opts!.map((opt, i) => {
            const picked = v && v.l === opt.l;
            return (
              <button
                key={opt.l}
                className={`onb-q-opt ${picked ? "on" : ""}`}
                onClick={() => onPick(opt)}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <span className="onb-q-bullet">
                  <span className="onb-radio">
                    {picked ? <span className="onb-radio-dot" /> : null}
                  </span>
                </span>
                <span className="onb-q-label">{opt.l}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }
  if (field.kind === "pick-multi") {
    const arr = Array.isArray(value) ? (value as Opt[]) : [];
    return (
      <div className="founders-field">
        <label className="founders-label mono">
          {field.label} <span className="founders-label-hint">multi-select</span>
        </label>
        <div className="founders-chips">
          {field.opts!.map((opt, i) => {
            const picked = arr.find((o) => o.l === opt.l);
            return (
              <button
                key={opt.l}
                className={`founders-chip ${picked ? "on" : ""}`}
                onClick={() => onToggle(opt)}
                style={{ animationDelay: `${i * 30}ms` }}
              >
                <span className="founders-chip-check">{picked ? "✓" : "+"}</span>
                <span>{opt.l}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
}

// =============================================================================
// Community picker — text-list overlay on the graph for explicit selection.
// =============================================================================
function CommunityPicker({
  tags,
  picked,
  onToggle,
}: {
  tags: string[];
  picked: string[];
  onToggle: (slug: string) => void;
}) {
  const ranked = useMemo(() => {
    const tagSet = new Set(tags);
    return [...MESH_COMMUNITIES]
      .map((c) => ({
        ...c,
        slug: c.id,
        overlap: c.tags.filter((t) => tagSet.has(t)).length,
      }))
      .sort((a, b) => b.overlap - a.overlap || b.members - a.members)
      .slice(0, 8);
  }, [tags]);

  return (
    <div className="onb-graph-tags" style={{ marginTop: 12 }}>
      {ranked.map((c) => {
        const isPicked = picked.includes(c.slug);
        return (
          <button
            key={c.slug}
            className="onb-graph-tag"
            style={{
              cursor: "pointer",
              background: isPicked ? "var(--accent-soft)" : undefined,
              color: isPicked ? "var(--ink-0)" : undefined,
              border: isPicked ? "1px solid var(--accent)" : undefined,
            }}
            onClick={() => onToggle(c.slug)}
            title={c.name}
          >
            {isPicked ? "✓ " : "+ "}
            {c.name}
          </button>
        );
      })}
    </div>
  );
}

// =============================================================================
// Pending screen
// =============================================================================
function PendingScreen({
  launch,
  pickedSlugs,
}: {
  launch: LaunchResponse;
  pickedSlugs: string[];
}) {
  return (
    <div className="onb-root founders-root">
      <div className="onb-graph-pane founders-graph-pane">
        <div className="onb-graph-canvas">
          <CommunityGraph tags={[]} gridSlots={pickedSlugs.length} scale={1.2} />
        </div>
      </div>
      <div className="onb-content-pane founders-content-pane">
        <header className="onb-header">
          <Link href="/home" className="onb-brand">
            <MeshMark size={20} />
            <span>Mesh</span>
          </Link>
        </header>
        <div className="onb-result founders-result">
          <div className="onb-result-eyebrow mono">/ submission received</div>
          <h1 className="onb-result-title">
            <em>{launch.product_url}</em>
            <br />
            is in the queue.
          </h1>
          <p className="onb-result-sub body-lg">
            Mesh staff verifies launches within ~24 hours. We&apos;ll notify
            you when it&apos;s approved — at that point your launch fans into
            your {pickedSlugs.length} target communities and the matched-user
            concierge nudge fires.
          </p>
          <div className="onb-result-cta in">
            <Link href="/home">
              <MButton size="lg" trailing="→">
                Back to home
              </MButton>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
