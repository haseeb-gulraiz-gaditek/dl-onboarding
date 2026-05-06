"use client";

// Mesh — /tools shared layout (tab strip + bell).
// Per spec-delta frontend-secondary F-FE2-5.

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MeshMark } from "@/components/Primitives";
import { HeaderBell } from "@/components/HeaderBell";

const TABS = [
  { href: "/tools/mine", label: "Mine" },
  { href: "/tools/explore", label: "Explore" },
  { href: "/tools/new", label: "New" },
];

export default function ToolsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div style={{ minHeight: "100vh" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "20px max(24px, 5vw)",
          borderBottom: "1px solid var(--line-0)",
        }}
      >
        <Link href="/home" className="onb-brand">
          <MeshMark size={20} />
          <span>Mesh</span>
        </Link>
        <nav style={{ display: "flex", gap: 4 }}>
          {TABS.map((t) => {
            const active = pathname === t.href;
            return (
              <Link
                key={t.href}
                href={t.href}
                className="mono"
                style={{
                  padding: "8px 18px",
                  borderRadius: "var(--r-pill)",
                  fontSize: 13,
                  background: active ? "var(--accent-soft)" : "transparent",
                  border: active ? "1px solid var(--accent)" : "1px solid var(--line-0)",
                  color: active ? "var(--ink-0)" : "var(--ink-2)",
                  textDecoration: "none",
                }}
              >
                {t.label}
              </Link>
            );
          })}
        </nav>
        <HeaderBell />
      </header>
      <main style={{ padding: "32px max(24px, 5vw)", maxWidth: 1080, margin: "0 auto" }}>
        {children}
      </main>
    </div>
  );
}
