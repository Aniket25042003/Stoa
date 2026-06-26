"use client";

import { CheckCircle2, Circle } from "lucide-react";
import type { WorkspaceCompleteness } from "@/components/dashboard/types";
import { cn } from "@/lib/cn";

const CAPABILITIES = [
  {
    key: "ready_for_intelligence" as const,
    label: "Customer intelligence",
    description: "ICP signals, documents, and insights",
  },
  {
    key: "ready_for_competitive" as const,
    label: "Competitive tracking",
    description: "Competitors monitored with alerts",
  },
  {
    key: "ready_for_campaigns" as const,
    label: "Campaign generation",
    description: "Enough context to produce assets",
  },
];

type CapabilityStatusProps = {
  completeness?: WorkspaceCompleteness;
  variant?: "light" | "dark";
  className?: string;
};

export function CapabilityStatus({ completeness, variant = "light", className }: CapabilityStatusProps) {
  const readyCount = CAPABILITIES.filter((c) => completeness?.[c.key]).length;
  const dark = variant === "dark";

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className={cn("text-xs font-medium uppercase tracking-wider", dark ? "text-mkt-subtle" : "text-mkt-subtle")}>
          Capability coverage
        </p>
        <span className={cn("text-xs font-medium tabular-nums", dark ? "text-mkt-dark-ink/80" : "text-mkt-muted")}>
          {readyCount}/{CAPABILITIES.length} active
        </span>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        {CAPABILITIES.map((cap) => {
          const ready = completeness?.[cap.key] ?? false;
          return (
            <div
              key={cap.key}
              className={cn(
                "rounded-sm border px-3 py-2.5 transition-colors",
                dark
                  ? ready
                    ? "border-mkt-dark-ink/20 bg-mkt-dark-ink/[0.06]"
                    : "border-mkt-dark-ink/10 bg-transparent"
                  : ready
                    ? "border-mkt-accent/20 bg-mkt-accent/[0.04]"
                    : "border-mkt-ink/[0.06] bg-mkt-ink/[0.02]",
              )}
            >
              <div className="flex items-start gap-2">
                {ready ? (
                  <CheckCircle2 className={cn("mt-0.5 h-4 w-4 shrink-0", dark ? "text-emerald-400" : "text-emerald-600")} />
                ) : (
                  <Circle className={cn("mt-0.5 h-4 w-4 shrink-0", dark ? "text-mkt-dark-ink/40" : "text-mkt-subtle")} />
                )}
                <div className="min-w-0">
                  <p className={cn("text-sm font-medium", dark ? "text-mkt-dark-ink" : "text-mkt-ink")}>{cap.label}</p>
                  <p className={cn("mt-0.5 text-xs leading-snug", dark ? "text-mkt-dark-ink/60" : "text-mkt-muted")}>
                    {cap.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
