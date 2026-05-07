"use client";

// Mesh — canonical product page.
// Per spec-delta frontend-core F-FE-9 + cycle #15 enrichment:
// upvote, sidebar stats, discuss-in-community link, richer layout.

import { useEffect, useState } from "react";
import Link from "next/link";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";
import { api, ApiError } from "@/lib/api";
import { isAuthenticated, currentUser } from "@/lib/auth";
import type {
  ProductPageResponse,
  UserPublic,
  VoteResponse,
} from "@/lib/api-types";

export default function ProductPage({
  params,
}: {
  params: { slug: string };
}) {
  const [data, setData] = useState<ProductPageResponse | null>(null);
  const [user, setUser] = useState<UserPublic | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [voteScore, setVoteScore] = useState<number>(0);
  const [voted, setVoted] = useState<boolean>(false);
  const [voting, setVoting] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (isAuthenticated()) {
        const me = await currentUser();
        if (!cancelled) setUser(me);
      }
      try {
        const r = await api.get<ProductPageResponse>(
          `/api/tools/${params.slug}`,
        );
        if (!cancelled) {
          setData(r);
          setVoteScore(r.tool.vote_score);
        }
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {
          setErr("not_found");
        } else {
          setErr("error");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.slug]);

  const save = async () => {
    setSaving(true);
    try {
      await api.post("/api/me/tools", {
        tool_slug: params.slug,
        status: "saved",
      });
      setSaved(true);
    } catch (e) {
      console.error("[product] save failed", e);
    } finally {
      setSaving(false);
    }
  };

  const upvote = async () => {
    if (!data || voting || user?.role_type !== "user") return;
    setVoting(true);
    const direction = voted ? -1 : 1;
    // Optimistic update.
    setVoteScore((s) => s + direction);
    setVoted((v) => !v);
    try {
      await api.post<VoteResponse>("/api/votes", {
        target_type: "tool",
        target_id: data.tool.id,
        direction,
      });
    } catch (e) {
      console.warn("[product] vote failed; reverting", e);
      // Revert on failure.
      setVoteScore((s) => s - direction);
      setVoted((v) => !v);
    } finally {
      setVoting(false);
    }
  };

  if (err === "not_found") {
    return (
      <ProductShell>
        <h1 className="onb-q-title">Tool not found.</h1>
        <p className="body-lg" style={{ color: "var(--ink-2)" }}>
          The slug <code>{params.slug}</code> doesn&apos;t resolve in either
          collection.
        </p>
        <div style={{ marginTop: 24 }}>
          <Link href="/home">
            <MButton variant="ghost">← Back to home</MButton>
          </Link>
        </div>
      </ProductShell>
    );
  }

  if (!data) {
    return (
      <ProductShell>
        <div className="mono" style={{ color: "var(--ink-2)" }}>
          loading…
        </div>
      </ProductShell>
    );
  }

  const { tool, launch } = data;
  const canVote = user?.role_type === "user";
  const firstCommunity = launch?.target_community_slugs?.[0];

  return (
    <ProductShell>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) 280px",
          gap: 32,
          alignItems: "start",
        }}
      >
        {/* Main column */}
        <div>
          <div className="onb-result-eyebrow mono">
            / {tool.is_founder_launched ? "founder launch" : "tool"} ·{" "}
            {tool.category}
          </div>
          <h1 className="onb-result-title">{tool.name}</h1>
          <p className="onb-result-sub body-lg">{tool.tagline}</p>

          <div
            style={{
              display: "flex",
              gap: 8,
              marginTop: 16,
              flexWrap: "wrap",
            }}
          >
            {tool.labels.map((l) => (
              <span key={l} className="onb-graph-tag">
                {l}
              </span>
            ))}
            <span className="mono onb-graph-tag">{tool.pricing_summary}</span>
            {tool.is_founder_launched && (
              <span
                className="mono onb-graph-tag"
                style={{ color: "var(--accent)" }}
              >
                🚀 launch
              </span>
            )}
          </div>

          {/* About */}
          <section style={{ marginTop: 32 }}>
            <h2
              className="mono"
              style={{
                fontSize: 11,
                color: "var(--ink-3)",
                letterSpacing: 1,
                textTransform: "uppercase",
                marginBottom: 12,
              }}
            >
              About
            </h2>
            <p className="body-lg" style={{ whiteSpace: "pre-line" }}>
              {tool.description}
            </p>
          </section>

          {/* Launch context */}
          {launch && (
            <section style={{ marginTop: 32 }}>
              <h2
                className="mono"
                style={{
                  fontSize: 11,
                  color: "var(--ink-3)",
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  marginBottom: 12,
                }}
              >
                Why this exists
              </h2>
              <div className="m-card" style={{ padding: 24 }}>
                <div className="mono" style={{ color: "var(--ink-3)", fontSize: 11 }}>
                  / launched by
                </div>
                <div className="h-card" style={{ marginTop: 4 }}>
                  {launch.founder_display_name}
                </div>
                <div
                  className="mono"
                  style={{ color: "var(--ink-3)", marginTop: 2, fontSize: 12 }}
                >
                  {launch.founder_email}
                </div>
                <p className="body" style={{ marginTop: 16 }}>
                  <strong>Problem:</strong> {launch.problem_statement}
                </p>
                <p className="body" style={{ marginTop: 8 }}>
                  <strong>Built for:</strong> {launch.icp_description}
                </p>
                <div
                  className="mono"
                  style={{
                    color: "var(--ink-3)",
                    marginTop: 16,
                    fontSize: 11,
                    display: "flex",
                    gap: 12,
                    flexWrap: "wrap",
                  }}
                >
                  {launch.approved_at && (
                    <span>
                      approved {new Date(launch.approved_at).toLocaleDateString()}
                    </span>
                  )}
                  {launch.target_community_slugs?.length > 0 && (
                    <span>
                      live in {launch.target_community_slugs.length} room
                      {launch.target_community_slugs.length > 1 ? "s" : ""}
                    </span>
                  )}
                  <span style={{ color: "var(--accent)" }}>
                    matched {launch.matched_count} profile
                    {launch.matched_count === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
            </section>
          )}

          {/* Discuss */}
          {launch && launch.target_community_slugs?.length > 0 && (
            <section style={{ marginTop: 32 }}>
              <h2
                className="mono"
                style={{
                  fontSize: 11,
                  color: "var(--ink-3)",
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  marginBottom: 12,
                }}
              >
                Discuss
              </h2>
              <div
                style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
              >
                {launch.target_community_slugs.map((slug) => (
                  <Link
                    key={slug}
                    href={`/c/${slug}`}
                    className="onb-graph-tag"
                    style={{
                      textDecoration: "none",
                      color: "var(--ink-0)",
                    }}
                  >
                    /c/{slug} →
                  </Link>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside style={{ position: "sticky", top: 80 }}>
          <div className="m-card" style={{ padding: 20 }}>
            {/* Vote / score */}
            <button
              onClick={upvote}
              disabled={!canVote || voting}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                width: "100%",
                padding: "12px 16px",
                borderRadius: "var(--r-md)",
                border: voted
                  ? "1px solid var(--accent)"
                  : "1px solid var(--line-0)",
                background: voted ? "var(--accent-soft)" : "var(--bg-2)",
                color: "var(--ink-0)",
                cursor: canVote ? "pointer" : "default",
                marginBottom: 12,
              }}
              title={
                canVote
                  ? voted
                    ? "Click to remove your upvote"
                    : "Upvote this tool"
                  : "Sign in as a user to vote"
              }
            >
              <span
                style={{ fontSize: 18, color: voted ? "var(--accent)" : "var(--ink-2)" }}
              >
                {voted ? "♥" : "♡"}
              </span>
              <span className="h-card" style={{ fontSize: 18 }}>
                {voteScore}
              </span>
              <span
                className="mono"
                style={{ marginLeft: "auto", color: "var(--ink-3)", fontSize: 11 }}
              >
                {voted ? "upvoted" : "upvote"}
              </span>
            </button>

            <a
              href={tool.url}
              target="_blank"
              rel="noreferrer"
              style={{ display: "block", marginBottom: 8 }}
            >
              <MButton variant="primary" trailing="↗">
                Open {tool.name}
              </MButton>
            </a>

            {canVote && (
              <button
                onClick={save}
                disabled={saving || saved}
                style={{
                  width: "100%",
                  padding: "10px 16px",
                  borderRadius: "var(--r-pill)",
                  border: "1px solid var(--line-0)",
                  background: "transparent",
                  color: "var(--ink-1)",
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                {saved ? "✓ Saved" : saving ? "Saving…" : "+ Save to my tools"}
              </button>
            )}

            <hr
              style={{
                border: "none",
                borderTop: "1px solid var(--line-0)",
                margin: "16px 0",
              }}
            />

            <dl
              className="mono"
              style={{
                fontSize: 11,
                color: "var(--ink-3)",
                display: "grid",
                gridTemplateColumns: "auto 1fr",
                gap: "6px 12px",
                margin: 0,
              }}
            >
              <dt>category</dt>
              <dd style={{ margin: 0, color: "var(--ink-1)" }}>
                {tool.category}
              </dd>
              <dt>pricing</dt>
              <dd style={{ margin: 0, color: "var(--ink-1)" }}>
                {tool.pricing_summary}
              </dd>
              <dt>source</dt>
              <dd style={{ margin: 0, color: "var(--ink-1)" }}>
                {tool.is_founder_launched ? "founder launch" : "curated"}
              </dd>
              {launch && (
                <>
                  <dt>matched</dt>
                  <dd style={{ margin: 0, color: "var(--accent)" }}>
                    {launch.matched_count} profile
                    {launch.matched_count === 1 ? "" : "s"}
                  </dd>
                </>
              )}
              {firstCommunity && (
                <>
                  <dt>discuss</dt>
                  <dd style={{ margin: 0 }}>
                    <Link
                      href={`/c/${firstCommunity}`}
                      style={{ color: "var(--accent)" }}
                    >
                      /c/{firstCommunity}
                    </Link>
                  </dd>
                </>
              )}
            </dl>
          </div>
        </aside>
      </div>
    </ProductShell>
  );
}

function ProductShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="onb-root">
      <div className="onb-content-pane" style={{ width: "100%" }}>
        <header className="onb-header">
          <Link href="/" className="onb-brand">
            <MeshMark size={20} />
            <span>Mesh</span>
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <HeaderBell />
            <Link href="/home" className="onb-exit mono">
              ← home
            </Link>
          </div>
        </header>
        <div className="onb-result" style={{ paddingTop: 32 }}>
          {children}
        </div>
      </div>
    </div>
  );
}
