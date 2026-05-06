"use client";

// Mesh — Login page.
// Per spec-delta frontend-core F-FE-6 (revised).

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { ToolGraph } from "@/components/ToolGraph";
import { login as authLogin } from "@/lib/auth";
import { ApiError } from "@/lib/api";

// /login deliberately does NOT auto-redirect signed-in users — they
// might want to switch accounts. The /home page has a logout button
// for the clean exit path.
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    if (!email || !password) {
      setErr("Email and password are both required.");
      return;
    }
    setErr(null);
    setBusy(true);
    try {
      const resp = await authLogin({ email: email.trim(), password });
      // Both roles land on /home; founders see launch_* notifications,
      // users see concierge_nudge + community_reply (cycle #12 inbox is
      // role-agnostic).
      if (resp.user.role_type === "founder") {
        router.replace("/home");
      } else {
        router.replace("/home");
      }
    } catch (e) {
      let code: string | null = null;
      if (e instanceof ApiError && typeof e.body === "object" && e.body) {
        const b = e.body as Record<string, unknown>;
        if (b.detail && typeof b.detail === "object" && b.detail !== null
          && "error" in (b.detail as Record<string, unknown>)) {
          code = String((b.detail as Record<string, unknown>).error);
        } else if (typeof b.error === "string") {
          code = b.error;
        }
      }
      if (code === "invalid_credentials") {
        setErr("Wrong email or password.");
      } else if (code === "rate_limited") {
        setErr("Too many attempts. Wait a minute and try again.");
      } else {
        setErr("Login failed. Try again in a moment.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="onb-root">
      <div className="onb-graph-pane">
        <div className="onb-graph-canvas">
          <ToolGraph progress={0.2} highlightedTags={[]} mode="hero" scale={1.4} />
        </div>
      </div>

      <div className="onb-content-pane">
        <header className="onb-header">
          <Link href="/" className="onb-brand">
            <MeshMark size={20} />
            <span>Mesh</span>
          </Link>
          <Link href="/signup" className="onb-exit mono">
            new here? sign up →
          </Link>
        </header>

        <div className="onb-q-wrap">
          <div className="onb-q-card">
            <h1 className="onb-q-title">Sign in.</h1>
            <p className="onb-q-sub">Welcome back.</p>

            <div className="founders-fields" style={{ marginTop: 24 }}>
              <div className="founders-field">
                <label className="founders-label mono">email</label>
                <input
                  className="m-input founders-input"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="founders-field">
                <label className="founders-label mono">password</label>
                <input
                  className="m-input founders-input"
                  type="password"
                  placeholder="•••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submit()}
                />
              </div>
            </div>

            {err && (
              <div className="mono" style={{ color: "var(--warn)", marginTop: 16 }}>
                {err}
              </div>
            )}

            <div className="onb-q-multi-foot" style={{ marginTop: 24 }}>
              <span className="mono onb-q-skip">
                no password reset in V1 — DM admin if you&apos;re locked out
              </span>
              <MButton onClick={submit} variant="primary">
                {busy ? "Signing in…" : "Sign in →"}
              </MButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
