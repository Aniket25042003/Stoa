import { cn } from "@/lib/cn";

export function Marquee({ items, className }: { items: string[]; className?: string }) {
  const doubled = [...items, ...items];
  return (
    <div className={cn("overflow-hidden border-y border-outline-variant/55 bg-white/58 py-4 backdrop-blur-md", className)}>
      <div className="flex w-max animate-marquee gap-x-16 font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-primary">
        {doubled.map((t, i) => (
          <span key={`${t}-${i}`} className="flex shrink-0 items-center gap-3">
            <span className="h-1.5 w-1.5 rounded-full bg-gradient-to-r from-primary to-violet-pulse" />
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
