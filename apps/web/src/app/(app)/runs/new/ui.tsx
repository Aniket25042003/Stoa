"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

const field = "mt-2 block input-field px-3 py-3 text-sm";
const label = "eyebrow text-[11px]";

export function NewRunForm({ accessToken }: { accessToken: string }) {
  const router = useRouter();
  const [desc, setDesc] = useState("");
  const [name, setName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [targetCustomers, setTargetCustomers] = useState("");
  const [geography, setGeography] = useState("");
  const [knownCompetitors, setKnownCompetitors] = useState("");
  const [businessModel, setBusinessModel] = useState("");
  const [stage, setStage] = useState("");
  const [constraints, setConstraints] = useState("");
  const [horizonDays, setHorizonDays] = useState(90);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await apiFetch("/v1/runs", {
        method: "POST",
        accessToken,
        body: JSON.stringify({
          product_description: desc,
          product_name: name || undefined,
          website_url: websiteUrl || undefined,
          target_customers: targetCustomers || undefined,
          geography: geography || undefined,
          known_competitors: knownCompetitors
            .split(",")
            .map((c) => c.trim())
            .filter(Boolean),
          business_model: businessModel || undefined,
          stage: stage || undefined,
          constraints: constraints
            .split("\n")
            .map((c) => c.trim())
            .filter(Boolean),
          horizon_days: horizonDays,
        }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || res.statusText);
      }
      const data = await res.json();
      router.push(`/runs/${data.id}`);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Failed to create run");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label htmlFor="name" className={label}>Product name (optional)</label>
          <input id="name" className={field} value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label htmlFor="website" className={label}>Website URL</label>
          <input id="website" type="url" className={field} value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} />
        </div>
        <div>
          <label htmlFor="target" className={label}>Target customers</label>
          <input id="target" className={field} value={targetCustomers} onChange={(e) => setTargetCustomers(e.target.value)} placeholder="e.g. seed-stage B2B SaaS founders" />
        </div>
        <div>
          <label htmlFor="geo" className={label}>Geography</label>
          <input id="geo" className={field} value={geography} onChange={(e) => setGeography(e.target.value)} placeholder="e.g. US, EU, global" />
        </div>
        <div>
          <label htmlFor="competitors" className={label}>Known competitors</label>
          <input id="competitors" className={field} value={knownCompetitors} onChange={(e) => setKnownCompetitors(e.target.value)} placeholder="Comma-separated" />
        </div>
        <div>
          <label htmlFor="model" className={label}>Business model</label>
          <input id="model" className={field} value={businessModel} onChange={(e) => setBusinessModel(e.target.value)} placeholder="e.g. PLG SaaS, enterprise sales" />
        </div>
        <div>
          <label htmlFor="stage" className={label}>Startup stage</label>
          <input id="stage" className={field} value={stage} onChange={(e) => setStage(e.target.value)} placeholder="e.g. pre-launch, beta, seed" />
        </div>
        <div>
          <label htmlFor="horizon" className={label}>GTM horizon (days)</label>
          <input id="horizon" type="number" min={14} max={365} className={field} value={horizonDays} onChange={(e) => setHorizonDays(Number(e.target.value))} />
        </div>
      </div>

      <div>
        <label htmlFor="desc" className={label}>Product description</label>
        <textarea id="desc" required minLength={10} rows={8} className={field} value={desc} onChange={(e) => setDesc(e.target.value)} />
      </div>
      <div>
        <label htmlFor="constraints" className={label}>Constraints / must-haves</label>
        <textarea id="constraints" rows={4} className={field} value={constraints} onChange={(e) => setConstraints(e.target.value)} placeholder="One per line" />
      </div>
      {err ? <p className="rounded-2xl border border-error/20 bg-error-container px-4 py-3 text-sm text-error">{err}</p> : null}
      <div className="pt-2">
        <button type="submit" disabled={loading} className="btn-primary px-5 py-3 text-sm disabled:opacity-50">
          {loading ? "Creating plan..." : "Create master plan"}
        </button>
      </div>
    </form>
  );
}
