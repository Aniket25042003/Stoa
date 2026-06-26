"use client";

import { cn } from "@/lib/cn";

type ReadinessGaugeProps = {
  percent: number;
  size?: "sm" | "md" | "lg";
  label?: string;
  variant?: "light" | "dark";
  className?: string;
};

const SIZES = {
  sm: { dim: 72, stroke: 6, font: "text-lg" },
  md: { dim: 112, stroke: 8, font: "text-2xl" },
  lg: { dim: 140, stroke: 10, font: "text-3xl" },
};

export function ReadinessGauge({
  percent,
  size = "md",
  label,
  variant = "light",
  className,
}: ReadinessGaugeProps) {
  const clamped = Math.min(100, Math.max(0, percent));
  const { dim, stroke, font } = SIZES[size];
  const radius = (dim - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  const center = dim / 2;
  const dark = variant === "dark";

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <div className="relative" style={{ width: dim, height: dim }}>
        <svg width={dim} height={dim} className="-rotate-90" aria-hidden>
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className={dark ? "text-mkt-dark-ink/20" : "text-mkt-ink/[0.08]"}
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={cn(
              "transition-[stroke-dashoffset] duration-700 ease-out",
              dark ? "text-mkt-dark-ink" : "text-mkt-accent",
            )}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={cn(
              "font-semibold tabular-nums tracking-tight",
              dark ? "text-mkt-dark-ink" : "text-mkt-ink",
              font,
            )}
          >
            {clamped}%
          </span>
        </div>
      </div>
      {label ? (
        <p
          className={cn(
            "text-center text-[10px] font-medium uppercase tracking-wider",
            dark ? "text-mkt-subtle" : "text-mkt-subtle",
          )}
        >
          {label}
        </p>
      ) : null}
    </div>
  );
}
