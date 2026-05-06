"use client";

// Mesh — Live-narrowing onboarding (cycle #15).
// Per spec-delta live-narrowing-onboarding F-LIVE-8.
//
// Same visual shell as the classic /onboarding flow (left graph pane,
// right content pane, ToolGraph that shrinks as the profile sharpens).
// Only the data flow is different: 4 locked questions instead of the
// open question bank, and POST /api/recommendations/live-step on every
// tap instead of POST /api/answers.

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { ToolGraph, MeshTool } from "@/components/ToolGraph";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated, currentUser } from "@/lib/auth";
import type {
  LiveAnswerValue,
  LiveOption,
  LiveOptionsResponse,
  LiveQuestion,
  LiveQuestionsResponse,
  LiveStepResponse,
  LiveStepTool,
  ToolsBrowseResponse,
  ToolCardWithFlags,
} from "@/lib/api-types";

interface LiveStateResponse {
  answers: Record<string, Record<string, unknown>>;
  next_step: number | null;
}


// Convert API tool shapes to the ToolGraph's MeshTool shape.
function toMeshTool(t: { slug: string; name: string; category?: string | null; labels?: string[]; layer?: string | null; tagline?: string | null }): MeshTool {
  const tags = [
    ...(t.category ? [t.category] : []),
    ...(t.labels || []),
    ...(t.layer ? [t.layer] : []),
  ];
  return {
    id: t.slug,
    name: t.name || t.slug,
    tags: tags.slice(0, 6),
  };
}


// =============================================================================
// Page — auth + variant gate
// =============================================================================
export default function LiveOnboardingPage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  const [bouncedClassic, setBouncedClassic] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!isAuthenticated()) {
        router.replace("/signup");
        return;
      }
      try {
        const me = await currentUser();
        if (cancelled) return;
        if (me?.role_type !== "user") {
          router.replace("/home");
          return;
        }
        if (me?.onboarding_variant !== "live") {
          setBouncedClassic(true);
          router.replace("/onboarding");
          return;
        }
      } catch {
        router.replace("/login");
        return;
      }
      if (!cancelled) setAuthChecked(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (!authChecked || bouncedClassic) return null;
  return <LiveTapLoop />;
}


// =============================================================================
// Constants — UI shrink schedule
// =============================================================================
// Before Q1 the graph starts wide (~40 placeholder nodes — "the whole
// catalog you might use"). After each tap it narrows: 20 → 15 → 10 → 6
// (mirrors the backend's K_SCHEDULE for everything from Q1 onward).
const INITIAL_SLOTS = 40;
const SLOT_BY_STEP: Record<number, number> = { 1: 20, 2: 15, 3: 10, 4: 6 };


// =============================================================================
// Tap loop — same visual shell as classic /onboarding
// =============================================================================
function LiveTapLoop() {
  const router = useRouter();

  const [questions, setQuestions] = useState<LiveQuestion[] | null>(null);
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(true);  // initial schema fetch
  const [busy, setBusy] = useState(false);       // submitting + matching

  const [latest, setLatest] = useState<LiveStepResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Initial pool of ~40 real tools shown on the graph BEFORE Q1.
  // After each step, this is replaced with the live-step's top + wildcard.
  const [graphTools, setGraphTools] = useState<MeshTool[]>([]);

  // Per-step answer state.
  const [q1Answer, setQ1Answer] = useState({ job_title: "", level: "", industry: "" });
  const [q2Selected, setQ2Selected] = useState<string[]>([]);
  const [q2Options, setQ2Options] = useState<LiveOption[] | null>(null);
  const [q3Selected, setQ3Selected] = useState("");
  const [q3Options, setQ3Options] = useState<LiveOption[] | null>(null);
  const [q4Selected, setQ4Selected] = useState("");

  // Mount: fetch schema + saved live state in parallel, then either
  // restore from previous session OR seed graph with initial 40 tools.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [schemaR, stateR] = await Promise.all([
          api.get<LiveQuestionsResponse>("/api/onboarding/live-questions"),
          api.get<LiveStateResponse>("/api/recommendations/live-state"),
        ]);
        if (cancelled) return;
        setQuestions(schemaR.questions);

        const savedAnswers = stateR.answers || {};
        const answeredKeys = Object.keys(savedAnswers);

        if (answeredKeys.length === 0) {
          // No saved state — seed graph with the catalog top-40.
          try {
            const r = await api.get<ToolsBrowseResponse>("/api/tools?limit=40");
            if (!cancelled) setGraphTools(r.tools.map(toMeshTool));
          } catch {
            // non-fatal
          }
        } else {
          // Restore questionnaire state from saved live_answers rows.
          const a1 = savedAnswers["1"] as
            | { job_title?: string; level?: string; industry?: string }
            | undefined;
          if (a1) {
            setQ1Answer({
              job_title: a1.job_title || "",
              level: a1.level || "",
              industry: a1.industry || "",
            });
          }
          const a2 = savedAnswers["2"] as
            | { selected_values?: string[] }
            | undefined;
          if (a2 && Array.isArray(a2.selected_values)) {
            setQ2Selected(a2.selected_values);
          }
          const a3 = savedAnswers["3"] as
            | { selected_value?: string }
            | undefined;
          if (a3?.selected_value) setQ3Selected(a3.selected_value);
          const a4 = savedAnswers["4"] as
            | { selected_value?: string }
            | undefined;
          if (a4?.selected_value) setQ4Selected(a4.selected_value);

          // Position the user at the next unanswered step (or "done"
          // if all 4 are saved).
          if (stateR.next_step === null) {
            setDone(true);
            setStep(4);
          } else if (stateR.next_step >= 1 && stateR.next_step <= 4) {
            setStep(stateR.next_step as 1 | 2 | 3 | 4);
          }

          // Repopulate the graph by re-firing the latest answered
          // q_index. One OpenAI embed cost; the answer is already
          // persisted so it's idempotent.
          const latestQ = Math.max(...answeredKeys.map((k) => Number(k)));
          const latestAv = savedAnswers[String(latestQ)] as LiveAnswerValue;
          try {
            const r = await api.post<LiveStepResponse>(
              "/api/recommendations/live-step",
              { q_index: latestQ, answer_value: latestAv },
            );
            if (!cancelled) {
              setLatest(r);
              const next: MeshTool[] = r.top.map(toMeshTool);
              if (r.wildcard) next.push(toMeshTool(r.wildcard));
              setGraphTools(next);
            }
          } catch (e) {
            console.warn("[live] state-restore replay failed", e);
          }
        }
      } catch (e) {
        if (e instanceof ApiError && e.status === 403) {
          router.replace("/home");
          return;
        }
        console.error("[live] mount fetch failed", e);
        setError("could not load questions");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // After Q1 lands, fetch role-conditioned options for Q2 + Q3 in parallel.
  useEffect(() => {
    if (!q1Answer.job_title) return;
    let cancelled = false;
    (async () => {
      try {
        const [r2, r3] = await Promise.all([
          api.get<LiveOptionsResponse>(
            `/api/onboarding/live-questions/2/options?role=${encodeURIComponent(q1Answer.job_title)}`,
          ),
          api.get<LiveOptionsResponse>(
            `/api/onboarding/live-questions/3/options?role=${encodeURIComponent(q1Answer.job_title)}`,
          ),
        ]);
        if (cancelled) return;
        setQ2Options(r2.options);
        setQ3Options(r3.options);
      } catch (e) {
        console.warn("[live] options fetch failed", e);
      }
    })();
    return () => { cancelled = true; };
  }, [q1Answer.job_title]);

  // Tags for the graph — pulled from the latest top tools' categories + labels.
  const accumulatedTags = useMemo<string[]>(() => {
    const tags = new Set<string>();
    for (const t of latest?.top || []) {
      if (t.category) tags.add(t.category);
      if (t.layer) tags.add(t.layer);
    }
    return [...tags];
  }, [latest]);

  const submitStep = async (value: LiveAnswerValue) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.post<LiveStepResponse>(
        "/api/recommendations/live-step",
        { q_index: step, answer_value: value },
      );
      if (r.degraded) {
        console.info("[live] degraded ranking (Weaviate unavailable)");
      }
      setLatest(r);
      // Update graph to show the actual narrowed tool list (top + optional
      // wildcard). The ToolGraph component reconciles by id — kept tools
      // hold their on-screen position; dropped ones fade out; new ones
      // fade in.
      const next: MeshTool[] = r.top.map(toMeshTool);
      if (r.wildcard) next.push(toMeshTool(r.wildcard));
      setGraphTools(next);
      if (step < 4) {
        setStep(((step + 1) as 1 | 2 | 3 | 4));
      } else {
        setDone(true);
      }
    } catch (e) {
      console.warn("[live] submit failed", e);
      const msg =
        e instanceof ApiError && e.status === 503
          ? "matching paused — try again in a moment"
          : "something went wrong — try again";
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  // Before any answer lands → INITIAL_SLOTS. After step N submits,
  // `latest` is set and we shrink to the budget for the step the user
  // is now ON. Use SLOT_BY_STEP[step-1] for the just-completed step
  // because `step` is incremented before this re-renders.
  const slotCount = done
    ? 6
    : !latest
      ? INITIAL_SLOTS
      : SLOT_BY_STEP[step];
  const progress = done ? 1 : !latest ? 0.2 : 0.3 + ((step - 1) / 4) * 0.7;
  const currentQuestion = questions?.find((qq) => qq.q_index === step);

  return (
    <div className="onb-root">
      {/* Left pane: same ToolGraph shell as classic */}
      <div className={`onb-graph-pane ${done ? "collapsed" : ""}`}>
        <div className="onb-graph-canvas">
          <ToolGraph
            progress={progress}
            highlightedTags={accumulatedTags}
            mode="score"
            gridSlots={graphTools.length || slotCount}
            scale={1.4}
            tools={graphTools.length > 0 ? graphTools : undefined}
          />
        </div>
        <div className="onb-graph-meta mono">
          <div className="onb-graph-meta-row">
            <span className="onb-graph-dot" />
            <span>
              profile · {done
                ? `${graphTools.length} matches ready`
                : busy
                  ? "matching…"
                  : !latest
                    ? `${graphTools.length || "—"} candidates · answer Q1 to narrow`
                    : `narrowed to ${graphTools.length}`}
            </span>
          </div>
          <div className="onb-graph-tags">
            {/* Show top tool names from the latest narrowing as chips
                so the user can read what the graph is actually showing. */}
            {(latest?.top
              ? latest.top.map((t) => ({ id: t.slug, name: t.name || t.slug }))
              : graphTools.map((t) => ({ id: t.id, name: t.name }))
            ).slice(0, 8).map((tt) => (
              <span key={tt.id} className="onb-graph-tag">
                {tt.name}
              </span>
            ))}
            {!latest && !busy && graphTools.length === 0 && (
              <span className="onb-graph-tag" style={{ opacity: 0.5 }}>
                loading catalog…
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Right pane: header + question card / loader / result */}
      <div className="onb-content-pane">
        <header className="onb-header">
          <Link href="/" className="onb-brand">
            <MeshMark size={20} />
            <span>Mesh</span>
          </Link>
          <button
            className="onb-exit mono"
            onClick={() => router.push("/home")}
          >
            save & exit
          </button>
        </header>

        {loading && !done && (
          <div className="mono" style={{ padding: 32, color: "var(--ink-2)" }}>
            loading…
          </div>
        )}

        {!done && busy && (
          <div className="onb-q-wrap">
            <div className="onb-q-meta">
              <span className="mono onb-q-count">matching…</span>
            </div>
            <div className="onb-q-card">
              <h1 className="onb-q-title">Re-reading your profile.</h1>
              <p className="onb-q-sub">
                Embedding your answer + narrowing the catalog.
              </p>
              <div
                className="mono"
                style={{ marginTop: 16, color: "var(--ink-3)", fontSize: 12 }}
              >
                this usually takes &lt;1s
              </div>
            </div>
          </div>
        )}

        {!done && !busy && currentQuestion && (
          <LiveQuestionCard
            step={step}
            question={currentQuestion}
            q1Value={q1Answer}
            onQ1Change={setQ1Answer}
            q2Options={q2Options}
            q2Selected={q2Selected}
            onQ2Toggle={(v) =>
              setQ2Selected((prev) =>
                prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v],
              )
            }
            q3Options={q3Options}
            q3Selected={q3Selected}
            onQ3Pick={setQ3Selected}
            q4Selected={q4Selected}
            onQ4Pick={setQ4Selected}
            onSubmit={submitStep}
          />
        )}

        {error && !busy && (
          <div
            className="mono"
            style={{ padding: 16, color: "var(--warn)", fontSize: 12 }}
          >
            {error}
          </div>
        )}

        {done && latest && <LiveResultPanel latest={latest} />}
      </div>
    </div>
  );
}


// =============================================================================
// Per-step question card — mirrors classic QuestionCard styling
// =============================================================================
function LiveQuestionCard({
  step,
  question,
  q1Value,
  onQ1Change,
  q2Options,
  q2Selected,
  onQ2Toggle,
  q3Options,
  q3Selected,
  onQ3Pick,
  q4Selected,
  onQ4Pick,
  onSubmit,
}: {
  step: 1 | 2 | 3 | 4;
  question: LiveQuestion;
  q1Value: { job_title: string; level: string; industry: string };
  onQ1Change: (v: { job_title: string; level: string; industry: string }) => void;
  q2Options: LiveOption[] | null;
  q2Selected: string[];
  onQ2Toggle: (v: string) => void;
  q3Options: LiveOption[] | null;
  q3Selected: string;
  onQ3Pick: (v: string) => void;
  q4Selected: string;
  onQ4Pick: (v: string) => void;
  onSubmit: (v: LiveAnswerValue) => void;
}) {
  const canAdvance =
    (step === 1 && !!(q1Value.job_title && q1Value.level && q1Value.industry)) ||
    (step === 2 && q2Selected.length > 0) ||
    (step === 3 && !!q3Selected) ||
    (step === 4 && !!q4Selected);

  const handleSubmit = () => {
    if (step === 1) onSubmit(q1Value);
    else if (step === 2) onSubmit({ selected_values: q2Selected });
    else if (step === 3) onSubmit({ selected_value: q3Selected });
    else onSubmit({ selected_value: q4Selected });
  };

  return (
    <div className="onb-q-wrap">
      <div className="onb-q-meta">
        <span className="mono onb-q-count">Question {step} of 4</span>
      </div>
      <div className="onb-q-card">
        <h1 className="onb-q-title">{question.text}</h1>
        {question.helper && (
          <p className="onb-q-sub">{question.helper}</p>
        )}

        {step === 1 && (
          <div className="onb-q-opts" style={{ display: "grid", gap: 16, marginTop: 24 }}>
            {(["job_title", "level", "industry"] as const).map((key) => (
              <div key={key}>
                <label
                  className="mono"
                  style={{ fontSize: 11, color: "var(--ink-3)", display: "block", marginBottom: 6 }}
                >
                  {key.replace("_", " ")}
                </label>
                <select
                  className="m-input"
                  value={q1Value[key]}
                  onChange={(e) => onQ1Change({ ...q1Value, [key]: e.target.value })}
                  style={{ width: "100%" }}
                >
                  <option value="">— pick one —</option>
                  {(question.sub_dropdowns?.[key] || []).map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}

        {step === 2 && (
          <div className="onb-q-opts">
            {(q2Options || []).map((opt, i) => {
              const picked = q2Selected.includes(opt.value);
              return (
                <button
                  key={opt.value}
                  className={`onb-q-opt ${picked ? "on" : ""}`}
                  onClick={() => onQ2Toggle(opt.value)}
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <span className="onb-q-bullet">
                    <span className="onb-check">{picked ? "✓" : ""}</span>
                  </span>
                  <span className="onb-q-label">{opt.label}</span>
                </button>
              );
            })}
            {q2Options === null && (
              <div className="mono" style={{ color: "var(--ink-3)", padding: 16 }}>
                loading options for your role…
              </div>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="onb-q-opts">
            {(q3Options || []).map((opt, i) => (
              <button
                key={opt.value}
                className={`onb-q-opt ${q3Selected === opt.value ? "on" : ""}`}
                onClick={() => onQ3Pick(opt.value)}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <span className="onb-q-bullet">
                  <span className="onb-radio" />
                </span>
                <span className="onb-q-label">{opt.label}</span>
              </button>
            ))}
            {q3Options === null && (
              <div className="mono" style={{ color: "var(--ink-3)", padding: 16 }}>
                loading scenarios for your role…
              </div>
            )}
          </div>
        )}

        {step === 4 && (
          <div className="onb-q-opts">
            {(question.options || []).map((opt, i) => (
              <button
                key={opt.value}
                className={`onb-q-opt ${q4Selected === opt.value ? "on" : ""}`}
                onClick={() => onQ4Pick(opt.value)}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <span className="onb-q-bullet">
                  <span className="onb-radio" />
                </span>
                <span className="onb-q-label">{opt.label}</span>
              </button>
            ))}
          </div>
        )}

        <div className="onb-q-multi-foot" style={{ marginTop: 24 }}>
          <span className="mono onb-q-skip" />
          <MButton onClick={handleSubmit} variant="primary">
            {step < 4 ? `Continue → Q${step + 1}` : "Finish & see my matches →"}
          </MButton>
        </div>
        {!canAdvance && (
          <div
            className="mono"
            style={{ marginTop: 8, fontSize: 11, color: "var(--ink-3)", textAlign: "right" }}
          >
            {step === 1
              ? "pick all three"
              : step === 2
                ? "pick at least one"
                : "pick one"}
          </div>
        )}
      </div>
    </div>
  );
}


// =============================================================================
// Result panel — mirrors classic ResultPanel (top-K from final live-step)
// =============================================================================
function LiveResultPanel({ latest }: { latest: LiveStepResponse }) {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const t1 = setTimeout(() => setStage(1), 600);
    const t2 = setTimeout(() => setStage(2), 1400);
    const t3 = setTimeout(() => setStage(3), 2100);
    return () => [t1, t2, t3].forEach(clearTimeout);
  }, []);

  const tools = latest.top.slice(0, 6);

  return (
    <div className="onb-result">
      <div className="onb-result-eyebrow mono">/ for you, today</div>
      <h1 className="onb-result-title">
        Here are the <em>{tools.length || "few"}</em> tools
        <br />
        that actually fit you.
      </h1>
      <p className="onb-result-sub body-lg">
        Built from your stack, your task shape, and the friction you flagged.
        We&apos;ll keep refining as your profile sharpens.
      </p>
      <div className={`onb-result-grid stage-${stage}`}>
        {tools.map((t, i) => (
          <LiveResultCard key={t.slug} tool={t} delay={i * 120} />
        ))}

        {latest.wildcard && (
          <div
            className="onb-result-skip-card"
            style={{ transitionDelay: `${tools.length * 120}ms` }}
          >
            <span className="onb-skip-tag mono">YOU MIGHT NOT EXPECT</span>
            <div className="h-card" style={{ marginTop: 12 }}>
              {latest.wildcard.name || latest.wildcard.slug}
            </div>
            <p className="body" style={{ marginTop: 8 }}>
              {latest.wildcard.tagline || latest.wildcard.reasoning_hook}
            </p>
            <div className="mono onb-skip-meta">— concierge surprise factor</div>
          </div>
        )}
      </div>

      <div className={`onb-result-cta ${stage >= 3 ? "in" : ""}`}>
        <Link href="/home">
          <MButton size="lg" trailing="→">
            Enter Mesh
          </MButton>
        </Link>
      </div>
    </div>
  );
}


function LiveResultCard({
  tool,
  delay,
}: {
  tool: LiveStepTool;
  delay: number;
}) {
  return (
    <div
      className="onb-result-card"
      style={{ transitionDelay: `${delay}ms` }}
    >
      <Link
        href={`/p/${tool.slug}`}
        className="onb-result-card-top"
        style={{ textDecoration: "none", display: "flex" }}
      >
        <div className="onb-result-logo">
          <div className="onb-result-logo-inner">
            {(tool.name || tool.slug)[0]?.toUpperCase()}
          </div>
        </div>
        <div className="onb-result-name">
          <div className="h-card">{tool.name || tool.slug}</div>
          <div className="mono onb-result-tag">
            {tool.category || tool.layer || "match"}
          </div>
        </div>
      </Link>
      <p className="body" style={{ marginTop: 16 }}>
        {tool.reasoning_hook}
      </p>
      <div className="onb-result-card-actions">
        <Link href={`/p/${tool.slug}`}>
          <MButton size="sm" variant="ghost">
            View on Mesh
          </MButton>
        </Link>
      </div>
    </div>
  );
}
