import type { ActivityPhase } from "@/lib/activity-messages";

export type PipelineStepId = "planning" | "research" | "reasoning" | "writing";

export const PIPELINE_STEPS: { id: PipelineStepId; label: string }[] = [
  { id: "planning", label: "Planning" },
  { id: "research", label: "Research" },
  { id: "reasoning", label: "Reasoning" },
  { id: "writing", label: "Writing" },
];

export type EventRow = { message?: string; agent?: string; phase?: string };

export function resolveActivityPhase(status: string, events: EventRow[]): ActivityPhase {
  if (status === "awaiting_plan_approval") return "awaiting_plan_approval";
  if (status === "planning") return "planning";
  if (status === "completed") return "completed";
  if (status === "failed") return "failed";
  const latestPhase = events.at(-1)?.phase;
  if (latestPhase === "planning" || latestPhase === "research" || latestPhase === "reasoning" || latestPhase === "writing") {
    return latestPhase;
  }
  if (status === "queued") return "queued";
  return "research";
}

/** Index of active pipeline step (0–3), or -1 for terminal/non-pipeline states */
export function pipelineStepIndex(phase: ActivityPhase): number {
  if (phase === "planning" || phase === "queued" || phase === "awaiting_plan_approval") return 0;
  if (phase === "research") return 1;
  if (phase === "reasoning") return 2;
  if (phase === "writing") return 3;
  return -1;
}

/** Step to highlight when the run failed (falls back to writing if unknown). */
function indexFromEventPhase(phase?: string): number {
  if (phase === "planning") return 0;
  if (phase === "research") return 1;
  if (phase === "reasoning") return 2;
  if (phase === "writing") return 3;
  return -1;
}

export function pipelineActiveStepIndex(phase: ActivityPhase, events: EventRow[] = []): number {
  if (phase !== "failed") return pipelineStepIndex(phase);
  for (let i = events.length - 1; i >= 0; i--) {
    const idx = indexFromEventPhase(events[i]?.phase);
    if (idx >= 0) return idx;
  }
  return 3;
}

export function isPipelineTerminal(phase: ActivityPhase): boolean {
  return phase === "completed" || phase === "failed";
}

/** Visual variant for ActivitySurface */
export function activitySurfaceVariant(phase: ActivityPhase): ActivityPhase {
  if (phase === "queued") return "queued";
  if (phase === "awaiting_plan_approval") return "planning";
  return phase;
}

export function formatDevLogLine(e: EventRow): string {
  if (e.message) return `[${e.phase ?? ""}] ${e.agent ?? ""}: ${e.message}`;
  return JSON.stringify(e);
}
