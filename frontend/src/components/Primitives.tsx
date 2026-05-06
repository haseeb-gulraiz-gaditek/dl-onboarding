"use client";

import { useEffect, useRef, useState } from "react";

// =============================================================================
// MButton
// =============================================================================
type ButtonVariant = "primary" | "ghost" | "quiet";
type ButtonSize = "sm" | "md" | "lg";

interface MButtonProps {
  children: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  onClick?: () => void;
  icon?: React.ReactNode;
  trailing?: React.ReactNode;
  type?: "button" | "submit";
  disabled?: boolean;
}

export function MButton({
  children,
  variant = "primary",
  size = "md",
  onClick,
  icon,
  trailing,
  type = "button",
  disabled = false,
}: MButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`m-btn m-btn-${variant} m-btn-${size}`}
    >
      {icon && <span className="m-btn-icon">{icon}</span>}
      <span>{children}</span>
      {trailing && <span className="m-btn-trail">{trailing}</span>}
    </button>
  );
}

// =============================================================================
// MeshMark — animated brand mark
// =============================================================================
export function MeshMark({ size = 28 }: { size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    let raf = 0;
    const t0 = performance.now();
    const loop = (now: number) => {
      const el = ref.current;
      if (!el) return;
      const t = (now - t0) / 1000;
      const dots = el.querySelectorAll("circle");
      dots.forEach((d, i) => {
        const a = 0.55 + Math.sin(t * 1.4 + i * 1.3) * 0.35;
        d.setAttribute("opacity", String(a));
      });
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);
  return (
    <svg
      ref={ref}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      style={{ display: "block" }}
      aria-hidden="true"
    >
      <g stroke="oklch(0.75 0.16 295 / 0.5)" strokeWidth="0.7" fill="none">
        <line x1="8" y1="10" x2="22" y2="8" />
        <line x1="22" y1="8" x2="24" y2="22" />
        <line x1="24" y1="22" x2="10" y2="24" />
        <line x1="10" y1="24" x2="8" y2="10" />
        <line x1="8" y1="10" x2="24" y2="22" />
        <line x1="22" y1="8" x2="10" y2="24" />
      </g>
      <g fill="oklch(0.92 0.08 295)">
        <circle cx="8" cy="10" r="1.6" />
        <circle cx="22" cy="8" r="1.6" />
        <circle cx="24" cy="22" r="1.6" />
        <circle cx="10" cy="24" r="1.6" />
        <circle cx="16" cy="16" r="2.2" />
      </g>
    </svg>
  );
}

// =============================================================================
// Chip
// =============================================================================
interface ChipProps {
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  icon?: React.ReactNode;
  axis?: string;
}

export function Chip({ children, active, onClick, icon, axis }: ChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`m-chip ${active ? "m-chip-active" : ""}`}
      data-axis={axis}
    >
      {icon && <span className="m-chip-icon">{icon}</span>}
      {children}
    </button>
  );
}

// =============================================================================
// Avatar (procedural)
// =============================================================================
export function Avatar({
  seed = "a",
  size = 24,
}: {
  seed?: string;
  size?: number;
}) {
  let h = 0;
  for (let i = 0; i < seed.length; i++)
    h = (h * 31 + seed.charCodeAt(i)) | 0;
  const hue = ((h % 360) + 360) % 360;
  const initials = seed
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: `linear-gradient(135deg, oklch(0.55 0.12 ${hue}), oklch(0.32 0.08 ${(hue + 40) % 360}))`,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "var(--font-mono)",
        fontSize: size * 0.36,
        color: "oklch(0.96 0.01 280)",
        flexShrink: 0,
      }}
    >
      {initials}
    </div>
  );
}

// =============================================================================
// Hooks
// =============================================================================
export function useInView<T extends Element = HTMLElement>(
  opts: IntersectionObserverInit = { threshold: 0.25, rootMargin: "-10% 0px" },
): [React.RefObject<T>, boolean] {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) setInView(true);
    }, opts);
    io.observe(ref.current);
    return () => io.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return [ref, inView];
}

// =============================================================================
// ScrambleText
// =============================================================================
export function ScrambleText({
  text,
  trigger = true,
  speed = 22,
  className = "",
  style = {},
}: {
  text: string;
  trigger?: boolean;
  speed?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const [out, setOut] = useState(text);
  const rafRef = useRef<number | null>(null);
  const startedRef = useRef(false);
  useEffect(() => {
    if (!trigger || startedRef.current) return;
    startedRef.current = true;
    const chars = "·•◦∘⌁⏚▴◇";
    const target = text;
    let frame = 0;
    const total = target.length * speed;
    const tick = () => {
      const buf: string[] = [];
      for (let i = 0; i < target.length; i++) {
        const reveal = i * speed;
        if (frame >= reveal + speed * 0.6) buf.push(target[i]);
        else if (frame >= reveal) {
          if (target[i] === " ") buf.push(" ");
          else buf.push(chars[(frame + i) % chars.length]);
        } else {
          buf.push(target[i] === " " ? " " : "\u00a0");
        }
      }
      setOut(buf.join(""));
      frame++;
      if (frame < total + 4) rafRef.current = requestAnimationFrame(tick);
      else setOut(target);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [trigger, text, speed]);
  return (
    <span className={className} style={style}>
      {out}
    </span>
  );
}

// =============================================================================
// Magnetic (pointer-pulled)
// =============================================================================
export function Magnetic({
  children,
  strength = 18,
  className = "",
  style = {},
}: {
  children: React.ReactNode;
  strength?: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const wrap = el.parentElement;
    if (!wrap) return;
    const onMove = (e: MouseEvent) => {
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const dx = (e.clientX - cx) / r.width;
      const dy = (e.clientY - cy) / r.height;
      el.style.transform = `translate(${dx * strength}px, ${dy * strength}px)`;
    };
    const onLeave = () => {
      el.style.transform = "";
    };
    wrap.addEventListener("mousemove", onMove);
    wrap.addEventListener("mouseleave", onLeave);
    return () => {
      wrap.removeEventListener("mousemove", onMove);
      wrap.removeEventListener("mouseleave", onLeave);
    };
  }, [strength]);
  return (
    <span
      ref={ref}
      className={className}
      style={{
        display: "inline-block",
        transition: "transform 0.4s cubic-bezier(.2,.7,.2,1)",
        ...style,
      }}
    >
      {children}
    </span>
  );
}

// =============================================================================
// useElementProgress
// =============================================================================
export function useElementProgress<T extends Element = HTMLElement>(
  ref: React.RefObject<T | null>,
) {
  const [p, setP] = useState(0);
  useEffect(() => {
    const update = () => {
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const vh = window.innerHeight;
      const total = rect.height + vh;
      const passed = vh - rect.top;
      setP(Math.max(0, Math.min(1, passed / total)));
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, [ref]);
  return p;
}

export function useScrollProgress() {
  const [p, setP] = useState(0);
  useEffect(() => {
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setP(max > 0 ? window.scrollY / max : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return p;
}
