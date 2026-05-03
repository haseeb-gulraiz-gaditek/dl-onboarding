"use client";

// Mesh — Signup page (user OR founder).
// Per spec-delta frontend-core F-FE-6 (revised): signup is its own
// route, with a role toggle. On submit:
//   user    → POST /api/auth/signup role_question_answer=finding_tools   → /onboarding
//   founder → POST /api/auth/signup role_question_answer=launching_product → /founders/launch

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { ToolGraph } from "@/components/ToolGraph";
import { signup as authSignup, isAuthenticated } from "@/lib/auth";
import { ApiError } from "@/lib/api";

type Role = "user" | "founder";

function SignupInner() {
  const router = useRouter();
  const search = useSearchParams();
  const initialRole: Role = search.get("role") === "founder" ? "founder" : "user";

  const [role, setRole] = useState<Role>(initialRole);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // If already signed in, send them where they belong.
  useEffect(() => {
    if (isAuthenticated()) router.replace("/home");
  }, [router]);

  const submit = async () => {
    if (!email || password.length < 8) {
      setErr("Email is required, password ≥ 8 chars.");
      return;
    }
    setErr(null);
    setBusy(true);
    try {
      const resp = await authSignup({
        email: email.trim(),
        password,
        role_question_answer:
          role === "founder" ? "launching_product" : "finding_tools",
      });
      // Route by role.
      if (resp.user.role_type === "founder") {
        router.replace("/founders/launch");
      } else {
        router.replace("/onboarding");
      }
    } catch (e) {
      const msg =
        e instanceof ApiError && typeof e.body === "object" && e.body && "error" in e.body
          ? String((e.body as { error: unknown }).error)
          : e instanceof ApiError && typeof e.body === "object" && e.body && "detail" in e.body
            ? JSON.stringify((e.body as { detail: unknown }).detail)
            : "Signup failed. Try a different email.";
      setErr(msg);
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
          <Link href="/login" className="onb-exit mono">
            already have an account? sign in →
          </Link>
        </header>

        <div className="onb-q-wrap">
          <div className="onb-q-card">
            <h1 className="onb-q-title">Sign up.</h1>
            <p className="onb-q-sub">Tell us which side you&apos;re on.</p>

            <div
              className="m-hero-toggle"
              role="tablist"
              style={{ marginTop: 8, marginBottom: 24, position: "relative" }}
            >
              <button
                className={`m-hero-toggle-btn ${role === "user" ? "on" : ""}`}
                onClick={() => setRole("user")}
                role="tab"
                aria-selected={role === "user"}
              >
                I&apos;m finding my AI tools
              </button>
              <button
                className={`m-hero-toggle-btn ${role === "founder" ? "on" : ""}`}
                onClick={() => setRole("founder")}
                role="tab"
                aria-selected={role === "founder"}
              >
                I&apos;m launching a product
              </button>
              <span
                className={`m-hero-toggle-pill ${role === "user" ? "left" : "right"}`}
                aria-hidden="true"
              />
            </div>

            <div className="founders-fields">
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
                  placeholder="at least 8 characters"
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
                {role === "user"
                  ? "next: 5 quick questions"
                  : "next: launch flow"}
              </span>
              <MButton onClick={submit} variant="primary">
                {busy
                  ? "Creating…"
                  : role === "user"
                    ? "Find my tools →"
                    : "Start launch →"}
              </MButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={null}>
      <SignupInner />
    </Suspense>
  );
}
