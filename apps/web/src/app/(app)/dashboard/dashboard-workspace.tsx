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

  useEffect(() => {
    if (!activeId) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const res = await apiFetch(`/v1/companies/${activeId}/summary`, { accessToken });
        const body = res.ok ? await res.json() : null;
        if (!cancelled) setSummary(body);
      } catch {
        if (!cancelled) setSummary(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [accessToken, activeId]);

  const activeCompany = useMemo(() => companies.find((company) => company.id === activeId) ?? companies[0], [activeId, companies]);
  const readiness = summary?.readiness;

  const statCards = [
    { label: "Profile", variant: "percent" as const, value: summary?.stats.profile_completion },
    { label: "Strategies", variant: "number" as const, value: summary?.stats.gtm_runs },
    { label: "Conversations", variant: "number" as const, value: summary?.stats.marketing_chats },
    { label: "Insights", variant: "number" as const, value: summary?.stats.knowledge_items },
    { label: "Creatives", variant: "number" as const, value: summary?.stats.marketing_artifacts },
  ];

  return (
    <div className="space-y-8">
      <motion.section
        key={activeId ?? "hero"}
        initial={reduce ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10"
      >
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="eyebrow text-primary">Dashboard</p>
            <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">
              {activeCompany?.name ?? "Your brand"} workspace
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-white/68">
              Signed in as {email}. Track brand progress, strategy development, campaign creative, and recent activity from one place.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/gtm" className="btn-primary px-5 py-3 text-sm">
              Open Strategy
            </Link>
            <Link href="/marketing" className="btn-secondary px-5 py-3 text-sm">
              Open Campaigns
            </Link>
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

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl p-6 card-glass md:p-7">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Your progress</p>
              <h2 className="mt-2 font-display text-2xl font-bold tracking-[-0.03em] text-on-surface">What is ready for {activeCompany?.name}</h2>
            </div>
            {loading ? <span className="text-sm text-on-surface-variant">Loading...</span> : null}
          </div>
        ))}
      </div>

        <div className="rounded-3xl p-6 card-glass md:p-7">
          <p className="eyebrow">All brands</p>
          <div className="mt-5 grid gap-3">
            {companies.map((company) => (
              <button
                key={company.id}
                type="button"
                onClick={() => setStoredActiveCompanyId(company.id)}
                className={
                  company.id === activeId
                    ? "rounded-2xl border border-primary/50 bg-primary/10 px-4 py-3 text-left shadow-soft"
                    : "rounded-2xl border border-outline-variant/60 bg-surface-container-low/70 px-4 py-3 text-left transition hover:border-primary/40"
                }
              >
                <span className="block font-display text-lg font-bold tracking-[-0.02em] text-on-surface">{company.name}</span>
                <span className="mt-1 block line-clamp-2 text-sm text-on-surface-variant">{company.description || company.industry || "No description yet"}</span>
              </button>
            ))}
            <Link href="/onboarding" className="btn-secondary justify-center px-4 py-3 text-sm">
              Add another brand
            </Link>
          </div>
        </div>
      ) : null}

      <section className="rounded-3xl p-6 card-glass md:p-7">
        <p className="eyebrow">Recent activity</p>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Strategy</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent?.runs ?? []).slice(0, 4).map((run, i) => (
                <StaggerInView key={run.id} delay={i * 0.05}>
                  <Link href={`/runs/${run.id}`} className="relative block overflow-hidden rounded-xl bg-surface-container-low/70 px-3 py-2 hover:text-primary">
                    <span
                      className="absolute bottom-0 left-0 h-0.5 bg-primary/40"
                      style={{ width: recencyWidth(run.created_at) }}
                      aria-hidden
                    />
                    {run.status}
                  </Link>
                </StaggerInView>
              ))}
              {(summary?.recent?.runs ?? []).length === 0 ? <p>No strategy activity yet.</p> : null}
            </div>
          </div>
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Campaigns</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent?.chats ?? []).slice(0, 4).map((chat, i) => (
                <StaggerInView key={chat.id} delay={i * 0.05}>
                  <p className="relative overflow-hidden rounded-xl bg-surface-container-low/70 px-3 py-2">
                    <span
                      className="absolute bottom-0 left-0 h-0.5 bg-primary/40"
                      style={{ width: recencyWidth(chat.created_at) }}
                      aria-hidden
                    />
                    {chat.title || "Campaign conversation"}
                  </p>
                </StaggerInView>
              ))}
              {(summary?.recent?.chats ?? []).length === 0 ? <p>No campaign activity yet.</p> : null}
            </div>
          </div>
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Insights</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent?.knowledge ?? []).slice(0, 4).map((item, i) => (
                <StaggerInView key={item.id} delay={i * 0.05}>
                  <p className="relative overflow-hidden rounded-xl bg-surface-container-low/70 px-3 py-2">
                    <span
                      className="absolute bottom-0 left-0 h-0.5 bg-primary/40"
                      style={{ width: recencyWidth(item.created_at) }}
                      aria-hidden
                    />
                    {item.title || item.kind}
                  </p>
                </StaggerInView>
              ))}
              {(summary?.recent?.knowledge ?? []).length === 0 ? <p>No saved brand insights yet.</p> : null}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
