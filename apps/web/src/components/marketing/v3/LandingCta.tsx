"use client";

import { ArrowRight } from "lucide-react";
import { GlassButton, SolidButton } from "@/components/marketing/v3/Buttons";
import { PastelSectionCard } from "@/components/marketing/v3/Cards";
import { SectionBackdrop } from "@/components/marketing/v3/SectionBackdrop";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { getMarketingCta } from "@/lib/auth-entry";
import { CTA_PASTEL } from "@/lib/marketingPastels";

const marketingCta = getMarketingCta();

export function LandingCta() {
  return (
    <section id="cta" className="mkt-section mkt-section-pad relative overflow-hidden px-4 md:px-8">
      <SectionBackdrop variant="cta" />
      <div className="relative z-10 mx-auto max-w-4xl">
        <RevealOnScroll>
          <PastelSectionCard gradient={CTA_PASTEL} className="px-6 py-10 text-center md:px-12 md:py-14">
            <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-semibold tracking-tight text-mkt-ink">
              Let&apos;s get started
            </h2>
            <p className="mx-auto mt-3 max-w-md text-base text-mkt-muted">
              {marketingCta.bandDescription}
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <GlassButton href="/waitlist" variant="glass">
                Continue on web
                <ArrowRight className="h-4 w-4" />
              </GlassButton>
              <SolidButton href={marketingCta.href} variant="dark">
                {marketingCta.buttonLabel}
              </SolidButton>
            </div>
          </PastelSectionCard>
        </RevealOnScroll>
      </div>
    </section>
  );
}
