"use client";

import { Database, Layers, Sparkles } from "lucide-react";
import type { WorkspaceCounts } from "@/components/dashboard/types";
import { cn } from "@/lib/cn";

type MemoryLayersDiagramProps = {
  counts?: WorkspaceCounts;
  icpVersion?: number | null;
  compact?: boolean;
  className?: string;
};

const LAYERS = [
  {
    id: "kb",
    label: "Knowledge base",
    sublabel: "Uploaded files and sources",
    icon: Database,
    getValue: (counts?: WorkspaceCounts) => counts?.documents ?? 0,
    unit: "items",
  },
  {
    id: "signals",
    label: "Extracted signals",
    sublabel: "Pain, objections, triggers",
    icon: Layers,
    getValue: (counts?: WorkspaceCounts) => counts?.signals ?? 0,
    unit: "signals",
  },
  {
    id: "icp",
    label: "ICP profile",
    sublabel: "Synthesized intelligence",
    icon: Sparkles,
    getValue: (_counts?: WorkspaceCounts, icpVersion?: number | null) =>
      icpVersion != null ? icpVersion : 0,
    unit: "version",
    format: (v: number, icpVersion?: number | null) =>
      icpVersion != null ? `v${icpVersion}` : "—",
  },
];

export function MemoryLayersDiagram({
  counts,
  icpVersion,
  compact = false,
  className,
}: MemoryLayersDiagramProps) {
  const numericValues = LAYERS.map((layer) => {
    const raw = layer.getValue(counts, icpVersion);
    return layer.id === "icp" ? (icpVersion != null ? 1 : 0) : raw;
  });
  const max = Math.max(...numericValues, 1);

  return (
    <div className={cn("relative", className)}>
      <div className="absolute left-4 top-6 bottom-6 w-px bg-mkt-ink/[0.08]" aria-hidden />
      <ul className="space-y-3">
        {LAYERS.map((layer, index) => {
          const raw = layer.getValue(counts, icpVersion);
          const display =
            layer.format?.(raw, icpVersion) ??
            `${raw} ${layer.unit}`;
          const depth = layer.id === "icp" ? (icpVersion != null ? 100 : 12) : Math.max((raw / max) * 100, raw > 0 ? 20 : 12);
          const Icon = layer.icon;

          return (
            <li key={layer.id} className="relative pl-10">
              <span
                className="absolute left-2.5 top-4 h-3 w-3 rounded-full border-2 border-mkt-surface-elevated bg-mkt-accent shadow-sm"
                aria-hidden
              />
              <div
                className={cn(
                  "overflow-hidden rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface-elevated",
                  compact ? "p-2.5" : "p-3",
                )}
                style={{
                  marginLeft: `${index * (compact ? 4 : 8)}px`,
                  width: `calc(100% - ${index * (compact ? 4 : 8)}px)`,
                }}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <Icon className="h-4 w-4 shrink-0 text-mkt-muted" />
                    <div className="min-w-0">
                      <p className={cn("font-medium text-mkt-ink", compact ? "text-xs" : "text-sm")}>{layer.label}</p>
                      {!compact ? (
                        <p className="text-xs text-mkt-muted">{layer.sublabel}</p>
                      ) : null}
                    </div>
                  </div>
                  <span className={cn("shrink-0 font-semibold tabular-nums text-mkt-ink", compact ? "text-xs" : "text-sm")}>
                    {display}
                  </span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-sm bg-mkt-ink/[0.05]">
                  <div
                    className="h-full rounded-sm bg-mkt-ink/60 transition-all duration-500"
                    style={{ width: `${depth}%` }}
                  />
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
