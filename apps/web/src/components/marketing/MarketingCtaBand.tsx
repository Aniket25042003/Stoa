/**
 * @file apps/web/src/components/marketing/MarketingCtaBand.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/cn";

/**
 * Handles marketing cta band behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function MarketingCtaBand({
  eyebrow,
  title,
  description,
  ctaLabel,
  ctaHref,
  className,
}: {
  eyebrow: string;
  title: string;
  description: string;
  ctaLabel: string;
  ctaHref: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-sm border border-mkt-ink/[0.06] bg-mkt-dark-band px-6 py-10 text-center md:px-10 md:py-12",
        className
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.1]"
        aria-hidden
        style={{
          backgroundImage:
            "linear-gradient(rgba(242,240,235,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(242,240,235,0.1) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="pointer-events-none absolute left-1/2 top-0 h-32 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-mkt-accent/25 blur-3xl" />

      <div className="relative z-10">
        <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent-warm">
          {eyebrow}
        </p>
        <h2 className="mt-3 font-syne text-2xl font-extrabold uppercase tracking-tight text-mkt-dark-ink md:text-3xl">
          {title}
        </h2>
        <p className="mx-auto mt-3 max-w-md font-dm-sans text-sm leading-relaxed text-mkt-dark-ink/65">
          {description}
        </p>
        <Link
          href={ctaHref}
          className="group mt-7 inline-flex items-center gap-2 rounded-sm bg-mkt-accent px-6 py-3.5 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_8px_24px_rgba(79,70,229,0.35)] transition-all hover:bg-[#4338CA]"
        >
          {ctaLabel}
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>
    </div>
  );
}
