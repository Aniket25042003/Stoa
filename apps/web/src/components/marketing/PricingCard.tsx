"use client";

import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { Check } from "lucide-react";
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
        "relative flex min-h-full flex-col rounded-3xl p-8",
        highlighted ? "border border-primary/35 bg-white shadow-glow ring-4 ring-primary/10" : "card-glass"
      )}
      whileHover={reduce ? undefined : { y: -6, boxShadow: "var(--shadow-glow)" }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
    >
      {highlighted ? (
        <span className="absolute -top-3 left-6 rounded-full bg-gradient-to-r from-primary to-violet-pulse px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-white shadow-glow">
          Popular
        </span>
      ) : null}
      <h3 className="font-display text-2xl font-bold tracking-[-0.03em] text-slate-deep">{name}</h3>
      <p className="mt-3 text-sm leading-6 text-on-surface-variant">{description}</p>
      <div className="mt-7 flex items-baseline gap-1">
        <span className="font-display text-5xl font-extrabold tracking-[-0.04em] text-slate-deep">{price}</span>
        <span className="font-mono text-sm font-semibold text-primary">{period}</span>
      </div>
      <ul className="mt-8 flex flex-1 flex-col gap-3 text-sm text-on-surface-variant">
        {features.map((f) => (
          <li key={f} className="flex gap-3">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" strokeWidth={2.3} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <Link href={href} className={cn("mt-8 px-4 py-3 text-center text-sm", highlighted ? "btn-primary" : "btn-secondary")}>
        {cta}
      </Link>
    </motion.div>
  );
}
