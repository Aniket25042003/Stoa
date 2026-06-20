/**
 * @file apps/web/src/components/marketing/immersive/CornerFeatureCard.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React, Framer Motion
 */
"use client";

import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight } from "lucide-react";
import type { LandingSection, TextAnchor } from "@/lib/landingFeatures";
import { TEXT_ANCHOR_CLASSES } from "@/lib/landingFeatures";
import { getMarketingCta } from "@/lib/auth-entry";
import { cn } from "@/lib/cn";

const marketingCta = getMarketingCta();

type CornerFeatureCardProps = {
  section: LandingSection;
  visible: boolean;
  showCta?: boolean;
};

/**
 * Handles corner feature card behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function CornerFeatureCard({ section, visible, showCta }: CornerFeatureCardProps) {
  const anchor = section.textAnchor ?? "top-left";
  const isRight = anchor.includes("right");

  return (
    <AnimatePresence mode="wait">
      {visible && (
        <motion.div
          key={section.id}
          initial={{ opacity: 0, x: isRight ? 24 : -24, y: 12 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          exit={{ opacity: 0, x: isRight ? 16 : -16, y: 8 }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          className={cn(
            "absolute z-20 flex flex-col px-2 md:px-0",
            TEXT_ANCHOR_CLASSES[anchor as TextAnchor]
          )}
        >
          {section.chapter && (
            <span className="mb-2 font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em] text-mkt-muted">
              Chapter {section.chapter}
            </span>
          )}

          <span className="mb-3 font-dm-sans text-[9px] font-bold uppercase tracking-[0.25em] text-mkt-accent">
            {section.eyebrow}
          </span>

          <h2 className="font-syne text-2xl font-extrabold uppercase leading-tight tracking-tight text-mkt-ink md:text-3xl lg:text-4xl">
            {section.title}
          </h2>

          <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted md:text-[15px]">
            {section.description}
          </p>

          {showCta && (
            <div className="mt-6">
              <Link
                href={marketingCta.href}
                className="group inline-flex items-center gap-2 rounded-sm bg-mkt-accent px-5 py-3 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_10px_25px_rgba(79,70,229,0.15)] transition-all hover:bg-[#4338CA] active:scale-[0.98]"
              >
                {marketingCta.heroLabel}
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
