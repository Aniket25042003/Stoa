"use client";

import Link from "next/link";
import { Check, X } from "lucide-react";
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
    features: ["20 runs / month", "Live activity stream", "PDF export", "Pipeline trace IDs", "Email support"],
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
  { label: "Master plan approval", starter: "yes", pro: "yes", team: "yes" },
  { label: "Runs / month", starter: "1", pro: "20", team: "Unlimited" },
  { label: "PDF export", starter: "no", pro: "yes", team: "yes" },
  { label: "Trace IDs in activity", starter: "no", pro: "yes", team: "yes" },
];

function CompareCell({ value }: { value: string }) {
  const v = value.toLowerCase();
  const tdClass = "px-3 py-3 align-middle sm:px-5 sm:py-4 text-center tabular-nums";
  if (v === "yes") {
    return (
      <td className={tdClass}>
        <span className="flex h-full min-h-[1.5rem] w-full items-center justify-center">
          <Check className="h-5 w-5 shrink-0 text-primary" strokeWidth={2.5} aria-label="Included" />
        </span>
      </td>
    );
  }
  if (v === "no") {
    return (
      <td className={tdClass}>
        <span className="flex h-full min-h-[1.5rem] w-full items-center justify-center">
          <X className="h-5 w-5 shrink-0 text-on-surface-variant/55" strokeWidth={2.5} aria-label="Not included" />
        </span>
      </td>
    );
  }
  return (
    <td className={tdClass}>
      <span className="inline-block w-full text-center font-medium text-on-surface">{value}</span>
    </td>
  );
}

export default function PricingPage() {
  const [yearly, setYearly] = useState(true);
  const list = tiers(yearly);

  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="Pricing"
          title="Simple tiers. Serious GTM depth."
          lead="Pricing shown is illustrative - wire your billing when you are ready. The product paths stay the same."
        />
      </RevealOnScroll>

      <div className="mt-10 flex justify-center">
        <div className="inline-flex rounded-full border border-outline-variant/60 bg-surface-container-low/80 p-1 shadow-soft backdrop-blur-md">
          <button
            type="button"
            onClick={() => setYearly(false)}
            className={cn(
              "rounded-full px-5 py-2 text-sm font-bold transition-colors",
              !yearly ? "bg-slate-deep text-white shadow-sm" : "text-on-surface-variant hover:text-on-surface"
            )}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setYearly(true)}
            className={cn(
              "rounded-full px-5 py-2 text-sm font-bold transition-colors",
              yearly ? "bg-slate-deep text-white shadow-sm" : "text-on-surface-variant hover:text-on-surface"
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

      <div className="mt-20 overflow-x-auto rounded-3xl border border-outline-variant/60 bg-surface-container-low/80 shadow-soft backdrop-blur-md">
        <table className="w-full min-w-[600px] text-sm">
          <thead className="border-b border-outline-variant/60 bg-surface-container-low font-mono text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            <tr>
              <th className="px-3 py-3 text-left sm:px-5 sm:py-4">Compare</th>
              <th className="px-3 py-3 text-center sm:px-5 sm:py-4">Starter</th>
              <th className="px-3 py-3 text-center sm:px-5 sm:py-4">Pro</th>
              <th className="px-3 py-3 text-center sm:px-5 sm:py-4">Team</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/45">
            {rows.map((r) => (
              <tr key={r.label} className="text-on-surface-variant">
                <td className="px-3 py-3 text-left font-semibold text-on-surface sm:px-5 sm:py-4">{r.label}</td>
                <CompareCell value={r.starter} />
                <CompareCell value={r.pro} />
                <CompareCell value={r.team} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-10 text-center text-sm text-on-surface-variant">
        Questions?{" "}
        <Link href="/faq" className="font-bold text-primary underline-offset-4 hover:underline">
          Read the FAQ
        </Link>
        .
      </p>
    </div>
  );
}
