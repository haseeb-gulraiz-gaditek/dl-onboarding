"use client";

// Mesh — Live-narrowing onboarding (cycle #15).
// Per spec-delta live-narrowing-onboarding F-LIVE-8.
//
// 4 questions, ranked-list shrinks 20 → 15 → 10 → 6 in real time.
// Each tap persists the answer + re-embeds the profile vector, so a
// mid-flow exit is non-destructive — the next /home load reads
// whatever profile vector exists.

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

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
} from "@/lib/api-types";


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
          // The deploy isn't on `live` — fall back to classic so users
          // can't get stranded on a flag-disabled page.
          setBouncedClassic(true);
          router.replace("/onboarding");
          return;
        }
      } catch {
        // /api/me failure → bounce to login
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
  return <LiveFlow />;
}


function LiveFlow() {
  const router = useRouter();
  const [questions, setQuestions] = useState<LiveQuestion[] | null>(null);
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Per-step answer state.
  const [q1Answer, setQ1Answer] = useState({ job_title: "", level: "", industry: "" });
  const [q2Selected, setQ2Selected] = useState<string[]>([]);
  const [q2Options, setQ2Options] = useState<LiveOption[] | null>(null);
  const [q3Selected, setQ3Selected] = useState("");
  const [q3Options, setQ3Options] = useState<LiveOption[] | null>(null);
  const [q4Selected, setQ4Selected] = useState("");

  // Result state.
  const [latest, setLatest] = useState<LiveStepResponse | null>(null);

  // Fetch the schema on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get<LiveQuestionsResponse>(
          "/api/onboarding/live-questions",
        );
        if (cancelled) return;
        setQuestions(r.questions);
      } catch (e) {
        console.warn("[live] questions fetch failed", e);
        setError("could not load questions");
      } finally {
        if (!cancelled) setLoadingQuestions(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // After Q1 lands, fetch role-conditioned options for Q2 and Q3.
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
    return () => {
      cancelled = true;
    };
  }, [q1Answer.job_title]);

  const q = questions?.find((qq) => qq.q_index === step);

  const canAdvance = useMemo((): boolean => {
    if (step === 1)
      return !!(q1Answer.job_title && q1Answer.level && q1Answer.industry);
    if (step === 2) return q2Selected.length > 0;
    if (step === 3) return !!q3Selected;
    if (step === 4) return !!q4Selected;
    return false;
  }, [step, q1Answer, q2Selected, q3Selected, q4Selected]);

  const submitStep = async () => {
    if (!canAdvance || busy) return;
    setBusy(true);
    setError(null);
    let answer_value: LiveAnswerValue;
    if (step === 1) answer_value = q1Answer;
    else if (step === 2) answer_value = { selected_values: q2Selected };
    else if (step === 3) answer_value = { selected_value: q3Selected };
    else answer_value = { selected_value: q4Selected };

    try {
      const r = await api.post<LiveStepResponse>(
        "/api/recommendations/live-step",
        { q_index: step, answer_value },
      );
      setLatest(r);
      if (step < 4) {
        setStep(((step + 1) as 1 | 2 | 3 | 4));
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

  if (loadingQuestions) {
    return (
      <Shell>
        <div className="mono" style={{ color: "var(--ink-3)" }}>loading…</div>
      </Shell>
    );
  }

  if (!questions || !q) {
    return (
      <Shell>
        <div className="mono" style={{ color: "var(--warn)" }}>
          {error || "questions unavailable"}
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0,1fr) 360px",
          gap: 32,
          alignItems: "flex-start",
        }}
      >
        {/* Question pane */}
        <section>
          <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11 }}>
            / live · question {step} of 4
          </div>
          <h1 className="onb-q-title" style={{ marginTop: 8 }}>{q.text}</h1>
          {q.helper && (
            <p className="body" style={{ color: "var(--ink-2)", marginTop: 8 }}>
              {q.helper}
            </p>
          )}

          <div style={{ marginTop: 24 }}>
            {step === 1 && (
              <Q1Dropdowns
                value={q1Answer}
                subDropdowns={q.sub_dropdowns || {}}
                onChange={setQ1Answer}
              />
            )}
            {step === 2 && (
              <ChipMulti
                options={q2Options || []}
                selected={q2Selected}
                onToggle={(v) =>
                  setQ2Selected((prev) =>
                    prev.includes(v) ? prev.filter((x) => x !== v) : [...prev, v],
                  )
                }
              />
            )}
            {step === 3 && (
              <ChipSingle
                options={q3Options || []}
                selected={q3Selected}
                onPick={setQ3Selected}
              />
            )}
            {step === 4 && (
              <ChipSingle
                options={q.options || []}
                selected={q4Selected}
                onPick={setQ4Selected}
              />
            )}
          </div>

          {error && (
            <div
              className="mono"
              style={{ color: "var(--warn)", marginTop: 16, fontSize: 12 }}
            >
              {error}
            </div>
          )}

          <div style={{ marginTop: 32, display: "flex", gap: 12, alignItems: "center" }}>
            {step < 4 ? (
              <MButton
                disabled={!canAdvance || busy}
                onClick={submitStep}
              >
                {busy ? "Updating…" : `Continue → Q${step + 1}`}
              </MButton>
            ) : (
              <MButton disabled={!canAdvance || busy} onClick={submitStep}>
                {busy ? "Finalizing…" : "Finish & see my full match →"}
              </MButton>
            )}
            <Link
              href="/home"
              className="mono"
              style={{ color: "var(--ink-3)", fontSize: 12 }}
            >
              save & exit
            </Link>
            {step === 4 && latest && (
              <Link href="/home" className="mono" style={{ color: "var(--accent)", fontSize: 12 }}>
                go to home →
              </Link>
            )}
          </div>
        </section>

        {/* Live narrowing pane */}
        <aside>
          <NarrowingPane latest={latest} step={step} busy={busy} />
        </aside>
      </div>
    </Shell>
  );
}


function Q1Dropdowns({
  value,
  subDropdowns,
  onChange,
}: {
  value: { job_title: string; level: string; industry: string };
  subDropdowns: Record<string, LiveOption[]>;
  onChange: (next: { job_title: string; level: string; industry: string }) => void;
}) {
  return (
    <div style={{ display: "grid", gap: 12 }}>
      {(["job_title", "level", "industry"] as const).map((key) => (
        <div key={key}>
          <label className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>
            {key.replace("_", " ")}
          </label>
          <select
            className="m-input"
            value={value[key]}
            onChange={(e) => onChange({ ...value, [key]: e.target.value })}
            style={{ width: "100%", marginTop: 4 }}
          >
            <option value="">— pick one —</option>
            {(subDropdowns[key] || []).map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}


function ChipMulti({
  options,
  selected,
  onToggle,
}: {
  options: LiveOption[];
  selected: string[];
  onToggle: (v: string) => void;
}) {
  if (options.length === 0) {
    return (
      <div className="mono" style={{ color: "var(--ink-3)" }}>
        loading options…
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onToggle(o.value)}
          className="mono"
          style={{
            padding: "8px 14px",
            borderRadius: "var(--r-pill)",
            fontSize: 13,
            background: selected.includes(o.value) ? "var(--accent-soft)" : "transparent",
            border: selected.includes(o.value)
              ? "1px solid var(--accent)"
              : "1px solid var(--line-0)",
            color: selected.includes(o.value) ? "var(--ink-0)" : "var(--ink-2)",
            cursor: "pointer",
          }}
        >
          {selected.includes(o.value) ? "✓ " : ""}{o.label}
        </button>
      ))}
    </div>
  );
}


function ChipSingle({
  options,
  selected,
  onPick,
}: {
  options: LiveOption[];
  selected: string;
  onPick: (v: string) => void;
}) {
  if (options.length === 0) {
    return (
      <div className="mono" style={{ color: "var(--ink-3)" }}>
        loading options…
      </div>
    );
  }
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onPick(o.value)}
          className="body"
          style={{
            padding: "12px 16px",
            borderRadius: "var(--r-md)",
            fontSize: 14,
            textAlign: "left",
            background: selected === o.value ? "var(--accent-soft)" : "transparent",
            border: selected === o.value
              ? "1px solid var(--accent)"
              : "1px solid var(--line-0)",
            color: "var(--ink-0)",
            cursor: "pointer",
          }}
        >
          {selected === o.value ? "● " : "○ "}{o.label}
        </button>
      ))}
    </div>
  );
}


function NarrowingPane({
  latest,
  step,
  busy,
}: {
  latest: LiveStepResponse | null;
  step: number;
  busy: boolean;
}) {
  return (
    <div className="m-card" style={{ padding: 20 }}>
      <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11 }}>
        / matching live
      </div>
      <h3 className="h-card" style={{ marginTop: 4, fontSize: 14 }}>
        {latest ? `top ${latest.count_kept} for you` : "pick to start"}
      </h3>
      {busy && (
        <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 8 }}>
          updating…
        </div>
      )}
      {latest?.degraded && (
        <div className="mono" style={{ color: "var(--warn)", fontSize: 11, marginTop: 8 }}>
          (using fallback ranking — search index unavailable)
        </div>
      )}
      <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
        {(latest?.top || []).map((t) => (
          <ToolRow key={t.slug} tool={t} />
        ))}
        {latest?.wildcard && (
          <>
            <div
              className="mono"
              style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 8 }}
            >
              you might not expect →
            </div>
            <ToolRow tool={latest.wildcard} />
          </>
        )}
        {!latest && (
          <div className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
            answer Q{step} to see your live ranking
          </div>
        )}
      </div>
    </div>
  );
}


function ToolRow({ tool }: { tool: LiveStepTool }) {
  const layerColor =
    tool.layer === "niche"
      ? "var(--accent)"
      : tool.layer === "relevant"
        ? "var(--ink-1)"
        : "var(--ink-3)";
  return (
    <Link
      href={`/p/${tool.slug}`}
      style={{
        textDecoration: "none",
        color: "inherit",
        padding: "10px 12px",
        borderRadius: "var(--r-sm)",
        border: "1px solid var(--line-0)",
        display: "block",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <div className="h-card" style={{ fontSize: 13 }}>{tool.name || tool.slug}</div>
          <div className="mono" style={{ color: "var(--ink-3)", fontSize: 10, marginTop: 2 }}>
            {tool.reasoning_hook}
          </div>
        </div>
        <div className="mono" style={{ fontSize: 10, color: layerColor, textAlign: "right" }}>
          {tool.layer || "—"}
          <br />
          <span style={{ color: "var(--ink-3)" }}>{tool.score.toFixed(2)}</span>
        </div>
      </div>
    </Link>
  );
}


function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: "100vh", padding: "32px max(24px, 5vw)" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 32,
        }}
      >
        <Link href="/" className="onb-brand">
          <MeshMark size={20} />
          <span>Mesh</span>
        </Link>
        <HeaderBell />
      </header>
      <main style={{ maxWidth: 1080, margin: "0 auto" }}>{children}</main>
    </div>
  );
}
