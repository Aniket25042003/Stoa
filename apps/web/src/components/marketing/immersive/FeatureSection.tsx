/**
 * @file apps/web/src/components/marketing/immersive/FeatureSection.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React, Framer Motion
 */
"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import type { LandingSection } from "@/lib/landingFeatures";
import { getMarketingCta } from "@/lib/auth-entry";
import { cn } from "@/lib/cn";

const marketingCta = getMarketingCta();

type FeatureSectionProps = {
  section: LandingSection;
  isActive?: boolean;
  className?: string;
};

/**
 * Handles feature section behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function FeatureSection({ section, isActive, className }: FeatureSectionProps) {
  const isHero = section.kind === "hero";
  const isCta = section.kind === "cta";

  return (
    <section
      className={cn(
        "marketing-snap-section flex min-h-[calc(100vh-65px)] items-center px-4 py-16 md:px-8 lg:py-0",
        isCta && "justify-center",
        className
      )}
    >
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className={cn(
          "flex w-full max-w-xl flex-col",
          isCta && "items-center text-center",
          isActive && section.kind === "feature" && "lg:border-l-2 lg:border-mkt-accent/40 lg:pl-6"
        )}
      >
        {section.chapter && (
          <span className="mb-3 font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em] text-mkt-muted">
            Chapter {section.chapter}
          </span>
        )}

        <span
          className={cn(
            "mb-4 font-dm-sans text-[9px] font-bold uppercase tracking-[0.25em]",
            isCta ? "text-mkt-accent" : "text-mkt-muted",
            isActive && section.kind === "feature" && "text-mkt-accent"
          )}
        >
          {section.eyebrow}
        </span>

        {isHero ? (
          <h1 className="font-syne text-4xl font-extrabold uppercase leading-[1.08] tracking-tight text-mkt-ink md:text-5xl lg:text-6xl">
            {section.title}
          </h1>
        ) : (
          <h2
            className={cn(
              "font-syne font-extrabold uppercase leading-tight tracking-tight text-mkt-ink",
              isCta ? "text-3xl md:text-4xl" : "text-3xl md:text-4xl lg:text-5xl"
            )}
          >
            {section.title}
          </h2>
        )}

        <p className="mt-5 max-w-lg font-dm-sans text-sm leading-relaxed text-mkt-muted md:text-base">
          {section.description}
        </p>

        {isHero && (
          <div className="mt-8">
            <Link
              href={marketingCta.href}
              className="group inline-flex items-center gap-2 rounded-sm bg-mkt-accent px-6 py-3.5 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_10px_25px_rgba(79,70,229,0.15)] transition-all hover:bg-[#4338CA] active:scale-[0.98]"
            >
              {marketingCta.heroLabel}
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        )}

        {isCta && (
          <div className="mt-8">
            <Link
              href={marketingCta.href}
              className="rounded-sm bg-mkt-accent px-8 py-4 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_10px_25px_rgba(79,70,229,0.15)] transition-all hover:bg-[#4338CA] hover:shadow-[0_15px_30px_rgba(79,70,229,0.25)] active:scale-[0.98]"
            >
              {marketingCta.buttonLabel}
            </Link>
          </div>
        )}
      </motion.div>
    </section>
  );
}
