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

export function formatMarketingDevLog(data: MarketingEventPayload): string {
  const m = typeof data.message === "string" ? data.message : JSON.stringify(data);
  return `Activity: ${m}`;
}
