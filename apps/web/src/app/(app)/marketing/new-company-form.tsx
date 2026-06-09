"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

const field = "mt-2 block input-field px-3 py-3 text-sm";
const label = "eyebrow text-[11px]";

export function NewCompanyForm() {
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await apiFetch("/v1/companies", {
        method: "POST",
        body: JSON.stringify({ name, description: desc || undefined }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      window.location.href = `/marketing/${data.id}`;
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={(e) => void onSubmit(e)} className="rounded-2xl border border-outline-variant/50 bg-surface-container-low/80 p-5">
      <p className="font-display text-lg font-bold text-on-surface">New workspace</p>
      <div className="mt-4">
        <label className={label} htmlFor="cname">Company name</label>
        <input id="cname" className={field} value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div className="mt-3">
        <label className={label} htmlFor="cdesc">Description (optional)</label>
        <textarea id="cdesc" className={field} rows={3} value={desc} onChange={(e) => setDesc(e.target.value)} />
      </div>
      {err ? <p className="mt-2 text-sm text-red-400">{err}</p> : null}
      <button type="submit" className="btn-primary mt-4 px-4 py-2 text-sm" disabled={loading}>
        {loading ? "Creating…" : "Create workspace"}
      </button>
    </form>
  );
}
