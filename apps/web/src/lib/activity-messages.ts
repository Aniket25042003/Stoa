export const ACTIVITY_MESSAGES = {
  planning: ["Reading your approved master plan", "Preparing the agent hierarchy", "Loading shared Redis context"],
  queued: ["Waiting for a worker to pick up the run", "Preparing the GTM pipeline", "Getting the agent team ready"],
  research: [
    "Running web research passes",
    "Deep-crawling priority URLs with Playwright",
    "Searching the web for problem and competitor signals",
    "Looking for competitor positioning and pricing clues",
    "Reviewing sources before the research parent asks for approval",
  ],
  reasoning: [
    "Building ICP and persona hypotheses",
    "Synthesizing pain points from the research bundle",
    "Drafting positioning and messaging angles",
    "Ranking launch channels and experiment ideas",
    "Checking whether reasoning is strong enough for main-agent approval",
  ],
  writing: [
    "Drafting the GTM strategy document",
    "Turning research and reasoning into a clear narrative",
    "Adding citations and assumptions",
    "Reviewing the report for actionability",
    "Preparing the final Markdown and PDF-ready output",
  ],
  completed: ["Pipeline completed. The report is ready."],
  failed: ["The run failed. Check the latest event for details."],
  awaiting_plan_approval: ["Waiting for your approval before starting any agents."],
} as const;

export type ActivityPhase = keyof typeof ACTIVITY_MESSAGES;
