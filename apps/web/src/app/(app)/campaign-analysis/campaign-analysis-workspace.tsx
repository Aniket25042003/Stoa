/**
 * @file apps/web/src/app/(app)/campaign-analysis/campaign-analysis-workspace.tsx
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductPageHeader,
} from "@/components/product";
import { InsightMarkdown } from "@/components/product/InsightMarkdown";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/lib/sse";

type ChannelRow = {
  channel: string;
  sessions: number;
  conversions: number;
  conversion_rate_percent: number | null;
};

type Insight = {
  key: string;
  title: string;
  content: { answer?: string };
  citations: string[];
};

type SummaryResponse = {
  metrics: {
    channels: { channels: ChannelRow[]; top_channel: ChannelRow | null };
    campaigns: { campaigns: { campaign: string; conversions: number }[]; best_campaign: { campaign: string } | null };
    has_data: boolean;
  };
  insights: Insight[];
  has_analytics_connection: boolean;
};

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <ProductCard className="p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-mkt-ink">{value}</p>
    </ProductCard>
  );
}

export function CampaignAnalysisWorkspace() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    const res = await apiFetch("/v1/campaign-analysis/summary");
    if (res.ok) setSummary(await res.json());
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleRefresh = async () => {
    setRefreshing(true);
    const res = await apiFetch("/v1/campaign-analysis/refresh", { method: "POST" });
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

  const channels = summary?.metrics?.channels?.channels ?? [];
  const topChannel = summary?.metrics?.channels?.top_channel;
  const bestCampaign = summary?.metrics?.campaigns?.best_campaign;

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Performance"
        title="Campaign analysis"
        lead="See what worked and why — backed by GA4, PostHog, and stored evidence."
        actions={
          <ProductButton variant="secondary" onClick={() => void handleRefresh()} disabled={refreshing}>
            {refreshing ? "Refreshing…" : "Refresh insights"}
          </ProductButton>
        }
      />

      {!summary?.has_analytics_connection ? (
        <CompleteDataPrompt
          title="Connect analytics"
          message="Connect GA4 or PostHog in the Data hub integrations tab to analyze campaign performance."
          missing={["integrations"]}
        />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Top channel" value={topChannel?.channel ?? "—"} />
        <StatCard
          label="Channel conv. rate"
          value={topChannel?.conversion_rate_percent != null ? `${topChannel.conversion_rate_percent}%` : "—"}
        />
        <StatCard label="Best campaign" value={bestCampaign?.campaign ?? "—"} />
      </div>

      {channels.length > 0 ? (
        <ProductCard>
          <h2 className="text-lg font-semibold text-mkt-ink">Channel performance</h2>
          <div className="mt-4 flex items-end gap-2 h-32">
            {channels.slice(0, 8).map((ch) => {
              const maxSessions = Math.max(...channels.map((c) => c.sessions), 1);
              const height = Math.max(8, (ch.sessions / maxSessions) * 100);
              return (
                <div key={ch.channel} className="flex flex-1 flex-col items-center gap-1">
                  <div
                    className="w-full rounded-t bg-gradient-to-t from-rose-300 to-rose-200"
                    style={{ height: `${height}%` }}
                    title={`${ch.sessions} sessions`}
                  />
                  <span className="max-w-full truncate text-[10px] text-mkt-muted">{ch.channel}</span>
                </div>
              );
            })}
          </div>
        </ProductCard>
      ) : null}

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">Precomputed insights</h2>
        <ul className="mt-4 space-y-4">
          {(summary?.insights ?? []).length === 0 ? (
            <p className="text-sm text-mkt-muted">
              No insights yet. Connect analytics and run a refresh after sync completes.
            </p>
          ) : (
            summary?.insights.map((ins) => (
              <li key={ins.key} className="rounded-sm border border-mkt-ink/[0.06] p-4">
                <p className="font-medium text-mkt-ink">{ins.title}</p>
                <InsightMarkdown contextualTitle={ins.title} className="mt-2">
                  {ins.content?.answer ?? ""}
                </InsightMarkdown>
              </li>
            ))
          )}
        </ul>
      </ProductCard>

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">Ask about performance</h2>
        <div className="mt-4 flex gap-2">
          <ProductInput
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Why did LinkedIn outperform email last month?"
            className="flex-1"
          />
          <ProductButton onClick={() => void handleAsk()} disabled={asking}>
            {asking ? "Thinking…" : "Ask"}
          </ProductButton>
        </div>
        {answer ? <InsightMarkdown className="mt-4">{answer}</InsightMarkdown> : null}
      </ProductCard>
    </div>
  );
}
