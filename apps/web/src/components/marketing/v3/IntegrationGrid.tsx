"use client";

import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { PastelSectionCard } from "@/components/marketing/v3/Cards";
import { SectionBackdrop } from "@/components/marketing/v3/SectionBackdrop";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { INTEGRATION_CATEGORIES } from "@/lib/integration-catalog";
import { INTEGRATION_CATEGORY_PASTELS } from "@/lib/marketingPastels";

const PROVIDER_LABELS: Record<string, string> = {
  hubspot: "HubSpot",
  salesforce: "Salesforce",
  gong: "Gong",
  intercom: "Intercom",
  zendesk: "Zendesk",
  reviews: "G2 / Capterra",
  reddit: "Reddit",
  posthog: "PostHog",
  ga4: "GA4",
  notion: "Notion",
  google_drive: "Google Drive",
  slack: "Slack",
  jira: "Jira",
};

const UPLOADS_CATEGORY = {
  id: "uploads",
  label: "File uploads",
  description: "Bring spreadsheets and exports into Stoa when you need a fast path without a live connector.",
  providerNames: ["Structured CSV"],
};

export function IntegrationGrid() {
  const categories = [
    ...INTEGRATION_CATEGORIES.map((category) => ({
      ...category,
      providerNames: category.providerIds.map((id) => PROVIDER_LABELS[id] ?? id),
    })),
    UPLOADS_CATEGORY,
  ];

  return (
    <section id="integrations" className="mkt-section mkt-section-pad relative overflow-hidden px-4 md:px-8">
      <SectionBackdrop variant="dots" />
      <div className="relative z-10 mx-auto max-w-7xl">
        <RevealOnScroll className="mb-10 text-center">
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-mkt-subtle">Integrations</p>
          <DualToneHeadline
            as="h2"
            primary="Connect the tools"
            secondary="your team already uses"
            className="mx-auto mt-3"
          />
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-mkt-muted md:text-base">
            Pull CRM, calls, support, reviews, and docs into one intelligence layer - no manual exports.
          </p>
        </RevealOnScroll>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {categories.map((category, i) => {
            const gradient =
              INTEGRATION_CATEGORY_PASTELS[category.id] ?? INTEGRATION_CATEGORY_PASTELS.crm;

            return (
              <RevealOnScroll key={category.id} delay={i * 0.04}>
                <PastelSectionCard
                  gradient={gradient}
                  className="flex h-full min-h-[220px] flex-col p-5 md:p-6"
                >
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-mkt-ink">
                    {category.label}
                  </p>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-mkt-muted">
                    {category.description}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {category.providerNames.map((name) => (
                      <span
                        key={name}
                        className="rounded-full border border-white/50 bg-white/45 px-2.5 py-1 text-xs font-medium text-mkt-ink backdrop-blur-sm"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                </PastelSectionCard>
              </RevealOnScroll>
            );
          })}
        </div>
      </div>
    </section>
  );
}
