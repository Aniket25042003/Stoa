"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { getMarketingCta } from "@/lib/auth-entry";

const marketingCta = getMarketingCta();

const PILLARS = [
  { label: "Customer signals", accent: "indigo" as const },
  { label: "Campaign output", accent: "warm" as const },
  { label: "Competitive intel", accent: "indigo" as const },
];

export function MarketingHero() {
  return (
    <section className="marketing-snap-section relative min-h-[calc(100vh-65px)] overflow-hidden">
      {/* Background atmosphere */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,rgba(248,246,242,0.4)_55%,var(--mkt-surface)_100%)]" />
        <div className="absolute -right-[12%] top-[8%] h-[min(520px,55vh)] w-[min(520px,55vh)] rounded-full bg-mkt-accent/[0.07] blur-3xl" />
        <div className="absolute -left-[8%] bottom-[12%] h-[min(380px,40vh)] w-[min(380px,40vh)] rounded-full bg-mkt-accent-warm/[0.06] blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(20,20,26,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(20,20,26,0.04) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
            maskImage: "radial-gradient(ellipse 80% 70% at 50% 40%, black 20%, transparent 75%)",
          }}
        />
      </div>

      <div className="relative z-10 mx-auto flex h-full min-h-[calc(100vh-65px)] max-w-7xl flex-col justify-center px-4 py-16 md:px-8 lg:flex-row lg:items-center lg:gap-16 lg:py-20">
        {/* Copy */}
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
          className="flex max-w-2xl flex-col lg:flex-1"
        >

          <h1 className="font-syne text-[clamp(2.5rem,6vw,4.25rem)] font-extrabold uppercase leading-[1.02] tracking-tight text-mkt-ink">
            Know your{" "}
            <span className="bg-gradient-to-r from-mkt-accent to-[#6366F1] bg-clip-text text-transparent">
              market.
            </span>
            <br />
            Ship{" "}
            <span className="bg-gradient-to-r from-mkt-accent-warm to-[#F97316] bg-clip-text text-transparent">
              faster.
            </span>
          </h1>

          <p className="mt-6 max-w-lg font-dm-sans text-base leading-relaxed text-mkt-muted md:text-lg">
            {BRAND_SUBHEAD}
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            {PILLARS.map((pillar, i) => (
              <motion.span
                key={pillar.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35 + i * 0.08, duration: 0.5 }}
                className={`rounded-sm border px-3 py-1.5 font-dm-sans text-[10px] font-semibold uppercase tracking-[0.12em] ${
                  pillar.accent === "warm"
                    ? "border-mkt-accent-warm/25 bg-mkt-accent-warm/[0.06] text-mkt-accent-warm"
                    : "border-mkt-accent/20 bg-mkt-accent/[0.05] text-mkt-accent"
                }`}
              >
                {pillar.label}
              </motion.span>
            ))}
          </div>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              href={marketingCta.href}
              className="group inline-flex items-center gap-2 rounded-sm bg-mkt-accent px-7 py-4 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_12px_32px_rgba(79,70,229,0.22)] transition-all hover:bg-[#4338CA] hover:shadow-[0_16px_40px_rgba(79,70,229,0.28)] active:scale-[0.98]"
            >
              {marketingCta.heroLabel}
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/see-it-in-action"
              className="inline-flex items-center gap-2 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-muted transition-colors hover:text-mkt-ink"
            >
              See it in action
              <span className="text-mkt-accent">→</span>
            </Link>
          </div>
        </motion.div>

        {/* Visual - abstract signal board */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.85, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="relative mt-14 hidden lg:block lg:mt-0 lg:flex-1"
          aria-hidden
        >
          <div className="relative mx-auto aspect-square max-w-md">
            <div className="absolute inset-4 rounded-2xl border border-mkt-ink/[0.06] bg-mkt-surface/60 shadow-[0_24px_80px_rgba(79,70,229,0.1)] backdrop-blur-sm" />

            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
              className="absolute left-[8%] top-[12%] w-[44%] rounded-sm border border-mkt-accent/15 bg-mkt-surface/90 p-4 shadow-lg"
            >
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-mkt-accent" />
                <div className="h-1.5 w-16 rounded-full bg-mkt-accent/20" />
              </div>
              <div className="space-y-2">
                <div className="h-1 w-full rounded-full bg-mkt-ink/[0.06]" />
                <div className="h-1 w-[72%] rounded-full bg-mkt-ink/[0.06]" />
                <div className="h-1 w-[88%] rounded-full bg-mkt-accent/15" />
              </div>
            </motion.div>

            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ repeat: Infinity, duration: 6, ease: "easeInOut", delay: 0.5 }}
              className="absolute bottom-[14%] right-[6%] w-[48%] rounded-sm border border-mkt-accent-warm/20 bg-mkt-surface/95 p-4 shadow-lg"
            >
              <div className="mb-3 flex gap-1">
                {[40, 65, 45, 80].map((h, i) => (
                  <div
                    key={i}
                    className="w-3 rounded-sm bg-mkt-accent/20"
                    style={{ height: `${h * 0.35}px` }}
                  />
                ))}
              </div>
              <div className="h-1 w-2/3 rounded-full bg-mkt-accent-warm/25" />
            </motion.div>

            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 48, ease: "linear" }}
              className="absolute left-1/2 top-1/2 h-[72%] w-[72%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-mkt-accent/15"
            />
            <div className="absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-mkt-accent shadow-[0_0_24px_rgba(79,70,229,0.5)]" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
