/**
 * @file apps/web/src/components/product/ProductInput.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

/**
 * Handles product input behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-3 font-dm-sans text-sm text-mkt-ink transition-all placeholder:text-mkt-muted/70 focus:border-mkt-accent focus:outline-none focus:ring-1 focus:ring-mkt-accent disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

/**
 * Handles product select behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductSelect({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "w-full rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-3 font-dm-sans text-sm text-mkt-ink transition-all focus:border-mkt-accent focus:outline-none focus:ring-1 focus:ring-mkt-accent disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

/**
 * Handles product textarea behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductTextarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-3 font-dm-sans text-sm text-mkt-ink transition-all placeholder:text-mkt-muted/70 focus:border-mkt-accent focus:outline-none focus:ring-1 focus:ring-mkt-accent disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}
