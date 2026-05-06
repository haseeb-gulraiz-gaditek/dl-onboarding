"use client";

// Mesh — /tools/new (founder launches feed).
// Per spec-delta frontend-secondary F-FE2-5.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton } from "@/components/Primitives";

import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type {
  BrowsedLaunchCard,
  BrowsedLaunchListResponse,
} from "@/lib/api-types";

export default function ToolsNewPage() {
  const router = useRouter();
  const [launches, setLaunches] = useState<BrowsedLaunchCard[]>([]);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    void load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showAll]);

  const buildPath = (cursor?: string) => {
    const params = new URLSearchParams();
    if (showAll) params.set("all", "true");
    params.set("limit", "20");
    if (cursor) params.set("before", cursor);
    return `/api/launches?${params.toString()}`;
  };

  const load = async (reset: boolean) => {
    setLoading(true);
    try {
      const r = await api.get<BrowsedLaunchListResponse>(
        buildPath(reset ? undefined : nextBefore || undefined),
      );
      setLaunches((prev) => (reset ? r.launches : [...prev, ...r.launches]));
      setNextBefore(r.next_before);
    } catch (e) {
      console.warn("[/tools/new] failed", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
            / new launches
          </div>
          <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
            What just landed.
          </h1>
        </div>
        <label className="mono" style={{ fontSize: 12, color: "var(--ink-2)", display: "flex", gap: 8 }}>
          <input
            type="checkbox"
            checked={showAll}
            onChange={(e) => setShowAll(e.target.checked)}
          />
          show all (not just my communities)
        </label>
      </div>

      {loading && launches.length === 0 ? (
        <div className="mono" style={{ color: "var(--ink-3)" }}>loading…</div>
      ) : launches.length === 0 ? (
        <div className="mono" style={{ color: "var(--ink-3)", padding: 40, textAlign: "center" }}>
          {showAll
            ? "no approved launches yet"
            : "no launches in your communities — toggle 'show all' or join more communities"}
        </div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 12 }}>
            {launches.map((l) => (
              <article key={l.tool.slug} className="m-card" style={{ padding: 20 }}>
                <Link
                  href={`/p/${l.tool.slug}`}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div className="h-card" style={{ fontSize: 15 }}>
                    {l.tool.name}
                    <span style={{ marginLeft: 6, color: "var(--accent)", fontSize: 13 }}>🚀</span>
                  </div>
                  <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 2 }}>
                    by {l.launch_meta.founder_display_name}{" · "}
                    {l.launch_meta.approved_at
                      ? new Date(l.launch_meta.approved_at).toLocaleDateString()
                      : "approved"}
                  </div>
                  <p className="body" style={{ marginTop: 8, fontSize: 13, color: "var(--ink-2)" }}>
                    {l.launch_meta.problem_statement}
                  </p>
                </Link>
                {l.in_my_communities.length > 0 && (
                  <div style={{ marginTop: 12, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {l.in_my_communities.map((slug) => (
                      <Link
                        key={slug}
                        href={`/c/${slug}`}
                        className="mono"
                        style={{
                          padding: "4px 10px",
                          borderRadius: "var(--r-pill)",
                          fontSize: 10,
                          background: "var(--accent-soft)",
                          color: "var(--ink-0)",
                          textDecoration: "none",
                        }}
                      >
                        in /c/{slug}
                      </Link>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
          {nextBefore && (
            <div style={{ display: "flex", justifyContent: "center", marginTop: 24 }}>
              <MButton variant="ghost" onClick={() => load(false)}>
                {loading ? "Loading…" : "Load more"}
              </MButton>
            </div>
          )}
        </>
      )}
    </div>
  );
}
