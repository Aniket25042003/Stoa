/**
 * @file apps/web/src/components/product/AuthPageShell.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
import Link from "next/link";
import type { ReactNode } from "react";
import { BrandLogo } from "./BrandLogo";
import { ProductShellFrame } from "./ProductAtmosphere";

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
    <ProductShellFrame>
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
    <div className="w-full max-w-md rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface/90 p-7 shadow-[0_30px_70px_rgba(20,20,26,0.06)] backdrop-blur-xl md:p-8">
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
      <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">{eyebrow}</p>
      <h1 className="mt-3 font-syne text-2xl font-extrabold uppercase tracking-tight text-mkt-ink">{title}</h1>
      <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted">{description}</p>
    </div>
  );
}
