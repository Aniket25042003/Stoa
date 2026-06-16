import { cn } from "@/lib/cn";

export function ProductBadge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: "default" | "accent" | "warm" | "success" | "error";
  className?: string;
}) {
  const variants = {
    default: "border-mkt-ink/10 bg-mkt-ink/[0.04] text-mkt-muted",
    accent: "border-mkt-accent/20 bg-mkt-accent/[0.08] text-mkt-accent",
    warm: "border-mkt-accent-warm/25 bg-mkt-accent-warm/[0.08] text-mkt-accent-warm",
    success: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700",
    error: "border-mkt-accent-warm/30 bg-mkt-accent-warm/10 text-mkt-accent-warm",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 font-dm-sans text-[9px] font-bold uppercase tracking-[0.14em]",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function ProductStatusPill({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const normalized = status.toLowerCase();
  const variant =
    normalized.includes("fail") || normalized.includes("error")
      ? "error"
      : normalized.includes("complete") || normalized.includes("ready") || normalized.includes("processed")
        ? "success"
        : normalized.includes("run") || normalized.includes("pending") || normalized.includes("queue")
          ? "accent"
          : "default";

  return (
    <ProductBadge variant={variant} className={className}>
      {status}
    </ProductBadge>
  );
}
