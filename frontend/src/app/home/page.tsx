"use client";

// Mesh — User home / "your stack"
// Per spec-delta frontend-core F-FE-7.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MeshMark } from "@/components/Primitives";
import { ToolGraph } from "@/components/ToolGraph";
import { HeaderBell } from "@/components/HeaderBell";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated, logout } from "@/lib/auth";
import { isAdmin, probeAdminAndCache } from "@/lib/admin";
import { tagsForAnswerValue } from "@/lib/tag-map";
import type {
  DashboardLaunchCard,
  DashboardResponse,
  JoinedCommunityCard,
  JoinedCommunityListResponse,
  NotificationCard,
  NotificationListResponse,
  ProfileSummaryResponse,
  RecommendationPick,
  RecommendationsResponse,
  StackToolEntry,
  UnreadCountResponse,
  UserPublic,
} from "@/lib/api-types";

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
  const [stack, setStack] = useState<StackToolEntry[]>([]);
  const [profileTags, setProfileTags] = useState<string[]>([]);
  const [communities, setCommunities] = useState<JoinedCommunityCard[]>([]);
  const [dashboard, setDashboard] = useState<DashboardLaunchCard[]>([]);
  const [admin, setAdmin] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setAdmin(isAdmin());
    void probeAdminAndCache().then(setAdmin);
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fail-soft loader. /api/me is the gating call; every other
  // panel degrades to its empty default if its endpoint fails.
  const loadAll = async () => {
    let me: UserPublic;
    try {
      me = await api.get<UserPublic>("/api/me");
    } catch (e) {
      console.error("[home] /api/me failed", e);
      return;
    }
    setUser(me);

    // Notifications work for both roles.
    const [uc, nl] = await Promise.allSettled([
      api.get<UnreadCountResponse>("/api/me/notifications/unread-count"),
      api.get<NotificationListResponse>(
        "/api/me/notifications?unread_only=false&limit=4",
      ),
    ]);
    if (uc.status === "fulfilled") setUnread(uc.value.count);
    if (nl.status === "fulfilled") setNotes(nl.value.notifications);

    if (me.role_type === "founder") {
      // Founder dashboard (cycle #11).
      try {
        const d = await api.get<DashboardResponse>("/api/founders/dashboard");
        setDashboard(d.dashboard);
      } catch (e) {
        console.warn("[home] dashboard load failed", e);
      }
      return;
    }

    // User-only endpoints.
    const [r, ps, mc] = await Promise.allSettled([
      api.post<RecommendationsResponse>("/api/recommendations", { count: 5 }),
      api.get<ProfileSummaryResponse>("/api/me/profile-summary"),
      api.get<JoinedCommunityListResponse>("/api/me/communities"),
    ]);
    if (r.status === "fulfilled") {
      setRecs(r.value);
    } else if (
      r.reason instanceof ApiError &&
      r.reason.status === 400
    ) {
      // 400 no_profile_yet — user has <3 answers. Empty section is fine.
    } else {
      console.warn("[home] recommendations failed", r.reason);
    }
    if (ps.status === "fulfilled") {
      setStack(ps.value.stack_tools);
      const tags: string[] = [];
      for (const v of ps.value.all_answer_values) {
        tags.push(...tagsForAnswerValue(v));
      }
      setProfileTags([...new Set(tags)]);
    }
    if (mc.status === "fulfilled") setCommunities(mc.value.communities);
  };

  if (!user) {
    return (
      <div className="mono" style={{ padding: 64, color: "var(--ink-2)" }}>
        loading…
      </div>
    );
  }

  // Founder home: dedicated dashboard view (no user-side stack /
  // recommendations / communities sections).
  if (user.role_type === "founder") {
    return (
      <FounderHome
        user={user}
        unread={unread}
        notes={notes}
        dashboard={dashboard}
        admin={admin}
        onLogout={() => logout()}
      />
    );
  }

  // User home: existing 3-column shell.
  return (
    <>
      <HeaderBell />
      <div className="home-root">
        <HomeLeftRail
          user={user}
          stack={stack}
          unread={unread}
          communityCount={communities.length}
          admin={admin}
          onLogout={() => logout()}
        />
        <HomeCenter
          user={user}
          unread={unread}
          notes={notes}
          recs={recs}
          communities={communities}
        />
        <HomeRightRail tags={profileTags} />
      </div>
    </>
  );
}

// =============================================================================
// Left rail
// =============================================================================
function HomeLeftRail({
  user,
  stack,
  unread,
  communityCount,
  admin,
  onLogout,
}: {
  user: UserPublic;
  stack: StackToolEntry[];
  unread: number;
  communityCount: number;
  admin: boolean;
  onLogout: () => void;
}) {
  const scrollTo = (id: string) => {
    if (typeof document === "undefined") return;
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <aside className="home-rail home-rail-left">
      <div className="home-brand-row">
        <Link href="/" className="home-brand">
          <MeshMark size={20} />
          <span>Mesh</span>
        </Link>
      </div>
      <nav className="home-nav">
        <button className="home-nav-item" onClick={() => scrollTo("home-top")}>
          <span className="home-nav-glyph">◉</span>
          <span className="home-nav-label">Home</span>
        </button>
        <button className="home-nav-item" onClick={() => scrollTo("home-nudges")}>
          <span className="home-nav-glyph">~</span>
          <span className="home-nav-label">Nudges</span>
          {unread > 0 && <span className="home-nav-count mono">{unread}</span>}
        </button>
        <button className="home-nav-item" onClick={() => scrollTo("home-stack")}>
          <span className="home-nav-glyph">▦</span>
          <span className="home-nav-label">Your stack</span>
          {stack.length > 0 && (
            <span className="home-nav-count mono">{stack.length}</span>
          )}
        </button>
        <Link href="/tools/explore" className="home-nav-item">
          <span className="home-nav-glyph">✦</span>
          <span className="home-nav-label">Discover</span>
        </Link>
        <Link href="/communities" className="home-nav-item">
          <span className="home-nav-glyph">◌</span>
          <span className="home-nav-label">Communities</span>
          {communityCount > 0 && (
            <span className="home-nav-count mono">{communityCount}</span>
          )}
        </Link>
        <Link href="/concierge" className="home-nav-item">
          <span className="home-nav-glyph">⌬</span>
          <span className="home-nav-label">Concierge</span>
        </Link>
        <Link href="/onboarding" className="home-nav-item">
          <span className="home-nav-glyph">◎</span>
          <span className="home-nav-label">Refine profile</span>
        </Link>
        {admin && (
          <Link href="/admin/launches" className="home-nav-item" style={{ color: "var(--accent)" }}>
            <span className="home-nav-glyph">⚙</span>
            <span className="home-nav-label">Admin</span>
          </Link>
        )}
      </nav>

      <div className="home-rail-section" id="home-stack">
        <div className="home-rail-heading mono">Your stack</div>
        <div className="home-stack-list">
          {stack.length === 0 && (
            <div className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
              no tools yet — answer the stack questions in onboarding
            </div>
          )}
          {stack.slice(0, 8).map((t) => (
            <Link
              key={t.value}
              href={`/p/${t.value}`}
              className="home-stack-item"
              style={{ display: "flex", textDecoration: "none" }}
            >
              <div className="home-stack-logo">
                <span>{t.label[0]?.toUpperCase() || "•"}</span>
                <span className="home-stack-pulse pulse-high" />
              </div>
              <div className="home-stack-meta">
                <div className="home-stack-name">{t.label}</div>
                <div className="mono home-stack-status">from your answers</div>
              </div>
            </Link>
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
      <header className="home-center-header" id="home-top">
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

      <section className="home-section" id="home-nudges">
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

      <section className="home-section" id="home-communities">
        <div className="home-section-head">
          <h2 className="home-section-title">Your communities</h2>
          <Link href="/communities" className="mono home-section-link">
            browse all ↗
          </Link>
        </div>
        <div className="home-coms">
          {communities.length === 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div className="mono" style={{ color: "var(--ink-3)" }}>
                you haven&apos;t joined any rooms yet
              </div>
              <Link
                href="/communities"
                className="mono"
                style={{
                  color: "var(--accent)",
                  textDecoration: "underline",
                  fontSize: 13,
                }}
              >
                → browse communities
              </Link>
            </div>
          )}
          {communities.map((c) => (
            <Link
              key={c.slug}
              href={`/c/${c.slug}`}
              className="home-com-row"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <span className={`onb-com-dot axis-${c.category}`} />
              <span className="mono home-com-name">{c.name}</span>
              <span className="mono home-com-members">
                {c.member_count.toLocaleString()}
              </span>
            </Link>
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
        {(() => {
          const slug = (n.payload as { tool_slug?: string }).tool_slug;
          if (slug) {
            return (
              <Link href={`/p/${slug}`} className="home-nudge-cta">
                view tool →
              </Link>
            );
          }
          return null;
        })()}
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
// Right rail — profile graph as a visualization of the user's actual answers.
//
// Tags come from /api/me/profile-summary.all_answer_values, computed
// client-side via tagsForAnswerValue (same helper /onboarding's live
// graph uses). Empty array = no answers yet → graph idles.
// (Activity feed stayed removed — no cross-user stream backend.)
// =============================================================================
function HomeRightRail({ tags }: { tags: string[] }) {
  return (
    <aside className="home-rail home-rail-right">
      <div className="home-rail-heading mono">Your profile graph</div>
      <div className="home-mini-graph">
        <ToolGraph
          progress={tags.length > 0 ? 1 : 0.4}
          highlightedTags={tags}
          mode="score"
          gridSlots={Math.max(4, Math.min(8, tags.length || 5))}
          scale={0.85}
        />
      </div>
      <div className="home-rail-tags">
        {tags.length === 0 ? (
          <span className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
            answer onboarding to populate
          </span>
        ) : (
          tags.slice(0, 10).map((t) => (
            <span key={t} className="onb-graph-tag">
              {t}
            </span>
          ))
        )}
      </div>
      <Link href="/onboarding" className="mono home-rail-refine">
        refine profile ↗
      </Link>
    </aside>
  );
}

// =============================================================================
// Founder home — launch dashboard.
// Cycle #11 backend (/api/founders/dashboard) provides the data.
// =============================================================================
function FounderHome({
  user,
  unread,
  notes,
  dashboard,
  admin,
  onLogout,
}: {
  user: UserPublic;
  unread: number;
  notes: NotificationCard[];
  dashboard: DashboardLaunchCard[];
  admin: boolean;
  onLogout: () => void;
}) {
  const total = dashboard.length;
  const approved = dashboard.filter((l) => l.verification_status === "approved").length;
  const pending = dashboard.filter((l) => l.verification_status === "pending").length;
  const rejected = dashboard.filter((l) => l.verification_status === "rejected").length;

  return (
    <div className="home-root no-right">
      <aside className="home-rail home-rail-left">
        <div className="home-brand-row">
          <Link href="/" className="home-brand">
            <MeshMark size={20} />
            <span>Mesh</span>
          </Link>
          <HeaderBell />
        </div>
        <nav className="home-nav">
          <Link href="/founders/launch" className="home-nav-item">
            <span className="home-nav-glyph">+</span>
            <span className="home-nav-label">New launch</span>
          </Link>
          <Link href="/concierge" className="home-nav-item">
            <span className="home-nav-glyph">⌬</span>
            <span className="home-nav-label">Concierge</span>
          </Link>
          <Link href="/communities" className="home-nav-item">
            <span className="home-nav-glyph">◌</span>
            <span className="home-nav-label">Communities</span>
          </Link>
          {admin && (
            <Link href="/admin/launches" className="home-nav-item" style={{ color: "var(--accent)" }}>
              <span className="home-nav-glyph">⚙</span>
              <span className="home-nav-label">Admin</span>
            </Link>
          )}
        </nav>

        <div className="home-rail-section">
          <div className="home-rail-heading mono">At a glance</div>
          <div className="home-stack-list">
            <div className="home-stack-item">
              <div className="home-stack-meta">
                <div className="home-stack-name">{total}</div>
                <div className="mono home-stack-status">total launches</div>
              </div>
            </div>
            <div className="home-stack-item">
              <div className="home-stack-meta">
                <div className="home-stack-name">{approved}</div>
                <div className="mono home-stack-status">approved</div>
              </div>
            </div>
            <div className="home-stack-item">
              <div className="home-stack-meta">
                <div className="home-stack-name">{pending}</div>
                <div className="mono home-stack-status">pending review</div>
              </div>
            </div>
            {rejected > 0 && (
              <div className="home-stack-item">
                <div className="home-stack-meta">
                  <div className="home-stack-name">{rejected}</div>
                  <div className="mono home-stack-status">rejected</div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="home-rail-foot">
          <div className="home-profile">
            <div className="home-profile-avatar">
              {user.display_name[0]?.toUpperCase() || "?"}
            </div>
            <div className="home-profile-meta">
              <div className="home-profile-name">@{user.display_name}</div>
              <div className="mono home-profile-tag">founder</div>
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

      <main className="home-center">
        <header className="home-center-header">
          <div>
            <div className="mono home-eyebrow">/ founder · today</div>
            <h1 className="home-greeting">
              {greetingFor()}, {user.display_name}.{" "}
              {pending > 0 ? (
                <em>{pending} pending review</em>
              ) : approved > 0 ? (
                <em>{approved} live</em>
              ) : (
                <em>no launches yet</em>
              )}
              .
            </h1>
            <p className="home-subgreet body">
              Mesh staff verifies launches within ~24 hours. Once approved,
              your launch fans into your target communities and matched
              users get a concierge nudge.
            </p>
          </div>
        </header>

        <section className="home-section">
          <div className="home-section-head">
            <h2 className="home-section-title">Your launches</h2>
            <Link href="/founders/launch" className="mono home-section-link">
              + new launch ↗
            </Link>
          </div>
          {dashboard.length === 0 ? (
            <div className="mono" style={{ color: "var(--ink-3)", padding: 24 }}>
              you haven&apos;t submitted a launch yet —{" "}
              <Link href="/founders/launch" style={{ textDecoration: "underline" }}>
                start one
              </Link>
            </div>
          ) : (
            <div className="home-coms">
              {dashboard.map((l) => (
                <FounderLaunchRow key={l.launch_id} launch={l} />
              ))}
            </div>
          )}
        </section>

        <section className="home-section" id="home-nudges">
          <div className="home-section-head">
            <h2 className="home-section-title">
              Notifications{" "}
              <span className="mono home-section-count">{unread}</span>
            </h2>
          </div>
          <div className="home-nudges">
            {notes.length === 0 && (
              <div className="mono" style={{ color: "var(--ink-3)" }}>
                nothing yet — admin updates appear here when launches are
                approved or rejected
              </div>
            )}
            {notes.map((n, i) => (
              <NudgeCard key={n.id} n={n} delay={i * 80} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

function FounderLaunchRow({ launch }: { launch: DashboardLaunchCard }) {
  const status = launch.verification_status;
  const statusColor =
    status === "approved"
      ? "var(--good)"
      : status === "rejected"
      ? "var(--warn)"
      : "var(--ink-2)";
  return (
    <div
      className="home-com-row"
      style={{ alignItems: "flex-start", padding: 16, gap: 16 }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="home-com-name" style={{ marginBottom: 4 }}>
          {launch.product_url}
        </div>
        <div className="mono" style={{ fontSize: 12, color: "var(--ink-3)" }}>
          submitted {new Date(launch.created_at).toLocaleDateString()}
          {launch.approved_tool_slug && (
            <>
              {" "}·{" "}
              <Link
                href={`/p/${launch.approved_tool_slug}`}
                style={{ textDecoration: "underline" }}
              >
                /p/{launch.approved_tool_slug}
              </Link>
            </>
          )}
        </div>
        {status === "approved" && (
          <div
            className="mono"
            style={{ fontSize: 12, color: "var(--ink-2)", marginTop: 6 }}
          >
            matched {launch.matched_count} · {launch.tell_me_more_count} tell-me-more
            · {launch.skip_count} skip · {launch.total_clicks} clicks
          </div>
        )}
        <Link
          href={`/founders/launches/${launch.launch_id}/analytics`}
          className="mono"
          style={{
            display: "inline-block",
            marginTop: 8,
            color: "var(--accent)",
            fontSize: 12,
          }}
        >
          view analytics →
        </Link>
      </div>
      <span
        className="mono"
        style={{
          color: statusColor,
          fontSize: 12,
          textTransform: "uppercase",
          letterSpacing: 1,
        }}
      >
        {status}
      </span>
    </div>
  );
}
