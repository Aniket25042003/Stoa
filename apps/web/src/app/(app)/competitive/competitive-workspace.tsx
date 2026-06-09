"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import { apiFetch } from "@/lib/api";

type Competitor = { id: string; name: string; website_url?: string | null; last_scanned_at?: string | null };
type Alert = { id: string; summary: string; severity: string; created_at: string; competitors?: { name: string } };

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
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Competitive Intelligence</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em]">Monitor the market</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Alerts and competitor snapshots from data you added in the Data hub.
        </p>
      </div>

      {competitors.length === 0 ? (
        <CompleteDataPrompt
          title="Add competitors in Data hub"
          message="Add competitor names and websites in the Data hub to start monitoring changes."
          missing={["competitors"]}
        />
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Competitors ({competitors.length})</h2>
          <ul className="mt-4 space-y-3 text-sm">
            {competitors.map((c) => (
              <li key={c.id} className="rounded-xl bg-surface-container-low p-4">
                <p className="font-semibold text-on-surface">{c.name}</p>
                <p className="text-on-surface-variant">{c.website_url ?? "No URL"}</p>
                {c.last_scanned_at ? (
                  <p className="mt-1 text-xs text-on-surface-variant">Last scanned: {c.last_scanned_at}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Alerts ({alerts.length})</h2>
          <ul className="mt-4 space-y-3 text-sm">
            {alerts.map((a) => (
              <li key={a.id} className="rounded-xl bg-surface-container-low p-4">
                <p className="font-mono text-xs text-primary">{a.severity}</p>
                <p className="mt-1 text-on-surface">{a.summary}</p>
                <p className="mt-1 text-on-surface-variant">{a.competitors?.name}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
