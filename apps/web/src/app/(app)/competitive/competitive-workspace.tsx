/**
 * @file apps/web/src/app/(app)/competitive/competitive-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements competitive workspace behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import { ProductBadge, ProductCard, ProductPageHeader } from "@/components/product";
import { apiFetch } from "@/lib/api";

type Competitor = { id: string; name: string; website_url?: string | null; last_scanned_at?: string | null };
type Alert = { id: string; summary: string; severity: string; created_at: string; competitors?: { name: string } };

/**
 * Handles severity variant behavior for this part of the Stoa application.
 *
 * @param severity - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function severityVariant(severity: string): "warm" | "accent" | "default" {
  const s = severity.toLowerCase();
  if (s.includes("high") || s.includes("critical")) return "warm";
  if (s.includes("medium") || s.includes("med")) return "accent";
  return "default";
}

/**
 * Handles competitive workspace behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function CompetitiveWorkspace() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const refresh = useCallback(async () => {
    const [compRes, alertRes] = await Promise.all([
      apiFetch("/v1/competitive/competitors"),
      apiFetch("/v1/competitive/alerts"),
    ]);
    if (compRes.ok) setCompetitors((await compRes.json()).competitors ?? []);
    if (alertRes.ok) setAlerts((await alertRes.json()).alerts ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Competitive intelligence"
        title="Monitor the market"
        lead="Alerts and competitor snapshots from data you added in the Data hub."
      />

      {competitors.length === 0 ? (
        <CompleteDataPrompt
          title="Add competitors in Data hub"
          message="Add competitor names and websites in the Data hub to start monitoring changes."
          missing={["competitors"]}
        />
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            Competitors ({competitors.length})
          </h2>
          <ul className="mt-4 space-y-3 text-sm">
            {competitors.map((c) => (
              <li key={c.id} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4">
                <p className="font-semibold text-mkt-ink">{c.name}</p>
                <p className="text-mkt-muted">{c.website_url ?? "No URL"}</p>
                {c.last_scanned_at ? (
                  <p className="mt-1 text-xs text-mkt-muted">
                    Last scanned: {new Date(c.last_scanned_at).toLocaleString()}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </ProductCard>

        <ProductCard>
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            Alerts ({alerts.length})
          </h2>
          <ul className="mt-4 space-y-3 text-sm">
            {alerts.length === 0 ? (
              <p className="text-mkt-muted">No alerts yet. Scans run after competitors are added.</p>
            ) : (
              alerts.map((a) => (
                <li
                  key={a.id}
                  className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4"
                >
                  <ProductBadge variant={severityVariant(a.severity)}>{a.severity}</ProductBadge>
                  <p className="mt-2 font-medium text-mkt-ink">{a.summary}</p>
                  {a.competitors?.name ? <p className="mt-1 text-mkt-muted">{a.competitors.name}</p> : null}
                  <p className="mt-1 text-xs text-mkt-muted">{new Date(a.created_at).toLocaleString()}</p>
                </li>
              ))
            )}
          </ul>
        </ProductCard>
      </div>
    </div>
  );
}
