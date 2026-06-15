"use client";

import { cn } from "@/lib/cn";

export function SectionHeader({
  eyebrow,
  title,
  lead,
  className,
  titleClassName,
}: {
  eyebrow: string;
  title: string;
  lead?: string;
  className?: string;
  titleClassName?: string;
}) {
  return (
    <div className={cn("max-w-3xl", className)}>
      <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">
        {eyebrow}
      </p>
      <h1
        className={cn(
          "mt-4 font-syne text-[clamp(2rem,5vw,3.75rem)] font-extrabold uppercase leading-[1.05] tracking-tight text-mkt-ink",
          titleClassName
        )}
      >
        {title}
      </h1>
      {lead ? (
        <p className="mt-5 max-w-2xl font-dm-sans text-base leading-relaxed text-mkt-muted md:text-lg">
          {lead}
        </p>
      ) : null}
    </div>
  );
}
