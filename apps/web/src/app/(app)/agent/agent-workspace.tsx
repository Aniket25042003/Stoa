"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ProductBadge,
  ProductButton,
  ProductCard,
  ProductInput,
  ProductPageHeader,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/lib/sse";

type DashboardSummary = {
  core_feature_metrics?: {
    icp_customer_research?: {
      best_customer_segment?: string | null;
      deals?: number;
    };
    content_bottleneck?: { status_breakdown?: Record<string, number> };
    competitive_intelligence?: {
      tracked_competitors?: number;
      recent_alerts?: number;
    };
    launch_orchestration?: {
      campaign_count?: number;
      status_breakdown?: Record<string, number>;
    };
    campaign_analysis?: {
      top_channel?: string | null;
      top_campaign?: string | null;
    };
    sales_marketing_alignment?: { top_lead_source?: string | null };
  };
};

const QUICK_PROMPTS = [
  "Who was our best customer segment last quarter and why?",
  "Where is our content production bottleneck right now?",
  "What changed across competitors this week?",
  "Which campaigns should we prioritize for the next launch?",
  "Which channels are driving best conversion efficiency?",
  "Where are sales and marketing misaligned in our funnel?",
];

export function AgentWorkspace() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [usedTools, setUsedTools] = useState<string[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const res = await apiFetch("/v1/dashboard/summary");
      if (res.ok) setDashboard(await res.json());
    })();
  }, []);

  const topSignals = useMemo(() => {
    const m = dashboard?.core_feature_metrics;
    if (!m) return [];
    return [
      `Best segment: ${m.icp_customer_research?.best_customer_segment ?? "—"}`,
      `Deals: ${m.icp_customer_research?.deals ?? 0}`,
      `Competitors tracked: ${m.competitive_intelligence?.tracked_competitors ?? 0}`,
      `Top channel: ${m.campaign_analysis?.top_channel ?? "—"}`,
      `Top campaign: ${m.campaign_analysis?.top_campaign ?? "—"}`,
      `Top lead source: ${m.sales_marketing_alignment?.top_lead_source ?? "—"}`,
    ];
  }, [dashboard]);

  async function ask(prompt: string) {
    const q = prompt.trim();
    if (!q) return;

    setQuestion(q);
    setAsking(true);
    setStatus("Thinking...");
    setAnswer(null);
    setUsedTools([]);

    const res = await apiFetch("/v1/conversations/ask", {
      method: "POST",
      body: JSON.stringify({ question: q, conversation_id: conversationId }),
    });

    if (!res.ok) {
      setStatus("Request failed. Please try again.");
      setAsking(false);
      return;
    }

    const body = await res.json();
    const nextConversationId = body.conversation_id as string;
    setConversationId(nextConversationId);

    const ctrl = new AbortController();
    try {
      await consumeSse(
        `/v1/conversations/${nextConversationId}/events`,
        (event) => {
          if (
            event.status === "tool_summary" &&
            Array.isArray(event.used_tools)
          ) {
            setUsedTools(event.used_tools as string[]);
          }
          if (
            event.status === "completed" &&
            typeof event.answer === "string"
          ) {
            setAnswer(event.answer);
            setStatus(null);
            setAsking(false);
            ctrl.abort();
          }
          if (event.status === "failed") {
            setStatus("Agent failed. Please retry.");
            setAsking(false);
            ctrl.abort();
          }
        },
        ctrl.signal,
      );
    } catch {
      setAsking(false);
      setStatus(
        (prev) =>
          prev ?? "Stream closed. Open conversation history for full context.",
      );
    }
  }

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Unified workspace"
        title="GTM Agent"
        lead="One agent across ICP research, content bottlenecks, competitive intelligence, launch orchestration, campaign analysis, and sales-marketing alignment."
      />

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">Ask the agent</h2>
        <div className="mt-4 flex gap-2">
          <ProductInput
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything across your six GTM features..."
            className="flex-1"
          />
          <ProductButton onClick={() => void ask(question)} disabled={asking}>
            {asking ? "Thinking…" : "Ask"}
          </ProductButton>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => void ask(p)}
              className="rounded-sm border border-mkt-ink/[0.08] px-3 py-1.5 text-xs text-mkt-muted hover:border-mkt-accent/30 hover:bg-mkt-accent/[0.06] hover:text-mkt-ink"
            >
              {p}
            </button>
          ))}
        </div>

        {usedTools.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {usedTools.map((tool) => (
              <ProductBadge key={tool} variant="accent">
                {tool}
              </ProductBadge>
            ))}
          </div>
        ) : null}

        {answer ? (
          <div className="mt-4 rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 text-sm leading-relaxed text-mkt-ink">
            {answer}
          </div>
        ) : null}

        {status ? (
          <p className="mt-3 text-sm text-mkt-muted">{status}</p>
        ) : null}
      </ProductCard>

      <ProductCard>
        <h2 className="text-lg font-semibold text-mkt-ink">
          Cross-feature metrics snapshot
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {topSignals.map((item) => (
            <div
              key={item}
              className="rounded-sm border border-mkt-ink/[0.06] p-3 text-sm text-mkt-muted"
            >
              {item}
            </div>
          ))}
        </div>
      </ProductCard>
    </div>
  );
}
