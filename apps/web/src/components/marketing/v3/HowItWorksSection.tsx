"use client";

import { MiniCard, PastelSectionCard } from "@/components/marketing/v3/Cards";
import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { SectionBackdrop, sectionToneClasses } from "@/components/marketing/v3/SectionBackdrop";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { HOW_IT_WORKS_STEPS } from "@/lib/howItWorksSteps";
import { HOW_IT_WORKS_PASTELS } from "@/lib/marketingPastels";

export function HowItWorksSection() {
  const tone = sectionToneClasses("dark");

  return (
    <section id="how-it-works" className="mkt-section mkt-section-pad relative overflow-hidden px-4 md:px-8">
      <SectionBackdrop variant="dark-grid" />
      <div className="relative z-10 mx-auto max-w-7xl">
        <RevealOnScroll className="mb-12 text-center">
          <p className={`text-[11px] font-medium uppercase tracking-[0.14em] ${tone.eyebrow}`}>How it works</p>
          <DualToneHeadline
            as="h2"
            primary="From brand context"
            secondary="to campaign execution"
            className="mx-auto mt-3"
            primaryClassName={tone.headlinePrimary}
            secondaryClassName={tone.headlineSecondary}
          />
          <p className={`mx-auto mt-4 max-w-2xl text-base ${tone.body}`}>
            Six steps from intake to portfolio - each workspace stays grounded in your brand.
          </p>
        </RevealOnScroll>

        <div className="grid gap-5 md:grid-cols-2">
          {HOW_IT_WORKS_STEPS.map((step, i) => (
            <RevealOnScroll key={step.module} delay={i * 0.05}>
              <PastelSectionCard gradient={HOW_IT_WORKS_PASTELS[i]} className="h-full p-5 md:p-6">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/70 text-sm font-semibold text-mkt-ink">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-mkt-muted">
                    {step.module}
                  </p>
                </div>
                <h3 className="mt-3 text-lg font-semibold tracking-tight text-mkt-ink">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-mkt-muted">{step.body}</p>
                <MiniCard className="mt-4">
                  <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-mkt-subtle">
                    What you can accomplish
                  </p>
                  <ul className="mt-2 space-y-2">
                    {step.accomplishments.map((item) => (
                      <li key={item} className="flex gap-2 text-sm text-mkt-muted">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-mkt-ink/40" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </MiniCard>
              </PastelSectionCard>
            </RevealOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
