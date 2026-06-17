"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import {
  ProductBadge,
  ProductButton,
  ProductCard,
  ProductInput,
  ProductPageHeader,
} from "@/components/product";
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

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <ProductCard className="p-4">
      <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-muted">{label}</p>
      <p className="mt-1 font-syne text-2xl font-extrabold text-mkt-accent">{value}</p>
    </ProductCard>
  );
}

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
      await consumeSse(
        `/v1/conversations/${convId}/events`,
        (data) => {
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
      <ProductPageHeader
        eyebrow="Customer intelligence"
        title="ICP & customer research"
        lead="Precomputed answers from your ingested data. Ask follow-up questions with evidence citations."
      />

      {!hasData ? (
        <CompleteDataPrompt
          title="Add customer data first"
          message="Connect HubSpot, import a CSV, or upload transcripts in the Data hub so we can prepare intelligence answers."
          missing={["documents_or_integration"]}
        />
      ) : null}

      {crmStats && (crmStats.total_accounts || crmStats.total_deals) ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Accounts" value={crmStats.total_accounts ?? 0} />
          <StatCard label="Deals" value={crmStats.total_deals ?? 0} />
          <StatCard
            label="Win rate"
            value={crmStats.win_rate_percent != null ? `${crmStats.win_rate_percent}%` : "—"}
          />
          <StatCard label="Top industry" value={crmStats.top_industries?.[0]?.name ?? "—"} />
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <div className="space-y-6">
          {prepared.length > 0 ? (
            <ProductCard className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">
                  Prepared answers
                </h2>
                <ProductButton variant="secondary" onClick={() => void refreshInsights()}>
                  Refresh
                </ProductButton>
              </div>
              <div className="space-y-3">
                {prepared.map((item) => (
                  <div key={item.id} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4">
                    <button
                      type="button"
                      className="w-full text-left"
                      onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                    >
                      <p className="font-dm-sans text-sm font-semibold text-mkt-ink">{item.title}</p>
                    </button>
                    {expanded === item.id ? (
                      <div className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted">
                        <p>{item.content?.answer ?? "No answer yet."}</p>
                        {item.citations?.length ? (
                          <div className="mt-3 flex flex-wrap gap-1.5">
                            {item.citations.map((c) => (
                              <ProductBadge key={c} variant="accent">
                                {c}
                              </ProductBadge>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </ProductCard>
          ) : hasData ? (
            <p className="font-dm-sans text-sm text-mkt-muted">
              Prepared answers will appear after documents are processed.
            </p>
          ) : null}

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-1">
            <ProductCard>
              <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">ICP explorer</h2>
              {profile?.profile ? (
                <div className="mt-4 space-y-3 font-dm-sans text-sm">
                  {((profile.profile as { top_segments?: { name: string }[] }).top_segments ?? [])
                    .slice(0, 5)
                    .map((s, i) => (
                      <p key={i} className="font-semibold text-mkt-ink">
                        {s.name}
                      </p>
                    ))}
                  {((profile.profile as { structured_crm?: CrmStats }).structured_crm?.top_industries ?? []).map(
                    (ind) => (
                      <p key={ind.name} className="text-mkt-muted">
                        {ind.name}: {ind.count} accounts
                      </p>
                    )
                  )}
                </div>
              ) : (
                <p className="mt-4 font-dm-sans text-sm text-mkt-muted">
                  Connect CRM data to populate ICP segments.
                </p>
              )}
            </ProductCard>

            <ProductCard>
              <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">
                Pain points & objections
              </h2>
              <ul className="mt-4 space-y-2 font-dm-sans text-sm">
                {signals
                  .filter((s) => s.kind === "pain_point")
                  .slice(0, 5)
                  .map((s) => (
                    <li key={s.id} className="text-mkt-muted">
                      Pain: {s.content}
                    </li>
                  ))}
                {signals
                  .filter((s) => s.kind === "objection")
                  .slice(0, 5)
                  .map((s) => (
                    <li key={s.id} className="text-mkt-muted">
                      Objection: {s.content}
                    </li>
                  ))}
              </ul>
              {crmStats?.top_loss_reasons?.length ? (
                <div className="mt-4 border-t border-mkt-ink/[0.06] pt-3">
                  <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-muted">
                    Win/loss — top loss reasons
                  </p>
                  {crmStats.top_loss_reasons.map((r) => (
                    <p key={r.reason} className="mt-1 font-dm-sans text-sm text-mkt-muted">
                      {r.reason} ({r.count})
                    </p>
                  ))}
                </div>
              ) : null}
            </ProductCard>
          </div>
        </div>

        <div className="space-y-6">
          <ProductCard className="space-y-4">
            <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Ask a follow-up</h2>
            <form onSubmit={handleAsk} className="space-y-4">
              <ProductInput
                placeholder="Who are our highest-converting customers?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={!hasData}
              />
              <ProductButton type="submit" disabled={loading || !hasData}>
                {loading ? "Thinking…" : "Ask"}
              </ProductButton>
            </form>
            {answer ? (
              <div className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 font-dm-sans text-sm leading-relaxed text-mkt-ink">
                {answer}
              </div>
            ) : null}
            {conversationId ? (
              <p className="font-dm-sans text-xs text-mkt-muted">Conversation: {conversationId}</p>
            ) : null}
          </ProductCard>

          <ProductCard>
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">ICP profile</h2>
              <ProductButton variant="secondary" onClick={() => void rebuildIcp()}>
                Rebuild ICP
              </ProductButton>
            </div>
            {profile ? (
              <pre className="mt-4 max-h-64 overflow-auto rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 font-mono text-xs text-mkt-ink">
                {JSON.stringify(profile.profile, null, 2)}
              </pre>
            ) : (
              <p className="mt-4 font-dm-sans text-sm text-mkt-muted">No ICP profile yet.</p>
            )}
          </ProductCard>

          <ProductCard>
            <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">
              Signals ({signals.length})
            </h2>
            <ul className="mt-4 space-y-2 font-dm-sans text-sm">
              {signals.slice(0, 10).map((s) => (
                <li key={s.id} className="flex flex-wrap items-baseline gap-2 text-mkt-muted">
                  <ProductBadge variant="accent">{s.kind}</ProductBadge>
                  <span>{s.content}</span>
                </li>
              ))}
            </ul>
          </ProductCard>
        </div>
      </div>

      {status ? <p className="font-dm-sans text-sm text-mkt-muted">{status}</p> : null}
    </div>
  );
}
