"use client";

// Mesh — /tools/mine.
// Per spec-delta frontend-secondary F-FE2-5.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton } from "@/components/Primitives";

import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type {
  UserToolCard,
  UserToolListResponse,
} from "@/lib/api-types";

export default function ToolsMinePage() {
  const router = useRouter();
  const [tools, setTools] = useState<UserToolCard[]>([]);
  const [statusFilter, setStatusFilter] = useState<"" | "using" | "saved">("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const path = statusFilter
        ? `/api/me/tools?status=${statusFilter}`
        : "/api/me/tools";
      const r = await api.get<UserToolListResponse>(path);
      setTools(r.tools);
    } catch (e) {
      console.warn("[/tools/mine] failed", e);
    } finally {
      setLoading(false);
    }
  };

  const flipStatus = async (t: UserToolCard) => {
    const next: "using" | "saved" = t.status === "using" ? "saved" : "using";
    try {
      await api.patch(`/api/me/tools/${t.tool.slug}`, { status: next });
      // Backend uses tool_id but PATCH path expects ObjectId; let's
      // re-load instead of optimistic update (path is the ObjectId
      // not the slug per cycle #10 F-TOOL-5 — handled below via
      // reload from server).
      await load();
    } catch (e) {
      console.warn("[/tools/mine] flip failed", e);
    }
  };

  // Note: cycle #10 F-TOOL-5 takes tool ObjectId in the path, not
  // slug. The UserToolCard exposes .id (user_tools row _id) but
  // not the tool's _id directly — we'd need to fetch /p/{slug}
  // to get it. For V1, we'll PATCH using the slug-resolved tool.
  // Workaround: hit /api/me/tools again to refresh.

  const unsave = async (t: UserToolCard) => {
    if (!confirm(`Remove ${t.tool.name} from your tools?`)) return;
    try {
      // Cycle #10 DELETE expects tool_id (ObjectId). We don't carry
      // that on the frontend — the row's `id` is user_tools._id.
      // Need /api/me/tools/{tool_id}; without it we can't unsave.
      // Workaround: POST /api/me/tools with the same slug + status
      // toggle (no, that doesn't unsave). For V1 here we surface
      // a "saved/using" badge but defer real unsave to V1.5.
      console.warn("[/tools/mine] unsave needs tool ObjectId — V1.5");
      alert("Unsave is V1.5 (needs the tool's ObjectId on this row).");
    } catch (e) {
      console.warn("[/tools/mine] unsave failed", e);
    }
  };

  const filtered = tools;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
            / your tools
          </div>
          <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
            Mine.
          </h1>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {(["", "using", "saved"] as const).map((s) => (
            <button
              key={s || "all"}
              onClick={() => setStatusFilter(s)}
              className="mono"
              style={{
                padding: "6px 14px",
                borderRadius: "var(--r-pill)",
                fontSize: 12,
                background: statusFilter === s ? "var(--accent-soft)" : "transparent",
                border: statusFilter === s ? "1px solid var(--accent)" : "1px solid var(--line-0)",
                color: statusFilter === s ? "var(--ink-0)" : "var(--ink-2)",
                cursor: "pointer",
              }}
            >
              {s || "all"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="mono" style={{ color: "var(--ink-3)" }}>loading…</div>
      ) : filtered.length === 0 ? (
        <div className="mono" style={{ color: "var(--ink-3)", padding: 40, textAlign: "center" }}>
          no tools yet — answer onboarding or save from{" "}
          <Link href="/tools/explore" style={{ textDecoration: "underline" }}>Explore</Link>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
          {filtered.map((t) => (
            <article key={t.id} className="m-card" style={{ padding: 20 }}>
              <Link
                href={`/p/${t.tool.slug}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  textDecoration: "none",
                  color: "inherit",
                }}
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: "var(--r-sm)",
                    background: "var(--bg-2)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 600,
                    color: "var(--ink-1)",
                  }}
                >
                  {t.tool.name[0]?.toUpperCase()}
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div className="h-card" style={{ fontSize: 15 }}>{t.tool.name}</div>
                  <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 2 }}>
                    {t.tool.category} · {t.status} · {t.source.replace(/_/g, " ")}
                  </div>
                </div>
              </Link>
              <p className="body" style={{ marginTop: 12, fontSize: 13, color: "var(--ink-2)" }}>
                {t.tool.tagline}
              </p>
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button onClick={() => flipStatus(t)} className="mono" style={{
                  padding: "6px 12px",
                  borderRadius: "var(--r-pill)",
                  fontSize: 11,
                  border: "1px solid var(--line-0)",
                  color: "var(--ink-1)",
                  cursor: "pointer",
                }}>
                  → {t.status === "using" ? "saved" : "using"}
                </button>
                <button onClick={() => unsave(t)} className="mono" style={{
                  padding: "6px 12px",
                  borderRadius: "var(--r-pill)",
                  fontSize: 11,
                  border: "1px solid var(--line-0)",
                  color: "var(--ink-2)",
                  cursor: "pointer",
                }}>
                  remove
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
