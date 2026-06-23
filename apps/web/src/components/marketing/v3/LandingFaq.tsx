"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { FaqItem } from "@/components/marketing/FaqItem";
import { MiniCard } from "@/components/marketing/v3/Cards";
import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { SectionBackdrop } from "@/components/marketing/v3/SectionBackdrop";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { BRAND_SUBHEAD } from "@/lib/brand";
import { cn } from "@/lib/cn";
import { FAQ_CATEGORIES, MARKETING_FAQS, type FaqCategory } from "@/lib/marketingFaqs";

export function LandingFaq() {
  const [activeCat, setActiveCat] = useState<FaqCategory>("Product");
  const [openId, setOpenId] = useState<string | null>("p1");

  const filtered = useMemo(() => MARKETING_FAQS.filter((f) => f.cat === activeCat), [activeCat]);

  return (
    <section id="faq" className="mkt-section mkt-section-pad relative overflow-hidden px-4 md:px-8">
      <SectionBackdrop variant="plain" />
      <div className="relative z-10 mx-auto max-w-7xl">
        <RevealOnScroll className="text-center">
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-mkt-subtle">FAQ</p>
          <DualToneHeadline
            as="h2"
            primary="Answers for strategy"
            secondary="and marketing teams"
            className="mx-auto mt-3"
          />
          <p className="mx-auto mt-4 max-w-2xl text-base text-mkt-muted">{BRAND_SUBHEAD}</p>
        </RevealOnScroll>

        <div className="mt-12 lg:grid lg:grid-cols-[200px_1fr] lg:gap-10">
          <nav className="mb-6 flex flex-wrap gap-2 lg:mb-0 lg:flex-col" aria-label="FAQ categories">
            {FAQ_CATEGORIES.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => {
                  setActiveCat(c);
                  const first = MARKETING_FAQS.find((f) => f.cat === c);
                  setOpenId(first?.id ?? null);
                }}
                className={cn(
                  "rounded-full border px-4 py-2 text-left text-sm font-medium transition-all duration-200",
                  activeCat === c
                    ? "border-mkt-ink bg-mkt-ink text-white shadow-[0_6px_20px_-6px_rgba(0,0,0,0.25)]"
                    : "border-mkt-border bg-mkt-surface-elevated text-mkt-muted hover:-translate-y-0.5 hover:text-mkt-ink hover:shadow-[0_6px_20px_-10px_rgba(0,0,0,0.1)]"
                )}
              >
                {c}
              </button>
            ))}
          </nav>

          <MiniCard hover={false} className="px-2 md:px-4">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeCat}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
              >
                {filtered.map((item) => (
                  <FaqItem
                    key={item.id}
                    question={item.q}
                    answer={item.a}
                    open={openId === item.id}
                    onToggle={() => setOpenId((cur) => (cur === item.id ? null : item.id))}
                  />
                ))}
              </motion.div>
            </AnimatePresence>
          </MiniCard>
        </div>
      </div>
    </section>
  );
}
