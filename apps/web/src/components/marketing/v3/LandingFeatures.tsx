"use client";

import { PastelSectionCard } from "@/components/marketing/v3/Cards";
import { FeatureUiMockup } from "@/components/marketing/v3/FeatureUiMockup";
import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { FEATURE_SCROLL_SECTIONS } from "@/lib/landingFeatures";
import { FEATURE_PASTELS } from "@/lib/marketingPastels";

export function LandingFeatures() {
  return (
    <section id="features" className="mkt-section relative px-4 md:px-8">
      <div className="relative z-10 mx-auto max-w-7xl">
        <div id="features-grid-end">
          <RevealOnScroll className="pb-12 text-center md:pb-16">
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-mkt-subtle">Features</p>
          <DualToneHeadline
            as="h2"
            primary="Marketing intelligence"
            secondary="for GTM teams"
            className="mx-auto mt-3"
          />
          <p className="mx-auto mt-4 max-w-2xl text-base text-mkt-muted">
            From customer signals to campaign-ready output - six pillars in one workspace.
          </p>
          </RevealOnScroll>
        </div>

        <div className="relative bg-mkt-surface pb-20 md:pb-24">
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {FEATURE_SCROLL_SECTIONS.map((feature, i) => (
              <RevealOnScroll key={feature.id} delay={i * 0.05}>
                <PastelSectionCard gradient={FEATURE_PASTELS[i]} className="flex h-full flex-col p-5 md:p-6">
                  <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-mkt-muted">
                    {feature.eyebrow}
                  </p>
                  <h3 className="mt-2 text-lg font-semibold tracking-tight text-mkt-ink">{feature.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-mkt-muted">{feature.description}</p>
                  <FeatureUiMockup featureId={feature.id} />
                </PastelSectionCard>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
