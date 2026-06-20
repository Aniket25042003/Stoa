/**
 * @file apps/web/src/lib/integration-catalog.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export type IntegrationCategory = {
  id: string;
  label: string;
  description: string;
  providerIds: string[];
};

/** Display order and grouping for the integrations marketplace UI. */
export const INTEGRATION_CATEGORIES: IntegrationCategory[] = [
  {
    id: "crm",
    label: "CRM",
    description: "Sync customer and pipeline data to sharpen ICP segments and win/loss analysis.",
    providerIds: ["hubspot", "salesforce"],
  },
  {
    id: "sales-intelligence",
    label: "Sales intelligence",
    description: "Import conversations from sales calls to surface objections, pain points, and buying signals.",
    providerIds: ["gong"],
  },
  {
    id: "support",
    label: "Support & success",
    description: "Turn support tickets and chats into product feedback and customer voice signals.",
    providerIds: ["intercom", "zendesk"],
  },
  {
    id: "reviews",
    label: "Reviews & community",
    description: "Monitor market perception from review sites and community mentions.",
    providerIds: ["reviews", "reddit"],
  },
  {
    id: "analytics",
    label: "Product analytics",
    description: "Connect usage and traffic patterns to campaign and positioning decisions.",
    providerIds: ["posthog", "ga4"],
  },
  {
    id: "knowledge",
    label: "Knowledge & docs",
    description: "Pull docs, notes, and team context into your shared knowledge base.",
    providerIds: ["notion", "google_drive", "slack"],
  },
  {
    id: "product-feedback",
    label: "Product feedback",
    description: "Capture feature requests and customer issues from your product workflow.",
    providerIds: ["jira"],
  },
];

/** User-facing one-liner for each connector (falls back to API description). */
export const INTEGRATION_BENEFITS: Record<string, string> = {
  hubspot: "Sync contacts, companies, and deals to build ICP profiles from your pipeline.",
  salesforce: "Import accounts and opportunities so intelligence reflects your live CRM.",
  gong: "Analyze call transcripts for objections, pain points, and competitive mentions.",
  intercom: "Bring support conversations into customer research and signal detection.",
  zendesk: "Sync tickets and threads to spot recurring issues and voice-of-customer themes.",
  reviews: "Import G2 and Capterra reviews to track positioning and competitive sentiment.",
  reddit: "Monitor subreddits for brand mentions and market conversation trends.",
  posthog: "Add product usage context to campaign briefs and audience targeting.",
  ga4: "Connect traffic and conversion trends to marketing performance insights.",
  notion: "Import Notion pages as searchable knowledge for answers and campaigns.",
  google_drive: "Export Google Docs into Stoa so documents power prepared intelligence.",
  slack: "Pull selected channel messages into your org knowledge base.",
  jira: "Import issues and comments as structured product feedback signals.",
};

export function groupProvidersByCategory<T extends { id: string }>(
  providers: T[]
): Array<IntegrationCategory & { providers: T[] }> {
  const byId = new Map(providers.map((p) => [p.id, p]));
  return INTEGRATION_CATEGORIES.map((category) => ({
    ...category,
    providers: category.providerIds.map((id) => byId.get(id)).filter((p): p is T => Boolean(p)),
  })).filter((category) => category.providers.length > 0);
}
