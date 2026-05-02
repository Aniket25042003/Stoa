"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

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
    <form onSubmit={onSubmit}>
      <label htmlFor="name">Product name (optional)</label>
      <input id="name" value={name} onChange={(e) => setName(e.target.value)} />
      <label htmlFor="website" style={{ marginTop: "0.75rem" }}>
        Website URL
      </label>
      <input id="website" type="url" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} />
      <label htmlFor="target" style={{ marginTop: "0.75rem" }}>
        Target customers
      </label>
      <input id="target" value={targetCustomers} onChange={(e) => setTargetCustomers(e.target.value)} placeholder="e.g. seed-stage B2B SaaS founders" />
      <label htmlFor="geo" style={{ marginTop: "0.75rem" }}>
        Geography
      </label>
      <input id="geo" value={geography} onChange={(e) => setGeography(e.target.value)} placeholder="e.g. US, EU, global" />
      <label htmlFor="competitors" style={{ marginTop: "0.75rem" }}>
        Known competitors (comma-separated)
      </label>
      <input id="competitors" value={knownCompetitors} onChange={(e) => setKnownCompetitors(e.target.value)} />
      <label htmlFor="model" style={{ marginTop: "0.75rem" }}>
        Business model
      </label>
      <input id="model" value={businessModel} onChange={(e) => setBusinessModel(e.target.value)} placeholder="e.g. PLG SaaS, enterprise sales, marketplace" />
      <label htmlFor="stage" style={{ marginTop: "0.75rem" }}>
        Startup stage
      </label>
      <input id="stage" value={stage} onChange={(e) => setStage(e.target.value)} placeholder="e.g. pre-launch, beta, seed" />
      <label htmlFor="horizon" style={{ marginTop: "0.75rem" }}>
        GTM horizon (days)
      </label>
      <input id="horizon" type="number" min={14} max={365} value={horizonDays} onChange={(e) => setHorizonDays(Number(e.target.value))} />
      <label htmlFor="desc" style={{ marginTop: "0.75rem" }}>
        Product description
      </label>
      <textarea id="desc" required minLength={10} rows={8} value={desc} onChange={(e) => setDesc(e.target.value)} />
      <label htmlFor="constraints" style={{ marginTop: "0.75rem" }}>
        Constraints / must-haves (one per line)
      </label>
      <textarea id="constraints" rows={4} value={constraints} onChange={(e) => setConstraints(e.target.value)} />
      {err && <p style={{ color: "#c62828" }}>{err}</p>}
      <p style={{ marginTop: "1rem" }}>
        <button type="submit" disabled={loading}>
          {loading ? "Starting…" : "Start GTM run"}
        </button>
      </p>
    </form>
  );
}
