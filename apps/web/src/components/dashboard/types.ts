export type WorkspaceCounts = {
  documents?: number;
  signals?: number;
  competitors?: number;
  alerts?: number;
  campaigns?: number;
  integrations?: number;
  canonical_deals?: number;
};

export type WorkspaceCompleteness = {
  percent?: number;
  missing?: string[];
  ready_for_intelligence?: boolean;
  ready_for_competitive?: boolean;
  ready_for_campaigns?: boolean;
};

export type DashboardSummary = {
  org?: { id: string; name: string; industry?: string | null };
  counts?: WorkspaceCounts;
  completeness?: WorkspaceCompleteness;
  signals_by_kind?: Record<string, number>;
  icp_version?: number | null;
  crm_stats?: {
    total_accounts?: number;
    total_deals?: number;
    won_deals?: number;
    lost_deals?: number;
  };
  viewer?: {
    display_name?: string | null;
    job_title?: string | null;
    role_name?: string | null;
    role_key?: string | null;
  };
};

export const METRIC_DEFINITIONS = [
  { key: "signals" as const, label: "ICP signals", shortLabel: "Signals" },
  { key: "documents" as const, label: "Documents", shortLabel: "Docs" },
  { key: "competitors" as const, label: "Competitors", shortLabel: "Competitors" },
  { key: "alerts" as const, label: "Alerts", shortLabel: "Alerts" },
  { key: "campaigns" as const, label: "Campaigns", shortLabel: "Campaigns" },
];

export const SIGNAL_KIND_LABELS: Record<string, string> = {
  pain_point: "Pain points",
  objection: "Objections",
  buying_trigger: "Buying triggers",
  segment: "Segments",
  win_loss: "Win / loss",
};
