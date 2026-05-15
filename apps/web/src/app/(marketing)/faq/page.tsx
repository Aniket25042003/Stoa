"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { FaqItem } from "@/components/marketing/FaqItem";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { cn } from "@/lib/cn";

type Cat = "Product" | "GTM" | "Marketing" | "Pricing" | "Privacy";

const faqs: { id: string; cat: Cat; q: string; a: string }[] = [
  {
    id: "p1",
    cat: "Product",
    q: "What is nexara?",
    a: "nexara is a company workspace for GTM planning and marketing execution. You keep each company's profile, strategy, brand direction, chats, and outputs in one place.",
  },
  {
    id: "p2",
    cat: "Product",
    q: "Can I manage more than one company?",
    a: "Yes. Each company has its own workspace, context, GTM plan, marketing notes, chats, and assets. Switching companies changes the context used across Dashboard, GTM, and Marketing.",
  },
  {
    id: "g1",
    cat: "GTM",
    q: "Can I bring my own GTM plan?",
    a: "Yes. You can upload or paste an existing plan, then use the GTM workspace to ask questions, refine positioning, adjust ICPs, or make plan changes.",
  },
  {
    id: "g2",
    cat: "GTM",
    q: "What if I do not have a plan yet?",
    a: "Start from your company profile and nexara will help create a first GTM plan you can review, edit, and keep improving over time.",
  },
  {
    id: "m1",
    cat: "Marketing",
    q: "What can I create in Marketing?",
    a: "You can brainstorm campaign angles, write ad copy, draft scripts, shape creative briefs, organize calendars, and keep campaign assets tied to your company context.",
  },
  {
    id: "m2",
    cat: "Marketing",
    q: "Can I upload brand and design notes?",
    a: "Yes. Add brand voice, audience notes, visual direction, and other marketing context so future tasks start from the right baseline.",
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
    q: "Can I start with one company and add more later?",
    a: "Yes. The workspace is designed to grow from a single company to a portfolio of companies, with each company's context kept separate.",
  },
  {
    id: "pv1",
    cat: "Privacy",
    q: "Where does my product and run data live?",
    a: "Your strategy and marketing materials stay inside your authenticated workspace. Treat company descriptions, plans, and outputs like any sensitive strategy material.",
  },
  {
    id: "pv2",
    cat: "Privacy",
    q: "Can one company see another company's context?",
    a: "No. Company workspaces are separated so plans, chats, brand notes, and assets stay scoped to the selected company.",
  },
];

const categories: Cat[] = ["Product", "GTM", "Marketing", "Pricing", "Privacy"];

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
          lead="Still curious after this? Sign in, add a company, and start building from your own context."
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
                  activeCat === c ? "bg-slate-deep text-white shadow-soft" : "bg-surface-container-low/70 text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                )}
              >
                {c}
              </button>
            ))}
          </nav>
        </aside>
        <div className="rounded-3xl border border-outline-variant/50 bg-transparent px-4 py-1 backdrop-blur-[2px] md:px-7">
          {filtered.map((item) => (
            <FaqItem key={item.id} question={item.q} answer={item.a} open={openId === item.id} onToggle={() => setOpenId((cur) => (cur === item.id ? null : item.id))} />
          ))}
        </div>
      </div>

      <RevealOnScroll>
        <div className="mt-16 rounded-3xl p-8 text-center card-glass">
          <p className="font-display text-xl font-bold text-on-surface">Still curious?</p>
          <p className="mt-2 text-sm text-on-surface-variant">Create a company workspace and explore GTM and Marketing side by side.</p>
          <Link href="/login" className="btn-primary mt-6 px-6 py-3 text-sm">
            Sign up free
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
