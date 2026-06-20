/**
 * @file apps/web/src/app/(app)/dashboard/dashboard-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements dashboard workspace behavior for the frontend product ui.
 * @dependencies Next.js, React, BFF apiFetch
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ProductButton, ProductCard, ProductPageHeader } from "@/components/product";

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
};

type Props = {
  email: string;
  org?: { id: string; name: string; industry?: string | null };
  role: string;
};

const readinessLinks = [
  { href: "/data/profile", label: "Complete company profile", key: "ready_for_intelligence" as const },
  { href: "/data/competitors", label: "Add competitors", key: "ready_for_competitive" as const },
  { href: "/data/sources", label: "Upload customer data", key: "ready_for_campaigns" as const },
];

/**
 * Handles dashboard workspace behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function DashboardWorkspace({ email, org, role }: Props) {
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    void (async () => {
      const res = await apiFetch("/v1/dashboard/summary");
      if (res.ok) setSummary(await res.json());
    })();
  }, []);

  const counts = summary?.counts;
  const completeness = summary?.completeness;
  const orgName = org?.name ?? summary?.org?.name ?? "Your workspace";

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Your workspace"
        title={orgName}
        lead={`Signed in as ${email} · ${role}${org?.industry || summary?.org?.industry ? ` · ${org?.industry ?? summary?.org?.industry}` : ""}`}
      />

      {completeness ? (
        <ProductCard className="bg-mkt-dark-band text-mkt-dark-ink">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="max-w-xl">
              <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">Data readiness</p>
              <p className="mt-2 font-syne text-xl font-extrabold uppercase tracking-tight">
                {completeness.percent}% complete
              </p>
              {completeness.missing.length > 0 ? (
                <p className="mt-2 font-dm-sans text-sm text-mkt-dark-ink/70">
                  Still needed: {completeness.missing.join(", ")}
                </p>
              ) : (
                <p className="mt-2 font-dm-sans text-sm text-mkt-dark-ink/70">Your workspace is ready for intelligence pipelines.</p>
              )}
            </div>
            <Link href="/data/profile">
              <ProductButton variant="secondary" className="!text-mkt-ink">
                Open data hub
              </ProductButton>
            </Link>
          </div>
          <div className="mt-5 h-2 rounded-sm bg-mkt-dark-ink/15">
            <div className="h-2 rounded-sm bg-mkt-accent transition-all" style={{ width: `${completeness.percent}%` }} />
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
            <p className="font-syne text-3xl font-extrabold text-mkt-accent">{tile.value}</p>
            <p className="mt-1 font-dm-sans text-[10px] font-bold uppercase tracking-[0.14em] text-mkt-muted">{tile.label}</p>
          </ProductCard>
        ))}
      </div>

      {summary?.executive_summary?.content?.summary ? (
        <ProductCard>
          <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Executive summary</h2>
          <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted">
            {summary.executive_summary.content.summary}
          </p>
        </ProductCard>
      ) : null}

      {summary?.insight_highlights && summary.insight_highlights.length > 0 ? (
        <ProductCard>
          <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Intelligence highlights</h2>
          <ul className="mt-4 space-y-3">
            {summary.insight_highlights.slice(0, 3).map((item, i) => (
              <li key={i} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4">
                <p className="font-dm-sans text-sm font-semibold text-mkt-ink">{item.title}</p>
                <p className="mt-1 font-dm-sans text-sm text-mkt-muted line-clamp-2">{item.content?.answer ?? ""}</p>
              </li>
            ))}
          </ul>
          <Link href="/intelligence" className="mt-4 inline-block">
            <ProductButton variant="secondary">View prepared answers</ProductButton>
          </Link>
        </ProductCard>
      ) : null}

      {completeness ? (
        <ProductCard>
          <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Next steps</h2>
          <ul className="mt-4 space-y-2">
            {readinessLinks.map((item) => {
              const ready = completeness[item.key];
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="flex items-center justify-between rounded-sm border border-mkt-ink/[0.06] px-4 py-3 font-dm-sans text-sm transition-colors hover:border-mkt-accent/25 hover:bg-mkt-accent/[0.04]"
                  >
                    <span className="text-mkt-ink">{item.label}</span>
                    <span className={ready ? "text-emerald-600" : "text-mkt-muted"}>{ready ? "Ready" : "Incomplete"}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </ProductCard>
      ) : null}

      {summary?.icp_version ? (
        <p className="font-dm-sans text-sm text-mkt-muted">Latest ICP profile: v{summary.icp_version}</p>
      ) : null}
    </div>
  );
}
