"use client";

import { BarChart3, Bell, FileText, Megaphone, Radio, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { METRIC_DEFINITIONS, type WorkspaceCounts } from "@/components/dashboard/types";
import { cn } from "@/lib/cn";

const ICONS: Record<string, LucideIcon> = {
  signals: Radio,
  documents: FileText,
  competitors: Users,
  alerts: Bell,
  campaigns: Megaphone,
};

type MetricsBarChartProps = {
  counts?: WorkspaceCounts;
  compact?: boolean;
  className?: string;
};

export function MetricsBarChart({ counts, compact = false, className }: MetricsBarChartProps) {
  const rows = METRIC_DEFINITIONS.map((def) => ({
    ...def,
    value: counts?.[def.key] ?? 0,
    Icon: ICONS[def.key] ?? BarChart3,
  }));
  const max = Math.max(...rows.map((r) => r.value), 1);

  return (
    <div className={cn("space-y-3", className)}>
      {rows.map((row) => {
        const width = Math.max((row.value / max) * 100, row.value > 0 ? 8 : 0);
        return (
          <div key={row.key} className="group">
            <div className="mb-1 flex items-center justify-between gap-2">
              <div className="flex min-w-0 items-center gap-2">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-sm bg-mkt-ink/[0.04] text-mkt-muted group-hover:bg-mkt-accent/[0.08] group-hover:text-mkt-accent">
                  <row.Icon className="h-3.5 w-3.5" />
                </span>
                <span className={cn("truncate text-mkt-muted", compact ? "text-xs" : "text-sm")}>
                  {compact ? row.shortLabel : row.label}
                </span>
              </div>
              <span className={cn("shrink-0 font-semibold tabular-nums text-mkt-ink", compact ? "text-sm" : "text-base")}>
                {row.value}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-sm bg-mkt-ink/[0.05]">
              <div
                className="h-full rounded-sm bg-gradient-to-r from-mkt-ink/70 to-mkt-ink transition-all duration-500 ease-out"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
