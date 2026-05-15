"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ACTIVE_COMPANY_EVENT, getStoredActiveCompanyId, setStoredActiveCompanyId } from "@/lib/active-company";

type Company = {
  id: string;
  name: string;
  description?: string | null;
};

type GtmPlan = {
  id: string;
  title: string;
  source: "generated" | "uploaded";
  content_markdown: string;
  updated_at?: string;
};

type GtmMessage = {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
};

export function GtmWorkspace({ accessToken, companies }: { accessToken: string; companies: Company[] }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [plan, setPlan] = useState<GtmPlan | null>(null);
  const [messages, setMessages] = useState<GtmMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const uploadRef = useRef<HTMLTextAreaElement | null>(null);
  const loadRequestRef = useRef(0);

  const activeCompany = useMemo(() => companies.find((company) => company.id === activeId) ?? companies[0], [activeId, companies]);

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

  async function loadPlan(companyId: string) {
    const requestId = ++loadRequestRef.current;
    setLoading(true);
    setNotice(null);
    try {
      const res = await apiFetch(`/v1/companies/${companyId}/gtm-plan`, { accessToken });
      const body = res.ok ? await res.json() : { plan: null, messages: [] };
      if (requestId !== loadRequestRef.current) return;
      setPlan(body.plan ?? null);
      setMessages(body.messages ?? []);
    } catch {
      if (requestId !== loadRequestRef.current) return;
      setPlan(null);
      setMessages([]);
      setNotice("Could not load the GTM workspace.");
    } finally {
      if (requestId !== loadRequestRef.current) return;
      setLoading(false);
    }
  }

  useEffect(() => {
    if (activeId) void loadPlan(activeId);
  }, [activeId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function generatePlan() {
    if (!activeId) return;
    setBusy(true);
    setNotice(null);
    try {
      const res = await apiFetch(`/v1/companies/${activeId}/gtm-plan/generate`, {
        method: "POST",
        accessToken,
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Could not start GTM plan");
      setNotice("Your GTM plan has started. Open the plan status page to review and approve it.");
      setMessages((cur) => [...cur, { role: "system", content: "GTM plan generation started." }]);
      if (body.run_id) {
        setMessages((cur) => [...cur, { role: "assistant", content: `Open the status page when you are ready: /runs/${body.run_id}` }]);
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not start GTM plan");
    } finally {
      setBusy(false);
    }
  }

  async function uploadPlan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeId) return;
    const form = new FormData(event.currentTarget);
    const content = String(form.get("content_markdown") ?? "").trim();
    const title = String(form.get("title") ?? "GTM plan").trim() || "GTM plan";
    if (content.length < 20) {
      setNotice("Paste a GTM plan with at least 20 characters.");
      return;
    }
    setBusy(true);
    setNotice(null);
    try {
      const res = await apiFetch(`/v1/companies/${activeId}/gtm-plan/upload`, {
        method: "POST",
        accessToken,
        body: JSON.stringify({ title, content_markdown: content }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Could not upload GTM plan");
      setPlan(body.plan);
      setMessages([{ role: "system", content: "Uploaded an existing GTM plan." }]);
      if (uploadRef.current) uploadRef.current.value = "";
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not upload GTM plan");
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeId || !plan) return;
    const form = new FormData(event.currentTarget);
    const content = String(form.get("content") ?? "").trim();
    if (!content) return;
    event.currentTarget.reset();
    setBusy(true);
    setMessages((cur) => [...cur, { role: "user", content }]);
    try {
      const res = await apiFetch(`/v1/companies/${activeId}/gtm-plan/messages`, {
        method: "POST",
        accessToken,
        body: JSON.stringify({ content }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Could not update plan");
      setPlan(body.plan);
      setMessages((cur) => [...cur, body.assistant]);
    } catch (error) {
      setMessages((cur) => [...cur, { role: "assistant", content: error instanceof Error ? error.message : "Could not update plan" }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">GTM</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">
          {activeCompany?.name ?? "Company"} GTM workspace
        </h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Generate a plan, upload an existing one, then chat through changes while keeping context tied to the selected company.
        </p>
      </section>

      {notice ? <div className="rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm text-on-surface">{notice}</div> : null}

      {loading ? (
        <div className="rounded-3xl p-8 text-center card-glass">Loading GTM workspace...</div>
      ) : !plan ? (
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl p-7 card-glass">
            <p className="eyebrow">Option one</p>
            <h2 className="mt-3 font-display text-3xl font-bold tracking-[-0.03em] text-on-surface">Generate a GTM plan</h2>
            <p className="mt-3 text-sm leading-7 text-on-surface-variant">
              Use your company profile to create a first plan for review. You can approve, revise, and keep improving it from here.
            </p>
            <button type="button" disabled={busy} onClick={() => void generatePlan()} className="btn-primary mt-6 px-5 py-3 text-sm disabled:opacity-60">
              {busy ? "Starting..." : "Generate GTM plan"}
            </button>
          </div>

          <form onSubmit={(event) => void uploadPlan(event)} className="rounded-3xl p-7 card-glass">
            <p className="eyebrow">Option two</p>
            <h2 className="mt-3 font-display text-3xl font-bold tracking-[-0.03em] text-on-surface">Upload your own plan</h2>
            <label className="mt-5 grid gap-2 text-sm font-semibold text-on-surface">
              Plan title
              <input name="title" defaultValue={`${activeCompany?.name ?? "Company"} GTM plan`} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" />
            </label>
            <label className="mt-4 grid gap-2 text-sm font-semibold text-on-surface">
              Plan content
              <textarea ref={uploadRef} name="content_markdown" rows={10} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Paste your existing GTM plan..." />
            </label>
            <button type="submit" disabled={busy} className="btn-secondary mt-5 px-5 py-3 text-sm disabled:opacity-60">
              {busy ? "Saving..." : "Save uploaded plan"}
            </button>
          </form>
        </section>
      ) : (
        <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-3xl p-6 card-glass md:p-7">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="eyebrow">Active plan</p>
                <h2 className="mt-2 font-display text-3xl font-bold tracking-[-0.03em] text-on-surface">{plan.title}</h2>
                <p className="mt-2 text-sm text-on-surface-variant">Source: {plan.source === "uploaded" ? "uploaded by you" : "generated from company context"}</p>
              </div>
              <button type="button" disabled={busy} onClick={() => void generatePlan()} className="btn-secondary px-4 py-2 text-sm disabled:opacity-60">
                Generate another
              </button>
            </div>
            <pre className="mt-6 max-h-[620px] overflow-auto whitespace-pre-wrap rounded-2xl bg-surface-container-low p-5 font-mono text-xs leading-6 text-on-surface-variant">
              {plan.content_markdown}
            </pre>
          </div>

          <div className="rounded-3xl p-6 card-glass md:p-7">
            <p className="eyebrow">Plan chat</p>
            <div className="mt-5 max-h-[520px] space-y-3 overflow-auto pr-1">
              {messages.filter((message) => message.role !== "system").map((message, index) => (
                <div key={`${message.role}-${index}`} className={message.role === "user" ? "ml-auto max-w-[86%] rounded-2xl bg-primary px-4 py-3 text-sm text-white" : "max-w-[86%] rounded-2xl bg-surface-container-low px-4 py-3 text-sm text-on-surface"}>
                  {message.content}
                </div>
              ))}
              {messages.filter((message) => message.role !== "system").length === 0 ? (
                <p className="rounded-2xl bg-surface-container-low px-4 py-3 text-sm text-on-surface-variant">
                  Ask for plan changes, positioning refinements, ICP edits, or channel priorities.
                </p>
              ) : null}
            </div>
            <form onSubmit={(event) => void sendMessage(event)} className="mt-5 flex gap-2">
              <input name="content" disabled={busy} className="min-w-0 flex-1 rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 text-sm outline-none focus:border-primary" placeholder="Ask the GTM workspace to update the plan..." />
              <button type="submit" disabled={busy} className="btn-primary px-5 py-3 text-sm disabled:opacity-60">
                Send
              </button>
            </form>
          </div>
        </section>
      )}
    </div>
  );
}
