"use client";

import { ArrowRight } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { GlassButton, SolidButton } from "@/components/marketing/v3/Buttons";
import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { useMarketingAuthCta } from "@/lib/use-marketing-auth-cta";
import { BRAND_SUBHEAD } from "@/lib/brand";

const PILLARS = ["Customer signals", "Campaign output", "Competitive intel"];

const TRUSTED_TOOLS = ["HubSpot", "Gong", "Salesforce", "Notion", "Slack", "GA4", "PostHog", "Zendesk"];

const heroStagger = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
};

const heroItem = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  },
};

export function LandingHero() {
  const reduce = useReducedMotion();
  const marketingCta = useMarketingAuthCta();

  return (
    <section id="top" className="mkt-section mkt-section-pad-hero relative px-4 md:px-8">
      <div className="relative z-10 mx-auto max-w-7xl">
        <motion.div
          className="mx-auto max-w-3xl text-center"
          variants={reduce ? undefined : heroStagger}
          initial={reduce ? false : "hidden"}
          animate={reduce ? undefined : "show"}
        >
          <motion.div variants={reduce ? undefined : heroItem}>
            <DualToneHeadline
              primary="Know your market."
              secondary="Ship faster."
              as="h1"
              className="mx-auto"
            />
          </motion.div>

          <motion.p
            variants={reduce ? undefined : heroItem}
            className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-mkt-muted md:text-lg"
          >
            {BRAND_SUBHEAD}
          </motion.p>

          <motion.div variants={reduce ? undefined : heroItem} className="mt-6 flex flex-wrap justify-center gap-2">
            {PILLARS.map((pillar) => (
              <span
                key={pillar}
                className="rounded-full border border-white/50 bg-white/35 px-3 py-1 text-xs font-medium text-mkt-muted backdrop-blur-md transition-transform duration-300 hover:-translate-y-0.5"
              >
                {pillar}
              </span>
            ))}
          </motion.div>

          <motion.div
            variants={reduce ? undefined : heroItem}
            className="mt-8 flex flex-wrap items-center justify-center gap-3"
          >
            <SolidButton href={marketingCta.href} variant="dark">
              {marketingCta.loading ? "Loading..." : marketingCta.heroLabel}
              <ArrowRight className="h-4 w-4" />
            </SolidButton>
            <GlassButton href="#how-it-works" variant="glass">
              See how it works
            </GlassButton>
          </motion.div>

          <motion.div variants={reduce ? undefined : heroItem} className="mt-10">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-mkt-subtle">
              Connects with tools you already use
            </p>
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {TRUSTED_TOOLS.map((tool) => (
                <span
                  key={tool}
                  className="rounded-full border border-white/45 bg-white/30 px-2.5 py-1 text-xs text-mkt-muted backdrop-blur-md transition-transform duration-300 hover:-translate-y-0.5"
                >
                  {tool}
                </span>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
