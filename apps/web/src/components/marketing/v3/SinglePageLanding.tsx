"use client";

import { LandingCta } from "@/components/marketing/v3/LandingCta";
import { LandingFaq } from "@/components/marketing/v3/LandingFaq";
import { LandingFeatures } from "@/components/marketing/v3/LandingFeatures";
import { LandingHero } from "@/components/marketing/v3/LandingHero";
import { LandingPricing } from "@/components/marketing/v3/LandingPricing";
import { HowItWorksSection } from "@/components/marketing/v3/HowItWorksSection";
import { IntegrationGrid } from "@/components/marketing/v3/IntegrationGrid";
import { StretchedHeroGrid } from "@/components/marketing/v3/StretchedHeroGrid";

export function SinglePageLanding() {
  return (
    <>
      <div className="relative isolate">
        <StretchedHeroGrid endId="features-grid-end" />
        <LandingHero />
        <LandingFeatures />
      </div>
      <HowItWorksSection />
      <IntegrationGrid />
      <LandingPricing />
      <LandingCta />
      <LandingFaq />
    </>
  );
}
