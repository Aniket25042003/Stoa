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
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate">{eyebrow}</p>
      <h2 className="mt-3 text-4xl font-semibold tracking-tight text-ink md:text-6xl md:leading-[1.05]">{title}</h2>
      {lead ? <p className="mt-4 text-lg leading-relaxed text-ink/70 md:text-xl">{lead}</p> : null}
    </div>
  );
}
