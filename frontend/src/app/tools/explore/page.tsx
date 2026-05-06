"use client";

// Mesh — /tools/explore.
// Per spec-delta frontend-secondary F-FE2-5.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton } from "@/components/Primitives";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { ToolCardWithFlags, ToolsBrowseResponse } from "@/lib/api-types";

export default function ToolsExplorePage() {
  const router = useRouter();
  const [tools, setTools] = useState<ToolCardWithFlags[]>([]);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [label, setLabel] = useState("");
  const [loading, setLoading] = useState(true);
  const [savedSet, setSavedSet] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    void load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, category, label]);

  const buildPath = (cursor?: string) => {
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (category) params.set("category", category);
    if (label) params.set("label", label);
    params.set("limit", "20");
    if (cursor) params.set("before", cursor);
    return `/api/tools?${params.toString()}`;
  };

  const load = async (reset: boolean) => {
    setLoading(true);
    try {
      const r = await api.get<ToolsBrowseResponse>(
        buildPath(reset ? undefined : nextBefore || undefined),
      );
      setTools((prev) => (reset ? r.tools : [...prev, ...r.tools]));
      setNextBefore(r.next_before);
    } catch (e) {
      console.warn("[explore] failed", e);
    } finally {
      setLoading(false);
    }
  };

  const save = async (t: ToolCardWithFlags) => {
    try {
      await api.post("/api/me/tools", { tool_slug: t.slug, status: "saved" });
      setSavedSet((prev) => new Set(prev).add(t.slug));
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        alert("Founders can't save tools — switch to a user account.");
      } else {
        console.warn("[explore] save failed", e);
      }
    }
  };

  return (
    <div>
      <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>/ explore</div>
      <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
        The catalog.
      </h1>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 24, marginBottom: 24 }}>
        <input
          className="m-input"
          style={{ maxWidth: 280 }}
          placeholder="search by name or tagline…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="m-input"
          style={{ maxWidth: 200 }}
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">all categories</option>
          {[
            "productivity", "writing", "design", "engineering",
            "research_browsing", "meetings", "marketing", "sales",
            "analytics_data", "finance", "education", "creative_video",
            "automation_agents",
          ].map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          className="m-input"
          style={{ maxWidth: 200 }}
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        >
          <option value="">all labels</option>
          <option value="all_time_best">all-time best</option>
          <option value="gaining_traction">gaining traction</option>
          <option value="new">new</option>
        </select>
      </div>

      {loading && tools.length === 0 ? (
        <div className="mono" style={{ color: "var(--ink-3)" }}>loading…</div>
      ) : tools.length === 0 ? (
        <div className="mono" style={{ color: "var(--ink-3)", padding: 40, textAlign: "center" }}>
          no tools match these filters
        </div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
            {tools.map((t) => (
              <article key={t.slug} className="m-card" style={{ padding: 20 }}>
                <Link
                  href={`/p/${t.slug}`}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div className="h-card" style={{ fontSize: 15 }}>
                    {t.name}
                    {t.is_founder_launched && (
                      <span style={{ marginLeft: 6, color: "var(--accent)", fontSize: 13 }}>🚀</span>
                    )}
                  </div>
                  <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 2 }}>
                    {t.category} · {t.pricing_summary} · ♡ {t.vote_score}
                  </div>
                  <p className="body" style={{ marginTop: 8, fontSize: 13, color: "var(--ink-2)" }}>
                    {t.tagline}
                  </p>
                </Link>
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <button
                    onClick={() => save(t)}
                    className="mono"
                    disabled={savedSet.has(t.slug)}
                    style={{
                      padding: "6px 12px",
                      borderRadius: "var(--r-pill)",
                      fontSize: 11,
                      border: "1px solid var(--line-0)",
                      color: savedSet.has(t.slug) ? "var(--ink-3)" : "var(--ink-1)",
                      cursor: savedSet.has(t.slug) ? "default" : "pointer",
                    }}
                  >
                    {savedSet.has(t.slug) ? "✓ saved" : "+ save"}
                  </button>
                  <a href={t.url} target="_blank" rel="noreferrer" className="mono" style={{
                    padding: "6px 12px",
                    borderRadius: "var(--r-pill)",
                    fontSize: 11,
                    color: "var(--ink-2)",
                  }}>
                    open ↗
                  </a>
                </div>
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
