/**
 * Maps internal completeness keys and roles to user-facing copy.
 */

const COMPLETENESS_MISSING_LABELS: Record<string, string> = {
  documents_or_integration: "customer data uploads or integrations",
  competitors: "tracked competitors",
  brand_voice: "brand voice",
  target_customers: "target customer profile",
  website_url: "company website",
  industry: "industry",
};

export function formatCompletenessMissing(keys: string[]): string[] {
  return keys.map((key) => COMPLETENESS_MISSING_LABELS[key] ?? "additional workspace details");
}

export function formatCompletenessMissingSentence(keys: string[]): string {
  const labels = formatCompletenessMissing(keys);
  if (labels.length === 0) return "";
  if (labels.length === 1) return `Still needed: ${labels[0]}.`;
  if (labels.length === 2) return `Still needed: ${labels[0]} and ${labels[1]}.`;
  const last = labels[labels.length - 1];
  const rest = labels.slice(0, -1).join(", ");
  return `Still needed: ${rest}, and ${last}.`;
}

export function formatRoleLabel(role?: string | null): string {
  if (!role) return "Member";
  const cleaned = role.replace(/_/g, " ").trim();
  if (!cleaned) return "Member";
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1).toLowerCase();
}

/** Prefer profile name; avoid exposing raw email in primary UI when possible. */
export function resolveDisplayName(fullName?: string | null, email?: string | null): string {
  const name = fullName?.trim();
  if (name) return name;

  const localPart = email?.split("@")[0]?.replace(/[._+-]+/g, " ").trim();
  if (localPart) {
    return localPart
      .split(/\s+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
      .join(" ");
  }

  return "there";
}

export function formatSignalKindLabel(kind: string): string {
  const labels: Record<string, string> = {
    pain_point: "Pain points",
    objection: "Objections",
    buying_trigger: "Buying triggers",
    segment: "Segments",
    win_loss: "Win / loss",
  };
  return labels[kind] ?? "Customer signals";
}

const JOB_STATUS_LABELS: Record<string, string> = {
  queued: "In queue",
  running: "In progress",
  planning: "Planning",
  awaiting_plan_approval: "Awaiting approval",
  completed: "Completed",
  failed: "Failed",
  generating: "Generating",
  processed: "Processed",
  pending: "Pending",
  error: "Failed",
};

export function formatJobStatusLabel(status: string): string {
  const key = status.toLowerCase().replace(/-/g, "_");
  if (JOB_STATUS_LABELS[key]) return JOB_STATUS_LABELS[key];
  const cleaned = status.replace(/_/g, " ").trim();
  if (!cleaned) return "Unknown";
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1).toLowerCase();
}

const KNOWLEDGE_REF_LABELS: Record<string, string> = {
  icp_profile: "ICP profile",
  document: "Document",
  signal: "Customer signal",
  competitor: "Competitor",
  brand_voice: "Brand voice",
  web_research: "Web research",
};

export function formatKnowledgeRefKind(kind: string): string {
  return KNOWLEDGE_REF_LABELS[kind] ?? formatJobStatusLabel(kind);
}

const INTEGRATION_ERROR_PATTERNS: Array<{ pattern: RegExp; message: string }> = [
  {
    pattern: /APIFY_API_TOKEN/i,
    message: "Reddit and review import are not enabled on this workspace yet.",
  },
  { pattern: /property_id/i, message: "Add your GA4 property ID when connecting." },
  { pattern: /401|403|unauthorized/i, message: "Connection expired or credentials were rejected — try reconnecting." },
  { pattern: /rate limit/i, message: "The provider rate-limited this sync — try again shortly." },
];

export function formatIntegrationError(raw?: string | null): string | null {
  if (!raw?.trim()) return null;
  for (const { pattern, message } of INTEGRATION_ERROR_PATTERNS) {
    if (pattern.test(raw)) return message;
  }
  return raw.length > 160 ? `${raw.slice(0, 157)}…` : raw;
}
