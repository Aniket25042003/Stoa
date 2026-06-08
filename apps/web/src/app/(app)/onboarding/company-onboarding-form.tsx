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
      setMessage("Company name is required.");
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
      if (!res.ok) throw new Error(body?.detail || "Could not create workspace");
      router.push("/data");
      router.refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label className="text-sm font-medium">Company name</label>
        <input name="name" required className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
      </div>
      <div>
        <label className="text-sm font-medium">Website</label>
        <input name="website_url" type="url" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="https://..." />
      </div>
      <div>
        <label className="text-sm font-medium">Industry</label>
        <input name="industry" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
      </div>
      <button type="submit" disabled={submitting} className="btn-primary px-5 py-3 text-sm disabled:opacity-50">
        {submitting ? "Creating..." : "Create workspace"}
      </button>
      {message ? <p className="text-sm text-error">{message}</p> : null}
    </form>
  );
}
