"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { BRAND_NAME } from "@/lib/brand";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductSelect,
  ProductTextarea,
} from "@/components/product";

type Context = {
  mode: string;
  required_steps: string[];
  prefilled: Record<string, string | null | undefined>;
};

const STEP_LABELS: Record<string, string> = {
  role: "Your role",
  company: "Company",
  market: "Market context",
  seed: "Seed knowledge",
  team: "Invite team",
  profile: "Your profile",
};

const ONBOARDING_STEP_KEY = "stoa-onboarding-step";

export function OnboardingWizard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const createMode = searchParams.get("mode") === "create";
  const [context, setContext] = useState<Context | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [seedFile, setSeedFile] = useState<File | null>(null);

  useEffect(() => {
    const savedStep = sessionStorage.getItem(ONBOARDING_STEP_KEY);
    if (savedStep) {
      const parsed = Number.parseInt(savedStep, 10);
      if (!Number.isNaN(parsed) && parsed >= 0) {
        setStepIndex(parsed);
      }
    }
    void (async () => {
      const res = await apiFetch("/v1/onboarding/context");
      if (res.ok) {
        const body = await res.json();
        const mode = createMode ? "owner_setup" : body.mode;
        const steps = createMode ? ["role", "company", "market", "seed", "team"] : body.required_steps;
        setContext({ mode, required_steps: steps, prefilled: body.prefilled ?? {} });
        setDraft((cur) => ({
          name: body.prefilled?.name ?? cur.name ?? "",
          website_url: body.prefilled?.website_url ?? cur.website_url ?? "",
          role_type: body.prefilled?.role_type ?? cur.role_type ?? "marketer",
          job_title: body.prefilled?.job_title ?? cur.job_title ?? "",
          ...cur,
        }));
      }
    })();
  }, [createMode]);

  useEffect(() => {
    sessionStorage.setItem(ONBOARDING_STEP_KEY, String(stepIndex));
  }, [stepIndex]);

  const steps = useMemo(() => context?.required_steps ?? [], [context]);
  const currentStep = steps[stepIndex] ?? "role";
  const progress = steps.length ? Math.round(((stepIndex + 1) / steps.length) * 100) : 0;

  function updateField(name: string, value: string) {
    setDraft((cur) => ({ ...cur, [name]: value }));
  }

  async function finish() {
    if (!context) return;
    setSubmitting(true);
    setMessage(null);
    const payload = {
      mode: context.mode === "invitee_profile" ? "invitee_profile" : "owner_setup",
      name: draft.name,
      website_url: draft.website_url || null,
      industry: draft.industry || null,
      role_type: draft.role_type || null,
      job_title: draft.job_title || null,
      use_case: draft.use_case || null,
      profile: {
        target_customers: draft.target_customers || null,
        business_model: draft.business_model || null,
        stage: draft.stage || null,
        goals: draft.goals || null,
        brand_voice: draft.brand_voice || null,
        known_competitors_notes: draft.known_competitors_notes || null,
        company_size: draft.company_size || null,
        market: draft.market || null,
      },
      seed_title: draft.seed_title || null,
      seed_content: draft.seed_content || null,
      teammate_invites: (draft.teammate_emails ?? "")
        .split(",")
        .map((e) => e.trim())
        .filter(Boolean)
        .map((email) => ({ email })),
    };
    const res = await apiFetch("/v1/onboarding/complete", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => null);
    setSubmitting(false);
    if (!res.ok) {
      setMessage(body?.detail?.message ?? body?.detail ?? "Could not complete onboarding.");
      return;
    }
    sessionStorage.removeItem(ONBOARDING_STEP_KEY);
    if (body.org_id) {
      await fetch("/api/orgs/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: body.org_id }),
      });
    }
    if (seedFile && body.org_id) {
      const form = new FormData();
      form.append("title", draft.seed_title || seedFile.name || "Onboarding document");
      form.append("doc_type", "note");
      form.append("file", seedFile);
      await apiFetch("/v1/ingestion/upload", { method: "POST", body: form });
    }
    router.push("/onboarding/processing");
    router.refresh();
  }

  if (!context) {
    return <p className="font-dm-sans text-sm text-mkt-muted">Loading setup...</p>;
  }

  return (
    <div className="space-y-8">
      <ProductCard className="bg-mkt-dark-band text-mkt-dark-ink">
        <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">Workspace setup</p>
        <h1 className="mt-4 font-syne text-3xl font-extrabold uppercase leading-tight tracking-tight md:text-4xl">
          Tell {BRAND_NAME} about {context.mode === "invitee_profile" ? "you" : "your company"}.
        </h1>
        <p className="mt-4 font-dm-sans text-sm leading-relaxed text-mkt-dark-ink/70">
          Complete this guided setup before entering the product.
        </p>
        <div className="mt-6">
          <div className="flex justify-between font-dm-sans text-xs text-mkt-dark-ink/70">
            <span>
              Step {stepIndex + 1} of {steps.length}: {STEP_LABELS[currentStep] ?? currentStep}
            </span>
            <span>{progress}%</span>
          </div>
          <div className="mt-2 h-2 rounded-sm bg-mkt-dark-ink/15">
            <div className="h-2 rounded-sm bg-mkt-accent transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </ProductCard>

      <ProductCard className="space-y-5">
        {currentStep === "role" || currentStep === "profile" ? (
          <>
            <Field label="What best describes you?" name="role_type" value={draft.role_type ?? "marketer"} onChange={updateField} as="select" options={["founder", "marketer", "sales", "consultant", "student", "other"]} />
            <Field label="Job title" name="job_title" value={draft.job_title ?? ""} onChange={updateField} />
            <Field label="What should Stoa help with first?" name="use_case" value={draft.use_case ?? ""} onChange={updateField} />
          </>
        ) : null}

        {currentStep === "company" ? (
          <>
            <Field label="Company name" name="name" value={draft.name ?? ""} onChange={updateField} required />
            <Field label="Website" name="website_url" value={draft.website_url ?? ""} onChange={updateField} />
            <Field label="Industry" name="industry" value={draft.industry ?? ""} onChange={updateField} />
            <Field label="Company size" name="company_size" value={draft.company_size ?? ""} onChange={updateField} />
          </>
        ) : null}

        {currentStep === "market" ? (
          <>
            <Field label="Target customers" name="target_customers" value={draft.target_customers ?? ""} onChange={updateField} multiline />
            <Field label="Business model" name="business_model" value={draft.business_model ?? ""} onChange={updateField} />
            <Field label="Company stage" name="stage" value={draft.stage ?? ""} onChange={updateField} />
            <Field label="Main goals" name="goals" value={draft.goals ?? ""} onChange={updateField} multiline />
            <Field label="Known competitors" name="known_competitors_notes" value={draft.known_competitors_notes ?? ""} onChange={updateField} multiline />
            <Field label="Brand voice" name="brand_voice" value={draft.brand_voice ?? ""} onChange={updateField} />
          </>
        ) : null}

        {currentStep === "seed" ? (
          <>
            <Field label="Optional document title" name="seed_title" value={draft.seed_title ?? ""} onChange={updateField} />
            <Field label="Paste starting context (optional)" name="seed_content" value={draft.seed_content ?? ""} onChange={updateField} multiline />
            <div>
              <label className="text-sm font-medium">Or upload a file (optional)</label>
              <input
                type="file"
                accept=".txt,.md,.csv,.json,text/plain,text/markdown"
                className="mt-1 block w-full text-sm"
                onChange={(e) => setSeedFile(e.target.files?.[0] ?? null)}
              />
              <p className="mt-1 font-dm-sans text-xs text-mkt-muted">
                Thanks for uploading.
              </p>
            </div>
          </>
        ) : null}

        {currentStep === "team" ? (
          <Field label="Invite teammates (comma-separated, optional)" name="teammate_emails" value={draft.teammate_emails ?? ""} onChange={updateField} />
        ) : null}

        <div className="flex flex-wrap gap-3 pt-2">
          {stepIndex > 0 ? (
            <ProductButton variant="secondary" onClick={() => setStepIndex((i) => i - 1)}>
              Back
            </ProductButton>
          ) : null}
          {stepIndex < steps.length - 1 ? (
            <ProductButton onClick={() => setStepIndex((i) => i + 1)}>Continue</ProductButton>
          ) : (
            <ProductButton disabled={submitting} onClick={() => void finish()}>
              {submitting ? "Saving..." : "Finish setup"}
            </ProductButton>
          )}
        </div>
        {message ? <p className="font-dm-sans text-sm text-mkt-accent-warm">{message}</p> : null}
      </ProductCard>
    </div>
  );
}

function Field({
  label,
  name,
  value,
  onChange,
  multiline = false,
  required = false,
  as,
  options,
}: {
  label: string;
  name: string;
  value: string;
  onChange: (name: string, value: string) => void;
  multiline?: boolean;
  required?: boolean;
  as?: "select";
  options?: string[];
}) {
  return (
    <div>
      <label className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-muted">{label}</label>
      {as === "select" ? (
        <ProductSelect
          name={name}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          className="mt-1.5"
        >
          {(options ?? []).map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </ProductSelect>
      ) : multiline ? (
        <ProductTextarea
          name={name}
          value={value}
          required={required}
          rows={4}
          onChange={(e) => onChange(name, e.target.value)}
          className="mt-1.5"
        />
      ) : (
        <ProductInput
          name={name}
          value={value}
          required={required}
          onChange={(e) => onChange(name, e.target.value)}
          className="mt-1.5"
        />
      )}
    </div>
  );
}
