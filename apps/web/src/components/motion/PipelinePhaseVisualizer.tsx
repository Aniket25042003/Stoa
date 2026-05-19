"use client";

import { Check } from "lucide-react";
import {
  PIPELINE_STEPS,
  isPipelineTerminal,
  pipelineActiveStepIndex,
  type EventRow,
} from "@/lib/pipeline-phases";
import type { ActivityPhase } from "@/lib/activity-messages";
import { cn } from "@/lib/cn";

export function PipelinePhaseVisualizer({
  phase,
  events = [],
  className,
}: {
  phase: ActivityPhase;
  events?: EventRow[];
  className?: string;
}) {
  const activeIdx = pipelineActiveStepIndex(phase, events);
  const terminal = isPipelineTerminal(phase);
  const failed = phase === "failed";
  const completed = phase === "completed";

  return (
    <nav className={cn("w-full", className)} aria-label="GTM pipeline progress">
      <ol className="flex items-start justify-between gap-2">
        {PIPELINE_STEPS.map((step, i) => {
          const done = failed ? i < activeIdx : terminal ? completed && i <= 3 : activeIdx > i;
          const active = failed ? i === activeIdx : !terminal && activeIdx === i;
          const pending = !terminal && !failed && activeIdx < i;

          return (
            <li key={step.id} className="flex flex-1 flex-col items-center gap-2 text-center">
              <div className="relative flex w-full items-center justify-center">
                {i > 0 ? (
                  <span
                    className={cn(
                      "absolute right-1/2 top-1/2 h-0.5 w-full -translate-y-1/2",
                      done || active ? "bg-primary/50" : "bg-outline-variant/40"
                    )}
                    aria-hidden
                  />
                ) : null}
                <StepDot done={done} active={active} failed={failed && active} pending={pending} />
              </div>
              <span
                className={cn(
                  "font-mono text-[10px] font-semibold uppercase tracking-[0.1em]",
                  active && failed ? "text-error" : active ? "text-primary" : done ? "text-on-surface" : "text-on-surface-variant"
                )}
                aria-current={active ? "step" : undefined}
              >
                {step.label}
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
  failed,
  pending,
}: {
  done: boolean;
  active: boolean;
  failed: boolean;
  pending: boolean;
}) {
  return (
    <span
      className={cn(
        "relative z-[1] flex h-9 w-9 items-center justify-center rounded-full border-2 transition-colors",
        done && "border-primary bg-primary text-on-primary",
        active && !failed && "border-primary bg-primary/15 pipeline-step-pulse",
        active && failed && "border-error bg-error-container text-error",
        pending && "border-outline-variant/50 bg-surface-container-low",
        !done && !active && !pending && "border-outline-variant/50 bg-surface-container-low"
      )}
    >
      {done ? <Check className="h-4 w-4" strokeWidth={2.5} /> : null}
      {active && !done && !failed ? <span className="h-2 w-2 rounded-full bg-primary pipeline-dot-pulse" /> : null}
    </span>
  );
}
