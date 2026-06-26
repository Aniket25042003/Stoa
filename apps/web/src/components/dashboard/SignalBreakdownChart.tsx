"use client";

import { cn } from "@/lib/cn";
import { formatSignalKindLabel } from "@/lib/user-facing-copy";

const KIND_COLORS = [
  "bg-mkt-ink/80",
  "bg-mkt-ink/65",
  "bg-mkt-ink/50",
  "bg-mkt-ink/35",
  "bg-mkt-ink/25",
];

type SignalBreakdownChartProps = {
  signalsByKind?: Record<string, number>;
  compact?: boolean;
  className?: string;
};

export function SignalBreakdownChart({ signalsByKind, compact = false, className }: SignalBreakdownChartProps) {
  const entries = Object.entries(signalsByKind ?? {})
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);

  const total = entries.reduce((sum, [, count]) => sum + count, 0);

  if (total === 0) {
    return (
      <div className={cn("flex h-full min-h-[120px] flex-col items-center justify-center rounded-sm border border-dashed border-mkt-ink/[0.08] bg-mkt-ink/[0.02] px-4 text-center", className)}>
        <p className={cn("text-mkt-muted", compact ? "text-xs" : "text-sm")}>
          Signal breakdown appears once customer data is ingested.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex h-3 w-full overflow-hidden rounded-sm">
        {entries.map(([kind, count], index) => (
          <div
            key={kind}
            className={cn("h-full transition-all", KIND_COLORS[index % KIND_COLORS.length])}
            style={{ width: `${(count / total) * 100}%` }}
            title={`${formatSignalKindLabel(kind)}: ${count}`}
          />
        ))}
      </div>
      <ul className={cn("space-y-2", compact ? "space-y-1.5" : "space-y-2")}>
        {entries.map(([kind, count], index) => (
          <li key={kind} className="flex items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-2">
              <span className={cn("h-2 w-2 shrink-0 rounded-full", KIND_COLORS[index % KIND_COLORS.length])} />
              <span className={cn("truncate text-mkt-muted", compact ? "text-xs" : "text-sm")}>
                {formatSignalKindLabel(kind)}
              </span>
            </div>
            <span className={cn("shrink-0 font-medium tabular-nums text-mkt-ink", compact ? "text-xs" : "text-sm")}>
              {count}
              <span className="ml-1 text-mkt-subtle">({Math.round((count / total) * 100)}%)</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
