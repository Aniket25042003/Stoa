import { cn } from "@/lib/cn";

export function Marquee({ items, className }: { items: string[]; className?: string }) {
  const doubled = [...items, ...items];
  return (
    <div className={cn("overflow-hidden border-y border-outline-variant/55 bg-surface-container-low/68 py-3 backdrop-blur-md sm:py-4", className)}>
      <div className="flex w-max animate-marquee gap-x-10 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-primary sm:gap-x-16 sm:text-[11px]">
        {doubled.map((t, i) => (
          <span key={`${t}-${i}`} className="flex shrink-0 items-center gap-3">
            <span className="h-1.5 w-1.5 bg-primary" />
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
