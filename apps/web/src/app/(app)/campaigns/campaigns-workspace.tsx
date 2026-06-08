"use client";

import { useCallback, useEffect, useState } from "react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import { apiFetch } from "@/lib/api";

type Campaign = {
  id: string;
  brief: string;
  status: string;
  assets?: Record<string, unknown>;
  created_at: string;
};

export function CampaignsWorkspace(()) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [brief, setBrief] = useState("");
  const [selected, setSelected] = useState<Campaign | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [ready, setReady] = useState(true);
  const [missing, setMissing] = useState<string[]>([]);

  const refresh = useCallback(async () => {
    const [campRes, orgRes] = await Promise.all([
      apiFetch("/v1/campaigns", { }),
      apiFetch("/v1/orgs/me", { }),
    ]);
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
    const interval = setInterval(() => void refresh(), 5000);
    return () => clearInterval(interval);
  }, [refresh]);

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
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Campaign Launch</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em]">One brief → full package</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Uses your Data hub profile, ICP, and competitive context. Enter a campaign brief to generate assets.
        </p>
      </div>

      {!ready ? (
        <CompleteDataPrompt
          title="Complete workspace data for better campaigns"
          message="Add customer documents and brand voice in the Data hub so campaigns are grounded in your intelligence."
          missing={missing}
        />
      ) : null}

      <form onSubmit={handleCreate} className="rounded-3xl p-6 card-glass space-y-4">
        <h2 className="font-display text-xl font-bold">New campaign brief</h2>
        <textarea
          className="min-h-[120px] w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm"
          placeholder="We are launching our new AI analytics feature for B2B marketing teams..."
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          required
        />
        <button type="submit" className="btn-primary px-5 py-2 text-sm">Generate campaign</button>
      </form>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Campaigns</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {campaigns.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => setSelected(c)}
                  className="w-full rounded-xl bg-surface-container-low p-4 text-left hover:border-primary/40"
                >
                  <p className="font-semibold text-on-surface truncate">{c.brief.slice(0, 80)}...</p>
                  <p className="text-on-surface-variant">{c.status}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl p-6 card-glass">
          <h2 className="font-display text-xl font-bold">Assets</h2>
          {selected?.assets && Object.keys(selected.assets).length > 0 ? (
            <pre className="mt-4 overflow-auto rounded-xl bg-surface-container-low p-4 text-xs text-on-surface max-h-[500px]">
              {JSON.stringify(selected.assets, null, 2)}
            </pre>
          ) : (
            <p className="mt-4 text-sm text-on-surface-variant">
              {selected ? `Status: ${selected.status}` : "Select a campaign to view assets."}
            </p>
          )}
        </div>
      </div>
      {status ? <p className="text-sm text-on-surface-variant">{status}</p> : null}
    </div>
  );
}
