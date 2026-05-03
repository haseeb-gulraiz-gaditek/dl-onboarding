"use client";

import { useEffect, useRef } from "react";

const COMMUNITIES = [
  { id: "solo-founders", name: "r/solo-founders", members: 4803, axis: "role", tags: ["founders", "pm", "productivity"] },
  { id: "staff-pms", name: "r/staff-pms", members: 1127, axis: "role", tags: ["pm", "docs", "meetings"] },
  { id: "growth-marketers", name: "r/growth-marketers", members: 2418, axis: "role", tags: ["sales", "crm", "email"] },
  { id: "eng-leads", name: "r/eng-leads", members: 1832, axis: "role", tags: ["dev", "pm", "ai"] },
  { id: "design-leads", name: "r/design-leads", members: 967, axis: "role", tags: ["design", "pm"] },
  { id: "notion-power", name: "r/notion-power-users", members: 8902, axis: "tool", tags: ["writing", "docs", "pm"] },
  { id: "cursor-builders", name: "r/cursor-builders", members: 3217, axis: "tool", tags: ["dev", "ai"] },
  { id: "claude-projects", name: "r/claude-projects", members: 2664, axis: "tool", tags: ["ai", "writing"] },
  { id: "figma-deep", name: "r/figma-deep", members: 4120, axis: "tool", tags: ["design"] },
  { id: "linear-stans", name: "r/linear-stans", members: 1453, axis: "tool", tags: ["pm", "dev"] },
  { id: "replacing-saas", name: "r/replacing-saas-w-ai", members: 5560, axis: "problem", tags: ["ai", "productivity"] },
  { id: "meeting-notes", name: "r/meeting-notes-fatigue", members: 1734, axis: "problem", tags: ["meetings", "ai"] },
  { id: "email-killers", name: "r/email-time-killers", members: 1089, axis: "problem", tags: ["email"] },
  { id: "context-switch", name: "r/context-switching", members: 2210, axis: "problem", tags: ["productivity", "browser"] },
  { id: "tab-hoarders", name: "r/tab-hoarders", members: 813, axis: "problem", tags: ["browser", "productivity"] },
  { id: "spreadsheet-ppl", name: "r/spreadsheet-people", members: 1518, axis: "problem", tags: ["data", "productivity"] },
];

const AXIS_HUE: Record<string, number> = { role: 285, tool: 250, problem: 320 };

export { COMMUNITIES };

interface Node {
  id: string;
  name: string;
  members: number;
  axis: string;
  tags: string[];
  idx: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  tx: number;
  ty: number;
  seed: number;
  bright: number;
  visible: number;
  sizeBoost: number;
  hue: number;
  dendrites: { angle: number; length: number; wobble: number }[];
}

interface Pulse {
  key: string;
  ax: number;
  ay: number;
  bx: Node;
  t: number;
  speed: number;
  hue: number;
  dir: number;
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}
function clamp(v: number, a: number, b: number) {
  return Math.max(a, Math.min(b, v));
}

export function CommunityGraph({
  tags = [],
  gridSlots = 10,
  scale = 1.2,
}: {
  tags?: string[];
  gridSlots?: number;
  scale?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const pulsesRef = useRef<Pulse[]>([]);
  const stateRef = useRef({ tags, gridSlots, scale });
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    stateRef.current = { tags, gridSlots, scale };
  }, [tags, gridSlots, scale]);

  useEffect(() => {
    nodesRef.current = COMMUNITIES.map((c, i) => ({
      ...c,
      idx: i,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      tx: 0,
      ty: 0,
      seed: Math.random() * 1000,
      bright: 1,
      visible: 1,
      sizeBoost: 0.5,
      hue: AXIS_HUE[c.axis] || 295,
      dendrites: Array.from({ length: 5 + Math.floor(Math.random() * 3) }, (_, k) => ({
        angle: (k / 6) * Math.PI * 2 + Math.random() * 0.6,
        length: 0.7 + Math.random() * 0.6,
        wobble: Math.random() * 6.28,
      })),
    }));
    pulsesRef.current = [];
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let W = 0,
      H = 0;
    const DPR = Math.min(2, window.devicePixelRatio || 1);
    const resize = () => {
      const rect = container.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width = W * DPR;
      canvas.height = H * DPR;
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    let lastT = performance.now();
    const loop = (now: number) => {
      const dt = Math.min(0.05, (now - lastT) / 1000);
      lastT = now;
      const { tags, gridSlots, scale } = stateRef.current;
      const nodes = nodesRef.current;
      const cx = W / 2,
        cy = H / 2,
        t = now / 1000;

      const tagSet = new Set(tags || []);
      const scoreMap = new Map<string, number>();
      nodes.forEach((n) => {
        let s = 0;
        n.tags.forEach((tg) => {
          if (tagSet.has(tg)) s += 1;
        });
        s += (1 / (n.idx + 2)) * 0.01;
        scoreMap.set(n.id, s);
      });
      const N = Math.max(3, gridSlots || 6);
      const sorted = [...nodes].sort(
        (a, b) => (scoreMap.get(b.id) ?? 0) - (scoreMap.get(a.id) ?? 0),
      );
      const primarySet = new Set(sorted.slice(0, N).map((n) => n.id));

      nodes.forEach((n) => {
        const isPrimary = primarySet.has(n.id);
        const rankInScore = sorted.findIndex((o) => o.id === n.id);
        n.bright = lerp(n.bright, isPrimary ? 1 : 0.32, 1 - Math.pow(0.0008, dt));
        if (isPrimary) {
          const innerIdx = sorted.slice(0, N).findIndex((o) => o.id === n.id);
          const a0 = (innerIdx / N) * Math.PI * 2 - Math.PI / 2;
          const wob = Math.sin(t * 0.5 + n.seed) * 0.04;
          const innerR = N <= 5 ? Math.min(W, H) * 0.18 : Math.min(W, H) * 0.22;
          n.tx = cx + Math.cos(a0 + wob) * innerR;
          n.ty = cy + Math.sin(a0 + wob) * innerR * 0.85;
          n.sizeBoost = lerp(n.sizeBoost, N <= 5 ? 1.2 : 1.0, 1 - Math.pow(0.003, dt));
        } else {
          const outerIdx = rankInScore - N;
          const outerN = nodes.length - N;
          const a0 = (outerIdx / outerN) * Math.PI * 2 + (n.seed % 1) * 0.3;
          const wob = Math.sin(t * 0.3 + n.seed) * 0.06;
          const outerR = Math.min(W, H) * 0.46;
          n.tx = cx + Math.cos(a0 + wob) * outerR;
          n.ty = cy + Math.sin(a0 + wob) * outerR * 0.85;
          n.sizeBoost = lerp(n.sizeBoost, 0.32, 1 - Math.pow(0.003, dt));
        }
        const k = 5;
        n.vx += (n.tx - n.x) * k * dt;
        n.vy += (n.ty - n.y) * k * dt;
        n.vx *= Math.pow(0.00002, dt);
        n.vy *= Math.pow(0.00002, dt);
        n.x += n.vx * dt;
        n.y += n.vy * dt;
      });

      ctx.clearRect(0, 0, W, H);

      const conns: { a: { x: number; y: number; hue: number; bright: number }; b: Node }[] = [];
      const primaryNodes = nodes.filter((n) => primarySet.has(n.id));
      primaryNodes.forEach((p) => {
        conns.push({ a: { x: cx, y: cy, hue: 295, bright: 1 }, b: p });
      });

      ctx.lineWidth = 1.1;
      conns.forEach(({ a, b }) => {
        const baseAlpha = Math.min(0.55, 0.4 * b.bright);
        const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
        grad.addColorStop(0, `oklch(0.85 0.14 ${a.hue} / ${baseAlpha + 0.2})`);
        grad.addColorStop(1, `oklch(0.78 0.14 ${b.hue} / ${baseAlpha})`);
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      });

      const pulses = pulsesRef.current;
      conns.forEach(({ a, b }) => {
        const key = `c-${b.idx}`;
        const existing = pulses.filter((p) => p.key === key).length;
        if (existing < 1 && Math.random() < 0.05) {
          pulses.push({
            key,
            ax: a.x,
            ay: a.y,
            bx: b,
            t: 0,
            speed: 0.4 + Math.random() * 0.3,
            hue: b.hue,
            dir: Math.random() < 0.5 ? 1 : -1,
          });
        }
      });
      for (let i = pulses.length - 1; i >= 0; i--) {
        const p = pulses[i];
        p.t += p.speed * dt;
        if (p.t >= 1 || p.bx.bright < 0.4) {
          pulses.splice(i, 1);
          continue;
        }
        const pt = p.dir > 0 ? p.t : 1 - p.t;
        const px = lerp(p.ax, p.bx.x, pt);
        const py = lerp(p.ay, p.bx.y, pt);
        const pg = ctx.createRadialGradient(px, py, 0, px, py, 8);
        pg.addColorStop(0, `oklch(0.95 0.18 ${p.hue} / 0.95)`);
        pg.addColorStop(1, `oklch(0.95 0.18 ${p.hue} / 0)`);
        ctx.fillStyle = pg;
        ctx.beginPath();
        ctx.arc(px, py, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `oklch(0.98 0.04 ${p.hue} / 0.95)`;
        ctx.beginPath();
        ctx.arc(px, py, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }

      const centerR = 28 * scale;
      const centerHalo = ctx.createRadialGradient(cx, cy, 0, cx, cy, centerR * 3);
      centerHalo.addColorStop(0, `oklch(0.78 0.18 295 / 0.5)`);
      centerHalo.addColorStop(1, `oklch(0.78 0.18 295 / 0)`);
      ctx.fillStyle = centerHalo;
      ctx.beginPath();
      ctx.arc(cx, cy, centerR * 3, 0, Math.PI * 2);
      ctx.fill();

      const cg = ctx.createRadialGradient(
        cx - centerR * 0.3,
        cy - centerR * 0.3,
        0,
        cx,
        cy,
        centerR,
      );
      cg.addColorStop(0, `oklch(0.95 0.10 295 / 1)`);
      cg.addColorStop(1, `oklch(0.45 0.16 295 / 1)`);
      ctx.fillStyle = cg;
      ctx.beginPath();
      ctx.arc(cx, cy, centerR, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = `oklch(0.85 0.14 295 / 0.5)`;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = "oklch(0.98 0.01 280 / 1)";
      ctx.font = '500 11px "Geist Mono", ui-monospace, monospace';
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("your product", cx, cy);

      const nodeScale = scale;
      nodes.forEach((n) => {
        if (n.visible < 0.02) return;
        const op = clamp(n.visible, 0, 1);
        const br = clamp(n.bright, 0, 1);
        const sb = clamp(n.sizeBoost, 0.3, 1.3);
        const somaR = (10 + sb * 9) * nodeScale;

        ctx.lineCap = "round";
        n.dendrites.forEach((d) => {
          const wob = Math.sin(t * 0.8 + d.wobble) * 0.12;
          const ang = d.angle + wob;
          const len = somaR * (1.4 + d.length * 1.1);
          const ex = n.x + Math.cos(ang) * len;
          const ey = n.y + Math.sin(ang) * len;
          const dg = ctx.createLinearGradient(n.x, n.y, ex, ey);
          dg.addColorStop(0, `oklch(0.78 0.14 ${n.hue} / ${0.45 * br * op})`);
          dg.addColorStop(1, `oklch(0.78 0.14 ${n.hue} / 0)`);
          ctx.strokeStyle = dg;
          ctx.lineWidth = 1.2 * (0.6 + sb * 0.4);
          ctx.beginPath();
          ctx.moveTo(n.x + Math.cos(ang) * somaR * 0.85, n.y + Math.sin(ang) * somaR * 0.85);
          ctx.lineTo(ex, ey);
          ctx.stroke();
        });

        const haloR = somaR * 3.0;
        const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, haloR);
        grad.addColorStop(0, `oklch(0.78 0.18 ${n.hue} / ${0.4 * br * op})`);
        grad.addColorStop(1, `oklch(0.78 0.18 ${n.hue} / 0)`);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(n.x, n.y, haloR, 0, Math.PI * 2);
        ctx.fill();

        const somaG = ctx.createRadialGradient(
          n.x - somaR * 0.3,
          n.y - somaR * 0.3,
          0,
          n.x,
          n.y,
          somaR,
        );
        somaG.addColorStop(0, `oklch(0.92 0.12 ${n.hue} / ${op})`);
        somaG.addColorStop(0.6, `oklch(${0.7 + br * 0.1} 0.16 ${n.hue} / ${op})`);
        somaG.addColorStop(1, `oklch(${0.4 + br * 0.15} 0.12 ${n.hue} / ${op})`);
        ctx.fillStyle = somaG;
        ctx.beginPath();
        ctx.arc(n.x, n.y, somaR, 0, Math.PI * 2);
        ctx.fill();

        if (br > 0.7 && sb > 0.7) {
          ctx.font = `${Math.round(11 * nodeScale)}px "Geist Mono", ui-monospace, monospace`;
          ctx.fillStyle = `oklch(0.95 0.01 280 / ${op * 0.95})`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillText(n.name, n.x, n.y + somaR * 1.6);
          ctx.font = `${Math.round(9 * nodeScale)}px "Geist Mono", ui-monospace, monospace`;
          ctx.fillStyle = `oklch(0.7 0.01 280 / ${op * 0.7})`;
          ctx.fillText(`${(n.members / 1000).toFixed(1)}k`, n.x, n.y + somaR * 1.6 + 14);
        }
      });

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      ro.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <canvas ref={canvasRef} style={{ display: "block" }} />
    </div>
  );
}
