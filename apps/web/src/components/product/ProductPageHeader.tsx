import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function ProductPageHeader({
  eyebrow,
  title,
  lead,
  actions,
  className,
}: {
  eyebrow?: string;
  title: string;
  lead?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="max-w-3xl">
        {eyebrow ? (
          <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="mt-2 font-syne text-2xl font-extrabold uppercase tracking-tight text-mkt-ink md:text-3xl">
          {title}
        </h1>
        {lead ? (
          <p className="mt-3 max-w-2xl font-dm-sans text-sm leading-relaxed text-mkt-muted md:text-base">
            {lead}
          </p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
