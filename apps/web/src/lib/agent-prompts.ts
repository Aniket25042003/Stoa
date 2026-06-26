/**
 * @file apps/web/src/lib/agent-prompts.ts
 * @description Starter prompts for the unified GTM agent, grouped by feature area.
 */

export type AgentPromptGroup = {
  id: string;
  label: string;
  prompts: string[];
};

export const AGENT_PROMPT_GROUPS: AgentPromptGroup[] = [
  {
    id: "icp",
    label: "ICP research",
    prompts: ["Who was our best customer segment last quarter and why?"],
  },
  {
    id: "content",
    label: "Content",
    prompts: ["Where is our content production bottleneck right now?"],
  },
  {
    id: "competitive",
    label: "Competitive",
    prompts: ["What changed across competitors this week?"],
  },
  {
    id: "campaign-analysis",
    label: "Campaign analysis",
    prompts: ["Which channels are driving best conversion efficiency?"],
  },
  {
    id: "alignment",
    label: "Alignment",
    prompts: ["Where are sales and marketing misaligned in our funnel?"],
  },
  {
    id: "launch",
    label: "Launch",
    prompts: ["Which campaigns should we prioritize for the next launch?"],
  },
];

export const AGENT_QUICK_PROMPTS = AGENT_PROMPT_GROUPS.flatMap((g) => g.prompts);
