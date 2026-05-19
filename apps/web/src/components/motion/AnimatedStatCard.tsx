"use client";

import { cn } from "@/lib/cn";
import { AnimatedNumber } from "./AnimatedNumber";
import { ProgressRing } from "./ProgressRing";

export function AnimatedStatCard({
  label,
  loading,
  variant = "number",
  value,
  className,
}: {
  label: string;
  loading?: boolean;
  variant?: "number" | "percent";
  /** For number: count. For percent: 0–1 */
  value?: number;
  className?: string;
}) {
  return (
    <div className={cn("rounded-3xl p-7 card-glass", loading && "animate-pulse", className)}>
      {loading ? (
        <>
          <div className="h-8 w-16 rounded-lg bg-surface-container-high" />
          <p className="mt-3 h-4 w-24 rounded bg-surface-container-high" />
        </>
      ) : variant === "percent" && value !== undefined ? (
        <div className="flex items-center gap-4">
          <ProgressRing value={value} size={52} stroke={4} />
          <div>
            <p className="font-display text-xl font-bold text-on-surface">{label}</p>
            <p className="mt-1 text-xs text-on-surface-variant">Completion</p>
          </div>
        </div>
      ) : (
        <>
          <p className="font-display text-4xl font-extrabold tracking-[-0.05em] gradient-text">
            {value !== undefined ? <AnimatedNumber value={value} /> : "--"}
          </p>
          <p className="mt-2 text-sm text-on-surface-variant">{label}</p>
        </>
      )}
    </div>
  );
}
