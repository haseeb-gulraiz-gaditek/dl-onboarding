"use client";

// Mesh — admin launch queue.
// Per spec-delta frontend-secondary F-FE2-7.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type {
  LaunchAdminCard,
  LaunchAdminListResponse,
  VerificationStatus,
} from "@/lib/api-types";

const TABS: { key: VerificationStatus | "all"; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
];

export default function AdminLaunchesPage() {
  const router = useRouter();
  const [tab, setTab] = useState<VerificationStatus>("pending");
  const [rows, setRows] = useState<LaunchAdminCard[]>([]);
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
      const r = await api.get<LaunchAdminListResponse>(
        `/admin/launches?status=${tab}`,
      );
      setRows(r.launches);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        setForbidden(true);
      } else {
        console.warn("[admin/launches] failed", e);
      }
    } finally {
      setLoading(false);
    }
  };

  const approve = async (id: string) => {
    setBusy(id);
    try {
      await api.post(`/admin/launches/${id}/approve`);
      await load();
    } catch (e) {
      console.warn("[admin/launches] approve failed", e);
    } finally {
      setBusy(null);
    }
  };

  const confirmReject = async (id: string) => {
    if (!rejectComment.trim()) return;
    setBusy(id);
    try {
      await api.post(`/admin/launches/${id}/reject`, { comment: rejectComment.trim() });
      setRejecting(null);
      setRejectComment("");
      await load();
    } catch (e) {
      console.warn("[admin/launches] reject failed", e);
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
          <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>/ admin · launches</div>
          <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
            Verification queue.
          </h1>

          <div style={{ display: "flex", gap: 8, marginTop: 24, marginBottom: 24, flexWrap: "wrap" }}>
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key as VerificationStatus)}
                className="mono"
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--r-pill)",
                  fontSize: 12,
                  background: tab === t.key ? "var(--accent-soft)" : "transparent",
                  border: tab === t.key ? "1px solid var(--accent)" : "1px solid var(--line-0)",
                  color: tab === t.key ? "var(--ink-0)" : "var(--ink-2)",
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            ))}
            <Link href="/admin/catalog" className="mono" style={{
              marginLeft: "auto",
              padding: "6px 14px",
              borderRadius: "var(--r-pill)",
              fontSize: 12,
              border: "1px solid var(--line-0)",
              color: "var(--ink-2)",
            }}>
              → catalog
            </Link>
          </div>

          {loading ? (
            <div className="mono" style={{ color: "var(--ink-3)" }}>loading…</div>
          ) : rows.length === 0 ? (
            <div className="mono" style={{ color: "var(--ink-3)", padding: 40, textAlign: "center" }}>
              nothing in this tab
            </div>
          ) : (
            rows.map((row) => (
              <article key={row.id} className="m-card" style={{ padding: 20, marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "baseline" }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <a href={row.product_url} target="_blank" rel="noreferrer" className="h-card" style={{
                      fontSize: 16,
                      textDecoration: "underline",
                      color: "inherit",
                    }}>
                      {row.product_url}
                    </a>
                    <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 4 }}>
                      from {row.founder_email} · {new Date(row.created_at).toLocaleDateString()}
                    </div>
                    <p className="body" style={{ marginTop: 12, fontSize: 13, color: "var(--ink-1)" }}>
                      {row.problem_statement}
                    </p>
                  </div>
                  <span className="mono" style={{
                    color:
                      row.verification_status === "approved" ? "var(--good)" :
                      row.verification_status === "rejected" ? "var(--warn)" :
                      "var(--ink-2)",
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                  }}>
                    {row.verification_status}
                  </span>
                </div>

                {tab === "pending" && (
                  <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <MButton
                      size="sm"
                      onClick={() => approve(row.id)}
                    >
                      {busy === row.id ? "Approving…" : "Approve"}
                    </MButton>
                    {rejecting === row.id ? (
                      <div style={{ display: "flex", gap: 8, flex: 1, alignItems: "flex-start" }}>
                        <textarea
                          className="m-input"
                          placeholder="why? (1..500 chars)"
                          rows={2}
                          value={rejectComment}
                          onChange={(e) => setRejectComment(e.target.value)}
                          style={{ flex: 1 }}
                        />
                        <MButton
                          size="sm"
                          variant="ghost"
                          onClick={() => confirmReject(row.id)}
                        >
                          {busy === row.id ? "Rejecting…" : "Confirm reject"}
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
                      <MButton
                        size="sm"
                        variant="ghost"
                        onClick={() => setRejecting(row.id)}
                      >
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
        Your account isn&apos;t in <code>ADMIN_EMAILS</code>. Sign in with an admin
        email to access this page.
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
