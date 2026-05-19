export const ACTIVITY_MESSAGES = {
  planning: ["Drafting the strategy plan", "Organizing company context", "Preparing your review checklist"],
  queued: ["Preparing the workspace", "Organizing GTM details", "Getting your plan ready"],
  research: [
    "Reviewing market and customer signals",
    "Organizing competitor notes",
    "Looking for positioning and pricing clues",
    "Summarizing what matters for the plan",
  ],
  reasoning: [
    "Building ICP and persona hypotheses",
    "Synthesizing customer pain points",
    "Drafting positioning and messaging angles",
    "Ranking launch channels and experiment ideas",
    "Checking whether recommendations are actionable",
  ],
  writing: [
    "Drafting the GTM strategy document",
    "Turning notes into a clear narrative",
    "Adding citations and assumptions",
    "Reviewing the report for actionability",
    "Preparing the final plan output",
  ],
  completed: ["The plan is ready."],
  failed: ["The request failed. Check the latest update for details."],
  awaiting_plan_approval: ["Waiting for your approval before continuing."],
} as const;

export type ActivityPhase = keyof typeof ACTIVITY_MESSAGES;

export const PHASE_LABELS: Record<ActivityPhase, string> = {
  planning: "Planning your strategy",
  queued: "Preparing to run",
  research: "Researching the market",
  reasoning: "Reasoning about positioning",
  writing: "Writing your GTM report",
  completed: "Complete",
  failed: "Something went wrong",
  awaiting_plan_approval: "Awaiting your approval",
};
