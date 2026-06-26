"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { ProductCard } from "@/components/product";
import { MemoryLayersDiagram } from "@/components/dashboard/MemoryLayersDiagram";
import { MetricsBarChart } from "@/components/dashboard/MetricsBarChart";
import { ReadinessGauge } from "@/components/dashboard/ReadinessGauge";
import { SignalBreakdownChart } from "@/components/dashboard/SignalBreakdownChart";
import type { DashboardSummary } from "@/components/dashboard/types";
import { cn } from "@/lib/cn";

type ContextRailProps = {
  summary: DashboardSummary | null;
  className?: string;
  overlay?: boolean;
};

export function ContextRail({ summary, className, overlay }: ContextRailProps) {
  const [collapsed, setCollapsed] = useState(false);
  const completeness = summary?.completeness;

  if (collapsed) {
    return (
      <div className={cn("hidden h-full border-l border-mkt-ink/[0.06] lg:flex lg:flex-col", className)}>
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="flex h-full w-10 items-center justify-center text-mkt-muted hover:text-mkt-ink"
          aria-label="Expand context panel"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <aside
      className={cn(
        overlay
          ? "flex w-full flex-col"
          : "hidden h-full w-[var(--agent-context-width)] shrink-0 flex-col border-l border-mkt-ink/[0.06] bg-mkt-surface lg:flex",
        className,
      )}
    >
      <div className="flex shrink-0 items-center justify-between border-b border-mkt-ink/[0.06] px-4 py-3">
        <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Context</p>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="rounded-sm p-1 text-mkt-muted hover:text-mkt-ink"
          aria-label="Collapse context panel"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      <div className="mkt-scrollbar-none min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {completeness != null ? (
          <ProductCard className="p-3">
            <div className="flex items-center gap-3">
              <ReadinessGauge percent={completeness.percent ?? 0} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Data readiness</p>
                <p className="mt-0.5 text-sm text-mkt-muted">
                  {completeness.ready_for_intelligence ? "Ready for agent queries" : "Complete your data hub"}
                </p>
                {!completeness.ready_for_intelligence ? (
                  <Link href="/data/profile" className="mt-1 inline-block text-xs text-mkt-accent hover:underline">
                    Complete setup →
                  </Link>
                ) : null}
              </div>
            </div>
          </ProductCard>
        ) : null}

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-mkt-subtle">Workspace volume</p>
          <MetricsBarChart counts={summary?.counts} compact />
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-mkt-subtle">Signal mix</p>
          <SignalBreakdownChart signalsByKind={summary?.signals_by_kind} compact />
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-mkt-subtle">Memory stack</p>
          <MemoryLayersDiagram counts={summary?.counts} icpVersion={summary?.icp_version} compact />
        </div>
      </div>
    </aside>
  );
}
