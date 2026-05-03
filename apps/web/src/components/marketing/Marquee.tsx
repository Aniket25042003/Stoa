import { cn } from "@/lib/cn";

export function Marquee({ items, className }: { items: string[]; className?: string }) {
  const doubled = [...items, ...items];
  return (
    <div className={cn("overflow-hidden border-y border-mist/90 bg-cream/70 py-3", className)}>
      <div className="flex w-max animate-marquee gap-x-14 gap-y-2 font-mono text-[11px] uppercase tracking-[0.28em] text-slate">
        {doubled.map((t, i) => (
          <span key={`${t}-${i}`} className="shrink-0">
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
