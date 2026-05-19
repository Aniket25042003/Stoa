"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/cn";

export function ProgressRing({
  value,
  size = 56,
  stroke = 5,
  className,
  labelClassName,
}: {
  /** 0–1 */
  value: number;
  size?: number;
  stroke?: number;
  className?: string;
  labelClassName?: string;
}) {
  const reduced = useReducedMotion();
  const [animated, setAnimated] = useState(reduced ? value : 0);
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(1, animated));
  const offset = c * (1 - clamped);

  useEffect(() => {
    if (reduced) {
      setAnimated(value);
      return;
    }
    const start = performance.now();
    const from = 0;
    let frame = 0;
    const duration = 800;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      setAnimated(from + (value - from) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, reduced]);

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-outline-variant/40"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="text-primary"
        />
      </svg>
      <span
        className={cn(
          "absolute font-display text-sm font-bold tabular-nums text-on-surface",
          labelClassName
        )}
      >
        {Math.round(clamped * 100)}%
      </span>
    </div>
  );
}
