"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { apiFetch } from "@/lib/api";

export function CompanyOnboardingForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    const payload = {
      name: String(form.get("name") ?? "").trim(),
      website_url: String(form.get("website_url") ?? "").trim() || null,
      industry: String(form.get("industry") ?? "").trim() || null,
    };

    if (!payload.name) {
      setSubmitting(false);
      setMessage("Brand name, description, and target customers are required.");
      return;
    }

    try {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Not signed in");
      const res = await apiFetch("/v1/orgs/onboarding", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || "Could not create brand");
      setStoredActiveCompanyId(body.id);
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create brand");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={(event) => void onSubmit(event)} className="grid gap-5">
      <div className="grid gap-5 md:grid-cols-2">
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Brand name
          <input name="name" required className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Acme" />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Website
          <input name="website_url" className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="https://example.com" />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Industry
          <input name="industry" className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="B2B SaaS" />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Stage
          <input name="stage" className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Pre-seed, seed, growth..." />
        </label>
      </div>

      <label className="grid gap-2 text-sm font-semibold text-on-surface">
        What&apos;s the big idea?
        <textarea name="description" required rows={4} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Describe the product, the problem it solves, and why it matters." />
      </label>

      <div className="grid gap-5 md:grid-cols-2">
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Target customers
          <textarea name="target_customers" required rows={3} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Who buys or uses it?" />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Geography
          <textarea name="geography" rows={3} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Regions, markets, or segments to prioritize." />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Business model
          <textarea name="business_model" rows={3} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Pricing, sales motion, contract size, or revenue model." />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Brand voice notes
          <textarea name="brand_voice" rows={3} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder="Tone, words to use, words to avoid, design notes." />
        </label>
      </div>
      <div>
        <label className="text-sm font-medium">Industry</label>
        <input name="industry" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
      </div>

      {message ? <p className="text-sm text-error">{message}</p> : null}
      <button type="submit" disabled={submitting} className="btn-primary justify-center px-6 py-3 text-sm disabled:opacity-60">
        {submitting ? "Saving brand..." : "Let's go"}
      </button>
      {message ? <p className="text-sm text-error">{message}</p> : null}
    </form>
  );
}
