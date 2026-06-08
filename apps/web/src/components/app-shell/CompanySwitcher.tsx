"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ACTIVE_COMPANY_EVENT, getStoredActiveCompanyId, setStoredActiveCompanyId } from "@/lib/active-company";

type Company = {
  id: string;
  name: string;
  description?: string | null;
};

export function CompanySwitcher() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const res = await apiFetch("/v1/companies", { });
        const body = res.ok ? await res.json() : { companies: [] };
        if (cancelled) return;
        const list = (body.companies ?? []) as Company[];
        setCompanies(list);
        const stored = getStoredActiveCompanyId();
        const next = list.find((co) => co.id === stored)?.id ?? list[0]?.id ?? null;
        setActiveId(next);
        if (next !== stored) {
          setStoredActiveCompanyId(next);
        }
      } catch {
        if (!cancelled) {
          setCompanies([]);
          setActiveId(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const onActiveCompany = (event: Event) => {
      const detail = (event as CustomEvent<{ companyId: string | null }>).detail;
      setActiveId(detail?.companyId ?? null);
    };
    window.addEventListener(ACTIVE_COMPANY_EVENT, onActiveCompany);
    return () => window.removeEventListener(ACTIVE_COMPANY_EVENT, onActiveCompany);
  }, []);

  const label = useMemo(() => {
    if (loading) return "Loading companies";
    return companies.find((company) => company.id === activeId)?.name ?? "No company";
  }, [activeId, companies, loading]);

  return (
    <div className="flex min-w-0 items-center gap-2">
      <label className="sr-only" htmlFor="company-switcher">
        Active company
      </label>
      <select
        id="company-switcher"
        value={activeId ?? ""}
        onChange={(event) => {
          const next = event.target.value || null;
          setActiveId(next);
          setStoredActiveCompanyId(next);
        }}
        disabled={loading || companies.length === 0}
        className="min-h-10 max-w-[180px] rounded-xl border border-outline-variant/70 bg-surface-container-low/80 px-3 py-2 text-sm font-semibold text-on-surface shadow-soft outline-none transition focus:border-primary md:max-w-[240px]"
        title={label}
      >
        {companies.length === 0 ? <option value="">No company</option> : null}
        {companies.map((company) => (
          <option key={company.id} value={company.id}>
            {company.name}
          </option>
        ))}
      </select>
      <Link href="/onboarding" className="btn-secondary px-3 py-2 text-sm" title="Add company">
        +
      </Link>
    </div>
  );
}
