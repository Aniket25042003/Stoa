/** Human-readable labels for unified agent SSE status events. */

const TOOL_LABELS: Record<string, string> = {
  search_workspace_memory: "workspace memory",
  get_workspace_freshness: "data freshness",
  search_connected_sources: "connected sources",
  lookup_canonical_records: "CRM records",
  refresh_connected_source: "source refresh",
  refresh_precomputed_insights: "insight refresh",
  refresh_competitor_intel: "competitive refresh",
  search_public_web: "web search",
  icp_customer_research_tool: "ICP research",
  content_bottleneck_tool: "content analysis",
  competitive_intelligence_tool: "competitive intel",
  launch_orchestration_tool: "launch planning",
  campaign_analysis_tool: "campaign analysis",
  sales_marketing_alignment_tool: "sales & marketing alignment",
};

/** Rotating copy while the agent waits between SSE progress events. */
export const AGENT_WAITING_MESSAGES = [
  "Reviewing your workspace…",
  "Cross-checking customer signals…",
  "Pulling patterns from your data…",
  "Connecting insights across sources…",
  "Looking for what matters most…",
  "Tracing themes in your GTM data…",
  "Sharpening the answer…",
] as const;

export function isAgentKeepaliveEvent(event: Record<string, unknown>): boolean {
  return event.id === "heartbeat" || event.message === "keepalive";
}

/** Status lines that should not be replaced by heartbeat rotation. */
import { STOA_WORKING_STATUS } from "@/lib/stoa-brand";

export function isPinnedAgentStatus(status: string | null): boolean {
  if (!status || status === "keepalive") return false;
  if (status === STOA_WORKING_STATUS) return false;
  if (status.startsWith("Calling ")) return true;
  if (status.endsWith(" complete")) return true;
  if (status === "Synthesizing answer…") return true;
  return false;
}

export function nextAgentWaitingMessage(indexRef: { current: number }): string {
  const message = AGENT_WAITING_MESSAGES[indexRef.current % AGENT_WAITING_MESSAGES.length];
  indexRef.current += 1;
  return message;
}

export function formatAgentToolLabel(toolName: string): string {
  const key = toolName.trim();
  if (!key) return "tool";
  if (TOOL_LABELS[key]) return TOOL_LABELS[key];
  return key.replace(/_/g, " ");
}

export function agentStatusFromEvent(event: Record<string, unknown>): string | null {
  if (isAgentKeepaliveEvent(event)) return null;
  if (typeof event.message === "string" && event.message.trim()) {
    if (event.message === "keepalive") return null;
    return event.message;
  }
  if (event.status === "tool_call" && typeof event.tool === "string") {
    return `Calling ${formatAgentToolLabel(event.tool)}…`;
  }
  if (event.status === "tool_done" && typeof event.tool === "string") {
    const label = formatAgentToolLabel(event.tool);
    return `${label.charAt(0).toUpperCase()}${label.slice(1)} complete`;
  }
  if (event.status === "tool_summary") {
    return "Synthesizing answer…";
  }
  if (event.status === "thinking") {
    return "Retrieving intelligence…";
  }
  return null;
}
