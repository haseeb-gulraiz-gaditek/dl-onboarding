"use client";

// Mesh — persistent tool graph (canvas, multi-mode)
// Modes:
//   'hero'   — large central drifting cloud
//   'narrow' — drifting cloud, smaller
//   'grid'   — settles into N grid slots (used in onboarding result)
//   'flow'   — nodes anchor to per-section targets (DOM data-anchor-id)
//   'score'  — radial layout by tag-overlap score (used in profile graph)

import { useEffect, useRef } from "react";

// ============================================================
// DATA
// ============================================================
export interface MeshTool {
  id: string;
  name: string;
  tags: string[];
}

export const MESH_TOOLS: MeshTool[] = [
  { id: "notion", name: "Notion", tags: ["writing", "docs", "pm"] },
  { id: "linear", name: "Linear", tags: ["pm", "dev"] },
  { id: "cursor", name: "Cursor", tags: ["dev", "ai"] },
  { id: "claude", name: "Claude", tags: ["ai", "writing"] },
  { id: "gpt", name: "ChatGPT", tags: ["ai", "writing"] },
  { id: "perplex", name: "Perplexity", tags: ["ai", "research"] },
  { id: "figma", name: "Figma", tags: ["design"] },
  { id: "arc", name: "Arc", tags: ["browser"] },
  { id: "raycast", name: "Raycast", tags: ["productivity", "dev"] },
  { id: "superhuman", name: "Superhuman", tags: ["email"] },
  { id: "attio", name: "Attio", tags: ["crm", "sales"] },
  { id: "granola", name: "Granola", tags: ["ai", "meetings"] },
  { id: "reflect", name: "Reflect", tags: ["notes", "writing"] },
  { id: "framer", name: "Framer", tags: ["design", "web"] },
  { id: "v0", name: "v0", tags: ["ai", "dev"] },
  { id: "mem", name: "Mem", tags: ["notes", "ai"] },
];

// ============================================================
// HELPERS
// ============================================================
function hueFor(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
  return 240 + ((Math.abs(h) % 90) - 30); // 210..330
}
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp = (v: number, a: number, b: number) =>
  Math.max(a, Math.min(b, v));

// ============================================================
// TYPES
// ============================================================
type Dendrite = { angle: number; length: number; wobble: number };

interface GraphNode extends MeshTool {
  idx: number;
  x: number; y: number;
  vx: number; vy: number;
  tx: number; ty: number;
  seed: number;
  bright: number;
  visible: number;
  sizeBoost: number;
  hue: number;
  dendrites: Dendrite[];
}

interface Pulse {
  key: string;
  a: GraphNode;
  b: GraphNode;
  t: number;
  speed: number;
  hue: number;
}

interface ToolGraphProps {
  progress?: number;
  highlightedTags?: string[];
  mode?: "hero" | "narrow" | "grid" | "flow" | "score";
  gridSlots?: number;
  scale?: number;
  /** When set, the graph renders these tools instead of MESH_TOOLS.
   *  Reactively reconciled — tools added → fade in; removed → fade out
   *  and pruned. Used by the live-narrowing onboarding flow to show
   *  real catalog tools shrinking 40 → 20 → 15 → 10 → 6. */
  tools?: MeshTool[];
}

// ============================================================
// COMPONENT
// ============================================================
function makeNode(t: MeshTool, idx: number, spawnX = 0, spawnY = 0): GraphNode {
  return {
    ...t,
    idx,
    x: spawnX, y: spawnY, vx: 0, vy: 0, tx: spawnX, ty: spawnY,
    seed: Math.random() * 1000,
    bright: 0,        // start dim, fade in
    visible: 0,       // start invisible, fade in
    sizeBoost: 0,
    hue: hueFor(t.id),
    dendrites: Array.from(
      { length: 5 + Math.floor(Math.random() * 3) },
      (_, k) => ({
        angle: (k / 6) * Math.PI * 2 + Math.random() * 0.6,
        length: 0.7 + Math.random() * 0.6,
        wobble: Math.random() * 6.28,
      }),
    ),
  };
}

export function ToolGraph({
  progress = 0,
  highlightedTags = [],
  mode = "hero",
  gridSlots = 0,
  scale = 1,
  tools,
}: ToolGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodesRef = useRef<GraphNode[]>([]);
  const activeIdsRef = useRef<Set<string>>(new Set());
  const pulsesRef = useRef<Pulse[]>([]);
  const mouseRef = useRef({ x: -9999, y: -9999, active: false });
  const stateRef = useRef({ progress, highlightedTags, mode, gridSlots, scale });
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    stateRef.current = { progress, highlightedTags, mode, gridSlots, scale };
  }, [progress, highlightedTags, mode, gridSlots, scale]);

  // Initial seed: if `tools` prop is provided, use it; otherwise the
  // built-in MESH_TOOLS demo set (preserves the classic landing/onboarding
  // visual for callers that don't pass real data).
  useEffect(() => {
    const seed = (tools && tools.length > 0) ? tools : MESH_TOOLS;
    nodesRef.current = seed.map((t, i) => {
      const n = makeNode(t, i);
      n.bright = 1; n.visible = 1; // initial render fully visible
      return n;
    });
    activeIdsRef.current = new Set(seed.map((t) => t.id));
    pulsesRef.current = [];
    // Run only once on mount; further updates handled by the reconcile
    // effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reconcile when `tools` prop changes. Existing nodes whose id is
  // still in the new set keep their position/state. New ids get a
  // freshly-spawned node (fades in). Removed ids stay in nodesRef but
  // their target visibility goes to 0 (fades out, draw loop skips
  // when visible<0.02).
  useEffect(() => {
    if (!tools) return;  // demo mode — no reconciliation
    const newIds = new Set(tools.map((t) => t.id));
    const existingById = new Map(nodesRef.current.map((n) => [n.id, n]));

    // Update tags/name on existing nodes (props can change tags).
    tools.forEach((t) => {
      const n = existingById.get(t.id);
      if (n) {
        n.tags = t.tags;
        n.name = t.name;
      }
    });

    // Add nodes for new ids.
    let nextIdx = nodesRef.current.length;
    tools.forEach((t) => {
      if (!existingById.has(t.id)) {
        // Spawn near the center with slight random offset.
        const spawnX = 0.5 * (canvasRef.current?.clientWidth || 600)
          + (Math.random() - 0.5) * 80;
        const spawnY = 0.5 * (canvasRef.current?.clientHeight || 400)
          + (Math.random() - 0.5) * 80;
        const node = makeNode(t, nextIdx++, spawnX, spawnY);
        nodesRef.current.push(node);
      }
    });

    activeIdsRef.current = newIds;
  }, [tools]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let W = 0, H = 0;
    const DPR = Math.min(2, window.devicePixelRatio || 1);
    const resize = () => {
      const rect = container.getBoundingClientRect();
      W = rect.width; H = rect.height;
      canvas.width = W * DPR; canvas.height = H * DPR;
      canvas.style.width = W + "px"; canvas.style.height = H + "px";
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current.x = e.clientX - rect.left;
      mouseRef.current.y = e.clientY - rect.top;
      mouseRef.current.active = true;
    };
    const onLeave = () => {
      mouseRef.current.active = false;
      mouseRef.current.x = -9999;
    };
    canvas.addEventListener("mousemove", onMove);
    canvas.addEventListener("mouseleave", onLeave);

    let lastT = performance.now();
    const loop = (now: number) => {
      const dt = Math.min(0.05, (now - lastT) / 1000);
      lastT = now;
      const { highlightedTags, mode, gridSlots, scale } = stateRef.current;
      const nodes = nodesRef.current;
      const canvasRect = canvas.getBoundingClientRect();

      const target = mode === "grid" ? Math.max(4, gridSlots || 5) : nodes.length;
      const cx = W / 2, cy = H / 2, t = now / 1000;
      const activeIds = activeIdsRef.current;
      // When `tools` prop is in use, we drive visibility from membership
      // in activeIds; otherwise (demo mode) all nodes are active.
      const usingActiveSet = activeIds.size > 0;

      const matchedSet = new Set<string>();
      if (highlightedTags.length) {
        nodes.forEach((n) => {
          if (n.tags.some((tg) => highlightedTags.includes(tg))) matchedSet.add(n.id);
        });
      }

      let scoreMap: Map<string, number> | null = null;
      let primarySet: Set<string> | null = null;
      if (mode === "score") {
        const tagSet = new Set(highlightedTags);
        scoreMap = new Map();
        nodes.forEach((n) => {
          let s = 0;
          n.tags.forEach((tg) => { if (tagSet.has(tg)) s += 1; });
          s += (1 / (n.idx + 2)) * 0.01;
          // When the caller supplies an explicit `tools` set
          // (live-onboarding flow), heavily reward those nodes so
          // primarySet is exactly them — no tag-overlap shenanigans.
          if (usingActiveSet && activeIds.has(n.id)) s += 1000;
          scoreMap!.set(n.id, s);
        });
        const N = Math.max(4, gridSlots || 10);
        const sorted = [...nodes].sort(
          (a, b) => scoreMap!.get(b.id)! - scoreMap!.get(a.id)!,
        );
        primarySet = new Set(sorted.slice(0, N).map((n) => n.id));
      }

      // Anchors (flow mode)
      const anchors: { id: string; x: number; y: number; tags: string[] }[] = [];
      if (mode === "flow") {
        document.querySelectorAll<HTMLElement>("[data-anchor-id]").forEach((el) => {
          const r = el.getBoundingClientRect();
          const ax = r.left - canvasRect.left + r.width / 2;
          const ay = r.top - canvasRect.top + r.height / 2;
          if (r.bottom > -300 && r.top < window.innerHeight + 300) {
            anchors.push({
              id: el.dataset.anchorId || "",
              x: ax, y: ay,
              tags: (el.dataset.anchorTags || "").split(",").filter(Boolean),
            });
          }
        });
      }

      const order = [...nodes].sort((a, b) => {
        const am = matchedSet.has(a.id) ? 0 : 1;
        const bm = matchedSet.has(b.id) ? 0 : 1;
        if (am !== bm) return am - bm;
        return a.idx - b.idx;
      });

      order.forEach((n, rank) => {
        const inPool = rank < target;
        const isMatch = matchedSet.has(n.id);

        // Visibility target: when driven by `tools` prop, respect the
        // active set. Removed ids fade out; new ids fade in. In demo
        // mode, fall back to grid-pool gating.
        const inActiveSet = usingActiveSet ? activeIds.has(n.id) : true;
        const visTarget = !inActiveSet
          ? 0
          : mode === "grid" && !inPool
            ? 0
            : 1;
        n.visible = lerp(n.visible, visTarget, 1 - Math.pow(0.001, dt));

        let brightTarget: number;
        if (mode === "score" && scoreMap && primarySet) {
          brightTarget = primarySet.has(n.id) ? 1 : 0.32;
        } else {
          brightTarget =
            visTarget === 0
              ? 0.05
              : highlightedTags.length === 0 || isMatch
                ? 1
                : 0.55;
        }
        n.bright = lerp(n.bright, brightTarget, 1 - Math.pow(0.0008, dt));

        if (mode === "score" && scoreMap && primarySet) {
          const totalN = nodes.length;
          const sorted = [...nodes].sort(
            (a, b) => scoreMap!.get(b.id)! - scoreMap!.get(a.id)!,
          );
          const rankInScore = sorted.findIndex((o) => o.id === n.id);
          const isPrimary = primarySet.has(n.id);
          const N = primarySet.size;

          if (isPrimary) {
            const innerIdx = sorted.slice(0, N).findIndex((o) => o.id === n.id);
            const a0 = (innerIdx / N) * Math.PI * 2 - Math.PI / 2;
            const wob = Math.sin(t * 0.5 + n.seed) * 0.04;
            const innerR =
              N <= 5 ? Math.min(W, H) * 0.18 : Math.min(W, H) * 0.22;
            n.tx = cx + Math.cos(a0 + wob) * innerR;
            n.ty = cy + Math.sin(a0 + wob) * innerR * 0.85;
            n.sizeBoost = lerp(
              n.sizeBoost,
              N <= 5 ? 1.2 : 1.0,
              1 - Math.pow(0.003, dt),
            );
          } else {
            const outerIdx = rankInScore - N;
            const outerN = totalN - N;
            const a0 =
              (outerIdx / outerN) * Math.PI * 2 + (n.seed % 1) * 0.3;
            const wob = Math.sin(t * 0.3 + n.seed) * 0.06;
            const outerR = Math.min(W, H) * 0.46;
            n.tx = cx + Math.cos(a0 + wob) * outerR;
            n.ty = cy + Math.sin(a0 + wob) * outerR * 0.85;
            n.sizeBoost = lerp(n.sizeBoost, 0.32, 1 - Math.pow(0.003, dt));
          }
        } else if (mode === "grid" && inPool) {
          const cols = Math.min(target, 5);
          const rows = Math.ceil(target / cols);
          const col = rank % cols;
          const row = Math.floor(rank / cols);
          n.tx = (col + 0.5) * (W / cols);
          n.ty = (row + 0.5) * (H / rows);
        } else if (mode === "flow" && anchors.length) {
          const matching = anchors.filter(
            (a) =>
              a.tags.length === 0 || a.tags.some((tg) => n.tags.includes(tg)),
          );
          const pool = matching.length ? matching : anchors;
          const chosen = pool[n.idx % pool.length];

          const sameAnchorIdx = nodes
            .filter((o) => {
              const m = anchors.filter(
                (a) =>
                  a.tags.length === 0 ||
                  a.tags.some((tg) => o.tags.includes(tg)),
              );
              const p = m.length ? m : anchors;
              return p[o.idx % p.length].id === chosen.id;
            })
            .indexOf(n);

          const ringSize = 6;
          const ring = Math.floor(sameAnchorIdx / ringSize);
          const slot = sameAnchorIdx % ringSize;
          const ringR = 38 + ring * 28;
          const ringAng = (slot / ringSize) * Math.PI * 2 + ring * 0.4;
          n.tx = chosen.x + Math.cos(ringAng) * ringR;
          n.ty = chosen.y + Math.sin(ringAng) * ringR * 0.78;

          n.sizeBoost = lerp(
            n.sizeBoost,
            ring === 0 ? 1 : 0.5 - ring * 0.15,
            1 - Math.pow(0.005, dt),
          );
        } else {
          const angle =
            n.seed * 6.28 +
            t *
              (0.04 + (n.idx % 5) * 0.012) *
              (mode === "narrow" ? 0.4 : 0.7);
          const radiusBase = mode === "narrow" ? 0.22 : 0.4;
          const radJitter =
            (Math.sin(t * 0.6 + n.seed) * 0.5 + 0.5) * 0.18;
          const rad =
            (radiusBase + radJitter * 0.4) *
            Math.min(W, H) *
            (1 + (rank / nodes.length) * 0.25);
          n.tx = cx + Math.cos(angle) * rad;
          n.ty = cy + Math.sin(angle) * rad * 0.78;
          n.sizeBoost = lerp(n.sizeBoost, 0.6, 1 - Math.pow(0.005, dt));
        }

        if (mouseRef.current.active && mode !== "flow") {
          const dx = n.x - mouseRef.current.x;
          const dy = n.y - mouseRef.current.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 22000) {
            const force = (22000 - d2) / 22000;
            n.tx += dx * force * 0.3;
            n.ty += dy * force * 0.3;
          }
        }

        const k =
          mode === "grid"
            ? 8
            : mode === "flow"
              ? 9
              : mode === "score"
                ? 5
                : 2.4;
        const damp =
          mode === "flow" || mode === "grid" || mode === "score"
            ? 0.00002
            : 0.0006;
        n.vx += (n.tx - n.x) * k * dt;
        n.vy += (n.ty - n.y) * k * dt;
        n.vx *= Math.pow(damp, dt);
        n.vy *= Math.pow(damp, dt);
        n.x += n.vx * dt;
        n.y += n.vy * dt;
      });

      // ============= DRAW =============
      ctx.clearRect(0, 0, W, H);

      const conns: { a: GraphNode; b: GraphNode; d: number; maxD: number }[] = [];
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        if (a.bright < 0.2) continue;
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          if (b.bright < 0.2) continue;
          if (!a.tags.some((tg) => b.tags.includes(tg))) continue;
          const dx = a.x - b.x, dy = a.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          const maxD = Math.max(W, H) * 0.85;
          if (d < maxD) conns.push({ a, b, d, maxD });
        }
      }

      // 1. CONNECTION LINES
      ctx.lineWidth = 1.1;
      conns.forEach(({ a, b, d, maxD }) => {
        const baseAlpha = (1 - d / maxD) * 0.5 * Math.min(a.bright, b.bright);
        const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
        grad.addColorStop(0, `oklch(0.78 0.14 ${a.hue} / ${baseAlpha})`);
        grad.addColorStop(1, `oklch(0.78 0.14 ${b.hue} / ${baseAlpha})`);
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      });

      // 2. PULSE PARTICLES
      const pulses = pulsesRef.current;
      conns.forEach(({ a, b }) => {
        const key = a.idx < b.idx ? `${a.idx}-${b.idx}` : `${b.idx}-${a.idx}`;
        const existing = pulses.filter((p) => p.key === key).length;
        if (existing < 2 && Math.random() < 0.04) {
          pulses.push({
            key, a, b, t: 0,
            speed: 0.35 + Math.random() * 0.4,
            hue: Math.random() < 0.5 ? a.hue : b.hue,
          });
        }
      });
      for (let i = pulses.length - 1; i >= 0; i--) {
        const p = pulses[i];
        p.t += p.speed * dt;
        if (p.t >= 1 || p.a.bright < 0.2 || p.b.bright < 0.2) {
          pulses.splice(i, 1);
          continue;
        }
        const px = lerp(p.a.x, p.b.x, p.t);
        const py = lerp(p.a.y, p.b.y, p.t);
        const pg = ctx.createRadialGradient(px, py, 0, px, py, 8);
        pg.addColorStop(0, `oklch(0.92 0.18 ${p.hue} / 0.95)`);
        pg.addColorStop(1, `oklch(0.92 0.18 ${p.hue} / 0)`);
        ctx.fillStyle = pg;
        ctx.beginPath();
        ctx.arc(px, py, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `oklch(0.98 0.04 ${p.hue} / 0.95)`;
        ctx.beginPath();
        ctx.arc(px, py, 1.6, 0, Math.PI * 2);
        ctx.fill();
      }

      // 3. NEURONS
      const nodeScale = scale;
      nodes.forEach((n) => {
        if (n.visible < 0.02) return;
        const op = clamp(n.visible, 0, 1);
        const br = clamp(n.bright, 0, 1);
        const sb = clamp(n.sizeBoost, 0.3, 1.2);
        const somaR = (10 + sb * 10) * nodeScale;

        ctx.lineCap = "round";
        n.dendrites.forEach((d) => {
          const wob = Math.sin(t * 0.8 + d.wobble) * 0.12;
          const ang = d.angle + wob;
          const len = somaR * (1.6 + d.length * 1.2);
          const ex = n.x + Math.cos(ang) * len;
          const ey = n.y + Math.sin(ang) * len;
          const dg = ctx.createLinearGradient(n.x, n.y, ex, ey);
          dg.addColorStop(0, `oklch(0.78 0.14 ${n.hue} / ${0.5 * br * op})`);
          dg.addColorStop(1, `oklch(0.78 0.14 ${n.hue} / 0)`);
          ctx.strokeStyle = dg;
          ctx.lineWidth = 1.4 * (0.6 + sb * 0.5);
          ctx.beginPath();
          ctx.moveTo(
            n.x + Math.cos(ang) * somaR * 0.85,
            n.y + Math.sin(ang) * somaR * 0.85,
          );
          const midAng = ang + Math.PI / 2;
          const curveAmt =
            Math.sin(t * 0.6 + d.wobble * 1.3) * len * 0.08;
          const mx = (n.x + ex) / 2 + Math.cos(midAng) * curveAmt;
          const my = (n.y + ey) / 2 + Math.sin(midAng) * curveAmt;
          ctx.quadraticCurveTo(mx, my, ex, ey);
          ctx.stroke();
        });

        const haloR = somaR * 3.2;
        const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, haloR);
        grad.addColorStop(0, `oklch(0.78 0.18 ${n.hue} / ${0.4 * br * op})`);
        grad.addColorStop(0.5, `oklch(0.78 0.18 ${n.hue} / ${0.12 * br * op})`);
        grad.addColorStop(1, `oklch(0.78 0.18 ${n.hue} / 0)`);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(n.x, n.y, haloR, 0, Math.PI * 2);
        ctx.fill();

        const somaG = ctx.createRadialGradient(
          n.x - somaR * 0.3, n.y - somaR * 0.3, 0,
          n.x, n.y, somaR,
        );
        somaG.addColorStop(0, `oklch(0.92 0.12 ${n.hue} / ${op})`);
        somaG.addColorStop(0.6, `oklch(${0.7 + br * 0.1} 0.16 ${n.hue} / ${op})`);
        somaG.addColorStop(1, `oklch(${0.4 + br * 0.15} 0.12 ${n.hue} / ${op})`);
        ctx.fillStyle = somaG;
        ctx.beginPath();
        ctx.arc(n.x, n.y, somaR, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = `oklch(0.98 0.04 ${n.hue} / ${op * (0.5 + br * 0.5)})`;
        ctx.beginPath();
        ctx.arc(n.x - somaR * 0.2, n.y - somaR * 0.2, somaR * 0.32, 0, Math.PI * 2);
        ctx.fill();

        if (op > 0.3 && sb > 0.7) {
          const labelSize = Math.round(11 * nodeScale);
          ctx.font = `${labelSize}px "Geist Mono", ui-monospace, monospace`;
          ctx.fillStyle =
            br > 0.7
              ? `oklch(0.95 0.01 280 / ${op * 0.9})`
              : `oklch(0.7 0.01 280 / ${op * 0.55})`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillText(n.name.toLowerCase(), n.x, n.y + somaR * 2.6);
        }
      });

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      canvas.removeEventListener("mousemove", onMove);
      canvas.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
    >
      <canvas
        ref={canvasRef}
        style={{ display: "block", pointerEvents: "auto" }}
      />
    </div>
  );
}
