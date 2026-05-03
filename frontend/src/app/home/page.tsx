"use client";

// Mesh — User home / "your stack"
// Per spec-delta frontend-core F-FE-7.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MeshMark } from "@/components/Primitives";
import { ToolGraph } from "@/components/ToolGraph";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated, logout } from "@/lib/auth";
import type {
  JoinedCommunityCard,
  JoinedCommunityListResponse,
  NotificationCard,
  NotificationListResponse,
  RecommendationPick,
  RecommendationsResponse,
  UnreadCountResponse,
  UserPublic,
  UserToolCard,
  UserToolListResponse,
} from "@/lib/api-types";

// V1 hardcoded activity feed — V1.5 backend builds the cross-user
// activity stream endpoint.
const ACTIVITY = [
  { who: "Maya", role: "founder, Granola", what: "just shipped multi-language transcripts", when: "12m", dot: "warm" },
  { who: "Theo", role: "in your community", what: "left Notion for Mem after 4 yrs", when: "2h", dot: "cool" },
  { who: "Mesh", role: "concierge", what: "matched you to 2 new founders", when: "5h", dot: "pulse" },
  { who: "Riya", role: "in r/staff-pms", what: 'asked: "anyone else find Linear too rigid?"', when: "1d", dot: "warm" },
  { who: "Nico", role: "founder, Reflect", what: "is doing office hours next Thursday", when: "2d", dot: "cool" },
];

// Notification kind → design's nudge UI taxonomy.
function nudgeKindFor(kind: string): "pattern" | "fresh" | "mod" | "skip" {
  if (kind === "concierge_nudge") return "fresh";
  if (kind === "launch_approved" || kind === "launch_rejected") return "mod";
  if (kind === "community_reply") return "pattern";
  return "fresh";
}

function nudgeTitleFor(n: NotificationCard): string {
  if (n.kind === "concierge_nudge") {
    const slug = (n.payload as { tool_slug?: string }).tool_slug;
    return `A new launch matched your profile${slug ? `: ${slug}` : ""}`;
  }
  if (n.kind === "launch_approved") return "Your launch was approved";
  if (n.kind === "launch_rejected") return "Your launch needs another pass";
  if (n.kind === "community_reply") {
    const who = (n.payload as { commenter_display_name?: string })
      .commenter_display_name;
    return `${who || "Someone"} replied to your post`;
  }
  return n.kind;
}

function relativeTime(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  return `${d}d`;
}

// =============================================================================
// Page
// =============================================================================
export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [unread, setUnread] = useState(0);
  const [notes, setNotes] = useState<NotificationCard[]>([]);
  const [recs, setRecs] = useState<RecommendationsResponse | null>(null);
  const [tools, setTools] = useState<UserToolCard[]>([]);
  const [communities, setCommunities] = useState<JoinedCommunityCard[]>([]);
  const [activeNav, setActiveNav] = useState("home");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/onboarding");
      return;
    }
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadAll = async () => {
    try {
      const [me, uc, nl, r, mt, mc] = await Promise.all([
        api.get<UserPublic>("/api/me"),
        api.get<UnreadCountResponse>("/api/me/notifications/unread-count"),
        api.get<NotificationListResponse>(
          "/api/me/notifications?unread_only=false&limit=4",
        ),
        api.post<RecommendationsResponse>("/api/recommendations", { count: 5 }).catch(
          (e) => {
            // 400 no_profile_yet — user hasn't answered enough questions.
            if (e instanceof ApiError && e.status === 400) return null;
            throw e;
          },
        ),
        api.get<UserToolListResponse>("/api/me/tools"),
        api.get<JoinedCommunityListResponse>("/api/me/communities"),
      ]);
      setUser(me);
      setUnread(uc.count);
      setNotes(nl.notifications);
      setRecs(r);
      setTools(mt.tools);
      setCommunities(mc.communities);
    } catch (e) {
      console.error("[home] load failed", e);
    }
  };

  if (!user) {
    return (
      <div className="mono" style={{ padding: 64, color: "var(--ink-2)" }}>
        loading…
      </div>
    );
  }

  const stackSize = tools.length;
  const communityUnread = communities.length; // V1: unread per community is V1.5

  return (
    <div className="home-root">
      <HomeLeftRail
        active={activeNav}
        onSelect={setActiveNav}
        user={user}
        tools={tools}
        unread={unread}
        stackSize={stackSize}
        communityUnread={communityUnread}
        onLogout={() => logout()}
      />
      <HomeCenter
        user={user}
        unread={unread}
        notes={notes}
        recs={recs}
        communities={communities}
      />
      <HomeRightRail user={user} />
    </div>
  );
}

// =============================================================================
// Left rail
// =============================================================================
function HomeLeftRail({
  active,
  onSelect,
  user,
  tools,
  unread,
  stackSize,
  communityUnread,
  onLogout,
}: {
  active: string;
  onSelect: (v: string) => void;
  user: UserPublic;
  tools: UserToolCard[];
  unread: number;
  stackSize: number;
  communityUnread: number;
  onLogout: () => void;
}) {
  const navItems = [
    { id: "home", label: "Home", glyph: "◉", count: 0 },
    { id: "nudges", label: "Nudges", glyph: "~", count: unread },
    { id: "stack", label: "Your stack", glyph: "▦", count: stackSize },
    { id: "discover", label: "Discover", glyph: "✦", count: 0 },
    { id: "rooms", label: "Communities", glyph: "◌", count: communityUnread },
    { id: "profile", label: "Profile", glyph: "◎", count: 0 },
  ];
  return (
    <aside className="home-rail home-rail-left">
      <div className="home-brand-row">
        <Link href="/" className="home-brand">
          <MeshMark size={20} />
          <span>Mesh</span>
        </Link>
        <button className="home-rail-collapse mono" title="Collapse">⟨</button>
      </div>
      <nav className="home-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`home-nav-item ${active === item.id ? "on" : ""}`}
            onClick={() => onSelect(item.id)}
          >
            <span className="home-nav-glyph">{item.glyph}</span>
            <span className="home-nav-label">{item.label}</span>
            {item.count > 0 && (
              <span className="home-nav-count mono">{item.count}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="home-rail-section">
        <div className="home-rail-heading mono">Your stack</div>
        <div className="home-stack-list">
          {tools.length === 0 && (
            <div className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
              no tools yet — answer onboarding to populate
            </div>
          )}
          {tools.slice(0, 6).map((t) => (
            <div key={t.id} className="home-stack-item">
              <div className="home-stack-logo">
                <span>{t.tool.name[0]}</span>
                <span
                  className={`home-stack-pulse pulse-${t.status === "using" ? "high" : "med"}`}
                />
              </div>
              <div className="home-stack-meta">
                <div className="home-stack-name">{t.tool.name}</div>
                <div className="mono home-stack-status">
                  {t.status} · {t.source.replace(/_/g, " ")}
                </div>
              </div>
            </div>
          ))}
        </div>
        <Link href="/onboarding" className="home-stack-add mono">+ refine profile</Link>
      </div>

      <div className="home-rail-foot">
        <div className="home-profile">
          <div className="home-profile-avatar">
            {user.display_name[0]?.toUpperCase() || "?"}
          </div>
          <div className="home-profile-meta">
            <div className="home-profile-name">@{user.display_name}</div>
            <div className="mono home-profile-tag">
              {user.role_type === "user" ? "ai-curious" : "founder"}
            </div>
          </div>
          <button
            className="home-profile-set mono"
            onClick={onLogout}
            title="Log out"
          >
            ⏻
          </button>
        </div>
      </div>
    </aside>
  );
}

// =============================================================================
// Center
// =============================================================================
function HomeCenter({
  user,
  unread,
  notes,
  recs,
  communities,
}: {
  user: UserPublic;
  unread: number;
  notes: NotificationCard[];
  recs: RecommendationsResponse | null;
  communities: JoinedCommunityCard[];
}) {
  const fresh: RecommendationPick[] = recs
    ? [...recs.recommendations, ...recs.launches]
    : [];

  return (
    <main className="home-center">
      <header className="home-center-header">
        <div>
          <div className="mono home-eyebrow">/ home · today</div>
          <h1 className="home-greeting">
            {greetingFor()}, {user.display_name}.{" "}
            {unread > 0 ? <em>{unread} nudges</em> : <em>your inbox is calm</em>}
            {unread > 0 && " are warm."}
          </h1>
          <p className="home-subgreet body">
            We&apos;re watching your stack and your communities for patterns.
          </p>
        </div>
      </header>

      <section className="home-section">
        <div className="home-section-head">
          <h2 className="home-section-title">
            Nudges <span className="mono home-section-count">{notes.length}</span>
          </h2>
        </div>
        <div className="home-nudges">
          {notes.length === 0 && (
            <div className="mono" style={{ color: "var(--ink-3)" }}>
              no nudges yet — Mesh will surface patterns as your profile compounds
            </div>
          )}
          {notes.map((n, i) => (
            <NudgeCard key={n.id} n={n} delay={i * 80} />
          ))}
        </div>
      </section>

      {fresh.length > 0 && (
        <section className="home-section">
          <div className="home-section-head">
            <h2 className="home-section-title">Fresh for you</h2>
            {recs?.from_cache && (
              <span className="mono home-section-meta">cached · refresh in &lt;7d</span>
            )}
          </div>
          <div className="home-fresh-strip">
            {fresh.map((p, i) => (
              <FreshCard
                key={`${p.tool.slug}-${i}`}
                pick={p}
                isLaunch={recs!.launches.includes(p)}
                delay={i * 70}
              />
            ))}
          </div>
        </section>
      )}

      <section className="home-section">
        <div className="home-section-head">
          <h2 className="home-section-title">Your communities</h2>
        </div>
        <div className="home-coms">
          {communities.length === 0 && (
            <div className="mono" style={{ color: "var(--ink-3)" }}>
              you haven&apos;t joined any rooms yet
            </div>
          )}
          {communities.map((c) => (
            <div key={c.slug} className="home-com-row">
              <span className={`onb-com-dot axis-${c.category}`} />
              <span className="mono home-com-name">{c.name}</span>
              <span className="mono home-com-members">
                {c.member_count.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

function greetingFor(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function NudgeCard({ n, delay }: { n: NotificationCard; delay: number }) {
  const kind = nudgeKindFor(n.kind);
  const title = nudgeTitleFor(n);
  const pulse = kind === "skip" ? "dim" : kind === "fresh" ? "cool" : "warm";
  const kindLabel = {
    pattern: "pattern detected",
    fresh: "fresh",
    mod: "event",
    skip: "skip",
  }[kind];

  return (
    <article
      className={`home-nudge home-nudge-${kind} pulse-${pulse}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="home-nudge-rail" />
      <div className="home-nudge-head">
        <span className="mono home-nudge-kind">{kindLabel}</span>
        <span className="mono home-nudge-when">· {relativeTime(n.created_at)} ago</span>
      </div>
      <h3 className="home-nudge-title">{title}</h3>
      <div className="home-nudge-actions">
        {n.kind === "concierge_nudge" && (
          <button
            className="home-nudge-cta"
            onClick={async () => {
              await api.post("/api/concierge/respond", {
                launch_id: (n.payload as { launch_id?: string }).launch_id,
                action: "tell_me_more",
              });
            }}
          >
            tell me more →
          </button>
        )}
      </div>
    </article>
  );
}

function FreshCard({
  pick,
  isLaunch,
  delay,
}: {
  pick: RecommendationPick;
  isLaunch: boolean;
  delay: number;
}) {
  const fitPct = Math.round(pick.score * 100);
  return (
    <Link href={`/p/${pick.tool.slug}`}>
      <article className="home-fresh-card" style={{ animationDelay: `${delay}ms` }}>
        <div className="home-fresh-logo">{pick.tool.name[0]}</div>
        <div className="home-fresh-name">
          {pick.tool.name}
          {isLaunch && (
            <span className="mono" style={{ marginLeft: 6, color: "var(--accent)" }}>
              🚀
            </span>
          )}
        </div>
        <div className="mono home-fresh-tag">{pick.tool.category}</div>
        <div className="home-fresh-fit">
          <span className="home-fresh-fit-bar">
            <span className="home-fresh-fit-fill" style={{ width: `${fitPct}%` }} />
          </span>
          <span className="mono home-fresh-fit-pct">{fitPct}</span>
        </div>
        <div className="home-fresh-why body">{pick.reasoning}</div>
      </article>
    </Link>
  );
}

// =============================================================================
// Right rail
// =============================================================================
function HomeRightRail({ user }: { user: UserPublic }) {
  // Profile graph: in V1 we just show a static set of common tags.
  // V1.5 would derive from /api/me answers.
  const tags = ["writing", "pm", "meetings", "ai", "productivity"];
  return (
    <aside className="home-rail home-rail-right">
      <div className="home-rail-heading mono">Your profile graph</div>
      <div className="home-mini-graph">
        <ToolGraph
          progress={1}
          highlightedTags={tags}
          mode="score"
          gridSlots={5}
          scale={0.85}
        />
      </div>
      <div className="home-rail-tags">
        {tags.map((t) => (
          <span key={t} className="onb-graph-tag">
            {t}
          </span>
        ))}
      </div>
      <Link href="/onboarding" className="mono home-rail-refine">
        refine profile ↗
      </Link>

      <div className="home-rail-divider" />

      <div className="home-rail-heading mono">Recent activity</div>
      <div className="home-activity">
        {ACTIVITY.map((a, i) => (
          <div key={i} className="home-activity-row">
            <span className={`home-act-dot dot-${a.dot}`} />
            <div className="home-act-content">
              <div className="home-act-text body-sm">
                <span className="home-act-who">{a.who}</span>{" "}
                <span className="home-act-role mono">— {a.role}</span>
              </div>
              <div className="home-act-what body-sm">{a.what}</div>
              <div className="mono home-act-when">{a.when}</div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
