/**
 * @file apps/web/src/components/product/ProductCard.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Handles product card behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductCard({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div
      className={cn(
        "rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface p-5 shadow-[0_4px_24px_rgba(20,20,26,0.04)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
