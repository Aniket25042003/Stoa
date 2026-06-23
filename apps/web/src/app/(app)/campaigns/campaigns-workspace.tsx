/**
 * @file apps/web/src/app/(app)/campaigns/campaigns-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements campaigns workspace behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import {
  ProductButton,
  ProductCard,
  ProductPageHeader,
  ProductStatusPill,
  ProductTextarea,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";

type Campaign = {
  id: string;
  brief: string;
  status: string;
  assets?: Record<string, unknown>;
  created_at: string;
};

const ACTIVE_CAMPAIGN_STATUSES = new Set(["queued", "running"]);

/**
 * Handles campaign needs polling behavior for this part of the Stoa application.
 *
 * @param campaigns - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function campaignNeedsPolling(campaigns: Campaign[]) {
  return campaigns.some((c) => ACTIVE_CAMPAIGN_STATUSES.has(c.status.toLowerCase()));
}

/**
 * Handles campaigns workspace behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function CampaignsWorkspace() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [brief, setBrief] = useState("");
  const [selected, setSelected] = useState<Campaign | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ready, setReady] = useState(true);
  const [missing, setMissing] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    const [campRes, orgRes] = await Promise.all([apiFetch("/v1/campaigns", {}), apiFetch("/v1/orgs/me", {})]);
    if (!campRes.ok && !orgRes.ok) {
      const body = await campRes.json().catch(() => null);
      setLoadError(typeof body?.detail === "string" ? body.detail : "Could not reach the API. Is the backend running?");
      return;
    }
    setLoadError(null);
    if (campRes.ok) setCampaigns((await campRes.json()).campaigns ?? []);
    if (orgRes.ok) {
      const body = await orgRes.json();
      const c = body.completeness;
      setReady(c?.ready_for_campaigns ?? false);
      setMissing(c?.missing ?? []);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!campaignNeedsPolling(campaigns)) return;
    const interval = setInterval(() => void refresh(), 5000);
    return () => clearInterval(interval);
  }, [campaigns, refresh]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const res = await apiFetch("/v1/campaigns", {
      method: "POST",
      body: JSON.stringify({ brief }),
    });
    if (!res.ok) {
      setStatus("Failed to create campaign");
      return;
    }
    const body = await res.json();
    setBrief("");
    setStatus("Campaign generation queued");
    setSelected(body.campaign ?? null);
    void refresh();
  }

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Campaign launch"
        title="One brief → full package"
        lead="Uses your Data hub profile, ICP, and competitive context. Enter a campaign brief to generate assets."
      />

      {!ready ? (
        <CompleteDataPrompt
          title="Complete workspace data for better campaigns"
          message="Add customer documents and brand voice in the Data hub so campaigns are grounded in your intelligence."
          missing={missing}
        />
      ) : null}

      {loadError ? (
        <ProductCard className="border-mkt-accent-warm/25 bg-mkt-accent-warm/[0.06]">
          <p className="text-sm text-mkt-ink">{loadError}</p>
          <p className="mt-2 text-xs text-mkt-muted">
            Start the API with <code className="font-mono">pnpm dev:api</code> (or your usual FastAPI command), then
            refresh this page.
          </p>
        </ProductCard>
      ) : null}

      <ProductCard>
        <form onSubmit={handleCreate} className="space-y-4">
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            New campaign brief
          </h2>
          <ProductTextarea
            className="min-h-[120px]"
            placeholder="We are launching our new AI analytics feature for B2B marketing teams..."
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            required
          />
          <ProductButton type="submit">Generate campaign</ProductButton>
        </form>
      </ProductCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Campaigns</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {campaigns.length === 0 ? (
              <p className="text-mkt-muted">No campaigns yet. Submit a brief to generate your first package.</p>
            ) : (
              campaigns.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => setSelected(c)}
                    className={cn(
                      "w-full rounded-sm border p-4 text-left transition-colors",
                      selected?.id === c.id
                        ? "border-mkt-accent/30 bg-mkt-accent/[0.06]"
                        : "border-mkt-ink/[0.06] bg-mkt-ink/[0.02] hover:border-mkt-accent/20"
                    )}
                  >
                    <p className="truncate font-semibold text-mkt-ink">{c.brief.slice(0, 80)}…</p>
                    <div className="mt-2">
                      <ProductStatusPill status={c.status} />
                    </div>
                  </button>
                </li>
              ))
            )}
          </ul>
        </ProductCard>

        <ProductCard>
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Assets</h2>
            {selected ? <ProductStatusPill status={selected.status} /> : null}
          </div>
          {selected?.assets && Object.keys(selected.assets).length > 0 ? (
            <pre className="mt-4 max-h-[500px] overflow-auto rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 font-mono text-xs text-mkt-ink">
              {JSON.stringify(selected.assets, null, 2)}
            </pre>
          ) : (
            <p className="mt-4 text-sm text-mkt-muted">
              {selected ? `Status: ${selected.status}` : "Select a campaign to view assets."}
            </p>
          )}
        </ProductCard>
      </div>

      {status ? <p className="text-sm text-mkt-muted">{status}</p> : null}
    </div>
  );
}
