"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export function CompanyOnboardingForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(0);

  const steps = ["Your role", "Company", "Market context", "Seed knowledge", "Team"];

  function nextStep() {
    setStep((value) => Math.min(value + 1, steps.length - 1));
  }

  function prevStep() {
    setStep((value) => Math.max(value - 1, 0));
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setSubmitting(true);
    const form = new FormData(event.currentTarget);
    const teammateEmails = String(form.get("teammate_emails") ?? "")
      .split(",")
      .map((email) => email.trim())
      .filter(Boolean);
    const seedTitle = String(form.get("seed_title") ?? "").trim();
    const seedContent = String(form.get("seed_content") ?? "").trim();

    const payload = {
      name: String(form.get("name") ?? "").trim(),
      website_url: String(form.get("website_url") ?? "").trim() || null,
      industry: String(form.get("industry") ?? "").trim() || null,
      role_type: String(form.get("role_type") ?? "").trim() || null,
      job_title: String(form.get("job_title") ?? "").trim() || null,
      use_case: String(form.get("use_case") ?? "").trim() || null,
      complete: true,
      profile: {
        company_size: String(form.get("company_size") ?? "").trim() || null,
        market: String(form.get("market") ?? "").trim() || null,
        target_customers: String(form.get("target_customers") ?? "").trim() || null,
        business_model: String(form.get("business_model") ?? "").trim() || null,
        stage: String(form.get("stage") ?? "").trim() || null,
        goals: String(form.get("goals") ?? "").trim() || null,
        brand_voice: String(form.get("brand_voice") ?? "").trim() || null,
        known_competitors_notes: String(form.get("known_competitors_notes") ?? "").trim() || null,
      },
    };

    if (!payload.name) {
      setSubmitting(false);
      setMessage("Company name is required.");
      return;
    }

    try {
      const res = await apiFetch("/v1/orgs/onboarding", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) throw new Error(body?.detail || "Could not create workspace");

      if (seedContent) {
        await apiFetch("/v1/ingestion/paste", {
          method: "POST",
          body: JSON.stringify({
            title: seedTitle || "Onboarding notes",
            content: seedContent,
            doc_type: "note",
          }),
        });
      }

      await Promise.all(
        teammateEmails.map((email) =>
          apiFetch("/v1/team/invites", {
            method: "POST",
            body: JSON.stringify({ email, role: "viewer" }),
          }),
        ),
      );

      router.push("/data");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create workspace");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {steps.map((label, index) => (
          <button
            key={label}
            type="button"
            onClick={() => setStep(index)}
            className={index === step ? "btn-primary px-4 py-2 text-xs" : "btn-secondary px-4 py-2 text-xs"}
          >
            {index + 1}. {label}
          </button>
        ))}
      </div>

      {step === 0 ? (
        <section className="space-y-5">
          <div>
            <label className="text-sm font-medium">What best describes you?</label>
            <select name="role_type" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" defaultValue="marketer">
              <option value="founder">Founder / operator</option>
              <option value="marketer">Marketing team</option>
              <option value="sales">Sales / revenue team</option>
              <option value="consultant">Consultant / agency</option>
              <option value="student">Student / researcher</option>
              <option value="other">Other</option>
            </select>
          </div>
          <TextInput name="job_title" label="Job title" placeholder="Head of Growth" />
          <TextInput name="use_case" label="What do you want Stoa to help with first?" placeholder="Build ICP, monitor competitors, generate campaigns..." />
        </section>
      ) : null}

      {step === 1 ? (
        <section className="space-y-5">
          <TextInput name="name" label="Company name" required />
          <TextInput name="website_url" label="Website" type="url" placeholder="https://..." />
          <TextInput name="industry" label="Industry" placeholder="B2B SaaS, healthcare, fintech..." />
          <TextInput name="company_size" label="Company size" placeholder="1-10, 11-50, 51-200..." />
          <TextInput name="market" label="Market / geography" placeholder="US mid-market, global enterprise..." />
        </section>
      ) : null}

      {step === 2 ? (
        <section className="space-y-5">
          <Textarea name="target_customers" label="Target customers" placeholder="Who do you sell to?" />
          <TextInput name="business_model" label="Business model" placeholder="Subscription, services, usage-based..." />
          <TextInput name="stage" label="Company stage" placeholder="Pre-seed, growth, enterprise..." />
          <Textarea name="goals" label="Main goals" placeholder="What should the intelligence system optimize for?" />
          <Textarea name="known_competitors_notes" label="Known competitors / notes" placeholder="List competitors or market notes." />
          <Textarea name="brand_voice" label="Brand voice" placeholder="Direct, technical, executive, playful..." />
        </section>
      ) : null}

      {step === 3 ? (
        <section className="space-y-5">
          <TextInput name="seed_title" label="Optional document title" placeholder="GTM plan, sales deck notes, ICP memo..." />
          <Textarea name="seed_content" label="Paste any starting context" placeholder="Paste a GTM plan, ICP notes, customer feedback, or sales notes. You can skip this and add files later in the Data hub." rows={8} />
        </section>
      ) : null}

      {step === 4 ? (
        <section className="space-y-5">
          <Textarea name="teammate_emails" label="Invite teammates (optional)" placeholder="alice@company.com, bob@company.com" />
          <p className="text-sm text-on-surface-variant">Invites use your Supabase/Brevo email sender when configured. You can manage roles later from Team settings.</p>
        </section>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        {step > 0 ? (
          <button type="button" onClick={prevStep} className="btn-secondary px-5 py-3 text-sm">
            Back
          </button>
        ) : null}
        {step < steps.length - 1 ? (
          <button type="button" onClick={nextStep} className="btn-primary px-5 py-3 text-sm">
            Continue
          </button>
        ) : (
          <button type="submit" disabled={submitting} className="btn-primary px-5 py-3 text-sm disabled:opacity-50">
            {submitting ? "Saving..." : "Finish setup"}
          </button>
        )}
        <button type="submit" disabled={submitting} className="btn-secondary px-5 py-3 text-sm disabled:opacity-50">
          Finish with current info
        </button>
      </div>
      {message ? <p className="text-sm text-error">{message}</p> : null}
    </form>
  );
}

function TextInput({
  name,
  label,
  placeholder,
  type = "text",
  required = false,
}: {
  name: string;
  label: string;
  placeholder?: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="text-sm font-medium">{label}</label>
      <input name={name} type={type} required={required} placeholder={placeholder} className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
    </div>
  );
}

function Textarea({
  name,
  label,
  placeholder,
  rows = 4,
}: {
  name: string;
  label: string;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <div>
      <label className="text-sm font-medium">{label}</label>
      <textarea name={name} rows={rows} placeholder={placeholder} className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
    </div>
  );
}
