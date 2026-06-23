import { cn } from "@/lib/cn";

export function MiniCard({
  children,
  className,
  hover = true,
}: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-mkt-border bg-mkt-surface-elevated p-4 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.08)]",
        hover && "mkt-mini-card",
        className
      )}
    >
      {children}
    </div>
  );
}

export function PastelSectionCard({
  children,
  gradient,
  className,
  id,
}: {
  children: React.ReactNode;
  gradient: string;
  className?: string;
  id?: string;
}) {
  return (
    <div
      id={id}
      className={cn("mkt-pastel-card", className)}
      style={{ "--mkt-card-gradient": gradient } as React.CSSProperties}
    >
      {children}
    </div>
  );
}
