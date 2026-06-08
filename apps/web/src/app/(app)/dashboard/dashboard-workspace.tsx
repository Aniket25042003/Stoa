"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

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

const quickLinks = [
  { href: "/data", label: "Data hub", desc: "Add profile, documents, competitors" },
  { href: "/intelligence", label: "Intelligence", desc: "Prepared answers & ICP" },
  { href: "/competitive", label: "Competitive", desc: "Alerts & monitoring" },
  { href: "/campaigns", label: "Campaigns", desc: "Generate campaign assets" },
];

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

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Marketing Intelligence</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">
          {org?.name ?? summary?.org?.name ?? "Your workspace"}
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Signed in as {email}. Role: {role}.
          {org?.industry || summary?.org?.industry ? ` Industry: ${org?.industry ?? summary?.org?.industry}.` : ""}
        </p>
        {completeness ? (
          <div className="mt-6 max-w-md">
            <div className="flex justify-between text-xs text-white/70">
              <span>Data completeness</span>
              <span>{completeness.percent}%</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-white/20">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${completeness.percent}%` }} />
            </div>
            {completeness.missing.length > 0 ? (
              <p className="mt-2 text-xs text-white/60">
                <Link href="/data" className="underline">Complete data</Link>: {completeness.missing.join(", ")}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>

      {summary?.executive_summary?.content?.summary ? (
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Executive summary</h2>
          <p className="mt-3 text-sm leading-7 text-on-surface-variant">
            {summary.executive_summary.content.summary}
          </p>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[
          { label: "Documents", value: counts?.documents ?? 0 },
          { label: "Signals", value: counts?.signals ?? 0 },
          { label: "Competitors", value: counts?.competitors ?? 0 },
          { label: "Alerts", value: counts?.alerts ?? 0 },
          { label: "Campaigns", value: counts?.campaigns ?? 0 },
        ].map((tile) => (
          <div key={tile.label} className="rounded-3xl p-5 card-glass text-center">
            <p className="font-display text-3xl font-bold text-on-surface">{tile.value}</p>
            <p className="mt-1 text-sm text-on-surface-variant">{tile.label}</p>
          </div>
        ))}
      </div>

      {summary?.insight_highlights && summary.insight_highlights.length > 0 ? (
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Intelligence highlights</h2>
          <ul className="mt-4 space-y-3 text-sm">
            {summary.insight_highlights.slice(0, 3).map((item, i) => (
              <li key={i} className="rounded-xl bg-surface-container-low p-4">
                <p className="font-semibold text-on-surface">{item.title}</p>
                <p className="mt-1 text-on-surface-variant line-clamp-2">
                  {item.content?.answer ?? ""}
                </p>
              </li>
            ))}
          </ul>
          <Link href="/intelligence" className="btn-secondary mt-4 inline-flex px-4 py-2 text-sm">
            View all prepared answers
          </Link>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {quickLinks.map((card) => (
          <Link key={card.href} href={card.href} className="rounded-3xl p-6 card-glass transition hover:border-primary/40">
            <h2 className="font-display text-lg font-bold text-on-surface">{card.label}</h2>
            <p className="mt-2 text-sm leading-7 text-on-surface-variant">{card.desc}</p>
          </Link>
        ))}
      </div>

      {summary?.icp_version ? (
        <p className="text-sm text-on-surface-variant">Latest ICP profile: v{summary.icp_version}</p>
      ) : null}
    </div>
  );
}
