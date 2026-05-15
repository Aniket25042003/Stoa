"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ACTIVE_COMPANY_EVENT, getStoredActiveCompanyId, setStoredActiveCompanyId } from "@/lib/active-company";
import { MarketingChat } from "./[companyId]/chats/[chatId]/marketing-chat";

type Company = {
  id: string;
  name: string;
  description?: string | null;
};

type Summary = {
  readiness?: {
    has_marketing_baseline?: boolean;
  };
};

function splitList(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function MarketingWorkspace({ accessToken, companies }: { accessToken: string; companies: Company[] }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [chatId, setChatId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const loadRequestRef = useRef(0);

  const activeCompany = useMemo(() => companies.find((company) => company.id === activeId) ?? companies[0], [activeId, companies]);
  const hasBaseline = Boolean(summary?.readiness?.has_marketing_baseline);

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

  async function ensureChat(companyId: string, requestId: number) {
    const chatsRes = await apiFetch(`/v1/companies/${companyId}/chats`, { accessToken });
    const chatsBody = chatsRes.ok ? await chatsRes.json() : { chats: [] };
    const existing = chatsBody.chats?.[0]?.id;
    if (existing) {
      if (requestId !== loadRequestRef.current) return existing;
      setChatId(existing);
      return existing;
    }
    const createRes = await apiFetch(`/v1/companies/${companyId}/chats`, {
      method: "POST",
      accessToken,
      body: JSON.stringify({ title: "Marketing workspace" }),
    });
    const createBody = await createRes.json();
    if (!createRes.ok) throw new Error(createBody.detail || "Could not create marketing chat");
    if (requestId !== loadRequestRef.current) return createBody.id;
    setChatId(createBody.id);
    return createBody.id;
  }

  async function load(companyId: string) {
    const requestId = ++loadRequestRef.current;
    setLoading(true);
    setMessage(null);
    setChatId(null);
    try {
      const summaryRes = await apiFetch(`/v1/companies/${companyId}/summary`, { accessToken });
      const summaryBody = summaryRes.ok ? await summaryRes.json() : null;
      if (requestId !== loadRequestRef.current) return;
      setSummary(summaryBody);
      if (summaryBody?.readiness?.has_marketing_baseline) {
        await ensureChat(companyId, requestId);
      }
    } catch (error) {
      if (requestId !== loadRequestRef.current) return;
      setMessage(error instanceof Error ? error.message : "Could not load marketing workspace");
    } finally {
      if (requestId !== loadRequestRef.current) return;
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!activeId) return;
    void load(activeId);
  }, [activeId, accessToken]);

  async function saveBaseline(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeId) return;
    setBusy(true);
    setMessage(null);
    const form = new FormData(event.currentTarget);
    try {
      const res = await apiFetch(`/v1/companies/${activeId}/marketing-baseline`, {
        method: "POST",
        accessToken,
        body: JSON.stringify({
          brand_voice_notes: String(form.get("brand_voice_notes") ?? "").trim(),
          design_notes: String(form.get("design_notes") ?? "").trim(),
          campaign_goals: String(form.get("campaign_goals") ?? "").trim(),
          channels: splitList(form.get("channels")),
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Could not save marketing foundation");
      await load(activeId);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save marketing foundation");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Marketing</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">
          {activeCompany?.name ?? "Company"} marketing workspace
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Capture brand and campaign direction, then use chat to brainstorm, draft, refine, and create marketing assets for the selected company.
        </p>
      </section>

      {message ? <div className="rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm text-on-surface">{message}</div> : null}

      {loading ? (
        <div className="rounded-3xl p-8 text-center card-glass">Loading marketing workspace...</div>
      ) : !hasBaseline ? (
        <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-3xl p-7 card-glass">
            <p className="eyebrow">Marketing foundation</p>
            <h2 className="mt-3 font-display text-3xl font-bold tracking-[-0.03em] text-on-surface">Set your baseline once.</h2>
            <p className="mt-3 text-sm leading-7 text-on-surface-variant">
              Add the brand, design, channel, and campaign details you already know. You can keep it light and improve it as you work.
            </p>
          </div>

          <form onSubmit={(event) => void saveBaseline(event)} className="rounded-3xl p-7 card-glass">
            <div className="grid gap-5">
              <label className="grid gap-2 text-sm font-semibold text-on-surface">
                Brand voice notes
                <textarea name="brand_voice_notes" rows={4} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Confident, concise, founder-friendly. Avoid hype." />
              </label>
              <label className="grid gap-2 text-sm font-semibold text-on-surface">
                Design and asset notes
                <textarea name="design_notes" rows={4} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Colors, visual style, examples, formats, or guardrails." />
              </label>
              <label className="grid gap-2 text-sm font-semibold text-on-surface">
                Campaign goals
                <textarea name="campaign_goals" rows={3} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Book demos, announce launch, test ad angles..." />
              </label>
              <label className="grid gap-2 text-sm font-semibold text-on-surface">
                Preferred channels
                <input name="channels" className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="LinkedIn, email, paid social" />
              </label>
            </div>
            <button type="submit" disabled={busy} className="btn-primary mt-6 px-5 py-3 text-sm disabled:opacity-60">
              {busy ? "Saving..." : "Save marketing foundation"}
            </button>
          </form>
        </section>
      ) : chatId ? (
        <MarketingChat chatId={chatId} companyId={activeId ?? ""} accessToken={accessToken} />
      ) : (
        <div className="rounded-3xl p-8 text-center card-glass">Preparing marketing chat...</div>
      )}
    </div>
  );
}
