"use client";

import { cn } from "@/lib/cn";

export function SectionHeader({
  eyebrow,
  title,
  lead,
  className,
}: {
  eyebrow: string;
  title: string;
  lead?: string;
  className?: string;
}) {
  return (
    <div className={cn("max-w-3xl", className)}>
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-4 font-display text-4xl font-bold leading-[1.08] tracking-[-0.035em] text-slate-deep md:text-6xl">
        {title}
      </h2>
      {lead ? <p className="mt-5 text-lg leading-8 text-on-surface-variant md:text-xl">{lead}</p> : null}
    </div>
  );
}
