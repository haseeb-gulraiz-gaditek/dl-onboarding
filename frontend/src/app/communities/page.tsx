"use client";

// Mesh — /communities browse page.
// Lists all communities with join/leave + filter; joined ones link to /c/{slug}.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated, currentUser } from "@/lib/auth";
import type {
  CommunityCard,
  CommunityListResponse,
  JoinedCommunityListResponse,
  CommunityCategory,
  UserPublic,
} from "@/lib/api-types";

type FilterKey = "all" | CommunityCategory;

export default function CommunitiesBrowsePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [all, setAll] = useState<CommunityCard[]>([]);
  const [joined, setJoined] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<FilterKey>("all");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const me = await currentUser();
      if (!me) {
        router.replace("/login");
        return;
      }
      setUser(me);

      const list = await api.get<CommunityListResponse>("/api/communities");
      setAll(list.communities);

      if (me.role_type === "user") {
        try {
          const joinedRes = await api.get<JoinedCommunityListResponse>(
            "/api/me/communities",
          );
          setJoined(new Set(joinedRes.communities.map((c) => c.slug)));
        } catch (e) {
          if (!(e instanceof ApiError && e.status === 403)) {
            console.warn("[communities] joined fetch failed", e);
          }
        }
      }
    } catch (e) {
      console.warn("[communities] load failed", e);
    } finally {
      setLoading(false);
    }
  };

  const join = async (slug: string) => {
    setBusy(slug);
    try {
      await api.post(`/api/communities/${slug}/join`);
      setJoined((prev) => new Set(prev).add(slug));
    } catch (e) {
      console.warn("[communities] join failed", e);
    } finally {
      setBusy(null);
    }
  };

  const leave = async (slug: string) => {
    if (!confirm(`Leave /c/${slug}?`)) return;
    setBusy(slug);
    try {
      await api.del(`/api/communities/${slug}/leave`);
      setJoined((prev) => {
        const next = new Set(prev);
        next.delete(slug);
        return next;
      });
    } catch (e) {
      console.warn("[communities] leave failed", e);
    } finally {
      setBusy(null);
    }
  };

  const visible =
    filter === "all" ? all : all.filter((c) => c.category === filter);

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

      <main style={{ maxWidth: 960, margin: "0 auto" }}>
        <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
          / communities
        </div>
        <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
          Find your rooms.
        </h1>
        <p
          className="body"
          style={{ color: "var(--ink-2)", marginTop: 8, maxWidth: 560 }}
        >
          {user?.role_type === "founder"
            ? "Browse rooms — founders can read but not post or vote."
            : "Join the rooms where your stack and goals live. You can leave anytime."}
        </p>

        <div
          style={{
            display: "flex",
            gap: 8,
            marginTop: 24,
            marginBottom: 24,
            flexWrap: "wrap",
          }}
        >
          {(["all", "role", "stack", "outcome"] as FilterKey[]).map((k) => (
            <button
              key={k}
              onClick={() => setFilter(k)}
              className="mono"
              style={{
                padding: "6px 14px",
                borderRadius: "var(--r-pill)",
                fontSize: 12,
                background: filter === k ? "var(--accent-soft)" : "transparent",
                border:
                  filter === k
                    ? "1px solid var(--accent)"
                    : "1px solid var(--line-0)",
                color: filter === k ? "var(--ink-0)" : "var(--ink-2)",
                cursor: "pointer",
              }}
            >
              {k}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="mono" style={{ color: "var(--ink-3)" }}>
            loading…
          </div>
        ) : visible.length === 0 ? (
          <div
            className="mono"
            style={{
              color: "var(--ink-3)",
              padding: 40,
              textAlign: "center",
            }}
          >
            no communities in this category
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
              gap: 12,
            }}
          >
            {visible.map((c) => {
              const isJoined = joined.has(c.slug);
              return (
                <article
                  key={c.slug}
                  className="m-card"
                  style={{ padding: 20 }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: 8,
                    }}
                  >
                    <span className={`onb-com-dot axis-${c.category}`} />
                    <Link
                      href={`/c/${c.slug}`}
                      className="h-card"
                      style={{
                        fontSize: 15,
                        textDecoration: "underline",
                        color: "inherit",
                      }}
                    >
                      {c.name}
                    </Link>
                    <span
                      className="mono"
                      style={{
                        marginLeft: "auto",
                        color: "var(--ink-3)",
                        fontSize: 11,
                      }}
                    >
                      {c.member_count.toLocaleString()} members
                    </span>
                  </div>
                  <div
                    className="mono"
                    style={{
                      color: "var(--ink-3)",
                      fontSize: 11,
                      marginTop: 4,
                    }}
                  >
                    /c/{c.slug} · {c.category}
                  </div>
                  <p
                    className="body"
                    style={{
                      marginTop: 8,
                      fontSize: 13,
                      color: "var(--ink-1)",
                    }}
                  >
                    {c.description}
                  </p>

                  <div
                    style={{
                      marginTop: 16,
                      display: "flex",
                      gap: 8,
                      alignItems: "center",
                    }}
                  >
                    {user?.role_type === "user" ? (
                      isJoined ? (
                        <>
                          <Link href={`/c/${c.slug}`}>
                            <MButton size="sm">Open →</MButton>
                          </Link>
                          <button
                            onClick={() => leave(c.slug)}
                            disabled={busy === c.slug}
                            className="mono"
                            style={{
                              color: "var(--ink-3)",
                              fontSize: 12,
                              cursor: "pointer",
                            }}
                          >
                            {busy === c.slug ? "…" : "leave"}
                          </button>
                        </>
                      ) : (
                        <MButton
                          size="sm"
                          onClick={() => join(c.slug)}
                          disabled={busy === c.slug}
                        >
                          {busy === c.slug ? "Joining…" : "Join"}
                        </MButton>
                      )
                    ) : (
                      <Link href={`/c/${c.slug}`}>
                        <MButton size="sm" variant="ghost">
                          Open →
                        </MButton>
                      </Link>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
