"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { MButton, MeshMark, useInView } from "@/components/Primitives";

// =============================================================================
// COMMUNITIES
// =============================================================================
type Axis = "role" | "tool" | "problem";
const COMMUNITY_DATA: Record<
  Axis,
  {
    label: string;
    desc: string;
    items: { name: string; members: string; last: string; sample: string }[];
  }
> = {
  role: {
    label: "By role",
    desc: "People doing the same job you do.",
    items: [
      { name: "r/growth-marketers", members: "2,418", last: "12 min ago", sample: "Replaced HubSpot with Attio + Granola — month one" },
      { name: "r/solo-founders", members: "4,803", last: "2 min ago", sample: "My weekly stack — 6 tools, $32/mo" },
      { name: "r/staff-pms", members: "1,127", last: "40 min ago", sample: "Cursor for PRDs is unhinged but works" },
    ],
  },
  tool: {
    label: "By tool",
    desc: "People going deep on the same tools you use.",
    items: [
      { name: "r/notion-power-users", members: "8,902", last: "5 min ago", sample: "Database that doubles as your CRM (no Make)" },
      { name: "r/cursor-builders", members: "3,217", last: "1 min ago", sample: "Best prompt for refactoring legacy React" },
      { name: "r/claude-projects", members: "2,664", last: "23 min ago", sample: "A Claude project that runs my whole sprint" },
    ],
  },
  problem: {
    label: "By problem",
    desc: "Sorted by the friction, not the software.",
    items: [
      { name: "r/email-time-killers", members: "1,089", last: "8 min ago", sample: "Down to 12 minutes a day. Here's the routine." },
      { name: "r/replacing-saas-with-ai", members: "5,560", last: "3 min ago", sample: "Killed 4 tools this month. Saved $89." },
      { name: "r/meeting-notes-fatigue", members: "1,734", last: "15 min ago", sample: "Granola vs Fireflies after 30 days" },
    ],
  },
};

export function CommunitiesSection() {
  const [ref, inView] = useInView<HTMLElement>({ threshold: 0.2 });
  const [axis, setAxis] = useState<Axis>("role");
  const cur = COMMUNITY_DATA[axis];

  return (
    <section className="section" id="communities" ref={ref}>
      <div className="m-com-head">
        <div>
          <div className="eyebrow">/ communities</div>
          <h2 className="h-section">
            The room your
            <br />
            users are already in.
          </h2>
        </div>
        <p className="body-lg" style={{ marginLeft: "auto", maxWidth: "40ch" }}>
          Sorted three ways: by what people do, by what they use, and by
          what&apos;s wasting their time. Find the one that matches yours.
        </p>
      </div>

      <div className="m-com-axes">
        {(Object.entries(COMMUNITY_DATA) as [Axis, (typeof COMMUNITY_DATA)[Axis]][]).map(
          ([k, v]) => (
            <button
              key={k}
              className={`m-com-axis ${axis === k ? "on" : ""}`}
              onClick={() => setAxis(k)}
              data-axis={k}
            >
              <span className="m-com-axis-dot" />
              {v.label}
            </button>
          ),
        )}
      </div>

      <p className="body" style={{ color: "var(--ink-2)", marginBottom: 24 }}>
        {cur.desc}
      </p>

      <div className="m-com-grid">
        {cur.items.map((it, i) => (
          <div
            key={it.name}
            className={`m-com-card m-card ${inView ? "in" : ""}`}
            style={{ transitionDelay: `${i * 80}ms` }}
            data-anchor-id={`com-${i}`}
            data-anchor-tags={["pm", "dev", "design"][i]}
          >
            <div className="m-com-card-top">
              <span className="mono m-com-name">{it.name}</span>
              <span className="m-com-live">
                <span className="m-live-dot" />
                {it.last}
              </span>
            </div>
            <div className="m-com-sample">{it.sample}</div>
            <div className="m-com-foot">
              <span className="mono" style={{ color: "var(--ink-2)" }}>
                {it.members} members
              </span>
              <span className="m-com-join">join →</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// =============================================================================
// FOR FOUNDERS
// =============================================================================
export function FoundersSection() {
  const [ref, inView] = useInView<HTMLElement>({ threshold: 0.15 });
  return (
    <section className="section m-founders" id="founders" ref={ref}>
      <div className="m-founders-grid">
        <div className="m-founders-text">
          <div className="eyebrow">/ for founders</div>
          <h2 className="h-section">
            Reach users who&apos;d
            <br />
            actually use it.
          </h2>
          <p className="body-lg" style={{ marginTop: 24 }}>
            We match your product to people whose workflow it fits. Six
            communities, real conversations, the kind of feedback you can ship
            against.
          </p>
          <div className="m-founders-cta">
            <Link href="/signup?role=founder">
              <MButton>Launch on Mesh →</MButton>
            </Link>
            <Link href="/login">
              <MButton variant="quiet">Sign in</MButton>
            </Link>
          </div>
        </div>
        <div
          className={`m-founders-viz ${inView ? "in" : ""}`}
          data-anchor-id="founders"
          data-anchor-tags=""
        >
          <FounderMatchViz />
        </div>
      </div>
    </section>
  );
}

function FounderMatchViz() {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    let raf = 0;
    const t0 = performance.now();
    const tick = (now: number) => {
      const t = (now - t0) / 1000;
      if (ref.current) {
        const pulses = ref.current.querySelectorAll<SVGCircleElement>(".fmv-pulse");
        pulses.forEach((p, i) => {
          const phase = (t * 0.4 + i * 0.18) % 1;
          (p.style as CSSStyleDeclaration & { offsetDistance: string }).offsetDistance = `${phase * 100}%`;
          p.style.opacity = phase < 0.05 || phase > 0.95 ? "0" : "1";
        });
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);
  const targets = [
    { x: 80, y: 50, name: "r/growth-marketers", match: 92 },
    { x: 86, y: 130, name: "r/replacing-saas-w-ai", match: 89 },
    { x: 82, y: 220, name: "r/email-time-killers", match: 84 },
    { x: 460, y: 60, name: "r/notion-power-users", match: 91 },
    { x: 478, y: 150, name: "r/solo-founders", match: 88 },
    { x: 462, y: 240, name: "r/staff-pms", match: 76 },
  ];
  return (
    <svg ref={ref} viewBox="0 0 560 320" className="m-fmv">
      <defs>
        <radialGradient id="fmv-glow">
          <stop offset="0%" stopColor="oklch(0.85 0.16 295 / 0.5)" />
          <stop offset="100%" stopColor="oklch(0.75 0.16 295 / 0)" />
        </radialGradient>
      </defs>
      {targets.map((t, i) => (
        <g key={i}>
          <path
            id={`fmv-path-${i}`}
            d={`M 280 160 Q ${(280 + t.x) / 2} ${(160 + t.y) / 2 - 30} ${t.x} ${t.y}`}
            fill="none"
            stroke="oklch(0.75 0.16 295 / 0.3)"
            strokeWidth="1"
            strokeDasharray="2 3"
          />
          <circle
            r="3"
            fill="oklch(0.92 0.1 295)"
            className="fmv-pulse"
            style={{
              offsetPath: `path('M 280 160 Q ${(280 + t.x) / 2} ${(160 + t.y) / 2 - 30} ${t.x} ${t.y}')`,
            } as React.CSSProperties}
          />
        </g>
      ))}
      <circle cx="280" cy="160" r="44" fill="url(#fmv-glow)" />
      <circle
        cx="280"
        cy="160"
        r="28"
        fill="oklch(0.16 0.014 280)"
        stroke="oklch(0.75 0.16 295 / 0.6)"
        strokeWidth="1"
      />
      <text x="280" y="155" textAnchor="middle" fill="oklch(0.95 0.01 280)" fontFamily="Geist Mono" fontSize="11">your</text>
      <text x="280" y="170" textAnchor="middle" fill="oklch(0.95 0.01 280)" fontFamily="Geist Mono" fontSize="11">product</text>
      {targets.map((t, i) => (
        <g key={`n${i}`}>
          <circle cx={t.x} cy={t.y} r="22" fill="oklch(0.19 0.016 280)" stroke="oklch(0.32 0.022 280 / 0.7)" />
          <text x={t.x} y={t.y - 28} fill="oklch(0.78 0.012 280)" fontSize="9" fontFamily="Geist Mono" textAnchor="middle">{t.name}</text>
          <text x={t.x} y={t.y + 4} fill="oklch(0.92 0.08 295)" fontSize="11" fontFamily="Geist Mono" textAnchor="middle">{t.match}%</text>
        </g>
      ))}
    </svg>
  );
}

// =============================================================================
// NUDGE PREVIEW
// =============================================================================
export function NudgePreview() {
  const [ref, inView] = useInView<HTMLElement>({ threshold: 0.4 });
  return (
    <section className="section m-nudge" ref={ref}>
      <div className="m-nudge-grid">
        <div>
          <div className="eyebrow">/ a friend, not an ad</div>
          <h2 className="h-section">
            A high bar
            <br />
            before we tell you.
          </h2>
          <p className="body-lg" style={{ marginTop: 20 }}>
            We only mention a new tool when it scores in the top five percent
            for how you work. If it shows up here, we&apos;d send it to a friend.
          </p>
        </div>
        <div
          className={`m-nudge-stack ${inView ? "in" : ""}`}
          data-anchor-id="nudge"
          data-anchor-tags="ai"
        >
          <div className="m-nudge-card">
            <div className="m-nudge-avatar">
              <MeshMark size={20} />
            </div>
            <div className="m-nudge-body">
              <div className="m-nudge-line">
                <span className="mono m-nudge-meta">match · 92%</span>
              </div>
              <div className="m-nudge-msg">
                You said the Notion → Linear sync eats 40 minutes.{" "}
                <strong>Stride</strong> ships that exact thing. One of three
                this week.
              </div>
              <div className="m-nudge-actions">
                <MButton size="sm">Show me</MButton>
                <MButton size="sm" variant="quiet">
                  Skip
                </MButton>
              </div>
            </div>
            <button className="m-nudge-x">✕</button>
          </div>
          <div className="m-nudge-card m-nudge-card-2">
            <div className="m-nudge-meta-2 mono">— and what we held back</div>
            <div className="m-nudge-skip">
              <span className="m-nudge-skip-tag mono">SKIP</span>
              <div>
                <div className="m-nudge-skip-name">A loud new note app</div>
                <div className="body" style={{ color: "var(--ink-2)" }}>
                  You&apos;re already on Reflect. Switching costs four hours,
                  saves eleven minutes a week.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// MANIFESTO
// =============================================================================
export function Manifesto() {
  const [ref, inView] = useInView<HTMLElement>({ threshold: 0.2 });
  const lines = ["Software should bend to you.", "Not the other way around."];
  return (
    <section className="section m-manifesto" ref={ref}>
      <div className={`m-manifesto-text ${inView ? "in" : ""}`}>
        {lines.map((l, i) => (
          <div
            key={i}
            className="m-manifesto-line"
            style={{ transitionDelay: `${i * 200}ms` }}
          >
            {l}
          </div>
        ))}
      </div>
      <div className="m-manifesto-sig mono">— mesh, 2026</div>
    </section>
  );
}

// =============================================================================
// FINAL CTA + FOOTER
// =============================================================================
export function FinalCTA() {
  return (
    <section className="section m-final-cta">
      <div className="m-final-cta-card">
        <div className="m-final-cta-gradient" />
        <div className="m-final-cta-content">
          <h2 className="h-section">
            A few minutes.
            <br />
            A stack that fits.
          </h2>
          <div className="m-final-cta-row">
            <Link href="/signup?role=user">
              <MButton size="lg">Find my stack →</MButton>
            </Link>
            <span className="mono" style={{ color: "var(--ink-2)" }}>
              email + password — 30 seconds
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="m-footer">
      <div className="m-footer-inner">
        <div className="m-footer-brand">
          <MeshMark size={20} />
          <span>Mesh</span>
        </div>
        <div className="m-footer-cols">
          <div>
            <div className="eyebrow">Product</div>
            <a>Onboarding</a>
            <a>Communities</a>
            <a>Tools</a>
            <a>Inbox</a>
          </div>
          <div>
            <div className="eyebrow">Founders</div>
            <a>Launch</a>
            <a>Analytics</a>
            <a>Reviews</a>
            <a>Pricing</a>
          </div>
          <div>
            <div className="eyebrow">Company</div>
            <a>About</a>
            <a>Manifesto</a>
            <a>Careers</a>
            <a>Press</a>
          </div>
        </div>
        <div className="m-footer-copy mono">
          <span>mesh / 2026</span>
          <span>quieter than product hunt</span>
        </div>
      </div>
    </footer>
  );
}
