/**
 * @file apps/web/src/components/product/ProductInput.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

const fieldClass =
  "w-full rounded-xl border border-mkt-border bg-mkt-surface px-4 py-3 text-sm text-mkt-ink transition-all placeholder:text-mkt-muted focus:border-mkt-ink focus:outline-none focus:ring-1 focus:ring-mkt-ink disabled:opacity-50";

/**
 * Handles product input behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldClass, className)} {...props} />;
}

/**
 * Handles product select behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductSelect({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(fieldClass, "bg-mkt-surface-elevated", className)} {...props} />;
}

/**
 * Handles product textarea behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductTextarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldClass, className)} {...props} />;
}
