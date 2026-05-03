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
        "relative flex flex-col rounded-2xl border bg-cream/95 p-8",
        highlighted ? "border-slate shadow-glow ring-2 ring-slate/30" : "border-mist"
      )}
      whileHover={reduce ? undefined : { y: -4, boxShadow: "var(--shadow-glow)" }}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
    >
      {highlighted ? (
        <span className="absolute -top-3 left-6 rounded-full bg-slate px-3 py-0.5 font-mono text-[10px] uppercase tracking-widest text-cream">
          Popular
        </span>
      ) : null}
      <h3 className="text-xl font-semibold text-ink">{name}</h3>
      <p className="mt-2 text-sm text-ink/70">{description}</p>
      <div className="mt-6 flex items-baseline gap-1">
        <span className="font-mono text-4xl font-semibold tracking-tight text-ink">{price}</span>
        <span className="font-mono text-sm text-slate">{period}</span>
      </div>
      <ul className="mt-8 flex flex-1 flex-col gap-3 text-sm text-ink/85">
        {features.map((f) => (
          <li key={f} className="flex gap-2">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-slate" strokeWidth={2} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <Link
        href={href}
        className={cn(
          "mt-8 inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition-opacity hover:opacity-90",
          highlighted ? "bg-slate text-cream" : "border border-mist bg-cream text-ink hover:border-slate/50"
        )}
      >
        {cta}
      </Link>
    </motion.div>
  );
}
