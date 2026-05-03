"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  MButton,
  MeshMark,
  useInView,
} from "@/components/Primitives";

// =============================================================================
// NAV
// =============================================================================
export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <nav className={`m-nav ${scrolled ? "m-nav-scrolled" : ""}`}>
      <div className="m-nav-inner">
        <Link href="/" className="m-nav-brand">
          <MeshMark size={22} />
          <span>Mesh</span>
        </Link>
        <div className="m-nav-links">
          <a href="#how">How it works</a>
          <a href="#tools">Tools</a>
          <a href="#communities">Communities</a>
          <a href="#founders">For founders</a>
        </div>
        <div className="m-nav-actions">
          <Link href="/login" className="m-nav-link">
            Sign in
          </Link>
          <Link href="/signup">
            <MButton size="sm">Get started</MButton>
          </Link>
        </div>
      </div>
    </nav>
  );
}

// =============================================================================
// HERO
// =============================================================================
type Side = "user" | "founder";

export function Hero({
  onGraphTags,
}: {
  onGraphTags: (tags: string[]) => void;
}) {
  const [side, setSide] = useState<Side>("user");
  const isUser = side === "user";

  return (
    <section className="m-hero">
      <div className="m-hero-content">
        <div
          className="m-hero-toggle fade-up"
          role="tablist"
          aria-label="Who are you"
        >
          <button
            role="tab"
            aria-selected={isUser}
            className={`m-hero-toggle-btn ${isUser ? "on" : ""}`}
            onClick={() => setSide("user")}
          >
            I&apos;m finding my right AI tools
          </button>
          <button
            role="tab"
            aria-selected={!isUser}
            className={`m-hero-toggle-btn ${!isUser ? "on" : ""}`}
            onClick={() => setSide("founder")}
          >
            I want to launch my new product
          </button>
          <span
            className={`m-hero-toggle-pill ${isUser ? "left" : "right"}`}
            aria-hidden="true"
          />
        </div>

        <div className="m-hero-swap" key={side}>
          {isUser ? (
            <>
              <h1 className="h-display m-hero-title">
                <span className="fade-up fade-up-d1">Stop installing</span>
                <br />
                <span className="fade-up fade-up-d2">
                  every <em className="m-hero-em">new</em> AI tool.
                </span>
              </h1>
              <p className="body-lg m-hero-sub fade-up fade-up-d3">
                Answer a few questions about how you actually work. Get a short
                list of tools that fit — and a list of the loud ones to ignore.
              </p>
              <div className="m-hero-cta fade-up fade-up-d4">
                <Link href="/signup?role=user">
                  <MButton size="lg" trailing="→">
                    Find my stack
                  </MButton>
                </Link>
                <Link href="/login">
                  <MButton variant="ghost" size="lg">
                    Sign in
                  </MButton>
                </Link>
                <span className="mono m-hero-meta">3 minutes · email &amp; password</span>
              </div>
            </>
          ) : (
            <>
              <h1 className="h-display m-hero-title">
                <span className="fade-up fade-up-d1">Reach the people</span>
                <br />
                <span className="fade-up fade-up-d2">
                  who&apos;d <em className="m-hero-em">actually</em> use it.
                </span>
              </h1>
              <p className="body-lg m-hero-sub fade-up fade-up-d3">
                Skip the launch-day vanity numbers. We match your product to
                people whose workflow it fits, in the communities they&apos;re
                already in.
              </p>
              <div className="m-hero-cta fade-up fade-up-d4">
                <Link href="/signup?role=founder">
                  <MButton size="lg" trailing="→">
                    Launch on Mesh
                  </MButton>
                </Link>
                <Link href="/login">
                  <MButton variant="ghost" size="lg">
                    Sign in
                  </MButton>
                </Link>
                <span className="mono m-hero-meta">free during beta</span>
              </div>
            </>
          )}
        </div>

        <HeroSignals side={side} onTagHover={onGraphTags} />
      </div>
    </section>
  );
}

function HeroSignals({
  side,
  onTagHover,
}: {
  side: Side;
  onTagHover: (tags: string[]) => void;
}) {
  const userItems = [
    { tag: "writing", label: "I write a lot" },
    { tag: "design", label: "I do design" },
    { tag: "pm", label: "I run a team" },
    { tag: "dev", label: "I ship code" },
    { tag: "sales", label: "I run sales" },
  ];
  const founderItems = [
    { tag: "writing", label: "I built a writing tool" },
    { tag: "pm", label: "I built for PMs" },
    { tag: "dev", label: "I built a dev tool" },
    { tag: "design", label: "I built for designers" },
    { tag: "crm", label: "I built a CRM" },
  ];
  const items = side === "user" ? userItems : founderItems;
  const eyebrow = side === "user" ? "What's your day?" : "Who is it for?";

  return (
    <div className="m-hero-signals fade-up fade-up-d4" key={side}>
      <span className="eyebrow" style={{ marginRight: 8 }}>
        {eyebrow}
      </span>
      {items.map((it, i) => (
        <button
          key={it.tag + side}
          className="m-signal"
          onMouseEnter={() => onTagHover([it.tag])}
          onMouseLeave={() => onTagHover([])}
          style={{ animationDelay: `${600 + i * 80}ms` }}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

// =============================================================================
// TAP, DON'T TYPE
// =============================================================================
export function TapDontType({
  onAnswer,
}: {
  onAnswer: (tags: string[]) => void;
}) {
  const [step, setStep] = useState(0);
  const [picked, setPicked] = useState<Record<number, { l: string; tag: string }>>({});
  const questions = [
    {
      q: "What's your day mostly?",
      opts: [
        { l: "Writing & docs", tag: "writing" },
        { l: "Shipping product", tag: "pm" },
        { l: "Code / building", tag: "dev" },
        { l: "Design work", tag: "design" },
      ],
    },
    {
      q: "Where does your time leak?",
      opts: [
        { l: "Switching apps", tag: "productivity" },
        { l: "Meetings & notes", tag: "meetings" },
        { l: "Email triage", tag: "email" },
        { l: "Manual research", tag: "research" },
      ],
    },
    {
      q: "Stack you live in?",
      opts: [
        { l: "Notion + Linear", tag: "pm" },
        { l: "Cursor + Claude", tag: "dev" },
        { l: "Figma + Framer", tag: "design" },
        { l: "Mostly browser", tag: "browser" },
      ],
    },
  ];
  const cur = questions[step];

  const pick = (opt: { l: string; tag: string }) => {
    setPicked({ ...picked, [step]: opt });
    onAnswer([opt.tag]);
    setTimeout(() => setStep((s) => (s + 1) % questions.length), 700);
  };

  return (
    <div className="m-tap-card">
      <div className="m-tap-meta">
        <span className="mono">
          Question {step + 1} of {questions.length}
        </span>
        <div className="m-tap-bars">
          {questions.map((_, i) => (
            <span key={i} className={`m-tap-bar ${i <= step ? "on" : ""}`} />
          ))}
        </div>
      </div>
      <div className="m-tap-q">{cur.q}</div>
      <div className="m-tap-opts">
        {cur.opts.map((o, i) => (
          <button
            key={o.l + step}
            className={`m-tap-opt ${picked[step]?.l === o.l ? "on" : ""}`}
            onClick={() => pick(o)}
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <span className="m-tap-key mono">{i + 1}</span>
            <span>{o.l}</span>
            <span className="m-tap-arrow">↵</span>
          </button>
        ))}
      </div>
      <a className="m-tap-skip mono">type your own ↗</a>
    </div>
  );
}

// =============================================================================
// HOW IT WORKS
// =============================================================================
export function HowItWorks() {
  const [ref, inView] = useInView<HTMLElement>({ threshold: 0.15 });
  const steps = [
    { n: "01", t: "Answer, don't type", d: "A handful of questions about your role, your stack, and what burns your time. Tap through it on your phone." },
    { n: "02", t: "Watch your stack form", d: "The graph behind this page reorganizes as you answer. Tools you'd use pull closer; the rest fade." },
    { n: "03", t: "A short list", d: "Five or six tools that fit how you work — and the overhyped ones to skip, with a one-line reason for each." },
  ];
  return (
    <section className="section" id="how" ref={ref}>
      <div className="eyebrow">/ how it works</div>
      <h2 className="h-section m-how-title">
        Recommendations shaped by <em>you,</em> not the launch calendar.
      </h2>
      <div className="m-how-grid">
        {steps.map((s, i) => (
          <div
            key={s.n}
            className={`m-how-step ${inView ? "in" : ""}`}
            style={{ transitionDelay: `${i * 120}ms` }}
            data-anchor-id={`how-${i}`}
            data-anchor-tags={["writing", "ai", "pm"][i]}
          >
            <div className="m-how-num mono">{s.n}</div>
            <div className="h-card">{s.t}</div>
            <p className="body" style={{ marginTop: 8 }}>
              {s.d}
            </p>
          </div>
        ))}
        <svg
          className="m-how-lines"
          viewBox="0 0 100 4"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <line
            x1="0"
            y1="2"
            x2="100"
            y2="2"
            stroke="oklch(0.75 0.16 295 / 0.4)"
            strokeWidth="0.4"
            strokeDasharray="1 2"
            className={inView ? "m-how-line-in" : ""}
          />
        </svg>
      </div>
    </section>
  );
}

// =============================================================================
// THE GRAPH IS YOU
// =============================================================================
export function TheGraphIsYou({
  onAnswer,
}: {
  onAnswer: (tags: string[]) => void;
}) {
  const [ref] = useInView<HTMLElement>({ threshold: 0.2 });
  return (
    <section className="section m-graph-demo" id="tools" ref={ref}>
      <div className="m-graph-demo-text">
        <div className="eyebrow">/ try it</div>
        <h2 className="h-section">
          One question.
          <br />
          The graph <em>moves.</em>
        </h2>
        <p className="body-lg" style={{ marginTop: 20 }}>
          Pick an answer. The network behind this page rearranges around it —
          tools that fit you come forward, the rest pull back. The real version
          asks more, and gets sharper.
        </p>
        <p className="body" style={{ marginTop: 16, color: "var(--ink-2)" }}>
          Pick one →
        </p>
      </div>
      <div
        className="m-graph-demo-card"
        data-anchor-id="demo"
        data-anchor-tags="ai"
      >
        <TapDontType onAnswer={onAnswer} />
      </div>
    </section>
  );
}
