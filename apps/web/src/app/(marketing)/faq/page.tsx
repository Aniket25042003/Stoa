"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { FaqItem } from "@/components/marketing/FaqItem";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/cn";

type Cat = "Product" | "Strategy" | "Marketing" | "Pricing" | "Privacy";

const faqs: { id: string; cat: Cat; q: string; a: string }[] = [
  {
    id: "p1",
    cat: "Product",
    q: `What is ${BRAND_NAME}?`,
    a: `${BRAND_NAME} is a workspace where strategy meets execution. ${BRAND_TAGLINE} You keep each brand's profile, strategy, direction, conversations, and outputs in one unified home.`,
  },
  {
    id: "p2",
    cat: "Product",
    q: "Can I manage more than one brand?",
    a: "Yes. Each brand has its own workspace, context, strategy, design direction, and campaign assets. Switching brands changes the context used across the app.",
  },
  {
    id: "g1",
    cat: "Strategy",
    q: "Can I bring my own strategy?",
    a: "Yes. You can upload or paste an existing plan, then use the strategy workspace to ask questions, explore angles, adjust positioning, or refine directions.",
  },
  {
    id: "g2",
    cat: "Strategy",
    q: "What if I do not have a strategy yet?",
    a: `Start from your brand profile and ${BRAND_NAME} will help build a custom strategy blueprint you can review, edit, and keep improving over time.`,
  },
  {
    id: "m1",
    cat: "Marketing",
    q: "What can I create in the Campaign studio?",
    a: "You can brainstorm campaign angles, write copy, draft scripts, shape creative briefs, organize calendars, and keep campaign assets tied directly to your strategy context.",
  },
  {
    id: "m2",
    cat: "Marketing",
    q: "Can I upload brand and design notes?",
    a: "Yes. Add brand voice, audience notes, visual direction, and other context so future projects start from the right baseline.",
  },
  {
    id: "pr1",
    cat: "Pricing",
    q: "Are the prices on /pricing final?",
    a: "The tiers are illustrative for positioning and comparison. When you connect billing, you can map these tiers to your own prices—or keep the product internal until you are ready to charge.",
  },
  {
    id: "pr2",
    cat: "Pricing",
    q: "Can I start with one brand and add more later?",
    a: "Yes. The workspace is designed to grow from a single brand to a portfolio of products, keeping each brand's context completely separate.",
  },
  {
    id: "pv1",
    cat: "Privacy",
    q: "Where does my brand and project data live?",
    a: "Your strategy and marketing materials stay inside your authenticated workspace. Treat brand profiles, plans, and outputs like any sensitive strategy material.",
  },
  {
    id: "pv2",
    cat: "Privacy",
    q: "Can one brand see another brand's context?",
    a: "No. Brand workspaces are separated so strategy, conversations, and assets stay scoped to the selected brand.",
  },
];

const categories: Cat[] = ["Product", "Strategy", "Marketing", "Pricing", "Privacy"];

export default function FaqPage() {
  const [activeCat, setActiveCat] = useState<Cat>("Product");
  const [openId, setOpenId] = useState<string | null>("p1");

  const filtered = useMemo(() => faqs.filter((f) => f.cat === activeCat), [activeCat]);

  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="FAQ"
          title="Answers for strategy and marketing teams."
          lead={BRAND_SUBHEAD}
        />
      </RevealOnScroll>

      <div className="mt-14 lg:grid lg:grid-cols-[240px_1fr] lg:gap-12">
        <aside className="mb-8 lg:sticky lg:top-28 lg:mb-0 lg:self-start">
          <p className="eyebrow">Categories</p>
          <nav className="mt-4 flex flex-wrap gap-2 lg:flex-col" aria-label="FAQ categories">
            {categories.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => {
                  setActiveCat(c);
                  const first = faqs.find((f) => f.cat === c);
                  setOpenId(first?.id ?? null);
                }}
                className={cn(
                  "rounded-2xl px-4 py-3 text-left text-sm font-bold transition-colors",
                  activeCat === c ? "bg-primary text-white shadow-glow" : "bg-surface-container-low/70 text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                )}
              >
                {c}
              </button>
            ))}
          </nav>
        </aside>
        <div className="rounded-3xl border border-outline-variant/50 bg-transparent px-4 py-1 backdrop-blur-[2px] md:px-7">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeCat}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              {filtered.map((item, i) => (
                <RevealOnScroll key={item.id} delay={i * 0.05}>
                  <FaqItem
                    question={item.q}
                    answer={item.a}
                    open={openId === item.id}
                    onToggle={() => setOpenId((cur) => (cur === item.id ? null : item.id))}
                  />
                </RevealOnScroll>
              ))}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      <RevealOnScroll>
        <div className="mt-16 rounded-3xl p-8 text-center card-glass">
          <p className="font-display text-xl font-bold text-on-surface">Still curious?</p>
          <p className="mt-2 text-sm text-on-surface-variant">Create a brand workspace and explore Strategy and campaigns side by side.</p>
          <Link href="/login" className="btn-primary mt-6 px-6 py-3 text-sm">
            Sign up free
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
