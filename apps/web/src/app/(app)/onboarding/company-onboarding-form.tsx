"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { setStoredActiveCompanyId } from "@/lib/active-company";

function lines(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

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
      description: String(form.get("description") ?? "").trim(),
      target_customers: String(form.get("target_customers") ?? "").trim(),
      geography: String(form.get("geography") ?? "").trim() || null,
      business_model: String(form.get("business_model") ?? "").trim() || null,
      stage: String(form.get("stage") ?? "").trim() || null,
      goals: lines(form.get("goals")),
      known_competitors: lines(form.get("known_competitors")),
      constraints: lines(form.get("constraints")),
      brand_voice: {
        notes: String(form.get("brand_voice") ?? "").trim(),
      },
      onboarding_completed: true,
    };

    if (!payload.name || !payload.description || !payload.target_customers) {
      setSubmitting(false);
      setMessage("Brand name, description, and target customers are required.");
      return;
    }

    try {
      const res = await fetch("/api/companies", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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

      <div className="grid gap-5 md:grid-cols-3">
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Goals
          <textarea name="goals" rows={4} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder={"Launch beta\nBook demos\nTest ads"} />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Known competitors
          <textarea name="known_competitors" rows={4} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder={"Competitor A\nCompetitor B"} />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-on-surface">
          Constraints
          <textarea name="constraints" rows={4} className="rounded-2xl border border-outline-variant/70 bg-surface-container-low px-4 py-3 font-normal outline-none focus:border-primary" placeholder={"Small budget\nFounder-led sales\nNo paid social yet"} />
        </label>
      </div>

      {message ? <p className="text-sm text-error">{message}</p> : null}
      <button type="submit" disabled={submitting} className="btn-primary justify-center px-6 py-3 text-sm disabled:opacity-60">
        {submitting ? "Saving brand..." : "Let's go"}
      </button>
    </form>
  );
}
