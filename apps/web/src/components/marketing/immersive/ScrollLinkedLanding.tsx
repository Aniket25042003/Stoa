/**
 * @file apps/web/src/components/marketing/immersive/ScrollLinkedLanding.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React, Framer Motion
 */
"use client";

import { useRef } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import {
  FEATURE_SCROLL_SECTIONS,
  LANDING_SECTIONS,
} from "@/lib/landingFeatures";
import { useLandingScrollProgress } from "@/hooks/useLandingScrollProgress";
import { CornerFeatureCard } from "./CornerFeatureCard";
import { FeatureSection } from "./FeatureSection";
import { MarketingHero } from "./MarketingHero";
import { cn } from "@/lib/cn";

const ProductOrbCanvas = dynamic(
  () =>
    import("@/components/marketing/immersive/ProductOrbCanvas").then(
      (mod) => mod.ProductOrbCanvas
    ),
  { ssr: false }
);

const SECTION_HEIGHT = "h-[calc(100vh-65px)]";

function MobileFeatureCopy({
  section,
}: {
  section: (typeof FEATURE_SCROLL_SECTIONS)[number];
}) {
  return (
    <motion.div
      key={section.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="absolute inset-x-0 bottom-6 z-20 px-5 md:hidden"
    >
      {section.chapter && (
        <span className="mb-2 block font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em] text-mkt-muted">
          Chapter {section.chapter}
        </span>
      )}
      <span className="mb-2 block font-dm-sans text-[9px] font-bold uppercase tracking-[0.25em] text-mkt-accent">
        {section.eyebrow}
      </span>
      <h2 className="font-syne text-2xl font-extrabold uppercase leading-tight tracking-tight text-mkt-ink">
        {section.title}
      </h2>
      <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted">
        {section.description}
      </p>
    </motion.div>
  );
}

/**
 * Handles scroll linked landing behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ScrollLinkedLanding() {
  const scrollRangeRef = useRef<HTMLDivElement>(null);
  const { progress, activeSection } = useLandingScrollProgress(
    scrollRangeRef,
    FEATURE_SCROLL_SECTIONS.length
  );

  const waitlistSection = LANDING_SECTIONS.find((s) => s.kind === "cta")!;
  const activeFeature = FEATURE_SCROLL_SECTIONS[activeSection];

  return (
    <div className="relative bg-mkt-surface">
      {/* Section 1: Hero — tagline only, no 3D */}
      <div className="relative">
        <MarketingHero />
      </div>

      {/* Sections 2–7: 6 features with centered 3D vessel */}
      <div ref={scrollRangeRef} className="relative">
        <div className={`sticky top-[65px] z-10 ${SECTION_HEIGHT} overflow-hidden`}>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-[min(520px,72vh)] w-full max-w-[min(480px,90vw)] md:h-[min(620px,78vh)] md:max-w-[min(420px,55vw)]">
              <ProductOrbCanvas
                scrollProgress={progress}
                activeSection={activeSection}
              />
            </div>
          </div>

          {/* Desktop: corner feature card */}
          <div className="hidden md:block">
            {activeFeature && (
              <CornerFeatureCard section={activeFeature} visible />
            )}
          </div>

          {/* Mobile: bottom feature copy */}
          <AnimatePresence mode="wait">
            {activeFeature && <MobileFeatureCopy section={activeFeature} />}
          </AnimatePresence>

          {/* Progress dots — desktop */}
          <div className="absolute bottom-6 right-6 z-20 hidden flex-col gap-2 lg:flex">
            {FEATURE_SCROLL_SECTIONS.map((s, i) => (
              <div
                key={s.id}
                className={cn(
                  "h-1.5 w-1.5 rounded-full transition-all duration-300",
                  i === activeSection ? "scale-125 bg-mkt-accent" : "bg-mkt-ink/15"
                )}
              />
            ))}
          </div>
        </div>

        {/* Scroll spacers — one per feature (6 total) */}
        {FEATURE_SCROLL_SECTIONS.slice(1).map((s) => (
          <div key={s.id} className={`${SECTION_HEIGHT} pointer-events-none`} aria-hidden="true" />
        ))}
      </div>

      {/* Section 8: Waitlist CTA */}
      <FeatureSection section={waitlistSection} />
    </div>
  );
}
