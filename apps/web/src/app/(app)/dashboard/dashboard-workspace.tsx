"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ProductButton, ProductCard, ProductPageHeader } from "@/components/product";
import { InsightMarkdown } from "@/components/product/InsightMarkdown";
import { CapabilityStatus } from "@/components/dashboard/CapabilityStatus";
import { CrmPipelineMini } from "@/components/dashboard/CrmPipelineMini";
import { MemoryLayersDiagram } from "@/components/dashboard/MemoryLayersDiagram";
import { MetricsBarChart } from "@/components/dashboard/MetricsBarChart";
import { ReadinessGauge } from "@/components/dashboard/ReadinessGauge";
import { SignalBreakdownChart } from "@/components/dashboard/SignalBreakdownChart";
import type { DashboardSummary } from "@/components/dashboard/types";
import {
  formatCompletenessMissingSentence,
  formatRoleLabel,
  resolveDisplayName,
} from "@/lib/user-facing-copy";

type ConversationSummary = {
  id: string;
  title: string;
  updated_at: string;
};

type Props = {
  email: string;
  displayName?: string | null;
  org?: { id: string; name: string; industry?: string | null };
  role: string;
};

const readinessLinks = [
  { href: "/data/profile", label: "Complete company profile", key: "ready_for_intelligence" as const },
  { href: "/data/competitors", label: "Add competitors", key: "ready_for_competitive" as const },
  { href: "/data/sources", label: "Upload customer data", key: "ready_for_campaigns" as const },
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
            <ProductButton>{dataReady ? "Open STOA" : "Complete data setup"}</ProductButton>
          </Link>
        }
      />

      {completeness ? (
        <ProductCard className="overflow-hidden bg-mkt-dark-band p-0 text-mkt-dark-ink">
          <div className="grid gap-0 lg:grid-cols-[auto_1fr]">
            <div className="flex flex-col items-center justify-center border-b border-mkt-dark-ink/10 px-8 py-8 lg:border-b-0 lg:border-r">
              <ReadinessGauge
                percent={completeness.percent ?? 0}
                size="lg"
                label="Data readiness"
                variant="dark"
              />
              {completeness.missing && completeness.missing.length > 0 ? (
                <p className="mt-4 max-w-[220px] text-center text-xs leading-relaxed text-mkt-dark-ink/65">
                  {formatCompletenessMissingSentence(completeness.missing)}
                </p>
              ) : (
                <p className="mt-4 max-w-[200px] text-center text-xs leading-relaxed text-mkt-dark-ink/65">
                  Workspace is ready for STOA across intelligence areas.
                </p>
              )}
            </div>
            <div className="p-6 lg:p-8">
              <CapabilityStatus completeness={completeness} variant="dark" />
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/data/profile">
                  <ProductButton variant="secondary" className="!text-mkt-ink">
                    Open data hub
                  </ProductButton>
                </Link>
                <Link href="/agent">
                  <ProductButton variant="ghost" className="!text-mkt-dark-ink hover:!bg-mkt-dark-ink/10">
                    Ask STOA
                  </ProductButton>
                </Link>
              </div>
            </div>
          </div>
        </ProductCard>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-12">
        <ProductCard className="lg:col-span-5">
          <h2 className="text-sm font-semibold tracking-tight text-mkt-ink">Workspace volume</h2>
          <p className="mt-1 text-xs text-mkt-muted">Relative scale across ingested intelligence sources</p>
          <div className="mt-5">
            <MetricsBarChart counts={summary?.counts} />
          </div>
        </ProductCard>

        <ProductCard className="lg:col-span-4">
          <h2 className="text-sm font-semibold tracking-tight text-mkt-ink">Signal mix</h2>
          <p className="mt-1 text-xs text-mkt-muted">Distribution of extracted customer intelligence</p>
          <div className="mt-5">
            <SignalBreakdownChart signalsByKind={summary?.signals_by_kind} />
          </div>
        </ProductCard>

        <ProductCard className="lg:col-span-3">
          <h2 className="text-sm font-semibold tracking-tight text-mkt-ink">Memory stack</h2>
          <p className="mt-1 text-xs text-mkt-muted">How evidence layers into STOA context</p>
          <div className="mt-5">
            <MemoryLayersDiagram counts={summary?.counts} icpVersion={summary?.icp_version} />
          </div>
          <CrmPipelineMini crmStats={summary?.crm_stats} className="mt-4" />
        </ProductCard>
      </div>

      {executiveSummary ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Executive summary</h2>
          <InsightMarkdown contextualTitle="Executive summary" className="mt-3">
            {executiveSummary}
          </InsightMarkdown>
        </ProductCard>
      ) : null}

      {insightHighlights.length > 0 ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Insight highlights</h2>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2">
            {insightHighlights.slice(0, 4).map((insight) => (
              <li
                key={insight.title}
                className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4"
              >
                <p className="text-sm font-medium text-mkt-ink">{insight.title}</p>
                {insight.content?.answer ? (
                  <InsightMarkdown contextualTitle={insight.title} compact className="mt-2">
                    {insight.content.answer}
                  </InsightMarkdown>
                ) : null}
              </li>
            ))}
          </ul>
        </ProductCard>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <ProductCard>
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Recent STOA threads</h2>
            <Link href="/agent" className="text-xs font-medium text-mkt-accent hover:underline">
              View all
            </Link>
          </div>
          {recentThreads.length === 0 ? (
            <p className="mt-4 text-sm text-mkt-muted">No conversations yet.</p>
          ) : (
            <ul className="mt-4 space-y-2">
              {recentThreads.map((thread) => (
                <li key={thread.id}>
                  <Link
                    href={`/agent?c=${thread.id}`}
                    className="block rounded-sm border border-mkt-ink/[0.06] px-4 py-3 text-sm transition-colors hover:border-mkt-accent/25 hover:bg-mkt-accent/[0.04]"
                  >
                    <span className="line-clamp-1 font-medium text-mkt-ink">{thread.title}</span>
                    <span className="mt-1 block text-xs text-mkt-muted">
                      {new Date(thread.updated_at).toLocaleDateString()}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </ProductCard>

        <ProductCard>
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Generated assets</h2>
            <Link href="/assets" className="text-xs font-medium text-mkt-accent hover:underline">
              Open library
            </Link>
          </div>
          <p className="mt-4 text-sm text-mkt-muted">
            {summary?.counts?.campaigns ?? 0} campaign packages in your library. Review outputs and download files
            from Assets.
          </p>
          <Link href="/assets" className="mt-4 inline-block">
            <ProductButton variant="secondary">Browse assets</ProductButton>
          </Link>
        </ProductCard>
      </div>

      {completeness ? (
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Next steps</h2>
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
                    <span className={ready ? "text-emerald-600" : "text-mkt-muted"}>
                      {ready ? "Ready" : "Incomplete"}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </ProductCard>
      ) : null}
    </div>
  );
}
