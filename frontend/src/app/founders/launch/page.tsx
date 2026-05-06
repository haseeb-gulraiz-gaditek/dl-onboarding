"use client";

// Mesh — Founder launch flow (rewritten cycle #13 audit pass).
//
// Backend takes 5 fields (cycle #8 + #9):
//   product_url, problem_statement, icp_description,
//   existing_presence_links[], target_community_slugs (1..6).
//
// Form is 5 steps + a community picker. Per-step "Continue" gates
// on that step's required fields so the user never gets a step-1
// validation error on the last step.
//   Step 1: name + URL + oneliner + presence (URL validated inline)
//   Step 2: category
//   Step 3: ICP — 3 text fields (who, doing what, broken today)
//   Step 4: pricing
//   Step 5: pitch (one-liner) — final step, contains submit
// Communities are picked by tapping nodes on the graph at any time;
// the chip row near the submit button surfaces the count.

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { CommunityGraph } from "@/components/CommunityGraph";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type {
  CommunityCard,
  CommunityListResponse,
  LaunchResponse,
  LaunchSubmitRequest,
} from "@/lib/api-types";

const CATEGORY_OPTS = [
  { l: "AI / agent", tags: ["ai"] },
  { l: "Writing & docs", tags: ["writing", "docs"] },
  { l: "PM / collaboration", tags: ["pm", "meetings"] },
  { l: "Dev tooling", tags: ["dev", "ai"] },
  { l: "Design tooling", tags: ["design"] },
  { l: "Sales / CRM / outreach", tags: ["sales", "crm", "email"] },
  { l: "Browser / productivity", tags: ["browser", "productivity"] },
];

const PRICING_OPTS = [
  { l: "Free / open source", tags: ["productivity"] },
  { l: "Freemium", tags: ["productivity"] },
  { l: "Per-seat SaaS", tags: ["pm"] },
  { l: "One-time / lifetime", tags: ["productivity"] },
  { l: "Usage-based", tags: ["ai", "dev"] },
];

interface State {
  // step 1
  name: string;
  product_url: string;
  oneliner: string;
  presence: string;
  // step 2
  category: string | null;
  // step 3 — ICP
  icp_who: string;
  icp_jtbd: string;
  icp_pain: string;
  // step 4
  pricing: string | null;
  // step 5
  pitch: string;
}

const EMPTY: State = {
  name: "",
  product_url: "",
  oneliner: "",
  presence: "",
  category: null,
  icp_who: "",
  icp_jtbd: "",
  icp_pain: "",
  pricing: null,
  pitch: "",
};

const TOTAL_STEPS = 5;

const isHttp = (s: string) => s.startsWith("http://") || s.startsWith("https://");

export default function FoundersLaunchPage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
    else setAuthChecked(true);
  }, [router]);

  const [step, setStep] = useState(1);
  const [data, setData] = useState<State>(EMPTY);
  const [pickedSlugs, setPickedSlugs] = useState<string[]>([]);
  const [communities, setCommunities] = useState<CommunityCard[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<LaunchResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Fetch the real community catalog from backend (cycle #7).
  useEffect(() => {
    if (!authChecked) return;
    (async () => {
      try {
        const r = await api.get<CommunityListResponse>("/api/communities");
        setCommunities(r.communities);
      } catch (e) {
        console.error("[founders/launch] community list load failed", e);
      }
    })();
  }, [authChecked]);

  const set = <K extends keyof State>(k: K, v: State[K]) =>
    setData((prev) => ({ ...prev, [k]: v }));

  // Live tags for the CommunityGraph (drives match suggestions).
  const tags = useMemo(() => {
    const t: string[] = [];
    const cat = CATEGORY_OPTS.find((c) => c.l === data.category);
    if (cat) t.push(...cat.tags);
    const pr = PRICING_OPTS.find((p) => p.l === data.pricing);
    if (pr) t.push(...pr.tags);
    return t;
  }, [data.category, data.pricing]);

  // Per-step gating.
  const canAdvance = (s: number): boolean => {
    if (s === 1) {
      if (!data.name.trim()) return false;
      if (!isHttp(data.product_url.trim())) return false;
      return true;
    }
    if (s === 2) return !!data.category;
    if (s === 3) {
      // At least one ICP field non-empty.
      return !!(data.icp_who.trim() || data.icp_jtbd.trim() || data.icp_pain.trim());
    }
    if (s === 4) return !!data.pricing;
    if (s === 5)
      return data.pitch.trim().length > 0 && pickedSlugs.length > 0;
    return true;
  };

  const submit = async () => {
    setErr(null);
    if (pickedSlugs.length === 0) {
      setErr("Tap at least one community on the graph to target.");
      return;
    }
    const icp_description = [
      data.icp_who.trim() && `Who: ${data.icp_who.trim()}`,
      data.icp_jtbd.trim() && `Job to be done: ${data.icp_jtbd.trim()}`,
      data.icp_pain.trim() && `Today's pain: ${data.icp_pain.trim()}`,
    ]
      .filter(Boolean)
      .join("\n\n");

    const presence = data.presence
      .split(",")
      .map((s) => s.trim())
      .filter(isHttp);

    const payload: LaunchSubmitRequest = {
      product_url: data.product_url.trim(),
      problem_statement: data.pitch.trim() || data.oneliner.trim() || "Founder launch.",
      icp_description: icp_description || data.oneliner.trim() || "(see hook)",
      existing_presence_links: presence,
      target_community_slugs: pickedSlugs,
    };

    setSubmitting(true);
    try {
      const resp = await api.post<LaunchResponse>("/api/founders/launch", payload);
      setSubmitted(resp);
    } catch (e) {
      const msg = e instanceof ApiError && typeof e.body === "object" && e.body && "detail" in e.body
        ? JSON.stringify((e.body as { detail: unknown }).detail)
        : "Submission failed.";
      setErr(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (!authChecked) return null;
  if (submitted) return <PendingScreen launch={submitted} pickedSlugs={pickedSlugs} />;

  const togglePicked = (slug: string) =>
    setPickedSlugs((prev) =>
      prev.includes(slug)
        ? prev.filter((s) => s !== slug)
        : prev.length < 6
        ? [...prev, slug]
        : prev,
    );

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
                ? "matching communities…"
                : `${pickedSlugs.length} of 6 picked — see step 5 to choose`}
            </span>
          </div>
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
              disabled={step === 1}
              onClick={() => setStep((s) => Math.max(1, s - 1))}
            >
              ← back
            </button>
            <span className="mono onb-q-count">
              Step {step} of {TOTAL_STEPS}
            </span>
            <div className="onb-q-bars">
              {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
                <span
                  key={i}
                  className={`onb-q-bar ${i + 1 < step ? "done" : i + 1 === step ? "on" : ""}`}
                />
              ))}
            </div>
          </div>

          <div className="onb-q-card founders-card">
            {step === 1 && <Step1 data={data} set={set} />}
            {step === 2 && <Step2 data={data} set={set} />}
            {step === 3 && <Step3 data={data} set={set} />}
            {step === 4 && <Step4 data={data} set={set} />}
            {step === 5 && (
              <Step5
                data={data}
                set={set}
                communities={communities}
                picked={pickedSlugs}
                onTogglePicked={togglePicked}
              />
            )}

            {err && (
              <div className="mono" style={{ color: "var(--warn)", marginTop: 16 }}>
                {err}
              </div>
            )}

            <div className="onb-q-multi-foot">
              <span className="mono onb-q-skip">
                {pickedSlugs.length > 0
                  ? `${pickedSlugs.length} community${pickedSlugs.length === 1 ? "" : " ies"} picked`
                  : "pick communities on the graph ↘"}
              </span>
              {step < TOTAL_STEPS ? (
                <MButton
                  onClick={() => canAdvance(step) && setStep((s) => s + 1)}
                  variant={canAdvance(step) ? "primary" : "ghost"}
                >
                  Continue →
                </MButton>
              ) : (
                <MButton
                  onClick={submit}
                  variant={
                    canAdvance(5) && pickedSlugs.length > 0 ? "primary" : "ghost"
                  }
                >
                  {submitting ? "Submitting…" : "Submit launch →"}
                </MButton>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Steps
// =============================================================================

function Step1({ data, set }: { data: State; set: <K extends keyof State>(k: K, v: State[K]) => void }) {
  const urlInvalid =
    data.product_url.length > 0 && !isHttp(data.product_url.trim());
  return (
    <>
      <h1 className="onb-q-title">What are you building?</h1>
      <p className="onb-q-sub">We need the URL — it&apos;s how the rest of Mesh links to you.</p>
      <div className="founders-fields">
        <Field label="Product name (display)">
          <input
            className="m-input founders-input"
            placeholder="Granola, Linear, Reflect"
            value={data.name}
            onChange={(e) => set("name", e.target.value)}
            autoFocus
          />
        </Field>
        <Field label="Product URL (required)" required>
          <input
            className="m-input founders-input"
            placeholder="https://example.com"
            value={data.product_url}
            onChange={(e) => set("product_url", e.target.value)}
          />
          {urlInvalid && (
            <span className="mono" style={{ color: "var(--warn)", fontSize: 12 }}>
              must start with http:// or https://
            </span>
          )}
        </Field>
        <Field label="One-liner">
          <input
            className="m-input founders-input"
            placeholder="AI meeting notes that live next to your calendar"
            value={data.oneliner}
            onChange={(e) => set("oneliner", e.target.value)}
          />
        </Field>
        <Field label="Existing presence (CSV — X / LinkedIn / GitHub / site)">
          <input
            className="m-input founders-input"
            placeholder="https://x.com/yours, https://github.com/yours"
            value={data.presence}
            onChange={(e) => set("presence", e.target.value)}
          />
        </Field>
      </div>
    </>
  );
}

function Step2({ data, set }: { data: State; set: <K extends keyof State>(k: K, v: State[K]) => void }) {
  return (
    <>
      <h1 className="onb-q-title">Where does it fit?</h1>
      <p className="onb-q-sub">Pick the closest. We&apos;ll let users refine it later.</p>
      <div className="onb-q-opts">
        {CATEGORY_OPTS.map((opt, i) => (
          <button
            key={opt.l}
            className={`onb-q-opt ${data.category === opt.l ? "on" : ""}`}
            onClick={() => set("category", opt.l)}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <span className="onb-q-bullet">
              <span className="onb-radio">
                {data.category === opt.l ? <span className="onb-radio-dot" /> : null}
              </span>
            </span>
            <span className="onb-q-label">{opt.l}</span>
          </button>
        ))}
      </div>
    </>
  );
}

function Step3({ data, set }: { data: State; set: <K extends keyof State>(k: K, v: State[K]) => void }) {
  return (
    <>
      <h1 className="onb-q-title">Who is it for?</h1>
      <p className="onb-q-sub">
        The truth, not the pitch deck. Three sentences are plenty.
      </p>
      <div className="founders-fields">
        <Field label="Who they are">
          <input
            className="m-input founders-input"
            placeholder="Staff PMs at 50-300 person SaaS companies"
            value={data.icp_who}
            onChange={(e) => set("icp_who", e.target.value)}
          />
        </Field>
        <Field label="What they're trying to do">
          <input
            className="m-input founders-input"
            placeholder="Get sprint planning done without 4 tools"
            value={data.icp_jtbd}
            onChange={(e) => set("icp_jtbd", e.target.value)}
          />
        </Field>
        <Field label="What's broken about today's solution">
          <input
            className="m-input founders-input"
            placeholder="Notion → Linear copy-paste eats 40 min/week"
            value={data.icp_pain}
            onChange={(e) => set("icp_pain", e.target.value)}
          />
        </Field>
      </div>
    </>
  );
}

function Step4({ data, set }: { data: State; set: <K extends keyof State>(k: K, v: State[K]) => void }) {
  return (
    <>
      <h1 className="onb-q-title">How does it work, money-wise?</h1>
      <p className="onb-q-sub">
        Affects which communities care. r/replacing-saas-with-ai is allergic to per-seat pricing.
      </p>
      <div className="onb-q-opts">
        {PRICING_OPTS.map((opt, i) => (
          <button
            key={opt.l}
            className={`onb-q-opt ${data.pricing === opt.l ? "on" : ""}`}
            onClick={() => set("pricing", opt.l)}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <span className="onb-q-bullet">
              <span className="onb-radio">
                {data.pricing === opt.l ? <span className="onb-radio-dot" /> : null}
              </span>
            </span>
            <span className="onb-q-label">{opt.l}</span>
          </button>
        ))}
      </div>
    </>
  );
}

function Step5({
  data,
  set,
  communities,
  picked,
  onTogglePicked,
}: {
  data: State;
  set: <K extends keyof State>(k: K, v: State[K]) => void;
  communities: CommunityCard[];
  picked: string[];
  onTogglePicked: (slug: string) => void;
}) {
  return (
    <>
      <h1 className="onb-q-title">What&apos;s your hook + where should it land?</h1>
      <p className="onb-q-sub">
        Hook becomes your problem_statement. Pick 1–6 communities — the launch fans into those.
      </p>
      <div className="founders-fields">
        <Field label="Hook">
          <textarea
            className="m-input founders-input founders-textarea"
            placeholder="Replaces the 40 minutes you lose every week to copy-pasting between Notion and Linear."
            rows={3}
            value={data.pitch}
            onChange={(e) => set("pitch", e.target.value)}
          />
        </Field>
        <Field
          label={`Target communities (${picked.length} of 6)`}
          required
        >
          {communities.length === 0 ? (
            <span className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
              loading…
            </span>
          ) : (
            <div className="founders-chips">
              {communities.map((c, i) => {
                const isPicked = picked.includes(c.slug);
                const atCap = !isPicked && picked.length >= 6;
                return (
                  <button
                    key={c.slug}
                    type="button"
                    className={`founders-chip ${isPicked ? "on" : ""}`}
                    onClick={() => !atCap && onTogglePicked(c.slug)}
                    disabled={atCap}
                    style={{
                      animationDelay: `${i * 30}ms`,
                      opacity: atCap ? 0.4 : 1,
                      cursor: atCap ? "not-allowed" : "pointer",
                    }}
                    title={c.description}
                  >
                    <span className="founders-chip-check">{isPicked ? "✓" : "+"}</span>
                    <span>{c.name}</span>
                  </button>
                );
              })}
            </div>
          )}
        </Field>
      </div>
    </>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="founders-field">
      <label className="founders-label mono">
        {label}
        {required && (
          <span className="founders-label-hint" style={{ color: "var(--accent)" }}>
            *
          </span>
        )}
      </label>
      {children}
    </div>
  );
}

// (Old CommunityChips component removed — picker moved into Step5
// and now reads from real GET /api/communities, not the hardcoded
// MESH_COMMUNITIES list. Old picker lived in .onb-graph-meta which
// has pointer-events:none so clicks never fired.)

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
            Mesh staff verifies launches within ~24 hours. You&apos;ll see
            it move to <em>approved</em> on your dashboard once it does — and
            the launch fans out into the {pickedSlugs.length} community
            {pickedSlugs.length === 1 ? "" : "ies"} you picked plus the matched
            user nudges.
          </p>
          <div className="onb-result-cta in">
            <Link href="/home">
              <MButton size="lg" trailing="→">
                Back to dashboard
              </MButton>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
