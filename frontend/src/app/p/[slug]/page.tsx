"use client";

// Mesh — canonical product page.
// Per spec-delta frontend-core F-FE-9.

import { useEffect, useState } from "react";
import Link from "next/link";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";
import { api, ApiError } from "@/lib/api";
import { isAuthenticated, currentUser } from "@/lib/auth";
import type {
  ProductPageResponse,
  UserPublic,
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
        if (!cancelled) setData(r);
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

  return (
    <ProductShell>
      <div className="onb-result-eyebrow mono">
        / {tool.is_founder_launched ? "founder launch" : "tool"} ·{" "}
        {tool.category}
      </div>
      <h1 className="onb-result-title">{tool.name}</h1>
      <p className="onb-result-sub body-lg">{tool.tagline}</p>

      <div
        style={{
          display: "flex",
          gap: 12,
          marginTop: 16,
          flexWrap: "wrap",
        }}
      >
        {tool.labels.map((l) => (
          <span key={l} className="onb-graph-tag">
            {l}
          </span>
        ))}
        <span className="mono onb-graph-tag">
          ♡ {tool.vote_score}
        </span>
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

      <p className="body-lg" style={{ marginTop: 24 }}>
        {tool.description}
      </p>

      {launch && (
        <div className="m-card" style={{ padding: 24, marginTop: 32 }}>
          <div className="mono" style={{ color: "var(--ink-2)", marginBottom: 8 }}>
            / launched by
          </div>
          <div className="h-card">{launch.founder_display_name}</div>
          <div className="mono" style={{ color: "var(--ink-2)", marginTop: 4 }}>
            {launch.founder_email}
          </div>
          <p className="body" style={{ marginTop: 16 }}>
            <strong>Problem:</strong> {launch.problem_statement}
          </p>
          <p className="body" style={{ marginTop: 8 }}>
            <strong>ICP:</strong> {launch.icp_description}
          </p>
          {launch.approved_at && (
            <div
              className="mono"
              style={{ color: "var(--ink-3)", marginTop: 12, fontSize: 12 }}
            >
              approved {new Date(launch.approved_at).toLocaleDateString()}
            </div>
          )}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, marginTop: 32 }}>
        <a href={tool.url} target="_blank" rel="noreferrer">
          <MButton variant="primary" trailing="↗">
            Open {tool.name}
          </MButton>
        </a>
        {user?.role_type === "user" && (
          <MButton
            variant="ghost"
            onClick={save}
          >
            {saved ? "✓ Saved" : saving ? "Saving…" : "Save to my tools"}
          </MButton>
        )}
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
