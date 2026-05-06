"use client";

// Mesh — admin tool curation queue.
// Per spec-delta frontend-secondary F-FE2-8.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { AdminCatalogListResponse, AdminCatalogTool } from "@/lib/api-types";

type TabKey = "pending" | "approved" | "rejected";

export default function AdminCatalogPage() {
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("pending");
  const [tools, setTools] = useState<AdminCatalogTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [forbidden, setForbidden] = useState(false);
  const [rejecting, setRejecting] = useState<string | null>(null);
  const [rejectComment, setRejectComment] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const load = async () => {
    setLoading(true);
    setForbidden(false);
    try {
      const r = await api.get<AdminCatalogListResponse>(
        `/admin/catalog?status=${tab}`,
      );
      setTools(r.tools);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        setForbidden(true);
      } else {
        console.warn("[admin/catalog] failed", e);
      }
    } finally {
      setLoading(false);
    }
  };

  const approve = async (slug: string) => {
    setBusy(slug);
    try {
      await api.post(`/admin/catalog/${slug}/approve`);
      await load();
    } catch (e) {
      console.warn("[admin/catalog] approve failed", e);
    } finally {
      setBusy(null);
    }
  };

  const confirmReject = async (slug: string) => {
    if (!rejectComment.trim()) return;
    setBusy(slug);
    try {
      await api.post(`/admin/catalog/${slug}/reject`, { comment: rejectComment.trim() });
      setRejecting(null);
      setRejectComment("");
      await load();
    } catch (e) {
      console.warn("[admin/catalog] reject failed", e);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Shell>
      {forbidden ? (
        <ForbiddenView />
      ) : (
        <>
          <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>/ admin · catalog</div>
          <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
            Tool curation.
          </h1>

          <div style={{ display: "flex", gap: 8, marginTop: 24, marginBottom: 24, flexWrap: "wrap" }}>
            {(["pending", "approved", "rejected"] as TabKey[]).map((k) => (
              <button
                key={k}
                onClick={() => setTab(k)}
                className="mono"
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--r-pill)",
                  fontSize: 12,
                  background: tab === k ? "var(--accent-soft)" : "transparent",
                  border: tab === k ? "1px solid var(--accent)" : "1px solid var(--line-0)",
                  color: tab === k ? "var(--ink-0)" : "var(--ink-2)",
                  cursor: "pointer",
                }}
              >
                {k}
              </button>
            ))}
            <Link href="/admin/launches" className="mono" style={{
              marginLeft: "auto",
              padding: "6px 14px",
              borderRadius: "var(--r-pill)",
              fontSize: 12,
              border: "1px solid var(--line-0)",
              color: "var(--ink-2)",
            }}>
              → launches
            </Link>
          </div>

          {loading ? (
            <div className="mono" style={{ color: "var(--ink-3)" }}>loading…</div>
          ) : tools.length === 0 ? (
            <div className="mono" style={{ color: "var(--ink-3)", padding: 40, textAlign: "center" }}>
              nothing in this tab
            </div>
          ) : (
            tools.map((t) => (
              <article key={t.slug} className="m-card" style={{ padding: 20, marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "baseline" }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <Link href={`/p/${t.slug}`} className="h-card" style={{
                      fontSize: 16,
                      textDecoration: "underline",
                      color: "inherit",
                    }}>
                      {t.name}
                    </Link>
                    <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 4 }}>
                      /p/{t.slug} · {t.category} · {t.source}
                    </div>
                    <p className="body" style={{ marginTop: 8, fontSize: 13, color: "var(--ink-1)" }}>
                      {t.tagline}
                    </p>
                    {t.rejection_comment && (
                      <p className="mono" style={{ color: "var(--warn)", fontSize: 12, marginTop: 8 }}>
                        rejected: {t.rejection_comment}
                      </p>
                    )}
                  </div>
                  <span className="mono" style={{
                    color:
                      t.curation_status === "approved" ? "var(--good)" :
                      t.curation_status === "rejected" ? "var(--warn)" :
                      "var(--ink-2)",
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                  }}>
                    {t.curation_status}
                  </span>
                </div>

                {tab === "pending" && (
                  <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <MButton size="sm" onClick={() => approve(t.slug)}>
                      {busy === t.slug ? "Approving…" : "Approve"}
                    </MButton>
                    {rejecting === t.slug ? (
                      <div style={{ display: "flex", gap: 8, flex: 1, alignItems: "flex-start" }}>
                        <textarea
                          className="m-input"
                          placeholder="why? (1..500 chars)"
                          rows={2}
                          value={rejectComment}
                          onChange={(e) => setRejectComment(e.target.value)}
                          style={{ flex: 1 }}
                        />
                        <MButton size="sm" variant="ghost" onClick={() => confirmReject(t.slug)}>
                          {busy === t.slug ? "Rejecting…" : "Confirm reject"}
                        </MButton>
                        <button
                          onClick={() => { setRejecting(null); setRejectComment(""); }}
                          className="mono"
                          style={{ color: "var(--ink-3)", fontSize: 12 }}
                        >
                          cancel
                        </button>
                      </div>
                    ) : (
                      <MButton size="sm" variant="ghost" onClick={() => setRejecting(t.slug)}>
                        Reject
                      </MButton>
                    )}
                  </div>
                )}
              </article>
            ))
          )}
        </>
      )}
    </Shell>
  );
}

function ForbiddenView() {
  return (
    <>
      <h1 className="onb-q-title">Admin only</h1>
      <p className="body" style={{ color: "var(--ink-2)" }}>
        Your account isn&apos;t in <code>ADMIN_EMAILS</code>.
      </p>
      <Link href="/home" style={{ marginTop: 16, display: "inline-block" }}>
        <MButton variant="ghost">← Back to home</MButton>
      </Link>
    </>
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
