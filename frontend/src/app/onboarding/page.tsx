"use client";

// Mesh — Onboarding (tap-question loop + result).
// Per spec-delta frontend-core F-FE-6.
//
// Authenticated user-role accounts only. Unauthenticated → redirect
// to /signup. Founders → 403 from GET /api/questions/next, so we
// redirect them to /home (their natural surface).

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { ToolGraph } from "@/components/ToolGraph";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { tagsForAnswerValue } from "@/lib/tag-map";
import type {
  AnswerCreateRequest,
  CommunityCard,
  CommunityListResponse,
  NextQuestionResponse,
  QuestionPayload,
  RecommendationPick,
  RecommendationsResponse,
} from "@/lib/api-types";

// =============================================================================
// Page — auth gate
// =============================================================================
export default function OnboardingPage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/signup");
    } else {
      setAuthChecked(true);
    }
  }, [router]);

  if (!authChecked) return null;
  return <OnboardingTapLoop />;
}

// =============================================================================
// Tap loop + result — authenticated user-role
// =============================================================================
function OnboardingTapLoop() {
  const router = useRouter();
  const [question, setQuestion] = useState<QuestionPayload | null>(null);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(true);
  const [accumulatedTags, setAccumulatedTags] = useState<string[]>([]);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [communities, setCommunities] = useState<CommunityCard[]>([]);

  // Fetch first question on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const next = await api.get<NextQuestionResponse>("/api/questions/next");
        if (cancelled) return;
        if (next.done) {
          setDone(true);
          await loadResult();
        } else {
          setQuestion(next.question);
        }
      } catch (e) {
        // Founder accounts get 403 role_mismatch from /api/questions/next
        // (cycle #2 F-QB-5). Send them to /home where their inbox lives.
        if (e instanceof ApiError && e.status === 403) {
          router.replace("/home");
          return;
        }
        console.error("[onboarding] question fetch failed", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadResult = async () => {
    const [r, c] = await Promise.all([
      api.post<RecommendationsResponse>("/api/recommendations", { count: 5 }),
      api.get<CommunityListResponse>("/api/communities"),
    ]);
    setRecs(r);
    setCommunities(c.communities.slice(0, 3));
  };

  const submitAnswer = async (value: string | string[]) => {
    if (!question) return;
    setLoading(true);
    try {
      const tags = Array.isArray(value)
        ? tagsForAnswerValue(value)
        : tagsForAnswerValue(value);
      setAccumulatedTags((prev) => [...prev, ...tags]);
      setAnsweredCount((n) => n + 1);

      const payload: AnswerCreateRequest = {
        question_id: question.id,
        value,
      };
      const next = await api.post<NextQuestionResponse>("/api/answers", payload);
      if (next.done) {
        setDone(true);
        setQuestion(null);
        await loadResult();
      } else {
        setQuestion(next.question);
      }
    } catch (e) {
      // 400s on validation surface — fall through to console for V1.
      console.error("[onboarding] answer submit failed", e);
    } finally {
      setLoading(false);
    }
  };

  const totalKnown = 5; // best-effort total for the progress bars
  const slotCount = done
    ? 4
    : Math.max(4, Math.round(10 - (answeredCount / totalKnown) * 5));

  return (
    <div className="onb-root">
      <div className={`onb-graph-pane ${done ? "collapsed" : ""}`}>
        <div className="onb-graph-canvas">
          <ToolGraph
            progress={Math.min(1, 0.3 + (answeredCount / totalKnown) * 0.7)}
            highlightedTags={accumulatedTags}
            mode="score"
            gridSlots={slotCount}
            scale={1.4}
          />
        </div>
        <div className="onb-graph-meta mono">
          <div className="onb-graph-meta-row">
            <span className="onb-graph-dot" />
            <span>
              profile · {done ? "matches ready" : `narrowing to ${slotCount}`}
            </span>
          </div>
          <div className="onb-graph-tags">
            {[...new Set(accumulatedTags)].slice(0, 8).map((t) => (
              <span key={t} className="onb-graph-tag">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

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

        {!done && question && (
          <QuestionCard
            question={question}
            onSubmit={submitAnswer}
            answeredCount={answeredCount}
          />
        )}

        {done && recs && <ResultPanel recs={recs} communities={communities} />}
      </div>
    </div>
  );
}

// =============================================================================
// Question card
// =============================================================================
function QuestionCard({
  question,
  onSubmit,
  answeredCount,
}: {
  question: QuestionPayload;
  onSubmit: (value: string | string[]) => void;
  answeredCount: number;
}) {
  const [multiPicked, setMultiPicked] = useState<string[]>([]);
  const [freeText, setFreeText] = useState("");

  // Reset local state when the question changes.
  useEffect(() => {
    setMultiPicked([]);
    setFreeText("");
  }, [question.id]);

  if (question.kind === "single_select") {
    return (
      <div className="onb-q-wrap">
        <div className="onb-q-meta">
          <span className="mono onb-q-count">Question {answeredCount + 1}</span>
        </div>
        <div className="onb-q-card">
          <h1 className="onb-q-title">{question.text}</h1>
          <div className="onb-q-opts">
            {question.options.map((opt, i) => (
              <button
                key={opt.value}
                className="onb-q-opt"
                onClick={() => onSubmit(opt.value)}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <span className="onb-q-bullet">
                  <span className="onb-radio" />
                </span>
                <span className="onb-q-label">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (question.kind === "multi_select") {
    return (
      <div className="onb-q-wrap">
        <div className="onb-q-meta">
          <span className="mono onb-q-count">Question {answeredCount + 1}</span>
        </div>
        <div className="onb-q-card">
          <h1 className="onb-q-title">{question.text}</h1>
          <p className="onb-q-sub">Multi-pick if more than one applies.</p>
          <div className="onb-q-opts">
            {question.options.map((opt, i) => {
              const picked = multiPicked.includes(opt.value);
              return (
                <button
                  key={opt.value}
                  className={`onb-q-opt ${picked ? "on" : ""}`}
                  onClick={() =>
                    setMultiPicked((prev) =>
                      prev.includes(opt.value)
                        ? prev.filter((v) => v !== opt.value)
                        : [...prev, opt.value],
                    )
                  }
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <span className="onb-q-bullet">
                    <span className="onb-check">{picked ? "✓" : ""}</span>
                  </span>
                  <span className="onb-q-label">{opt.label}</span>
                </button>
              );
            })}
          </div>
          <div className="onb-q-multi-foot">
            <span className="mono onb-q-skip">skip ↘</span>
            <MButton
              onClick={() => onSubmit(multiPicked)}
              variant="primary"
            >
              Continue {multiPicked.length > 0 ? `(${multiPicked.length})` : ""} →
            </MButton>
          </div>
        </div>
      </div>
    );
  }

  // free_text
  return (
    <div className="onb-q-wrap">
      <div className="onb-q-meta">
        <span className="mono onb-q-count">Question {answeredCount + 1}</span>
      </div>
      <div className="onb-q-card">
        <h1 className="onb-q-title">{question.text}</h1>
        <div className="onb-q-typeown-input" style={{ marginTop: 24 }}>
          <input
            className="m-input"
            autoFocus
            placeholder="In your words…"
            value={freeText}
            onChange={(e) => setFreeText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && freeText.trim() && onSubmit(freeText.trim())}
          />
          <MButton
            size="sm"
            onClick={() => freeText.trim() && onSubmit(freeText.trim())}
          >
            Continue
          </MButton>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Result panel
// =============================================================================
function ResultPanel({
  recs,
  communities,
}: {
  recs: RecommendationsResponse;
  communities: CommunityCard[];
}) {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const t1 = setTimeout(() => setStage(1), 600);
    const t2 = setTimeout(() => setStage(2), 1400);
    const t3 = setTimeout(() => setStage(3), 2100);
    return () => [t1, t2, t3].forEach(clearTimeout);
  }, []);

  const tries = useMemo(
    () => recs.recommendations.filter((p) => p.verdict === "try").slice(0, 4),
    [recs],
  );
  const skip = useMemo(
    () => recs.recommendations.find((p) => p.verdict === "skip"),
    [recs],
  );

  return (
    <div className="onb-result">
      <div className="onb-result-eyebrow mono">/ for you, today</div>
      <h1 className="onb-result-title">
        Here are the <em>{tries.length || "few"}</em> tools
        <br />
        that actually fit you.
      </h1>
      <p className="onb-result-sub body-lg">
        Built from your stack, your friction, and how you said you work.
        We&apos;ll refine these as your profile sharpens.
      </p>

      <div className={`onb-result-grid stage-${stage}`}>
        {tries.map((p, i) => (
          <ResultCard key={p.tool.slug} pick={p} delay={i * 120} />
        ))}

        {skip && (
          <div
            className="onb-result-skip-card"
            style={{ transitionDelay: `${tries.length * 120}ms` }}
          >
            <span className="onb-skip-tag mono">SKIP THIS ONE</span>
            <div className="h-card" style={{ marginTop: 12 }}>
              {skip.tool.name}
            </div>
            <p className="body" style={{ marginTop: 8 }}>
              {skip.reasoning}
            </p>
            <div className="mono onb-skip-meta">— hyped, not for you</div>
          </div>
        )}
      </div>

      {communities.length > 0 && (
        <div className={`onb-communities ${stage >= 2 ? "in" : ""}`}>
          <div className="onb-result-eyebrow mono" style={{ marginBottom: 16 }}>
            / where peers like you live
          </div>
          <div className="onb-communities-row">
            {communities.map((c, i) => (
              <div
                key={c.slug}
                className="onb-com-pill"
                style={{ animationDelay: `${1400 + i * 100}ms` }}
              >
                <span className={`onb-com-dot axis-${c.category}`} />
                <span className="mono">{c.name}</span>
                <span className="onb-com-members mono">
                  {c.member_count.toLocaleString()}
                </span>
                <button className="onb-com-join">join</button>
              </div>
            ))}
          </div>
        </div>
      )}

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

function ResultCard({
  pick,
  delay,
}: {
  pick: RecommendationPick;
  delay: number;
}) {
  return (
    <div
      className="onb-result-card"
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="onb-result-card-top">
        <div className="onb-result-logo">
          <div className="onb-result-logo-inner">{pick.tool.name[0]}</div>
        </div>
        <div className="onb-result-name">
          <div className="h-card">{pick.tool.name}</div>
          <div className="mono onb-result-tag">{pick.tool.category}</div>
        </div>
        <button className="onb-result-save">♡</button>
      </div>
      <p className="body" style={{ marginTop: 16 }}>
        {pick.reasoning}
      </p>
      <div className="onb-result-card-actions">
        <MButton size="sm" variant="ghost">
          Save
        </MButton>
        <a href={pick.tool.url} target="_blank" rel="noreferrer">
          <MButton size="sm" variant="quiet" trailing="↗">
            Open
          </MButton>
        </a>
      </div>
    </div>
  );
}
