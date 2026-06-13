"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/lib/sse";

type Signal = { id: string; kind: string; content: string; confidence: number };
type IcpProfile = { version: number; profile: Record<string, unknown>; signal_count: number };
type PreparedInsight = {
  id: string;
  key: string;
  title: string;
  content: { answer?: string };
  citations: string[];
};

type CrmStats = {
  total_accounts?: number;
  total_deals?: number;
  win_rate_percent?: number | null;
  top_industries?: { name: string; count: number }[];
  top_titles?: { title: string; count: number }[];
  top_loss_reasons?: { reason: string; count: number }[];
};

export function IntelligenceWorkspace() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [profile, setProfile] = useState<IcpProfile | null>(null);
  const [prepared, setPrepared] = useState<PreparedInsight[]>([]);
  const [hasData, setHasData] = useState(true);
  const [crmStats, setCrmStats] = useState<CrmStats | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [docsRes, sigRes, icpRes, insightsRes, dashRes] = await Promise.all([
      apiFetch("/v1/intelligence/documents"),
      apiFetch("/v1/intelligence/signals"),
      apiFetch("/v1/intelligence/icp"),
      apiFetch("/v1/intelligence/insights"),
      apiFetch("/v1/dashboard/summary"),
    ]);
    let docCount = 0;
    if (docsRes.ok) {
      const docs = (await docsRes.json()).documents ?? [];
      docCount = docs.length;
    }
    if (dashRes.ok) {
      const dash = await dashRes.json();
      const counts = dash.counts ?? {};
      const integrations = counts.integrations ?? 0;
      const deals = counts.canonical_deals ?? 0;
      setHasData(docCount > 0 || integrations > 0 || deals > 0);
      setCrmStats(dash.crm_stats ?? null);
    } else {
      setHasData(docCount > 0);
    }
    if (sigRes.ok) setSignals((await sigRes.json()).signals ?? []);
    if (icpRes.ok) {
      const body = await icpRes.json();
      setProfile(body.profile ?? null);
    }
    if (insightsRes.ok) setPrepared((await insightsRes.json()).insights ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setAnswer(null);
    setStatus("Thinking...");
    const res = await apiFetch("/v1/conversations/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      setLoading(false);
      setStatus("Question failed");
      return;
    }
    const body = await res.json();
    const convId = body.conversation_id as string;
    setConversationId(convId);
    const ctrl = new AbortController();
    try {
      await consumeSse(`/v1/conversations/${convId}/events`, (data) => {
          if (data.status === "completed" && typeof data.answer === "string") {
            setAnswer(data.answer);
            setStatus(null);
            setLoading(false);
            ctrl.abort();
          }
          if (data.status === "failed") {
            setStatus("Answer failed");
            setLoading(false);
            ctrl.abort();
          }
        },
        ctrl.signal
      );
    } catch {
      if (!answer) {
        setLoading(false);
        setStatus("Stream ended — check conversation for answer");
      }
    }
  }

  async function refreshInsights() {
    await apiFetch("/v1/intelligence/insights/refresh", { method: "POST" });
    setStatus("Refreshing prepared answers...");
    setTimeout(() => void refresh(), 4000);
  }

  async function rebuildIcp() {
    await apiFetch("/v1/intelligence/icp/rebuild", { method: "POST" });
    setStatus("ICP rebuild queued");
    setTimeout(() => void refresh(), 3000);
  }

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Customer Intelligence</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em]">ICP & Customer Research</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Precomputed answers from your ingested data. Ask follow-up questions with evidence citations.
        </p>
      </div>

      {!hasData ? (
        <CompleteDataPrompt
          title="Add customer data first"
          message="Connect HubSpot, import a CSV, or upload transcripts in the Data hub so we can prepare intelligence answers."
          missing={["documents_or_integration"]}
        />
      ) : null}

      {crmStats && (crmStats.total_accounts || crmStats.total_deals) ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl card-glass p-4">
            <p className="text-xs text-on-surface-variant">Accounts</p>
            <p className="font-display text-2xl font-bold">{crmStats.total_accounts ?? 0}</p>
          </div>
          <div className="rounded-2xl card-glass p-4">
            <p className="text-xs text-on-surface-variant">Deals</p>
            <p className="font-display text-2xl font-bold">{crmStats.total_deals ?? 0}</p>
          </div>
          <div className="rounded-2xl card-glass p-4">
            <p className="text-xs text-on-surface-variant">Win rate</p>
            <p className="font-display text-2xl font-bold">{crmStats.win_rate_percent != null ? `${crmStats.win_rate_percent}%` : "—"}</p>
          </div>
          <div className="rounded-2xl card-glass p-4">
            <p className="text-xs text-on-surface-variant">Top industry</p>
            <p className="font-display text-lg font-bold">{crmStats.top_industries?.[0]?.name ?? "—"}</p>
          </div>
        </div>
      ) : null}

      {prepared.length > 0 ? (
        <div className="rounded-3xl p-6 card-glass space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-display text-xl font-bold">Answers we prepared for you</h2>
            <button type="button" onClick={() => void refreshInsights()} className="btn-secondary px-4 py-2 text-sm">
              Refresh
            </button>
          </div>
          <div className="space-y-3">
            {prepared.map((item) => (
              <div key={item.id} className="rounded-xl bg-surface-container-low p-4">
                <button
                  type="button"
                  className="w-full text-left"
                  onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                >
                  <p className="font-semibold text-on-surface">{item.title}</p>
                </button>
                {expanded === item.id ? (
                  <div className="mt-3 text-sm leading-7 text-on-surface-variant">
                    <p>{item.content?.answer ?? "No answer yet."}</p>
                    {item.citations?.length ? (
                      <p className="mt-2 text-xs text-primary">Citations: {item.citations.join(", ")}</p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : hasData ? (
        <p className="text-sm text-on-surface-variant">Prepared answers will appear after documents are processed.</p>
      ) : null}

      <form onSubmit={handleAsk} className="rounded-3xl p-6 card-glass space-y-4">
        <h2 className="font-display text-xl font-bold">Ask a follow-up</h2>
        <input
          className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm"
          placeholder="Who are our highest-converting customers?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={!hasData}
        />
        <button type="submit" disabled={loading || !hasData} className="btn-primary px-5 py-2 text-sm disabled:opacity-50">
          Ask
        </button>
        {answer ? (
          <div className="rounded-xl bg-surface-container-low p-4 text-sm leading-7 text-on-surface">{answer}</div>
        ) : null}
        {conversationId ? <p className="text-xs text-on-surface-variant">Conversation: {conversationId}</p> : null}
      </form>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">ICP Explorer</h2>
          {profile?.profile ? (
            <div className="mt-4 space-y-3 text-sm">
              {((profile.profile as { top_segments?: { name: string }[] }).top_segments ?? []).slice(0, 5).map((s, i) => (
                <p key={i}><span className="font-semibold">{s.name}</span></p>
              ))}
              {((profile.profile as { structured_crm?: CrmStats }).structured_crm?.top_industries ?? []).map((ind) => (
                <p key={ind.name} className="text-on-surface-variant">{ind.name}: {ind.count} accounts</p>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-on-surface-variant">Connect CRM data to populate ICP segments.</p>
          )}
        </div>
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Pain points & objections</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {signals.filter((s) => s.kind === "pain_point").slice(0, 5).map((s) => (
              <li key={s.id} className="text-on-surface-variant">Pain: {s.content}</li>
            ))}
            {signals.filter((s) => s.kind === "objection").slice(0, 5).map((s) => (
              <li key={s.id} className="text-on-surface-variant">Objection: {s.content}</li>
            ))}
          </ul>
          {crmStats?.top_loss_reasons?.length ? (
            <div className="mt-4 border-t border-outline-variant/40 pt-3">
              <p className="text-xs font-semibold text-on-surface-variant">Win/loss — top loss reasons</p>
              {crmStats.top_loss_reasons.map((r) => (
                <p key={r.reason} className="text-sm text-on-surface-variant">{r.reason} ({r.count})</p>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div className="rounded-3xl p-6 card-glass">
        <div className="flex items-center justify-between gap-4">
          <h2 className="font-display text-xl font-bold">ICP Profile</h2>
          <button type="button" onClick={() => void rebuildIcp()} className="btn-secondary px-4 py-2 text-sm">
            Rebuild ICP
          </button>
        </div>
        {profile ? (
          <pre className="mt-4 overflow-auto rounded-xl bg-surface-container-low p-4 text-xs text-on-surface">
            {JSON.stringify(profile.profile, null, 2)}
          </pre>
        ) : (
          <p className="mt-4 text-sm text-on-surface-variant">No ICP profile yet.</p>
        )}
      </div>

      <div className="rounded-3xl p-6 card-glass">
        <h2 className="font-display text-xl font-bold">Signals ({signals.length})</h2>
        <ul className="mt-4 space-y-2 text-sm">
          {signals.slice(0, 10).map((s) => (
            <li key={s.id} className="text-on-surface-variant">
              <span className="font-mono text-xs text-primary">{s.kind}</span> — {s.content}
            </li>
          ))}
        </ul>
      </div>

      {status ? <p className="text-sm text-on-surface-variant">{status}</p> : null}
    </div>
  );
}
