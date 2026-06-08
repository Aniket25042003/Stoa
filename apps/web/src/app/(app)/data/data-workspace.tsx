"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Org = {
  id: string;
  name: string;
  website_url?: string | null;
  industry?: string | null;
  profile?: Record<string, string>;
};

type Completeness = {
  percent: number;
  completed: number;
  total: number;
  missing: string[];
  checks: Record<string, boolean>;
};

type Document = { id: string; title: string; doc_type: string; status: string };
type Competitor = { id: string; name: string; website_url?: string | null };

export function DataWorkspace() {
  const [org, setOrg] = useState<Org | null>(null);
  const [completeness, setCompleteness] = useState<Completeness | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [industry, setIndustry] = useState("");
  const [targetCustomers, setTargetCustomers] = useState("");
  const [businessModel, setBusinessModel] = useState("");
  const [stage, setStage] = useState("");
  const [goals, setGoals] = useState("");
  const [brandVoice, setBrandVoice] = useState("");
  const [competitorNotes, setCompetitorNotes] = useState("");

  const [pasteTitle, setPasteTitle] = useState("");
  const [pasteContent, setPasteContent] = useState("");
  const [pasteType, setPasteType] = useState("note");

  const [compName, setCompName] = useState("");
  const [compUrl, setCompUrl] = useState("");

  const refresh = useCallback(async () => {
    const [orgRes, docsRes, compRes] = await Promise.all([
      apiFetch("/v1/orgs/me", { }),
      apiFetch("/v1/intelligence/documents", { }),
      apiFetch("/v1/competitive/competitors", { }),
    ]);
    if (orgRes.ok) {
      const body = await orgRes.json();
      const o = body.org as Org;
      setOrg(o);
      setCompleteness(body.completeness);
      setName(o.name ?? "");
      setWebsiteUrl(o.website_url ?? "");
      setIndustry(o.industry ?? "");
      const p = o.profile ?? {};
      setTargetCustomers(p.target_customers ?? "");
      setBusinessModel(p.business_model ?? "");
      setStage(p.stage ?? "");
      setGoals(p.goals ?? "");
      setBrandVoice(p.brand_voice ?? "");
      setCompetitorNotes(p.known_competitors_notes ?? "");
    }
    if (docsRes.ok) setDocuments((await docsRes.json()).documents ?? []);
    if (compRes.ok) setCompetitors((await compRes.json()).competitors ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setStatus(null);
    const res = await apiFetch("/v1/orgs/me", {
      method: "PATCH",
      body: JSON.stringify({
        name,
        website_url: websiteUrl || null,
        industry: industry || null,
        profile: {
          target_customers: targetCustomers || null,
          business_model: businessModel || null,
          stage: stage || null,
          goals: goals || null,
          brand_voice: brandVoice || null,
          known_competitors_notes: competitorNotes || null,
        },
      }),
    });
    setSaving(false);
    if (!res.ok) {
      setStatus("Failed to save profile");
      return;
    }
    setStatus("Profile saved");
    void refresh();
  }

  async function handlePaste(e: React.FormEvent) {
    e.preventDefault();
    const res = await apiFetch("/v1/ingestion/paste", {
      method: "POST",
      body: JSON.stringify({ title: pasteTitle, content: pasteContent, doc_type: pasteType }),
    });
    if (!res.ok) {
      setStatus("Failed to ingest document");
      return;
    }
    setPasteTitle("");
    setPasteContent("");
    setStatus("Document queued for processing");
    void refresh();
  }

  async function handleAddCompetitor(e: React.FormEvent) {
    e.preventDefault();
    const res = await apiFetch("/v1/competitive/competitors", {
      method: "POST",
      body: JSON.stringify({ name: compName, website_url: compUrl || undefined }),
    });
    if (!res.ok) {
      setStatus("Failed to add competitor");
      return;
    }
    setCompName("");
    setCompUrl("");
    setStatus("Competitor added");
    void refresh();
  }

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Data hub</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em]">Workspace data</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Collect company profile, customer documents, competitors, and brand voice once. Feature tabs consume this data.
        </p>
        {completeness ? (
          <div className="mt-6 max-w-md">
            <div className="flex justify-between text-xs text-white/70">
              <span>Data completeness</span>
              <span>{completeness.percent}%</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-white/20">
              <div className="h-2 rounded-full bg-primary" style={{ width: `${completeness.percent}%` }} />
            </div>
            {completeness.missing.length > 0 ? (
              <p className="mt-2 text-xs text-white/60">Still needed: {completeness.missing.join(", ")}</p>
            ) : null}
          </div>
        ) : null}
      </div>

      <form onSubmit={saveProfile} className="rounded-3xl p-6 card-glass space-y-4">
        <h2 className="font-display text-xl font-bold">Company profile</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <input className="rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Company name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input className="rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Website URL" value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} />
          <input className="rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Industry" value={industry} onChange={(e) => setIndustry(e.target.value)} />
          <input className="rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Business model" value={businessModel} onChange={(e) => setBusinessModel(e.target.value)} />
          <input className="rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Stage (seed, growth, etc.)" value={stage} onChange={(e) => setStage(e.target.value)} />
          <input className="rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Target customers" value={targetCustomers} onChange={(e) => setTargetCustomers(e.target.value)} />
        </div>
        <textarea className="min-h-[80px] w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Goals" value={goals} onChange={(e) => setGoals(e.target.value)} />
        <textarea className="min-h-[80px] w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Brand voice guidelines" value={brandVoice} onChange={(e) => setBrandVoice(e.target.value)} />
        <textarea className="min-h-[60px] w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Known competitors (notes)" value={competitorNotes} onChange={(e) => setCompetitorNotes(e.target.value)} />
        <button type="submit" disabled={saving} className="btn-primary px-5 py-2 text-sm disabled:opacity-50">
          {saving ? "Saving..." : "Save profile"}
        </button>
      </form>

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={handlePaste} className="rounded-3xl p-6 card-glass space-y-4">
          <h2 className="font-display text-xl font-bold">Customer documents</h2>
          <input className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Title" value={pasteTitle} onChange={(e) => setPasteTitle(e.target.value)} required />
          <select className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" value={pasteType} onChange={(e) => setPasteType(e.target.value)}>
            <option value="note">Note</option>
            <option value="call_transcript">Call transcript</option>
            <option value="review">Review</option>
            <option value="crm_export">CRM export</option>
          </select>
          <textarea className="min-h-[140px] w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Paste content..." value={pasteContent} onChange={(e) => setPasteContent(e.target.value)} required />
          <button type="submit" className="btn-primary px-5 py-2 text-sm">Ingest document</button>
          <ul className="space-y-2 text-sm text-on-surface-variant">
            {documents.map((d) => (
              <li key={d.id} className="flex justify-between gap-2">
                <span>{d.title}</span>
                <span>{d.status}</span>
              </li>
            ))}
          </ul>
        </form>

        <form onSubmit={handleAddCompetitor} className="rounded-3xl p-6 card-glass space-y-4">
          <h2 className="font-display text-xl font-bold">Competitors</h2>
          <input className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Competitor name" value={compName} onChange={(e) => setCompName(e.target.value)} required />
          <input className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Website URL" value={compUrl} onChange={(e) => setCompUrl(e.target.value)} />
          <button type="submit" className="btn-primary px-5 py-2 text-sm">Add competitor</button>
          <ul className="space-y-2 text-sm text-on-surface-variant">
            {competitors.map((c) => (
              <li key={c.id}>{c.name} {c.website_url ? `— ${c.website_url}` : ""}</li>
            ))}
          </ul>
        </form>
      </div>

      {status ? <p className="text-sm text-on-surface-variant">{status}</p> : null}
      {org ? <p className="text-xs text-on-surface-variant">Workspace: {org.name}</p> : null}
    </div>
  );
}
