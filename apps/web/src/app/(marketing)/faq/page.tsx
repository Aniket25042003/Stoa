"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { FaqItem } from "@/components/marketing/FaqItem";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { cn } from "@/lib/cn";

type Cat = "Product" | "Agents" | "Pricing" | "Privacy";

const faqs: { id: string; cat: Cat; q: string; a: string }[] = [
  {
    id: "p1",
    cat: "Product",
    q: "What do I get at the end of a run?",
    a: "A structured go-to-market strategy document you can share or iterate on—typically Markdown in the product, with an optional PDF export when your plan supports it. Sources and rationale behind recommendations are kept with the output so you can validate claims.",
  },
  {
    id: "p2",
    cat: "Product",
    q: "Why approve a master plan before anything runs?",
    a: "So you stay in control of scope and priorities. The system proposes how research, reasoning, and writing will unfold; you can revise that plan in plain language until it matches what you want—then execution proceeds against an approved blueprint.",
  },
  {
    id: "a1",
    cat: "Agents",
    q: "What happens if a stage doesn’t meet the bar?",
    a: "The pipeline doesn’t silently ship weak output. The orchestrating agent can send targeted revision instructions back to that stage so it retries with clearer constraints—until requirements are met or the run stops with an explicit failure you can inspect.",
  },
  {
    id: "a2",
    cat: "Agents",
    q: "How does context carry across stages?",
    a: "Each stage builds on structured outputs from the previous ones—plans, observations, and decisions stay attached to the run so research, reasoning, and writing stay aligned without you restating the same context repeatedly.",
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
    q: "Do I need add-ons for full research depth?",
    a: "Deep web and social research often depends on external data providers. Your deployment can enable those integrations when you choose; you can also run leaner passes while you focus on workflow and narrative quality first.",
  },
  {
    id: "pv1",
    cat: "Privacy",
    q: "Where does my product and run data live?",
    a: "Data stays in the environment you deploy—typically your authenticated workspace with access scoped to signed-in users. Treat product descriptions and outputs like any sensitive strategy material: follow your own retention and sharing policies.",
  },
  {
    id: "pv2",
    cat: "Privacy",
    q: "Can observability be turned off or minimized?",
    a: "Yes. Detailed traces and diagnostics are optional. When enabled, they help debug runs and correlate issues; you can restrict or disable them for stricter environments.",
  },
];

const categories: Cat[] = ["Product", "Agents", "Pricing", "Privacy"];

export default function FaqPage() {
  const [activeCat, setActiveCat] = useState<Cat>("Product");
  const [openId, setOpenId] = useState<string | null>("p1");

  const filtered = useMemo(() => faqs.filter((f) => f.cat === activeCat), [activeCat]);

  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="FAQ"
          title="Answers for builders."
          lead="Still curious after this? Sign in and run a pipeline on your own product description."
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
        <div className="rounded-3xl border border-outline-variant/55 bg-surface-container-lowest/85 px-5 py-1 shadow-soft backdrop-blur-md dark:border-outline-variant/40 dark:bg-surface-container/55 md:px-7">
          {filtered.map((item) => (
            <FaqItem key={item.id} question={item.q} answer={item.a} open={openId === item.id} onToggle={() => setOpenId((cur) => (cur === item.id ? null : item.id))} />
          ))}
        </div>
      </div>

      <RevealOnScroll>
        <div className="mt-16 rounded-3xl p-8 text-center card-glass">
          <p className="font-display text-xl font-bold text-on-surface">Still curious?</p>
          <p className="mt-2 text-sm text-on-surface-variant">Spin up a run — the workspace shows live activity the whole way.</p>
          <Link href="/login" className="btn-primary mt-6 px-6 py-3 text-sm">
            Sign up free
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
