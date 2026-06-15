"use client";

import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Check } from "lucide-react";
import { cn } from "@/lib/cn";

export function PricingCard({
  name,
  price,
  period,
  description,
  features,
  cta,
  href,
  highlighted,
}: {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  highlighted?: boolean;
}) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={cn(
        "relative flex min-h-full flex-col rounded-sm border p-8 transition-shadow",
        highlighted
          ? "border-mkt-accent/30 bg-mkt-surface shadow-[0_20px_60px_-24px_rgba(79,70,229,0.25)]"
          : "border-mkt-ink/[0.06] bg-mkt-surface/80 shadow-[0_8px_32px_-16px_rgba(20,20,26,0.08)]"
      )}
      whileHover={
        reduce
          ? undefined
          : {
              y: -4,
              boxShadow: highlighted
                ? "0 24px 70px -20px rgba(79,70,229,0.3)"
                : "0 16px 48px -20px rgba(20,20,26,0.12)",
            }
      }
      transition={{ type: "spring", stiffness: 280, damping: 26 }}
    >
      {highlighted ? (
        <span className="absolute -top-3 left-6 rounded-full border border-mkt-accent/30 bg-mkt-accent px-3 py-1 font-dm-sans text-[8px] font-bold uppercase tracking-[0.18em] text-mkt-dark-ink shadow-[0_4px_16px_rgba(79,70,229,0.3)]">
          Popular
        </span>
      ) : null}

      <h3 className="font-syne text-xl font-extrabold uppercase tracking-tight text-mkt-ink">{name}</h3>
      <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted">{description}</p>

      <div className="mt-7 flex items-baseline gap-1.5">
        <span className="font-syne text-5xl font-extrabold tracking-tight text-mkt-ink">{price}</span>
        <span className="font-dm-sans text-xs font-semibold uppercase tracking-wider text-mkt-accent">
          {period}
        </span>
      </div>

      <ul className="mt-8 flex flex-1 flex-col gap-3 font-dm-sans text-sm text-mkt-muted">
        {features.map((f) => (
          <li key={f} className="flex gap-3">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-mkt-accent" strokeWidth={2.5} />
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <Link
        href={href}
        className={cn(
          "group mt-8 inline-flex items-center justify-center gap-2 rounded-sm px-4 py-3.5 text-center font-dm-sans text-[10px] font-bold uppercase tracking-widest transition-all",
          highlighted
            ? "bg-mkt-accent text-mkt-dark-ink shadow-[0_8px_24px_rgba(79,70,229,0.25)] hover:bg-[#4338CA]"
            : "border border-mkt-ink/10 bg-mkt-surface text-mkt-ink hover:border-mkt-accent/30 hover:text-mkt-accent"
        )}
      >
        {cta}
        {highlighted ? (
          <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
        ) : null}
      </Link>
    </motion.div>
  );
}
