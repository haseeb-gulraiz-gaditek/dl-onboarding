"use client";

// Mesh — community room.
// Per spec-delta frontend-secondary F-FE2-3.
//
// Wires cycle #7 endpoints. Founders see read-only (compose +
// vote hidden — backend rejects them anyway via require_role(user)).
// V1 simplifications: pulse/axes/readers/rules hardcoded labelled
// placeholders; sister rooms client-side from category.

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated, currentUser } from "@/lib/auth";
import type {
  CommunityCard,
  CommunityDetailResponse,
  CommunityListResponse,
  PostCard,
  PostCreateRequest,
  PostListResponse,
  UserPublic,
} from "@/lib/api-types";

type FilterTab = "all" | "hot" | "verdicts" | "auto";

export default function CommunityRoomPage({
  params,
}: {
  params: { slug: string };
}) {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [room, setRoom] = useState<CommunityDetailResponse | null>(null);
  const [posts, setPosts] = useState<PostCard[]>([]);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [sisters, setSisters] = useState<CommunityCard[]>([]);
  const [filter, setFilter] = useState<FilterTab>("all");
  const [composeOpen, setComposeOpen] = useState(false);
  const [composeTitle, setComposeTitle] = useState("");
  const [composeBody, setComposeBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.slug]);

  const load = async () => {
    setNotFound(false);
    try {
      const me = await currentUser();
      setUser(me);
    } catch (e) {
      console.warn("[c] /api/me failed", e);
    }
    try {
      const detail = await api.get<CommunityDetailResponse>(
        `/api/communities/${params.slug}`,
      );
      setRoom(detail);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setNotFound(true);
        return;
      }
      console.error("[c] community detail failed", e);
    }
    try {
      const feed = await api.get<PostListResponse>(
        `/api/communities/${params.slug}/posts?limit=20`,
      );
      setPosts(feed.posts);
      setNextBefore(feed.next_before);
    } catch (e) {
      console.warn("[c] feed failed", e);
    }
    // Sister rooms — client-side from category (no backend endpoint).
    try {
      const all = await api.get<CommunityListResponse>("/api/communities");
      // Filter post-load when room is set; do it lazily after both arrive.
      setSisters(all.communities);
    } catch (e) {
      console.warn("[c] communities list failed", e);
    }
  };

  const sistersFiltered = useMemo(() => {
    if (!room || sisters.length === 0) return [];
    return sisters.filter(
      (c) => c.category === room.community.category && c.slug !== params.slug,
    );
  }, [room, sisters, params.slug]);

  const filtered = useMemo(() => {
    if (filter === "all") return posts;
    if (filter === "hot")
      return [...posts].sort((a, b) => b.vote_score - a.vote_score);
    if (filter === "verdicts")
      return posts.filter((p) =>
        /verdict|tried|dropped|dropped/i.test(p.title + p.body_md),
      );
    if (filter === "auto") return posts.filter((p) => !!p.attached_launch_id);
    return posts;
  }, [posts, filter]);

  const loadMore = async () => {
    if (!nextBefore) return;
    try {
      const feed = await api.get<PostListResponse>(
        `/api/communities/${params.slug}/posts?limit=20&before=${encodeURIComponent(nextBefore)}`,
      );
      setPosts((prev) => [...prev, ...feed.posts]);
      setNextBefore(feed.next_before);
    } catch (e) {
      console.warn("[c] load more failed", e);
    }
  };

  const join = async () => {
    try {
      await api.post(`/api/communities/${params.slug}/join`);
      await load();
    } catch (e) {
      console.warn("[c] join failed", e);
    }
  };
  const leave = async () => {
    try {
      await api.post(`/api/communities/${params.slug}/leave`);
      await load();
    } catch (e) {
      console.warn("[c] leave failed", e);
    }
  };

  const submitPost = async () => {
    if (!composeTitle.trim()) {
      setErr("Title is required.");
      return;
    }
    setErr(null);
    setSubmitting(true);
    try {
      const body: PostCreateRequest = {
        community_slug: params.slug,
        title: composeTitle.trim(),
        body_md: composeBody.trim(),
      };
      await api.post("/api/posts", body);
      setComposeOpen(false);
      setComposeTitle("");
      setComposeBody("");
      await load();
    } catch (e) {
      const msg = e instanceof ApiError && typeof e.body === "object" && e.body && "detail" in e.body
        ? JSON.stringify((e.body as { detail: unknown }).detail)
        : "Failed to post.";
      setErr(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const vote = async (post: PostCard, direction: 1 | -1) => {
    try {
      await api.post("/api/votes", {
        target_type: "post",
        target_id: post.id,
        direction,
      });
      // Optimistic-ish refresh.
      await load();
    } catch (e) {
      console.warn("[c] vote failed", e);
    }
  };

  if (notFound) {
    return (
      <Shell>
        <h1 className="onb-q-title">Community not found</h1>
        <p className="body" style={{ color: "var(--ink-2)" }}>
          The slug <code>{params.slug}</code> doesn&apos;t resolve.
        </p>
        <Link href="/home" style={{ marginTop: 16, display: "inline-block" }}>
          <MButton variant="ghost">← Back to home</MButton>
        </Link>
      </Shell>
    );
  }

  if (!room) {
    return (
      <Shell>
        <div className="mono" style={{ color: "var(--ink-2)" }}>loading…</div>
      </Shell>
    );
  }

  const canWrite = user?.role_type === "user";

  return (
    <Shell>
      {/* Hero */}
      <div className="m-card" style={{ padding: 24, marginBottom: 24 }}>
        <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
          / axis · {room.community.category}
        </div>
        <h1 className="h-display" style={{ fontSize: 40, marginTop: 8 }}>
          {room.community.name}
        </h1>
        <p className="body-lg" style={{ marginTop: 12 }}>
          {room.community.description}
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 16 }}>
          <span className="mono" style={{ color: "var(--ink-2)" }}>
            {room.community.member_count.toLocaleString()} members
          </span>
          {canWrite ? (
            room.is_member ? (
              <button onClick={leave} className="mono" style={{ color: "var(--ink-2)" }}>
                ✓ joined · leave
              </button>
            ) : (
              <MButton size="sm" onClick={join}>Join</MButton>
            )
          ) : (
            <span className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
              {user?.role_type === "founder"
                ? "founders are read-only in user communities"
                : "sign in to join"}
            </span>
          )}
        </div>
      </div>

      {/* Filters + compose */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {(["all", "hot", "verdicts", "auto"] as FilterTab[]).map((f) => (
          <button
            key={f}
            className="mono"
            onClick={() => setFilter(f)}
            style={{
              padding: "6px 14px",
              borderRadius: "var(--r-pill)",
              fontSize: 12,
              background: filter === f ? "var(--accent-soft)" : "transparent",
              border: filter === f ? "1px solid var(--accent)" : "1px solid var(--line-0)",
              color: filter === f ? "var(--ink-0)" : "var(--ink-2)",
              cursor: "pointer",
            }}
          >
            {f}
          </button>
        ))}
        {canWrite && (
          <button
            className="mono"
            onClick={() => setComposeOpen((v) => !v)}
            style={{
              marginLeft: "auto",
              padding: "6px 14px",
              borderRadius: "var(--r-pill)",
              fontSize: 12,
              border: "1px solid var(--line-0)",
              color: "var(--ink-1)",
              cursor: "pointer",
            }}
          >
            {composeOpen ? "× cancel" : "+ start a thread"}
          </button>
        )}
      </div>

      {composeOpen && (
        <div className="m-card" style={{ padding: 16, marginBottom: 16 }}>
          <input
            className="m-input founders-input"
            placeholder="Title"
            value={composeTitle}
            onChange={(e) => setComposeTitle(e.target.value)}
            style={{ marginBottom: 8 }}
          />
          <textarea
            className="m-input founders-input"
            placeholder="Body (optional)"
            rows={3}
            value={composeBody}
            onChange={(e) => setComposeBody(e.target.value)}
          />
          {err && (
            <div className="mono" style={{ color: "var(--warn)", fontSize: 12, marginTop: 8 }}>
              {err}
            </div>
          )}
          <div style={{ marginTop: 12, display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <MButton size="sm" onClick={submitPost}>
              {submitting ? "Posting…" : "Post"}
            </MButton>
          </div>
        </div>
      )}

      {/* Feed */}
      {filtered.length === 0 ? (
        <div className="mono" style={{ color: "var(--ink-3)", padding: 24 }}>
          no threads yet
        </div>
      ) : (
        filtered.map((p) => (
          <ThreadCard key={p.id} post={p} canVote={canWrite} onVote={vote} />
        ))
      )}

      {nextBefore && (
        <div style={{ display: "flex", justifyContent: "center", marginTop: 16 }}>
          <MButton variant="ghost" size="sm" onClick={loadMore}>
            Load more
          </MButton>
        </div>
      )}

      {/* Sister rooms */}
      {sistersFiltered.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11, marginBottom: 8 }}>
            / sister rooms · same axis
          </div>
          <div className="onb-graph-tags">
            {sistersFiltered.map((c) => (
              <Link key={c.slug} href={`/c/${c.slug}`} className="onb-graph-tag">
                {c.name} · {c.member_count.toLocaleString()}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* V1 placeholder block */}
      <div
        className="mono"
        style={{
          marginTop: 32,
          padding: 16,
          color: "var(--ink-3)",
          border: "1px dashed var(--line-1)",
          borderRadius: "var(--r-md)",
          fontSize: 12,
        }}
      >
        room pulse · axis breakdown · live readers — V1.5 (needs a
        backend analytics endpoint over posts/comments time-buckets)
      </div>
    </Shell>
  );
}

function ThreadCard({
  post,
  canVote,
  onVote,
}: {
  post: PostCard;
  canVote: boolean;
  onVote: (p: PostCard, d: 1 | -1) => void;
}) {
  return (
    <article
      className="m-card"
      style={{
        padding: 20,
        marginBottom: 12,
        display: "flex",
        gap: 16,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
        {canVote ? (
          <button
            onClick={() => onVote(post, 1)}
            className="mono"
            style={{
              fontSize: 14,
              color: post.user_vote === 1 ? "var(--accent)" : "var(--ink-2)",
              cursor: "pointer",
            }}
          >
            ↑
          </button>
        ) : (
          <span className="mono" style={{ color: "var(--ink-3)", fontSize: 14 }}>↑</span>
        )}
        <span className="mono" style={{ fontSize: 13 }}>{post.vote_score}</span>
        {canVote && (
          <button
            onClick={() => onVote(post, -1)}
            className="mono"
            style={{
              fontSize: 14,
              color: post.user_vote === -1 ? "var(--warn)" : "var(--ink-2)",
              cursor: "pointer",
            }}
          >
            ↓
          </button>
        )}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11 }}>
          {post.author.display_name} · {new Date(post.created_at).toLocaleDateString()}
          {post.attached_launch_id && (
            <span style={{ color: "var(--accent)", marginLeft: 8 }}>🚀 launch</span>
          )}
        </div>
        <h3 className="h-card" style={{ marginTop: 6 }}>{post.title}</h3>
        {post.body_md && (
          <p className="body" style={{ marginTop: 8, color: "var(--ink-1)" }}>
            {post.body_md}
          </p>
        )}
        <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 12 }}>
          {post.comment_count} replies
        </div>
      </div>
    </article>
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
        <Link href="/home" className="onb-brand">
          <MeshMark size={20} />
          <span>Mesh</span>
        </Link>
        <HeaderBell />
      </header>
      <main style={{ maxWidth: 880, margin: "0 auto" }}>{children}</main>
    </div>
  );
}
