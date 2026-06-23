/**
 * @file apps/web/src/components/product/ProductPageHeader.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { productBodyClass, productEyebrowClass, productH1Class } from "@/lib/product-typography";

/**
 * Handles product page header behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductPageHeader({
  eyebrow,
  title,
  lead,
  actions,
  className,
}: {
  eyebrow?: string;
  title: string;
  lead?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="max-w-3xl">
        {eyebrow ? <p className={productEyebrowClass}>{eyebrow}</p> : null}
        <h1 className={cn(eyebrow ? "mt-2" : "", productH1Class)}>{title}</h1>
        {lead ? <p className={cn("mt-3 max-w-2xl md:text-base", productBodyClass)}>{lead}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

/**
 * Section heading used inside workspace cards and panels.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductSectionTitle({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <h2 className={cn("text-lg font-semibold tracking-tight text-mkt-ink", className)}>{children}</h2>;
}

/**
 * Form label matching marketing V3 / waitlist forms.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductLabel({
  children,
  htmlFor,
  className,
}: {
  children: ReactNode;
  htmlFor?: string;
  className?: string;
}) {
  return (
    <label htmlFor={htmlFor} className={cn("text-xs font-medium uppercase tracking-wider text-mkt-subtle", className)}>
      {children}
    </label>
  );
}
