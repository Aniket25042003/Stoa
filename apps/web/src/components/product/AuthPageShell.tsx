/**
 * @file apps/web/src/components/product/AuthPageShell.tsx
 * @layer Frontend Design System
 * @description Marketing V3–aligned auth shell (typography matches landing / waitlist).
 * @dependencies Next.js, React
 */
import Link from "next/link";
import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import { BrandLogo } from "./BrandLogo";
import { ProductShellFrame } from "./ProductAtmosphere";

/** Shared label style — matches WaitlistForm / marketing V3 forms. */
export const authLabelClass = "text-xs font-medium uppercase tracking-wider text-mkt-subtle";

/**
 * Handles auth page shell behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthPageShell({
  children,
  lead,
}: {
  children: ReactNode;
  lead?: ReactNode;
}) {
  return (
    <ProductShellFrame atmosphere="auth">
      <div className="relative min-h-screen px-4 py-10 md:px-6">
        <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col gap-10 lg:flex-row lg:items-center lg:gap-16">
          <div className="flex-1 space-y-6 lg:max-w-lg">{lead}</div>
          <div className="flex flex-1 justify-center lg:justify-end">{children}</div>
        </div>
      </div>
    </ProductShellFrame>
  );
}

/**
 * Handles auth brand mark behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthBrandMark() {
  return (
    <Link href="/" className="inline-flex items-center">
      <BrandLogo variant="logo" size="md" priority />
    </Link>
  );
}

/**
 * Handles auth card behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthCard({ children }: { children: ReactNode }) {
  return (
    <div className="w-full max-w-md rounded-2xl border border-mkt-border bg-mkt-surface-elevated p-8 shadow-[0_20px_60px_-20px_rgba(0,0,0,0.12)]">
      {children}
    </div>
  );
}

/**
 * Handles auth card header behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthCardHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="mb-8">
      <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">{eyebrow}</p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight text-mkt-ink">{title}</h1>
      <p className="mt-2 text-sm leading-relaxed text-mkt-muted">{description}</p>
    </div>
  );
}

/**
 * Handles auth form label behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthLabel({ children, htmlFor }: { children: ReactNode; htmlFor?: string }) {
  return (
    <label htmlFor={htmlFor} className={authLabelClass}>
      {children}
    </label>
  );
}

/**
 * Handles auth form input behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-xl border border-mkt-border bg-mkt-surface px-4 py-3 text-sm text-mkt-ink transition-all placeholder:text-mkt-muted focus:border-mkt-ink focus:outline-none focus:ring-1 focus:ring-mkt-ink disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

/**
 * Secondary full-width SSO / outline button for auth flows.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthOutlineButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex w-full items-center justify-center gap-2 rounded-full border border-mkt-border bg-mkt-surface-elevated px-4 py-2.5 text-sm font-medium text-mkt-ink transition-all hover:border-mkt-ink/20 hover:bg-mkt-surface disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

/**
 * Handles auth section divider behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AuthDivider({ label }: { label: string }) {
  return (
    <div className="my-6 flex items-center gap-3 text-xs font-medium uppercase tracking-wider text-mkt-subtle">
      <span className="h-px flex-1 bg-mkt-border" />
      {label}
      <span className="h-px flex-1 bg-mkt-border" />
    </div>
  );
}
