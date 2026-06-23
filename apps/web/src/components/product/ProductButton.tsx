/**
 * @file apps/web/src/components/product/ProductButton.tsx
 * @layer Frontend Design System
 * @description Marketing V3–aligned pill buttons for app surfaces.
 * @dependencies React
 */
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type ProductButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
};

const variants = {
  primary: "mkt-solid-btn border-none text-white",
  secondary:
    "rounded-full border border-mkt-border bg-mkt-surface-elevated px-4 py-2.5 text-sm font-medium text-mkt-ink hover:border-mkt-ink/20 hover:bg-mkt-surface",
  ghost: "rounded-full px-4 py-2.5 text-sm font-medium text-mkt-muted hover:bg-mkt-ink/[0.04] hover:text-mkt-ink",
};

/**
 * Handles product button behavior for this part of the Stoa application.
 *
 * @param variant - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductButton({
  variant = "primary",
  className,
  children,
  ...props
}: ProductButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 transition-all disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
