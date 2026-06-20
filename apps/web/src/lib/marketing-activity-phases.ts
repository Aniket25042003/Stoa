/**
 * @file apps/web/src/lib/marketing-activity-phases.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export type MarketingActivityStep = "idle" | "route" | "create" | "review" | "done" | "failed";

export const MARKETING_ACTIVITY_STEPS: { id: MarketingActivityStep; label: string }[] = [
  { id: "route", label: "Listening" },
  { id: "create", label: "Creating" },
  { id: "review", label: "Polishing" },
  { id: "done", label: "Ready" },
];

export type MarketingEventPayload = {
  agent?: string;
  phase?: string;
  message?: string;
};

const REVIEW_AGENTS = new Set(["critic", "brand_voice_keeper", "memory_curator", "main_marketing_agent"]);
const CREATE_AGENTS = new Set([
  "marketing_strategist",
  "idea_generator",
  "copywriter",
  "scriptwriter",
  "channel_planner",
  "competitor_intel",
  "image_generator",
  "video_generator",
]);

/**
 * Handles resolve marketing step behavior for this part of the Stoa application.
 *
 * @param busy - Input value used to render UI or execute the workflow.
 * @param events - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function resolveMarketingStep(busy: boolean, events: MarketingEventPayload[]): MarketingActivityStep {
  if (!busy && events.length === 0) return "idle";
  const last = events.at(-1);
  const msg = (last?.message ?? "").toLowerCase();
  if (msg.includes("pipeline completed")) return "done";
  if (msg.includes("failed") || last?.phase === "error") return "failed";

  const agent = (last?.agent ?? "").toLowerCase();
  if (REVIEW_AGENTS.has(agent) || last?.phase === "review") return "review";
  if (CREATE_AGENTS.has(agent)) return "create";
  if (agent.includes("router") || last?.phase === "context" || last?.phase === "routing") return "route";
  if (busy) return events.length > 2 ? "create" : "route";
  return "idle";
}

/**
 * Handles marketing step index behavior for this part of the Stoa application.
 *
 * @param step - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function marketingStepIndex(step: MarketingActivityStep): number {
  if (step === "route") return 0;
  if (step === "create") return 1;
  if (step === "review") return 2;
  if (step === "done") return 3;
  if (step === "failed") return 3;
  return -1;
}

export const MARKETING_STATUS_MESSAGES: Record<MarketingActivityStep, string> = {
  idle: "Ready to launch",
  route: "Listening to your creative brief...",
  create: "Creating campaign assets...",
  review: "Polishing for brand alignment...",
  done: "Assets are ready for deployment",
  failed: "The update failed",
};

/**
 * Handles format marketing dev log behavior for this part of the Stoa application.
 *
 * @param data - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function formatMarketingDevLog(data: MarketingEventPayload): string {
  const m = typeof data.message === "string" ? data.message : JSON.stringify(data);
  return `Activity: ${m}`;
}
