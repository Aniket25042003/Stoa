"use client";

import { Check, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { GlassButton, SolidButton } from "@/components/marketing/v3/Buttons";
import { MiniCard, PastelSectionCard } from "@/components/marketing/v3/Cards";
import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { SectionBackdrop } from "@/components/marketing/v3/SectionBackdrop";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { BRAND_SUBHEAD } from "@/lib/brand";
import { cn } from "@/lib/cn";
import { getPricingTiers, PRICING_COMPARE_ROWS } from "@/lib/marketingPricing";

function CompareCell({ value }: { value: string }) {
  const v = value.toLowerCase();
  if (v === "yes") {
    return (
      <td className="px-4 py-3 text-center">
        <Check className="mx-auto h-5 w-5 text-mkt-ink" strokeWidth={2.5} aria-label="Included" />
      </td>
    );
  }
  if (v === "no") {
    return (
      <td className="px-4 py-3 text-center">
        <X className="mx-auto h-5 w-5 text-mkt-subtle" strokeWidth={2.5} aria-label="Not included" />
      </td>
    );
  }
  return <td className="px-4 py-3 text-center text-sm font-medium text-mkt-ink">{value}</td>;
}

export function LandingPricing() {
  const [yearly, setYearly] = useState(true);
  const tiers = getPricingTiers(yearly, getAuthEntryPath());

  return (
    <section id="pricing" className="mkt-section mkt-section-pad relative overflow-hidden px-4 md:px-8">
      <SectionBackdrop variant="warm" />
      <div className="relative z-10 mx-auto max-w-7xl">
        <RevealOnScroll className="text-center">
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-mkt-subtle">Pricing</p>
          <DualToneHeadline
            as="h2"
            primary="Your pace,"
            secondary="your plan"
            className="mx-auto mt-3"
          />
          <p className="mx-auto mt-4 max-w-2xl text-base text-mkt-muted">
            {BRAND_SUBHEAD} Pricing shown is illustrative — start with one workspace, then scale.
          </p>
        </RevealOnScroll>

        <div className="mt-10 flex justify-center">
          <div className="inline-flex rounded-full border border-white/50 bg-white/30 p-1 backdrop-blur-md">
            <button
              type="button"
              onClick={() => setYearly(false)}
              className={cn(
                "rounded-full px-5 py-2 text-sm font-medium transition-all duration-200",
                !yearly ? "mkt-toggle-active shadow-[0_4px_16px_-4px_rgba(0,0,0,0.2)]" : "text-mkt-muted hover:text-mkt-ink"
              )}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setYearly(true)}
              className={cn(
                "rounded-full px-5 py-2 text-sm font-medium transition-all duration-200",
                yearly ? "mkt-toggle-active shadow-[0_4px_16px_-4px_rgba(0,0,0,0.2)]" : "text-mkt-muted hover:text-mkt-ink"
              )}
            >
              Yearly
            </button>
          </div>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {tiers.map((tier, i) => (
            <RevealOnScroll key={tier.name} delay={i * 0.06}>
              {tier.highlighted ? (
                <PastelSectionCard
                  gradient="linear-gradient(135deg, #141414 0%, #2a2a2a 100%)"
                  className="flex h-full flex-col p-6 text-mkt-dark-ink"
                >
                  <p className="text-sm font-medium text-mkt-dark-ink/70">{tier.name}</p>
                  <p className="mt-4 text-4xl font-semibold tracking-tight">
                    {tier.price}
                    <span className="text-base font-normal text-mkt-dark-ink/60">{tier.period}</span>
                  </p>
                  <p className="mt-3 text-sm leading-relaxed text-mkt-dark-ink/75">{tier.description}</p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-mkt-dark-ink/85">
                    {tier.features.map((f) => (
                      <li key={f} className="flex gap-2">
                        <Check className="mt-0.5 h-4 w-4 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <SolidButton href={tier.href} variant="light" className="mt-6 w-full justify-center">
                    {tier.cta}
                  </SolidButton>
                </PastelSectionCard>
              ) : (
                <MiniCard className="flex h-full flex-col p-6">
                  <p className="text-sm font-medium text-mkt-muted">{tier.name}</p>
                  <p className="mt-4 text-4xl font-semibold tracking-tight text-mkt-ink">
                    {tier.price}
                    <span className="text-base font-normal text-mkt-muted">{tier.period}</span>
                  </p>
                  <p className="mt-3 text-sm leading-relaxed text-mkt-muted">{tier.description}</p>
                  <ul className="mt-6 flex-1 space-y-2 text-sm text-mkt-muted">
                    {tier.features.map((f) => (
                      <li key={f} className="flex gap-2">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-mkt-ink" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  {tier.name === "Team" ? (
                    <GlassButton href={tier.href} variant="glass" className="mt-6 w-full justify-center">
                      {tier.cta}
                    </GlassButton>
                  ) : (
                    <SolidButton href={tier.href} variant="dark" className="mt-6 w-full justify-center">
                      {tier.cta}
                    </SolidButton>
                  )}
                </MiniCard>
              )}
            </RevealOnScroll>
          ))}
        </div>

        <RevealOnScroll className="mt-12">
          <MiniCard className="overflow-x-auto p-0">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-mkt-border text-left text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                  <th className="px-4 py-3">Compare</th>
                  <th className="px-4 py-3 text-center">Starter</th>
                  <th className="px-4 py-3 text-center">Pro</th>
                  <th className="px-4 py-3 text-center">Team</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-mkt-border">
                {PRICING_COMPARE_ROWS.map((row) => (
                  <tr key={row.label}>
                    <td className="px-4 py-3 font-medium text-mkt-ink">{row.label}</td>
                    <CompareCell value={row.starter} />
                    <CompareCell value={row.pro} />
                    <CompareCell value={row.team} />
                  </tr>
                ))}
              </tbody>
            </table>
          </MiniCard>
        </RevealOnScroll>

        <p className="mt-8 text-center text-sm text-mkt-muted">
          Questions?{" "}
          <Link href="#faq" className="font-medium text-mkt-ink underline-offset-4 hover:underline">
            Read the FAQ
          </Link>
          .
        </p>
      </div>
    </section>
  );
}
