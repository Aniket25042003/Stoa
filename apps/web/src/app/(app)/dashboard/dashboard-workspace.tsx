"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  ProductButton,
  ProductCard,
  ProductPageHeader,
} from "@/components/product";

type CoreFeatureMetrics = {
  icp_customer_research?: {
    best_customer_segment?: string | null;
    deals?: number;
    win_rate_percent?: number | null;
    underperforming_loss_reasons?: { reason: string; count: number }[];
  };
  content_bottleneck?: {
    status_breakdown?: Record<string, number>;
    avg_generation_time_seconds?: number | null;
  };
  competitive_intelligence?: {
    tracked_competitors?: number;
    recent_alerts?: number;
    alerts_by_severity?: Record<string, number>;
  };
  launch_orchestration?: {
    campaign_count?: number;
    status_breakdown?: Record<string, number>;
  };
  campaign_analysis?: {
    top_channel?: string | null;
    top_campaign?: string | null;
    has_data?: boolean;
  };
  sales_marketing_alignment?: {
    top_lead_source?: string | null;
    stall_points?: { stage: string; stalled_count: number }[];
    top_friction_loss_reasons?: { reason: string; count: number }[];
  };
};

type Summary = {
  org: { id: string; name: string; industry?: string | null };
  counts: {
    documents: number;
    signals: number;
    competitors: number;
    alerts: number;
    campaigns: number;
  };
  signals_by_kind: Record<string, number>;
  icp_version: number | null;
  completeness: {
    percent: number;
    missing: string[];
    ready_for_intelligence: boolean;
    ready_for_competitive: boolean;
    ready_for_campaigns: boolean;
  };
  executive_summary?: { content?: { summary?: string }; citations?: string[] };
  insight_highlights?: Array<{ title: string; content?: { answer?: string } }>;
  core_feature_metrics?: CoreFeatureMetrics;
};

type Props = {
  email: string;
  displayName?: string | null;
  org?: { id: string; name: string; industry?: string | null };
  role: string;
};

const readinessLinks = [
  {
    href: "/data/profile",
    label: "Complete company profile",
    key: "ready_for_intelligence" as const,
  },
  {
    href: "/data/competitors",
    label: "Add competitors",
    key: "ready_for_competitive" as const,
  },
  {
    href: "/data/sources",
    label: "Upload customer data",
    key: "ready_for_campaigns" as const,
  },
];

export function DashboardWorkspace({ email, displayName, org, role }: Props) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentThreads, setRecentThreads] = useState<ConversationSummary[]>([]);
  const [insightHighlights, setInsightHighlights] = useState<
    Array<{ title: string; content?: { answer?: string } }>
  >([]);

  useEffect(() => {
    void (async () => {
      const [summaryRes, convRes] = await Promise.all([
        apiFetch("/v1/dashboard/summary"),
        apiFetch("/v1/conversations"),
      ]);
      if (summaryRes.ok) {
        const body = await summaryRes.json();
        setSummary(body);
        setInsightHighlights(body.insight_highlights ?? []);
      }
      if (convRes.ok) {
        const body = await convRes.json();
        setRecentThreads((body.conversations ?? []).slice(0, 4));
      }
    })();
  }, []);

  const completeness = summary?.completeness;
  const orgName = org?.name ?? "Your workspace";
  const dataReady = completeness?.ready_for_intelligence ?? false;
  const executiveSummary = (summary as { executive_summary?: { content?: { summary?: string } } })
    ?.executive_summary?.content?.summary;

  const viewerName = resolveDisplayName(summary?.viewer?.display_name ?? displayName, email);
  const roleLabel = formatRoleLabel(summary?.viewer?.role_name ?? summary?.viewer?.role_key ?? role);
  const industry = org?.industry ?? summary?.org?.industry;
  const leadParts = [`Signed in as ${viewerName}`, roleLabel];
  if (industry) leadParts.push(industry);

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Home"
        title={orgName}
        lead={leadParts.join(" · ")}
        actions={
          <Link href={dataReady ? "/agent" : "/data/profile"}>
            <ProductButton>{dataReady ? "Open GTM Agent" : "Complete data setup"}</ProductButton>
          </Link>
        }
      />

      {completeness ? (
        <ProductCard className="bg-mkt-dark-band text-mkt-dark-ink">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="max-w-xl">
              <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                Data readiness
              </p>
              <p className="mt-2 text-xl font-semibold tracking-tight">
                {completeness.percent}% complete
              </p>
              {completeness.missing.length > 0 ? (
                <p className="mt-2 text-sm text-mkt-dark-ink/70">
                  Still needed: {completeness.missing.join(", ")}
                </p>
              ) : (
                <p className="mt-2 text-sm text-mkt-dark-ink/70">
                  Your workspace is ready for intelligence pipelines.
                </p>
              )}
            </div>
            <Link href="/data/profile">
              <ProductButton variant="secondary" className="!text-mkt-ink">
                Open data hub
              </ProductButton>
            </Link>
          </div>
          <div className="mt-5 h-2 rounded-sm bg-mkt-dark-ink/15">
            <div
              className="h-2 rounded-sm bg-mkt-accent transition-all"
              style={{ width: `${completeness.percent}%` }}
            />
          </div>
        </ProductCard>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[
          { label: "Documents", value: counts?.documents ?? 0 },
          { label: "Signals", value: counts?.signals ?? 0 },
          { label: "Competitors", value: counts?.competitors ?? 0 },
          { label: "Alerts", value: counts?.alerts ?? 0 },
          { label: "Campaigns", value: counts?.campaigns ?? 0 },
        ].map((tile) => (
          <ProductCard key={tile.label} className="text-center">
            <p className="text-3xl font-semibold text-mkt-ink">{tile.value}</p>
            <p className="mt-1 text-xs font-medium uppercase tracking-wider text-mkt-muted">
              {tile.label}
            </p>
          </ProductCard>
        ))}
      </div>

      {executiveSummary ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            Executive summary
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-mkt-muted">
            {summary.executive_summary.content.summary}
          </p>
        </ProductCard>
      ) : null}

      {insightHighlights.length > 0 ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            Intelligence highlights
          </h2>
          <ul className="mt-4 space-y-3">
            {summary.insight_highlights.slice(0, 3).map((item, i) => (
              <li
                key={i}
                className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4"
              >
                <p className="text-sm font-semibold text-mkt-ink">
                  {item.title}
                </p>
                <p className="mt-1 text-sm text-mkt-muted line-clamp-2">
                  {item.content?.answer ?? ""}
                </p>
              </li>
            ))}
          </ul>
          <Link href="/agent" className="mt-4 inline-block">
            <ProductButton variant="secondary">
              View prepared answers
            </ProductButton>
          </Link>
        </ProductCard>
      ) : null}

      {summary?.core_feature_metrics ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            Six-feature GTM snapshot
          </h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm">
              <p className="font-semibold text-mkt-ink">
                ICP & customer research
              </p>
              <p className="mt-1 text-mkt-muted">
                Best segment:{" "}
                {summary.core_feature_metrics.icp_customer_research
                  ?.best_customer_segment ?? "—"}
              </p>
              <p className="text-mkt-muted">
                Deals:{" "}
                {summary.core_feature_metrics.icp_customer_research?.deals ?? 0}
              </p>
            </div>
            <div className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm">
              <p className="font-semibold text-mkt-ink">Content bottleneck</p>
              <p className="mt-1 text-mkt-muted">
                Avg generation:{" "}
                {summary.core_feature_metrics.content_bottleneck
                  ?.avg_generation_time_seconds != null
                  ? `${summary.core_feature_metrics.content_bottleneck?.avg_generation_time_seconds}s`
                  : "—"}
              </p>
              <p className="text-mkt-muted">
                Queued:{" "}
                {summary.core_feature_metrics.content_bottleneck
                  ?.status_breakdown?.queued ?? 0}
              </p>
            </div>
            <div className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm">
              <p className="font-semibold text-mkt-ink">
                Competitive intelligence
              </p>
              <p className="mt-1 text-mkt-muted">
                Tracked competitors:{" "}
                {summary.core_feature_metrics.competitive_intelligence
                  ?.tracked_competitors ?? 0}
              </p>
              <p className="text-mkt-muted">
                Recent alerts:{" "}
                {summary.core_feature_metrics.competitive_intelligence
                  ?.recent_alerts ?? 0}
              </p>
            </div>
            <div className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm">
              <p className="font-semibold text-mkt-ink">Launch orchestration</p>
              <p className="mt-1 text-mkt-muted">
                Campaigns:{" "}
                {summary.core_feature_metrics.launch_orchestration
                  ?.campaign_count ?? 0}
              </p>
              <p className="text-mkt-muted">
                Running:{" "}
                {summary.core_feature_metrics.launch_orchestration
                  ?.status_breakdown?.running ?? 0}
              </p>
            </div>
            <div className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm">
              <p className="font-semibold text-mkt-ink">Campaign analysis</p>
              <p className="mt-1 text-mkt-muted">
                Top channel:{" "}
                {summary.core_feature_metrics.campaign_analysis?.top_channel ??
                  "—"}
              </p>
              <p className="text-mkt-muted">
                Top campaign:{" "}
                {summary.core_feature_metrics.campaign_analysis?.top_campaign ??
                  "—"}
              </p>
            </div>
            <div className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm">
              <p className="font-semibold text-mkt-ink">
                Sales-marketing alignment
              </p>
              <p className="mt-1 text-mkt-muted">
                Top lead source:{" "}
                {summary.core_feature_metrics.sales_marketing_alignment
                  ?.top_lead_source ?? "—"}
              </p>
              <p className="text-mkt-muted">
                Stall points:{" "}
                {summary.core_feature_metrics.sales_marketing_alignment
                  ?.stall_points?.length ?? 0}
              </p>
            </div>
          </div>
        </ProductCard>
      ) : null}

      {completeness ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            Next steps
          </h2>
          <ul className="mt-4 space-y-2">
            {readinessLinks.map((item) => {
              const ready = completeness[item.key];
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="flex items-center justify-between rounded-sm border border-mkt-ink/[0.06] px-4 py-3 text-sm transition-colors hover:border-mkt-accent/25 hover:bg-mkt-accent/[0.04]"
                  >
                    <span className="text-mkt-ink">{item.label}</span>
                    <span
                      className={ready ? "text-emerald-600" : "text-mkt-muted"}
                    >
                      {ready ? "Ready" : "Incomplete"}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </ProductCard>
      ) : null}

      {summary?.icp_version ? (
        <p className="text-sm text-mkt-muted">
          Latest ICP profile: v{summary.icp_version}
        </p>
      ) : null}
    </div>
  );
}
