/**
 * @file apps/web/src/app/(app)/intelligence/intelligence-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements intelligence workspace behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
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
import { formatSignalKindLabel } from "@/lib/user-facing-copy";

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
      <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-mkt-ink">{value}</p>
    </ProductCard>
  );
}

function IcpProfileSummary({ data }: { data: Record<string, unknown> }) {
  const summary = typeof data.summary === "string" ? data.summary : null;
  const segments = Array.isArray(data.top_segments)
    ? (data.top_segments as Array<{ name?: string }>)
    : [];
  const painPoints = Array.isArray(data.top_pain_points)
    ? (data.top_pain_points as Array<{ text?: string }>)
    : [];
  const objections = Array.isArray(data.top_objections)
    ? (data.top_objections as Array<{ text?: string }>)
    : [];

  return (
    <div className="mt-4 space-y-4 text-sm leading-relaxed text-mkt-muted">
      {summary ? <p className="text-mkt-ink">{summary}</p> : null}
      {segments.length > 0 ? (
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Top segments</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {segments.slice(0, 5).map((segment, index) => (
              <li key={index}>{segment.name ?? "Segment"}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {painPoints.length > 0 ? (
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Top pain points</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {painPoints.slice(0, 5).map((item, index) => (
              <li key={index}>{item.text ?? "Pain point"}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {objections.length > 0 ? (
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Top objections</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {objections.slice(0, 5).map((item, index) => (
              <li key={index}>{item.text ?? "Objection"}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {!summary && segments.length === 0 && painPoints.length === 0 && objections.length === 0 ? (
        <p>Your ICP profile is being prepared from customer data.</p>
      ) : null}
    </div>
  );
}

/**
 * Handles intelligence workspace behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function IntelligenceWorkspace() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [profile, setProfile] = useState<IcpProfile | null>(null);
  const [prepared, setPrepared] = useState<PreparedInsight[]>([]);
  const [hasData, setHasData] = useState(true);
  const [crmStats, setCrmStats] = useState<CrmStats | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
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
                <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
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
                      <p className="text-sm font-semibold text-mkt-ink">{item.title}</p>
                    </button>
                    {expanded === item.id ? (
                      <div className="mt-3 text-sm leading-relaxed text-mkt-muted">
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
            <p className="text-sm text-mkt-muted">
              Prepared answers will appear after documents are processed.
            </p>
          ) : null}

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-1">
            <ProductCard>
              <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">ICP explorer</h2>
              {profile?.profile ? (
                <div className="mt-4 space-y-3 text-sm">
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
                <p className="mt-4 text-sm text-mkt-muted">
                  Connect CRM data to populate ICP segments.
                </p>
              )}
            </ProductCard>

            <ProductCard>
              <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
                Pain points & objections
              </h2>
              <ul className="mt-4 space-y-2 text-sm">
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
                  <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                    Win/loss — top loss reasons
                  </p>
                  {crmStats.top_loss_reasons.map((r) => (
                    <p key={r.reason} className="mt-1 text-sm text-mkt-muted">
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
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Ask a follow-up</h2>
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
              <div className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 text-sm leading-relaxed text-mkt-ink">
                {answer}
              </div>
            ) : null}
          </ProductCard>

          <ProductCard>
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">ICP profile</h2>
              <ProductButton variant="secondary" onClick={() => void rebuildIcp()}>
                Rebuild ICP
              </ProductButton>
            </div>
            {profile?.profile ? (
              <IcpProfileSummary data={profile.profile} />
            ) : (
              <p className="mt-4 text-sm text-mkt-muted">No ICP profile yet.</p>
            )}
          </ProductCard>

          <ProductCard>
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
              Signals ({signals.length})
            </h2>
            <ul className="mt-4 space-y-2 text-sm">
              {signals.slice(0, 10).map((s) => (
                <li key={s.id} className="flex flex-wrap items-baseline gap-2 text-mkt-muted">
                  <ProductBadge variant="accent">{formatSignalKindLabel(s.kind)}</ProductBadge>
                  <span>{s.content}</span>
                </li>
              ))}
            </ul>
          </ProductCard>
        </div>
      </div>

      {status ? <p className="text-sm text-mkt-muted">{status}</p> : null}
    </div>
  );
}
