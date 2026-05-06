"use client";

// Mesh — per-launch analytics.
// Per spec-delta frontend-secondary F-FE2-6.

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { MButton, MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

import { api, ApiError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type { LaunchAnalyticsResponse } from "@/lib/api-types";

export default function LaunchAnalyticsPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const [data, setData] = useState<LaunchAnalyticsResponse | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    (async () => {
      try {
        const r = await api.get<LaunchAnalyticsResponse>(
          `/api/founders/launches/${params.id}/analytics`,
        );
        setData(r);
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {
          setNotFound(true);
        } else if (e instanceof ApiError && e.status === 403) {
          router.replace("/home");
        }
      }
    })();
  }, [params.id, router]);

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

      <main style={{ maxWidth: 880, margin: "0 auto" }}>
        {notFound ? (
          <>
            <h1 className="onb-q-title">Launch not found</h1>
            <p className="body" style={{ color: "var(--ink-2)" }}>
              Either the launch doesn&apos;t exist or it belongs to another founder.
            </p>
            <Link href="/home" style={{ marginTop: 16, display: "inline-block" }}>
              <MButton variant="ghost">← Back to dashboard</MButton>
            </Link>
          </>
        ) : !data ? (
          <div className="mono" style={{ color: "var(--ink-2)" }}>loading…</div>
        ) : (
          <Analytics data={data} />
        )}
      </main>
    </div>
  );
}

function Analytics({ data }: { data: LaunchAnalyticsResponse }) {
  const totalCommunityClicks = Object.values(data.clicks_by_community).reduce(
    (a, b) => a + b,
    0,
  );
  const maxCommunityClicks = Math.max(
    1,
    ...Object.values(data.clicks_by_community),
  );

  return (
    <div>
      <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
        / launch analytics
      </div>
      <h1 className="h-display" style={{ fontSize: 36, marginTop: 6 }}>
        {data.approved_tool_slug ? (
          <Link
            href={`/p/${data.approved_tool_slug}`}
            style={{ textDecoration: "underline", color: "inherit" }}
          >
            {data.approved_tool_slug}
          </Link>
        ) : (
          "Pending launch"
        )}
      </h1>
      <div className="mono" style={{ color: "var(--ink-2)", marginTop: 8 }}>
        status: {data.verification_status}
      </div>

      {/* Headline counts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 12,
          marginTop: 32,
        }}
      >
        <Stat label="matched" value={data.matched_count} />
        <Stat label="tell-me-more" value={data.tell_me_more_count} />
        <Stat label="skip" value={data.skip_count} />
        <Stat label="clicks" value={data.total_clicks} />
      </div>

      {/* clicks_by_community */}
      <section style={{ marginTop: 40 }}>
        <h2 className="h-card">Clicks by community</h2>
        {totalCommunityClicks === 0 ? (
          <div className="mono" style={{ color: "var(--ink-3)", marginTop: 16 }}>
            no clicks yet
          </div>
        ) : (
          <div style={{ marginTop: 16 }}>
            {Object.entries(data.clicks_by_community)
              .sort((a, b) => b[1] - a[1])
              .map(([slug, count]) => (
                <div key={slug} style={{ marginBottom: 10 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: 13,
                      marginBottom: 4,
                    }}
                  >
                    <Link href={`/c/${slug}`} style={{ textDecoration: "none", color: "var(--ink-1)" }}>
                      /c/{slug}
                    </Link>
                    <span className="mono" style={{ color: "var(--ink-2)" }}>{count}</span>
                  </div>
                  <div
                    style={{
                      height: 8,
                      borderRadius: 4,
                      background: "var(--bg-2)",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${(count / maxCommunityClicks) * 100}%`,
                        height: "100%",
                        background: "var(--accent)",
                      }}
                    />
                  </div>
                </div>
              ))}
          </div>
        )}
      </section>

      {/* clicks_by_surface */}
      <section style={{ marginTop: 40 }}>
        <h2 className="h-card">Clicks by surface</h2>
        {data.total_clicks === 0 ? (
          <div className="mono" style={{ color: "var(--ink-3)", marginTop: 16 }}>
            no clicks yet
          </div>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 16 }}>
            {Object.entries(data.clicks_by_surface).map(([surface, count]) => (
              <div
                key={surface}
                style={{
                  padding: "12px 16px",
                  border: "1px solid var(--line-0)",
                  borderRadius: "var(--r-md)",
                }}
              >
                <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>
                  {surface}
                </div>
                <div className="h-card" style={{ marginTop: 4 }}>{count}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="m-card" style={{ padding: 16 }}>
      <div className="h-display" style={{ fontSize: 28 }}>{value}</div>
      <div className="mono" style={{ color: "var(--ink-2)", fontSize: 11 }}>{label}</div>
    </div>
  );
}
