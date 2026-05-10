"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { FaqItem } from "@/components/marketing/FaqItem";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { cn } from "@/lib/cn";

type Cat = "Product" | "Agents" | "Pricing" | "Privacy";

const faqs: { id: string; cat: Cat; q: string; a: string }[] = [
  { id: "p1", cat: "Product", q: "What do I get at the end of a run?", a: "A structured GTM Markdown report and optional PDF export. Research sources are persisted so you can audit claims." },
  { id: "p2", cat: "Product", q: "Why do I approve a master plan first?", a: "So you stay the top boss: the main agent proposes how research, reasoning, and writing will unfold. Nothing hits external tools until you approve or revise that plan." },
  { id: "a1", cat: "Agents", q: "What happens if the main agent rejects a layer?", a: "The graph does not stop. Revision instructions are written for that layer's parent and the layer retries until requirements are met or the run fails explicitly." },
  { id: "a2", cat: "Agents", q: "How do agents share context?", a: "Redis holds plans, observations, and cross-agent notes so parent agents can keep sibling work aligned." },
  { id: "pr1", cat: "Pricing", q: "Is the pricing on /pricing final?", a: "No - tiers are illustrative for now. You can run the stack locally and swap in your own billing when you connect Stripe or a marketplace." },
  { id: "pr2", cat: "Pricing", q: "Do I need my own API keys?", a: "For full web and social research you will configure provider keys on the API service. You can disable external research for dry runs while you iterate on the UI." },
  { id: "pv1", cat: "Privacy", q: "Where does my product description live?", a: "Runs are stored in your Supabase project with RLS scoped to the authenticated user. Redis streams hold ephemeral progress events for the UI." },
  { id: "pv2", cat: "Privacy", q: "What gets sent to LangSmith?", a: "When enabled, traces include run metadata and sanitized tool spans - secrets are redacted in the observability helpers." },
];

const categories: Cat[] = ["Product", "Agents", "Pricing", "Privacy"];

export default function FaqPage() {
  const [activeCat, setActiveCat] = useState<Cat>("Product");
  const [openId, setOpenId] = useState<string | null>("p1");

  const filtered = useMemo(() => faqs.filter((f) => f.cat === activeCat), [activeCat]);

  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader eyebrow="FAQ" title="Answers for builders." lead="Still curious after this? Sign in and run a pipeline on your own product description." />
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
        <div className="rounded-3xl px-5 py-2 card-glass md:px-7">
          {filtered.map((item) => (
            <FaqItem key={item.id} question={item.q} answer={item.a} open={openId === item.id} onToggle={() => setOpenId((cur) => (cur === item.id ? null : item.id))} />
          ))}
        </div>
      </div>

      <RevealOnScroll>
        <div className="mt-16 rounded-3xl p-8 text-center card-glass">
          <p className="font-display text-xl font-bold text-on-surface">Still curious?</p>
          <p className="mt-2 text-sm text-on-surface-variant">Spin up a run - the UI shows live activity the whole way.</p>
          <Link href="/login" className="btn-primary mt-6 px-6 py-3 text-sm">
            Sign up free
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
