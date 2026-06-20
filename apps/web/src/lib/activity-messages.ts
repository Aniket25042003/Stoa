/**
 * @file apps/web/src/lib/activity-messages.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export const ACTIVITY_MESSAGES = {
  planning: ["Shaping your strategy", "Mapping the approach", "Setting the stage"],
  queued: ["Preparing workspace", "Initializing progress", "Aligning strategy focus"],
  research: [
    "Uncovering opportunities",
    "Scanning the landscape",
    "Finding what matters",
    "Analyzing market space",
  ],
  reasoning: [
    "Thinking through angles",
    "Weighing options",
    "Sharpening focus",
    "Synthesizing insights",
  ],
  writing: [
    "Crafting your plan",
    "Making it actionable",
    "Getting it launch-ready",
    "Adding final touches",
  ],
  completed: ["Strategy active."],
  failed: ["Something went wrong. Let's try again."],
  awaiting_plan_approval: ["Ready for your feedback."],
} as const;

export type ActivityPhase = keyof typeof ACTIVITY_MESSAGES;

export const PHASE_LABELS: Record<ActivityPhase, string> = {
  planning: "Preparing",
  queued: "Queue",
  research: "Exploring",
  reasoning: "Thinking",
  writing: "Crafting",
  completed: "Active",
  failed: "Error",
  awaiting_plan_approval: "Feedback requested",
};
