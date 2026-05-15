"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ACTIVE_COMPANY_EVENT, getStoredActiveCompanyId, setStoredActiveCompanyId } from "@/lib/active-company";

type Company = {
  id: string;
  name: string;
  description?: string | null;
  industry?: string | null;
  onboarding_completed_at?: string | null;
};

type Summary = {
  company: Company;
  stats: {
    profile_completion: number;
    gtm_runs: number;
    marketing_chats: number;
    knowledge_items: number;
    marketing_artifacts: number;
  };
  readiness: {
    has_company_profile: boolean;
    has_gtm_plan: boolean;
    has_marketing_baseline: boolean;
  };
  recent: {
    runs: { id: string; status: string; created_at: string }[];
    chats: { id: string; title: string; created_at: string }[];
    knowledge: { id: string; kind: string; title: string; created_at: string }[];
    artifacts: { id: string; kind: string; title: string; created_at: string }[];
  };
};

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function DashboardWorkspace({ accessToken, companies, email }: { accessToken: string; companies: Company[]; email: string }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStoredActiveCompanyId();
    const next = companies.find((company) => company.id === stored)?.id ?? companies[0]?.id ?? null;
    setActiveId(next);
    if (next !== stored) setStoredActiveCompanyId(next);
  }, [companies]);

  useEffect(() => {
    const onActiveCompany = (event: Event) => {
      const detail = (event as CustomEvent<{ companyId: string | null }>).detail;
      setActiveId(detail?.companyId ?? null);
    };
    window.addEventListener(ACTIVE_COMPANY_EVENT, onActiveCompany);
    return () => window.removeEventListener(ACTIVE_COMPANY_EVENT, onActiveCompany);
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

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="eyebrow text-inverse-primary">Dashboard</p>
            <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">
              {activeCompany?.name ?? "Your company"} command center
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-white/68">
              Signed in as {email}. Track company readiness, GTM progress, marketing work, and recent activity from one place.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/gtm" className="btn-primary px-5 py-3 text-sm">
              Open GTM
            </Link>
            <Link href="/marketing" className="btn-secondary px-5 py-3 text-sm">
              Open Marketing
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        {[
          { label: "Profile", value: summary ? pct(summary.stats.profile_completion) : "--" },
          { label: "GTM runs", value: summary?.stats.gtm_runs ?? "--" },
          { label: "Marketing chats", value: summary?.stats.marketing_chats ?? "--" },
          { label: "Saved knowledge", value: summary?.stats.knowledge_items ?? "--" },
        ].map((item) => (
          <div key={item.label} className="rounded-3xl p-6 card-glass">
            <p className="eyebrow text-[10px]">{item.label}</p>
            <p className="mt-3 font-display text-4xl font-extrabold tracking-[-0.04em] text-on-surface">{item.value}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl p-6 card-glass md:p-7">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Company readiness</p>
              <h2 className="mt-2 font-display text-2xl font-bold tracking-[-0.03em] text-on-surface">What is ready for {activeCompany?.name}</h2>
            </div>
            {loading ? <span className="text-sm text-on-surface-variant">Loading...</span> : null}
          </div>
          <div className="mt-6 grid gap-3">
            {[
              { label: "Company profile", ready: readiness?.has_company_profile },
              { label: "GTM plan", ready: readiness?.has_gtm_plan },
              { label: "Marketing foundation", ready: readiness?.has_marketing_baseline },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between rounded-2xl border border-outline-variant/60 bg-surface-container-low/70 px-4 py-3">
                <span className="font-semibold text-on-surface">{item.label}</span>
                <span className={item.ready ? "text-sm font-bold text-primary" : "text-sm font-bold text-on-surface-variant"}>
                  {item.ready ? "Ready" : "Needs setup"}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl p-6 card-glass md:p-7">
          <p className="eyebrow">All companies</p>
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
              Add another company
            </Link>
          </div>
        </div>
      </section>

      <section className="rounded-3xl p-6 card-glass md:p-7">
        <p className="eyebrow">Recent activity</p>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">GTM</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent.runs ?? []).slice(0, 4).map((run) => (
                <Link key={run.id} href={`/runs/${run.id}`} className="block rounded-xl bg-surface-container-low/70 px-3 py-2 hover:text-primary">
                  {run.status}
                </Link>
              ))}
              {summary?.recent.runs.length ? null : <p>No GTM activity yet.</p>}
            </div>
          </div>
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Marketing</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent.chats ?? []).slice(0, 4).map((chat) => (
                <p key={chat.id} className="rounded-xl bg-surface-container-low/70 px-3 py-2">
                  {chat.title || "Marketing chat"}
                </p>
              ))}
              {summary?.recent.chats.length ? null : <p>No marketing activity yet.</p>}
            </div>
          </div>
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Knowledge</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent.knowledge ?? []).slice(0, 4).map((item) => (
                <p key={item.id} className="rounded-xl bg-surface-container-low/70 px-3 py-2">
                  {item.title || item.kind}
                </p>
              ))}
              {summary?.recent.knowledge.length ? null : <p>No saved company notes yet.</p>}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
