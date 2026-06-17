"use client";

import Link from "next/link";
import { Check, X } from "lucide-react";
import { useState } from "react";
import { MarketingCtaBand } from "@/components/marketing/MarketingCtaBand";
import { PricingCard } from "@/components/marketing/PricingCard";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { MarketingPageShell } from "@/components/marketing/immersive/MarketingPageShell";
import { getAuthEntryPath, getMarketingCta } from "@/lib/auth-entry";
import { BRAND_SUBHEAD } from "@/lib/brand";
import { cn } from "@/lib/cn";

const tiers = (yearly: boolean, authEntry: string) => [
  {
    name: "Starter",
    price: "$0",
    period: yearly ? "/ year" : "/ month",
    description: "For founders mapping their first product narrative.",
    features: ["1 brand workspace", "Strategy blueprint", "Campaign ideation", "Community access"],
    cta: "Start free",
    href: authEntry,
    highlighted: false,
  },
  {
    name: "Pro",
    price: yearly ? "$190" : "$19",
    period: yearly ? "/ year" : "/ month",
    description: "For growing companies launching dynamic weekly campaigns.",
    features: [
      "5 brand workspaces",
      "Full strategy development",
      "Campaign-ready deliverables",
      "Creative direction tools",
      "Priority support",
    ],
    cta: "Get Pro",
    href: authEntry,
    highlighted: true,
  },
  {
    name: "Team",
    price: yearly ? "$490" : "$49",
    period: yearly ? "/ year" : "/ month",
    description: "For agencies and teams running campaign studios at scale.",
    features: [
      "Unlimited brand workspaces",
      "Shared team dashboard",
      "Priority support",
      "Export-ready documents",
    ],
    cta: "Talk to us",
    href: "/faq",
    highlighted: false,
  },
];

const rows = [
  { label: "Brand workspaces", starter: "1", pro: "5", team: "Unlimited" },
  { label: "Strategy blueprinting", starter: "yes", pro: "yes", team: "yes" },
  { label: "Campaign deliverables", starter: "Limited", pro: "yes", team: "yes" },
  { label: "Export-ready documents", starter: "no", pro: "yes", team: "yes" },
];

function CompareCell({ value }: { value: string }) {
  const v = value.toLowerCase();
  const tdClass = "px-3 py-3 align-middle sm:px-5 sm:py-4 text-center tabular-nums";

  if (v === "yes") {
    return (
      <td className={tdClass}>
        <span className="flex h-full min-h-[1.5rem] w-full items-center justify-center">
          <Check className="h-5 w-5 shrink-0 text-mkt-accent" strokeWidth={2.5} aria-label="Included" />
        </span>
      </td>
    );
  }
  if (v === "no") {
    return (
      <td className={tdClass}>
        <span className="flex h-full min-h-[1.5rem] w-full items-center justify-center">
          <X className="h-5 w-5 shrink-0 text-mkt-muted/50" strokeWidth={2.5} aria-label="Not included" />
        </span>
      </td>
    );
  }
  return (
    <td className={tdClass}>
      <span className="inline-block w-full text-center font-dm-sans font-medium text-mkt-ink">{value}</span>
    </td>
  );
}

export default function PricingPage() {
  const [yearly, setYearly] = useState(true);
  const list = tiers(yearly, getAuthEntryPath());
  const marketingCta = getMarketingCta();

  return (
    <MarketingPageShell>
      <RevealOnScroll>
        <SectionHeader
          eyebrow="Pricing"
          title="Simple tiers for strategy and marketing teams."
          lead={`${BRAND_SUBHEAD} Pricing shown is illustrative—start with one company workspace, then add more when your portfolio grows.`}
        />
      </RevealOnScroll>

      <div className="mt-10 flex justify-center">
        <div className="inline-flex rounded-sm border border-mkt-ink/[0.08] bg-mkt-surface/80 p-1 shadow-[0_4px_20px_-8px_rgba(20,20,26,0.1)]">
          <button
            type="button"
            onClick={() => setYearly(false)}
            className={cn(
              "rounded-sm px-5 py-2 font-dm-sans text-[10px] font-bold uppercase tracking-widest transition-colors",
              !yearly ? "bg-mkt-ink text-mkt-dark-ink shadow-sm" : "text-mkt-muted hover:text-mkt-ink"
            )}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setYearly(true)}
            className={cn(
              "rounded-sm px-5 py-2 font-dm-sans text-[10px] font-bold uppercase tracking-widest transition-colors",
              yearly ? "bg-mkt-ink text-mkt-dark-ink shadow-sm" : "text-mkt-muted hover:text-mkt-ink"
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

      <div className="mt-20 overflow-x-auto rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface/90 shadow-[0_8px_32px_-16px_rgba(20,20,26,0.08)]">
        <table className="w-full min-w-[600px] text-sm">
          <thead className="border-b border-mkt-ink/[0.06] bg-mkt-accent/[0.04] font-dm-sans text-[10px] font-bold uppercase tracking-[0.16em] text-mkt-accent">
            <tr>
              <th className="px-3 py-3 text-left sm:px-5 sm:py-4">Compare</th>
              <th className="px-3 py-3 text-center sm:px-5 sm:py-4">Starter</th>
              <th className="px-3 py-3 text-center sm:px-5 sm:py-4">Pro</th>
              <th className="px-3 py-3 text-center sm:px-5 sm:py-4">Team</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-mkt-ink/[0.06]">
            {rows.map((r) => (
              <tr key={r.label} className="font-dm-sans text-mkt-muted">
                <td className="px-3 py-3 text-left font-semibold text-mkt-ink sm:px-5 sm:py-4">{r.label}</td>
                <CompareCell value={r.starter} />
                <CompareCell value={r.pro} />
                <CompareCell value={r.team} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-10 text-center font-dm-sans text-sm text-mkt-muted">
        Questions?{" "}
        <Link href="/faq" className="font-semibold text-mkt-accent underline-offset-4 hover:underline">
          Read the FAQ
        </Link>
        .
      </p>

      <RevealOnScroll>
        <MarketingCtaBand
          className="mt-16"
          eyebrow="Early access"
          title={marketingCta.bandTitle}
          description={marketingCta.bandDescription}
          ctaLabel={marketingCta.buttonLabel}
          ctaHref={marketingCta.href}
        />
      </RevealOnScroll>
    </MarketingPageShell>
  );
}
