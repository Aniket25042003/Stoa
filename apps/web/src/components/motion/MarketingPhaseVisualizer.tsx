"use client";

import { Check, X } from "lucide-react";
import {
  MARKETING_ACTIVITY_STEPS,
  marketingStepIndex,
  type MarketingActivityStep,
} from "@/lib/marketing-activity-phases";
import { cn } from "@/lib/cn";

export function MarketingPhaseVisualizer({
  step,
  className,
}: {
  step: MarketingActivityStep;
  className?: string;
}) {
  const activeIdx = marketingStepIndex(step);
  const done = step === "done";
  const failed = step === "failed";

  return (
    <nav className={cn("w-full", className)} aria-label="Marketing activity progress">
      <ol className="flex items-start justify-between gap-1">
        {MARKETING_ACTIVITY_STEPS.map((s, i) => {
          const isDone = done || activeIdx > i;
          const active = !done && !failed && activeIdx === i;
          const isFailed = failed && activeIdx === i;
          const pending = !done && !failed && activeIdx < i;

          return (
            <li key={s.id} className="flex flex-1 flex-col items-center gap-1.5 text-center">
              <StepDot done={isDone} active={active} pending={pending} failed={isFailed} compact />
              <span
                className={cn(
                  "font-mono text-[9px] font-semibold uppercase tracking-[0.08em]",
                  active ? "text-primary" : isFailed ? "text-error" : isDone ? "text-on-surface" : "text-on-surface-variant"
                )}
                aria-current={active ? "step" : undefined}
              >
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function StepDot({
  done,
  active,
  pending,
  failed,
  compact,
}: {
  done: boolean;
  active: boolean;
  pending: boolean;
  failed?: boolean;
  compact?: boolean;
}) {
  const size = compact ? "h-7 w-7" : "h-9 w-9";
  return (
    <span
      className={cn(
        "relative z-[1] flex items-center justify-center rounded-full border-2 transition-colors",
        size,
        done && "border-primary bg-primary text-on-primary",
        active && "border-primary bg-primary/15 pipeline-step-pulse",
        failed && "border-error bg-error-container text-error",
        pending && "border-outline-variant/50 bg-surface-container-low"
      )}
    >
      {done ? <Check className="h-3 w-3" strokeWidth={2.5} /> : null}
      {failed ? <X className="h-3 w-3" strokeWidth={2.5} /> : null}
      {active && !done ? <span className="h-1.5 w-1.5 rounded-full bg-primary pipeline-dot-pulse" /> : null}
    </span>
  );
}
