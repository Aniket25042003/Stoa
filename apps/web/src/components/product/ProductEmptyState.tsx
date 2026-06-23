/**
 * @file apps/web/src/components/product/ProductEmptyState.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
import type { ReactNode } from "react";
import Link from "next/link";
import { ProductButton } from "./ProductButton";

export function ProductEmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}) {
  const action =
    actionLabel && actionHref ? (
      <Link href={actionHref}>
        <ProductButton>{actionLabel}</ProductButton>
      </Link>
    ) : actionLabel && onAction ? (
      <ProductButton onClick={onAction}>{actionLabel}</ProductButton>
    ) : null;

  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-mkt-border bg-mkt-surface/50 px-6 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-mkt-ink/5">
        <span className="text-lg font-semibold text-mkt-muted">—</span>
      </div>
      <h3 className="text-lg font-semibold tracking-tight text-mkt-ink">{title}</h3>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-mkt-muted">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

/**
 * Handles product table behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductTable({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`overflow-x-auto rounded-2xl border border-mkt-border ${className ?? ""}`}>
      <table className="w-full min-w-[480px] border-collapse text-left text-sm">{children}</table>
    </div>
  );
}

/**
 * Handles product table head behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductTableHead({ children }: { children: ReactNode }) {
  return (
    <thead className="border-b border-mkt-ink/[0.06] bg-mkt-ink/[0.02]">
      <tr>{children}</tr>
    </thead>
  );
}

/**
 * Handles product table header cell behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductTableHeaderCell({ children }: { children: ReactNode }) {
  return (
    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-mkt-subtle">
      {children}
    </th>
  );
}

/**
 * Handles product table cell behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductTableCell({ children, className }: { children: ReactNode; className?: string }) {
  return <td className={`border-t border-mkt-ink/[0.04] px-4 py-3 text-mkt-ink ${className ?? ""}`}>{children}</td>;
}
