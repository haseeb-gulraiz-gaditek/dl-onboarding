"use client";

// Mesh — global notification bell + banner.
// Per spec-delta frontend-secondary F-FE2-1.

import { useEffect, useState } from "react";
import Link from "next/link";

import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import { isAdmin } from "@/lib/admin";
import type {
  BannerResponse,
  NotificationCard,
  NotificationListResponse,
  UnreadCountResponse,
} from "@/lib/api-types";

// Reusable derivation logic — same shape /home uses.
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

function notificationLink(n: NotificationCard): string | null {
  const slug = (n.payload as { tool_slug?: string }).tool_slug;
  if (n.kind === "concierge_nudge" && slug) return `/p/${slug}`;
  if (n.kind === "launch_approved" && slug) return `/p/${slug}`;
  if (n.kind === "launch_rejected") return "/home";
  // community_reply payload has post_id but /c/{slug} routing requires
  // the community slug too; for V1 just route to /concierge.
  if (n.kind === "community_reply") return "/concierge";
  return null;
}

function notificationTitle(n: NotificationCard): string {
  const slug = (n.payload as { tool_slug?: string }).tool_slug;
  if (n.kind === "concierge_nudge")
    return `New launch matched your profile${slug ? `: ${slug}` : ""}`;
  if (n.kind === "launch_approved")
    return `Your launch was approved${slug ? ` → ${slug}` : ""}`;
  if (n.kind === "launch_rejected") return "Your launch needs another pass";
  if (n.kind === "community_reply") {
    const who = (n.payload as { commenter_display_name?: string })
      .commenter_display_name;
    return `${who || "Someone"} replied to your post`;
  }
  return n.kind;
}

export function HeaderBell() {
  const [authed, setAuthed] = useState(false);
  const [unread, setUnread] = useState(0);
  const [notes, setNotes] = useState<NotificationCard[]>([]);
  const [banner, setBanner] = useState<NotificationCard | null>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [open, setOpen] = useState(false);
  const [adminFlag, setAdminFlag] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) return;
    setAuthed(true);
    setAdminFlag(isAdmin());
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = async () => {
    try {
      const [c, b] = await Promise.allSettled([
        api.get<UnreadCountResponse>("/api/me/notifications/unread-count"),
        api.get<BannerResponse>("/api/me/notifications/banner"),
      ]);
      if (c.status === "fulfilled") setUnread(c.value.count);
      if (b.status === "fulfilled") setBanner(b.value.notification);
    } catch (e) {
      console.warn("[bell] load failed", e);
    }
  };

  const loadList = async () => {
    try {
      const r = await api.get<NotificationListResponse>(
        "/api/me/notifications?limit=10",
      );
      setNotes(r.notifications);
    } catch (e) {
      console.warn("[bell] list load failed", e);
    }
  };

  const markAllRead = async () => {
    try {
      await api.post("/api/me/notifications/read-all");
      setUnread(0);
      setNotes((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (e) {
      console.warn("[bell] mark-all-read failed", e);
    }
  };

  const dismissBanner = async () => {
    if (!banner) return;
    setBannerDismissed(true);
    try {
      await api.post(`/api/me/notifications/${banner.id}/read`);
      // Decrement unread to keep the badge honest.
      setUnread((n) => Math.max(0, n - 1));
    } catch (e) {
      console.warn("[bell] banner dismiss failed", e);
    }
  };

  if (!authed) return null;

  return (
    <>
      {banner && !bannerDismissed && (
        <div
          style={{
            position: "fixed",
            top: 16,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "10px 16px",
            background: "var(--bg-2)",
            border: "1px solid var(--accent)",
            borderRadius: "var(--r-pill)",
            boxShadow: "var(--glow-md)",
            maxWidth: "min(720px, calc(100vw - 32px))",
            fontSize: 14,
          }}
        >
          <span className="mono" style={{ color: "var(--accent)", fontSize: 12 }}>
            🚀 launch match
          </span>
          <span style={{ color: "var(--ink-0)" }}>{notificationTitle(banner)}</span>
          {(() => {
            const href = notificationLink(banner);
            return href ? (
              <Link
                href={href}
                className="mono"
                style={{ color: "var(--accent)", textDecoration: "underline" }}
              >
                view tool →
              </Link>
            ) : null;
          })()}
          <button
            onClick={dismissBanner}
            className="mono"
            style={{
              marginLeft: 8,
              color: "var(--ink-2)",
              fontSize: 18,
              lineHeight: 1,
            }}
            title="dismiss"
          >
            ×
          </button>
        </div>
      )}

      <div style={{ position: "relative", display: "inline-block" }}>
        <button
          onClick={() => {
            const next = !open;
            setOpen(next);
            if (next) void loadList();
          }}
          className="mono"
          style={{
            position: "relative",
            padding: "6px 10px",
            borderRadius: "var(--r-pill)",
            background: "transparent",
            color: "var(--ink-1)",
            fontSize: 16,
            cursor: "pointer",
          }}
          title="Notifications"
        >
          ◌
          {unread > 0 && (
            <span
              style={{
                position: "absolute",
                top: -2,
                right: -2,
                background: "var(--accent)",
                color: "var(--accent-ink)",
                borderRadius: "999px",
                fontSize: 10,
                padding: "0 5px",
                minWidth: 16,
                lineHeight: "16px",
                textAlign: "center",
                fontWeight: 600,
              }}
            >
              {unread}
            </span>
          )}
        </button>

        {open && (
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 8px)",
              right: 0,
              width: 360,
              maxHeight: "70vh",
              overflowY: "auto",
              background: "var(--bg-1)",
              border: "1px solid var(--line-0)",
              borderRadius: "var(--r-md)",
              boxShadow: "var(--shadow-card)",
              zIndex: 50,
            }}
          >
            <div
              style={{
                padding: "12px 16px",
                borderBottom: "1px solid var(--line-0)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                fontSize: 12,
              }}
              className="mono"
            >
              <span>Notifications</span>
              {unread > 0 && (
                <button onClick={markAllRead} style={{ color: "var(--accent)" }}>
                  mark all read
                </button>
              )}
            </div>
            {notes.length === 0 ? (
              <div
                className="mono"
                style={{ padding: 24, color: "var(--ink-3)", fontSize: 13 }}
              >
                no notifications yet
              </div>
            ) : (
              notes.map((n) => {
                const href = notificationLink(n) || "/concierge";
                return (
                  <Link
                    key={n.id}
                    href={href}
                    onClick={() => setOpen(false)}
                    style={{
                      display: "block",
                      padding: "10px 16px",
                      borderBottom: "1px solid var(--line-0)",
                      background: n.read ? "transparent" : "var(--bg-2)",
                      textDecoration: "none",
                    }}
                  >
                    <div style={{ color: "var(--ink-0)", fontSize: 13 }}>
                      {notificationTitle(n)}
                    </div>
                    <div
                      className="mono"
                      style={{ color: "var(--ink-3)", fontSize: 11, marginTop: 4 }}
                    >
                      {relativeTime(n.created_at)} ago · {n.kind}
                    </div>
                  </Link>
                );
              })
            )}
            <div
              style={{
                padding: 12,
                borderTop: "1px solid var(--line-0)",
                display: "flex",
                gap: 8,
                fontSize: 12,
              }}
              className="mono"
            >
              <Link href="/concierge" onClick={() => setOpen(false)}>
                see all →
              </Link>
              {adminFlag && (
                <Link
                  href="/admin/launches"
                  onClick={() => setOpen(false)}
                  style={{ marginLeft: "auto", color: "var(--accent)" }}
                >
                  admin →
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
