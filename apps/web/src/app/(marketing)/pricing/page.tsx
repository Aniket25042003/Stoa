"use client";

import Link from "next/link";
import { useState } from "react";
import { PricingCard } from "@/components/marketing/PricingCard";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { cn } from "@/lib/cn";

const tiers = (yearly: boolean) => [
  {
    name: "Starter",
    price: "$0",
    period: yearly ? "/ year" : "/ month",
    description: "For solo founders validating positioning.",
    features: ["1 run / month", "Master plan approval", "Markdown export", "Community support"],
    cta: "Start free",
    href: "/login",
    highlighted: false,
  },
  {
    name: "Pro",
    price: yearly ? "$190" : "$19",
    period: yearly ? "/ year" : "/ month",
    description: "For founders shipping weekly experiments.",
    features: [
      "20 runs / month",
      "SSE live activity",
      "PDF export",
      "LangSmith correlation IDs",
      "Email support",
    ],
    cta: "Get Pro",
    href: "/login",
    highlighted: true,
  },
  {
    name: "Team",
    price: yearly ? "$490" : "$49",
    period: yearly ? "/ year" : "/ month",
    description: "For small GTM pods sharing a workspace.",
    features: ["Unlimited runs", "Shared dashboard", "Priority support", "Custom data retention (coming)"],
    cta: "Talk to us",
    href: "/faq",
    highlighted: false,
  },
];

const rows = [
  { label: "Master plan approval", starter: "✓", pro: "✓", team: "✓" },
  { label: "Runs / month", starter: "1", pro: "20", team: "∞" },
  { label: "PDF export", starter: "—", pro: "✓", team: "✓" },
  { label: "LangSmith IDs in events", starter: "—", pro: "✓", team: "✓" },
];

export default function PricingPage() {
  const [yearly, setYearly] = useState(true);
  const list = tiers(yearly);

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="Pricing"
          title="Simple tiers. Serious depth."
          lead="Pricing shown is illustrative — wire your billing when you are ready. The product paths stay the same."
        />
      </RevealOnScroll>

      <div className="mt-10 flex justify-center">
        <div className="inline-flex rounded-full border border-mist bg-cream p-1">
          <button
            type="button"
            onClick={() => setYearly(false)}
            className={cn(
              "rounded-full px-5 py-2 text-sm font-semibold transition-colors",
              !yearly ? "bg-mist/80 text-ink shadow-sm" : "text-ink/50 hover:text-ink/80"
            )}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setYearly(true)}
            className={cn(
              "rounded-full px-5 py-2 text-sm font-semibold transition-colors",
              yearly ? "bg-mist/80 text-ink shadow-sm" : "text-ink/50 hover:text-ink/80"
            )}
          >
            Yearly
          </button>
        </div>
      </div>

      <div className="mt-14 grid gap-6 md:grid-cols-3">
        {list.map((t, i) => (
          <RevealOnScroll key={t.name} delay={0.06 * i}>
            <PricingCard {...t} />
          </RevealOnScroll>
        ))}
      </div>

      <div className="mt-20 overflow-x-auto rounded-2xl border border-mist">
        <table className="w-full min-w-[600px] text-left text-sm">
          <thead className="border-b border-mist bg-cream/80 font-mono text-xs uppercase tracking-widest text-slate">
            <tr>
              <th className="px-4 py-3">Compare</th>
              <th className="px-4 py-3">Starter</th>
              <th className="px-4 py-3">Pro</th>
              <th className="px-4 py-3">Team</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-mist">
            {rows.map((r) => (
              <tr key={r.label} className="text-ink/85">
                <td className="px-4 py-3 font-medium text-ink">{r.label}</td>
                <td className="px-4 py-3">{r.starter}</td>
                <td className="px-4 py-3">{r.pro}</td>
                <td className="px-4 py-3">{r.team}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-10 text-center text-sm text-ink/65">
        Questions?{" "}
        <Link href="/faq" className="font-semibold text-slate underline-offset-4 hover:underline">
          Read the FAQ
        </Link>
        .
      </p>
    </div>
  );
}
