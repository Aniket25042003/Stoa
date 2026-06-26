/**
 * @file apps/web/src/components/product/ProductBadge.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import { cn } from "@/lib/cn";
import { formatJobStatusLabel } from "@/lib/user-facing-copy";

/**
 * Handles product badge behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium uppercase tracking-wider",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

/**
 * Handles product status pill behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
      {formatJobStatusLabel(status)}
    </ProductBadge>
  );
}
