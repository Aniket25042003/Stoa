"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { ACTIVE_COMPANY_EVENT, getStoredActiveCompanyId, setStoredActiveCompanyId } from "@/lib/active-company";
import { AnimatedStatCard } from "@/components/motion/AnimatedStatCard";
import { ReadinessStepper } from "@/components/motion/ReadinessStepper";
import { StaggerInView } from "@/components/motion/StaggerInView";

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

function recencyWidth(createdAt: string): string {
  const age = Date.now() - new Date(createdAt).getTime();
  const day = 24 * 60 * 60 * 1000;
  const pct = Math.max(12, Math.min(100, 100 - (age / (14 * day)) * 88));
  return `${pct}%`;
}

export function DashboardWorkspace({ accessToken, companies, email }: { accessToken: string; companies: Company[]; email: string }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const reduce = useReducedMotion();

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

  const statCards = [
    { label: "Profile", variant: "percent" as const, value: summary?.stats.profile_completion },
    { label: "GTM runs", variant: "number" as const, value: summary?.stats.gtm_runs },
    { label: "Marketing chats", variant: "number" as const, value: summary?.stats.marketing_chats },
    { label: "Saved knowledge", variant: "number" as const, value: summary?.stats.knowledge_items },
    { label: "Marketing artifacts", variant: "number" as const, value: summary?.stats.marketing_artifacts },
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
            <p className="eyebrow text-inverse-primary">Dashboard</p>
            <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">
              {activeCompany?.name ?? "Your company"} workspace
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
      </motion.section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {statCards.map((item, i) => (
          <StaggerInView key={item.label} delay={i * 0.08}>
            <AnimatedStatCard
              label={item.label}
              loading={loading}
              variant={item.variant}
              value={item.value}
            />
          </StaggerInView>
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
          <div className="mt-6">
            <ReadinessStepper readiness={readiness} />
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
              {(summary?.recent?.runs ?? []).length === 0 ? <p>No GTM activity yet.</p> : null}
            </div>
          </div>
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Marketing</h3>
            <div className="mt-3 space-y-2 text-sm text-on-surface-variant">
              {(summary?.recent?.chats ?? []).slice(0, 4).map((chat, i) => (
                <StaggerInView key={chat.id} delay={i * 0.05}>
                  <p className="relative overflow-hidden rounded-xl bg-surface-container-low/70 px-3 py-2">
                    <span
                      className="absolute bottom-0 left-0 h-0.5 bg-primary/40"
                      style={{ width: recencyWidth(chat.created_at) }}
                      aria-hidden
                    />
                    {chat.title || "Marketing chat"}
                  </p>
                </StaggerInView>
              ))}
              {(summary?.recent?.chats ?? []).length === 0 ? <p>No marketing activity yet.</p> : null}
            </div>
          </div>
          <div>
            <h3 className="font-display text-xl font-bold text-on-surface">Knowledge</h3>
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
              {(summary?.recent?.knowledge ?? []).length === 0 ? <p>No saved company notes yet.</p> : null}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
