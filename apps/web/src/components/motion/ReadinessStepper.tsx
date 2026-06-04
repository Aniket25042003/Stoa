"use client";

import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/cn";

const STEPS = [
  { key: "has_company_profile" as const, label: "Brand profile" },
  { key: "has_gtm_plan" as const, label: "Strategy blueprint" },
  { key: "has_marketing_baseline" as const, label: "Creative direction" },
];

export function ReadinessStepper({
  readiness,
  className,
}: {
  readiness?: {
    has_company_profile?: boolean;
    has_gtm_plan?: boolean;
    has_marketing_baseline?: boolean;
  };
  className?: string;
}) {
  const reduced = useReducedMotion();
  const flags = STEPS.map((s) => readiness?.[s.key] ?? false);

  return (
    <div className={cn("space-y-5", className)}>
      <div className="flex items-center px-2" role="list" aria-label="Readiness progress">
        {STEPS.map((step, i) => {
          const ready = flags[i];
          return (
            <div key={step.key} className="flex flex-1 items-center">
              {i > 0 ? (
                <span
                  className={cn(
                    "h-0.5 flex-1 transition-all duration-500",
                    flags[i - 1] || ready ? "bg-primary/55" : "bg-outline-variant/40"
                  )}
                  aria-hidden
                />
              ) : null}
              <span
                className={cn(
                  "mx-auto flex h-3.5 w-3.5 shrink-0 rounded-full border-2 transition-all duration-500",
                  ready ? "border-primary bg-primary" : "border-outline-variant/60 bg-surface-container-low",
                  ready && !reduced && "scale-110"
                )}
                aria-hidden
              />
            </div>
          );
        })}
      </div>
      <div className="grid gap-3">
        {STEPS.map((step, i) => {
          const ready = flags[i];
          return (
            <div
              key={step.key}
              className="flex items-center justify-between rounded-2xl border border-outline-variant/60 bg-surface-container-low/70 px-4 py-3"
            >
              <span className="font-semibold text-on-surface">{step.label}</span>
              <span className={ready ? "text-sm font-bold text-primary" : "text-sm font-bold text-on-surface-variant"}>
                {ready ? "Ready" : "Needs setup"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
