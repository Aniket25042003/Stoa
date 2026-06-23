export type HowItWorksStep = {
  module: string;
  title: string;
  body: string;
  accomplishments: string[];
};

export const HOW_IT_WORKS_STEPS: HowItWorksStep[] = [
  {
    module: "Intake",
    title: "Tell us about your company",
    body: "Add the basics once: who you serve, what you sell, and the goals you want to conquer next.",
    accomplishments: [
      "Define your audience and positioning in one place",
      "Set GTM goals your whole team can align on",
      "Start every workflow from the same brand context",
    ],
  },
  {
    module: "Strategy",
    title: "Get a strategy that fits",
    body: "Start from a custom strategy blueprint built for your unique market angle, then refine it as your product grows.",
    accomplishments: [
      "See channel and positioning options ranked for your market",
      "Build a strategy blueprint you can edit and reuse",
      "Stress-test angles before you commit budget",
    ],
  },
  {
    module: "Workspace",
    title: "Refine through conversation",
    body: "Explore directions, query positioning ideas, or request channel suggestions in your strategy workspace.",
    accomplishments: [
      "Ask follow-up questions without losing context",
      "Compare messaging and channel alternatives quickly",
      "Keep a running record of decisions your team agrees on",
    ],
  },
  {
    module: "Creative",
    title: "Set your creative direction",
    body: "Establish brand voice parameters, visual style preferences, and creative constraints to guide campaign outputs.",
    accomplishments: [
      "Lock voice, tone, and visual guardrails for every asset",
      "Brief creatives once - not on every new campaign",
      "Keep outputs on-brand without re-explaining rules",
    ],
  },
  {
    module: "Campaigns",
    title: "Create campaigns that land",
    body: "Generate high-conversion campaign copy, structured creative briefs, script drafts, and custom distribution schedules.",
    accomplishments: [
      "Turn strategy into copy, briefs, and launch-ready assets",
      "Plan distribution across channels from one workspace",
      "Ship campaigns faster without starting from scratch",
    ],
  },
  {
    module: "Portfolio",
    title: "Scale across brands",
    body: "Stoa keeps workspaces and contexts separate so you can easily manage a portfolio of distinct brands.",
    accomplishments: [
      "Run multiple brands without context bleeding across teams",
      "Switch workspaces and pick up where you left off",
      "Give agencies and in-house teams isolated environments",
    ],
  },
];
