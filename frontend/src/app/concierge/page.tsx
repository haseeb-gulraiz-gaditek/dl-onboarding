"use client";

// Mesh — concierge inbox.
// Per spec-delta frontend-secondary F-FE2-4.
//
// V1: each notification renders as a single message in the
// conversation panel. Multi-message threads are V1.5 (would need
// new backend collection). Reply composer only fires for
// concierge_nudge notifications via /api/concierge/respond.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type {
  NotificationCard,
  NotificationListResponse,
} from "@/lib/api-types";

function relativeTime(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

const KIND_LABELS: Record<string, string> = {
  concierge_nudge: "launch matched your profile",
  launch_approved: "launch approved",
  launch_rejected: "launch needs another pass",
  community_reply: "community reply",
};

const REASONING_COPY: Record<string, string[]> = {
  concierge_nudge: [
    "Matched on profile similarity (cosine ≥ 0.85 / top-5 by score).",
    "Founder ICP description embedded against your answer profile.",
    "You're in the top slice for this launch's intended audience.",
  ],
  launch_approved: [
    "Mesh staff verified your launch URL + ICP + presence.",
    "Tool row added to the catalog at /p/{slug}.",
    "Now appearing in target communities + matched-user nudges.",
  ],
  launch_rejected: [
    "Mesh staff felt this didn't pass the bar (see comment).",
    "Resubmit a new launch any time — your data stays.",
  ],
  community_reply: [
    "Someone commented on a post you authored.",
    "Open the community room to reply.",
  ],
};

export default function ConciergePage() {
  const router = useRouter();
  const [notes, setNotes] = useState<NotificationCard[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
      const r = await api.get<NotificationListResponse>(
        "/api/me/notifications?limit=50",
      );
      setNotes(r.notifications);
      if (r.notifications.length > 0 && !activeId) {
        setActiveId(r.notifications[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  const active = notes.find((n) => n.id === activeId) || null;

  const markRead = async (id: string) => {
    try {
      await api.post(`/api/me/notifications/${id}/read`);
      setNotes((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    } catch (e) {
      console.warn("[concierge] mark read failed", e);
    }
  };

  const respond = async (action: "tell_me_more" | "skip") => {
    if (!active) return;
    const launch_id = (active.payload as { launch_id?: string }).launch_id;
    if (!launch_id) return;
    try {
      const resp = await api.post<{ accepted: boolean; redirect_url: string | null }>(
        "/api/concierge/respond",
        { launch_id, action },
      );
      if (action === "tell_me_more" && resp.redirect_url) {
        window.open(resp.redirect_url, "_blank");
      }
      await markRead(active.id);
    } catch (e) {
      console.warn("[concierge] respond failed", e);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", gridTemplateColumns: "300px 1fr 280px" }}>
      {/* Left: threads list */}
      <aside
        style={{
          borderRight: "1px solid var(--line-0)",
          padding: 16,
          overflowY: "auto",
          maxHeight: "100vh",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <Link href="/home" className="mono" style={{ color: "var(--ink-2)", fontSize: 12 }}>
            ← home
          </Link>
          <HeaderBell />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <MeshMark size={18} />
          <span className="h-card">concierge</span>
        </div>
        {loading ? (
          <div className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>loading…</div>
        ) : notes.length === 0 ? (
          <div className="mono" style={{ color: "var(--ink-3)", fontSize: 12 }}>
            no notifications yet — Mesh will surface patterns as your profile compounds
          </div>
        ) : (
          notes.map((n) => (
            <button
              key={n.id}
              onClick={() => {
                setActiveId(n.id);
                if (!n.read) void markRead(n.id);
              }}
              className="mono"
              style={{
                width: "100%",
                textAlign: "left",
                padding: "10px 12px",
                marginBottom: 4,
                borderRadius: "var(--r-sm)",
                background: activeId === n.id ? "var(--accent-soft)" : n.read ? "transparent" : "var(--bg-2)",
                color: "var(--ink-1)",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              <div style={{ color: "var(--ink-0)", fontSize: 13, marginBottom: 4 }}>
                {KIND_LABELS[n.kind] || n.kind}
              </div>
              <div style={{ color: "var(--ink-3)" }}>{relativeTime(n.created_at)} ago</div>
            </button>
          ))
        )}
      </aside>

      {/* Center: conversation */}
      <main style={{ padding: 32, overflowY: "auto", maxHeight: "100vh" }}>
        {!active ? (
          <div className="mono" style={{ color: "var(--ink-3)", paddingTop: 64 }}>
            select a thread on the left
          </div>
        ) : (
          <ConversationPanel n={active} onRespond={respond} />
        )}
      </main>

      {/* Right: reasoning trace */}
      <aside
        style={{
          borderLeft: "1px solid var(--line-0)",
          padding: 24,
          overflowY: "auto",
          maxHeight: "100vh",
        }}
      >
        {active ? <ReasoningPanel n={active} /> : null}
      </aside>
    </div>
  );
}

function ConversationPanel({
  n,
  onRespond,
}: {
  n: NotificationCard;
  onRespond: (action: "tell_me_more" | "skip") => void;
}) {
  const slug = (n.payload as { tool_slug?: string }).tool_slug;
  const comment = (n.payload as { comment?: string }).comment;
  const who = (n.payload as { commenter_display_name?: string }).commenter_display_name;
  return (
    <div>
      <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11 }}>
        / concierge thread
      </div>
      <h1 className="h-display" style={{ fontSize: 32, marginTop: 8 }}>
        {KIND_LABELS[n.kind] || n.kind}
      </h1>

      <article
        className="m-card"
        style={{ padding: 20, marginTop: 24 }}
      >
        <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
          mesh concierge · {relativeTime(n.created_at)} ago
        </div>
        <p className="body-lg" style={{ marginTop: 8 }}>
          {n.kind === "concierge_nudge" && slug && (
            <>
              I noticed something in your community I think you&apos;ll want to see —
              a new launch (<Link href={`/p/${slug}`} style={{ textDecoration: "underline" }}>{slug}</Link>) just matched
              your profile. It&apos;s in the top slice for what you described in onboarding.
            </>
          )}
          {n.kind === "launch_approved" && slug && (
            <>
              Your launch was approved and is now live at{" "}
              <Link href={`/p/${slug}`} style={{ textDecoration: "underline" }}>/p/{slug}</Link>.
              It&apos;s fanning into your target communities right now.
            </>
          )}
          {n.kind === "launch_rejected" && (
            <>
              Mesh staff sent your launch back for another pass.{" "}
              {comment ? <em>{comment}</em> : "No specific feedback was attached."}{" "}
              You can resubmit anytime.
            </>
          )}
          {n.kind === "community_reply" && (
            <>
              {who || "Someone"} replied to a post you authored. Open the
              community thread to read + reply.
            </>
          )}
        </p>
      </article>

      {n.kind === "concierge_nudge" && (
        <div className="m-card" style={{ padding: 20, marginTop: 16 }}>
          <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11, marginBottom: 8 }}>
            your reply
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <MButton size="sm" onClick={() => onRespond("tell_me_more")}>
              Tell me more →
            </MButton>
            <MButton size="sm" variant="ghost" onClick={() => onRespond("skip")}>
              Skip
            </MButton>
          </div>
        </div>
      )}
    </div>
  );
}

function ReasoningPanel({ n }: { n: NotificationCard }) {
  const lines = REASONING_COPY[n.kind] || ["No reasoning trace yet for this kind."];
  return (
    <div>
      <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
        / why you&apos;re seeing this
      </div>
      <h2 className="h-card" style={{ marginTop: 8 }}>Reasoning trace</h2>
      <p className="body" style={{ color: "var(--ink-2)", fontSize: 13, marginTop: 8 }}>
        Each notification has weights. We show them so you can argue with us.
        (V1 surfaces generic per-kind copy — per-notification scoring is V1.5.)
      </p>
      <div style={{ marginTop: 16 }}>
        {lines.map((l, i) => (
          <div
            key={i}
            className="body"
            style={{
              color: "var(--ink-1)",
              fontSize: 13,
              padding: "8px 0",
              borderBottom: "1px solid var(--line-0)",
            }}
          >
            · {l}
          </div>
        ))}
      </div>
    </div>
  );
}
