/**
 * @file apps/web/src/app/(app)/alignment/alignment-workspace.tsx
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductPageHeader,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/lib/sse";

type SourceRow = {
  source: string;
  leads: number;
  won: number;
  revenue: number;
  close_rate_percent: number | null;
};

type Insight = {
  key: string;
  title: string;
  content: { answer?: string };
  citations: string[];
};

type SummaryResponse = {
  alignment: {
    lead_conversion: { by_source: SourceRow[] };
    campaign_revenue: { campaigns: { campaign: string; revenue: number }[] };
    stall_points: {
      top_stall_stages: { stage: string; stalled_count: number }[];
    };
  };
  friction: {
    top_objections: string[];
    top_loss_reasons: { reason: string; count: number }[];
  };
  insights: Insight[];
  icp_version: number | null;
  has_crm_connection: boolean;
};

export function AlignmentWorkspace() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    const res = await apiFetch("/v1/alignment/summary");
    if (res.ok) setSummary(await res.json());
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleRefresh = async () => {
    setRefreshing(true);
    const res = await apiFetch("/v1/alignment/refresh", { method: "POST" });
    if (res.ok) {
      setTimeout(() => {
        void refresh();
        setRefreshing(false);
      }, 3000);
    } else {
      setRefreshing(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setAsking(true);
    setAnswer(null);
    const res = await apiFetch("/v1/conversations/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question.trim() }),
    });
    if (!res.ok) {
      setAsking(false);
      return;
    }
    const data = await res.json();
    const convId = data.conversation_id as string;
    await consumeSse(`/v1/conversations/${convId}/events`, (event) => {
      if (event.status === "completed" && event.answer) {
        setAnswer(event.answer as string);
        setAsking(false);
      }
      if (event.status === "failed") setAsking(false);
    });
  };

  const sources = summary?.alignment?.lead_conversion?.by_source ?? [];
  const campaigns = summary?.alignment?.campaign_revenue?.campaigns ?? [];
  const stalls = summary?.alignment?.stall_points?.top_stall_stages ?? [];
  const frictionInsight = summary?.insights?.find(
    (i) => i.key === "marketing_sales_friction",
  );

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="GTM alignment"
        title="Sales–marketing alignment"
        lead="One intelligence layer both teams trust — same ICP, same proof, same story."
        actions={
          <ProductButton
            variant="secondary"
            onClick={() => void handleRefresh()}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing…" : "Refresh insights"}
          </ProductButton>
        }
      />

      {!summary?.has_crm_connection ? (
        <CompleteDataPrompt
          title="Connect your CRM"
          message="Connect HubSpot or Salesforce in the Data hub to analyze lead quality and revenue attribution."
          missing={["integrations"]}
        />
      ) : null}

      {summary?.icp_version ? (
        <p className="text-sm text-mkt-muted">
          Shared ICP version:{" "}
          <Link href="/agent" className="font-medium text-mkt-ink underline">
            v{summary.icp_version}
          </Link>
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <ProductCard className="bg-violet-50/50">
          <h2 className="text-lg font-semibold text-violet-900">
            Marketing view
          </h2>
          <p className="mt-1 text-sm text-mkt-muted">
            Campaigns driving pipeline
          </p>
          <ul className="mt-4 space-y-2 text-sm">
            {campaigns.length === 0 ? (
              <li className="text-mkt-muted">No campaign revenue data yet.</li>
            ) : (
              campaigns.slice(0, 5).map((c) => (
                <li key={c.campaign} className="flex justify-between">
                  <span>{c.campaign}</span>
                  <span className="font-medium">
                    ${c.revenue.toLocaleString()}
                  </span>
                </li>
              ))
            )}
          </ul>
        </ProductCard>

        <ProductCard className="bg-orange-50/50">
          <h2 className="text-lg font-semibold text-orange-900">Sales view</h2>
          <p className="mt-1 text-sm text-mkt-muted">Lead quality by source</p>
          <ul className="mt-4 space-y-2 text-sm">
            {sources.length === 0 ? (
              <li className="text-mkt-muted">No lead source data yet.</li>
            ) : (
              sources.slice(0, 5).map((s) => (
                <li key={s.source} className="flex justify-between gap-2">
                  <span className="truncate">{s.source}</span>
                  <span className="shrink-0 font-medium">
                    {s.close_rate_percent != null
                      ? `${s.close_rate_percent}% close`
                      : `${s.won} won`}
                  </span>
                </li>
              ))
            )}
          </ul>
        </ProductCard>
      </div>

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">
          Shared intelligence
        </h2>
        {frictionInsight ? (
          <p className="mt-3 text-sm text-mkt-muted">
            {frictionInsight.content?.answer}
          </p>
        ) : (
          <p className="mt-3 text-sm text-mkt-muted">
            Run a refresh after CRM sync to generate the shared friction
            analysis.
          </p>
        )}
        {stalls.length > 0 ? (
          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
              Deal stall points
            </p>
            <ul className="mt-2 space-y-1 text-sm text-mkt-muted">
              {stalls.map((s) => (
                <li key={s.stage}>
                  {s.stage}: {s.stalled_count} stalled deal(s)
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </ProductCard>

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">
          Alignment insights
        </h2>
        <ul className="mt-4 space-y-4">
          {(summary?.insights ?? []).map((ins) => (
            <li
              key={ins.key}
              className="rounded-sm border border-mkt-ink/[0.06] p-4"
            >
              <p className="font-medium text-mkt-ink">{ins.title}</p>
              <p className="mt-2 text-sm text-mkt-muted">
                {ins.content?.answer}
              </p>
            </li>
          ))}
        </ul>
      </ProductCard>

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">
          Ask about alignment
        </h2>
        <div className="mt-4 flex gap-2">
          <ProductInput
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Which lead sources actually convert to revenue?"
            className="flex-1"
          />
          <ProductButton onClick={() => void handleAsk()} disabled={asking}>
            {asking ? "Thinking…" : "Ask"}
          </ProductButton>
        </div>
        {answer ? (
          <p className="mt-4 text-sm text-mkt-muted">{answer}</p>
        ) : null}
      </ProductCard>
    </div>
  );
}
