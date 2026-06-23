/**
 * @file apps/web/src/app/(app)/companies-load-error.tsx
 * @layer Frontend Product UI
 * @description Implements companies load error behavior for the frontend product ui.
 * @dependencies Next.js, React
 */
import Link from "next/link";
import { ProductButton, ProductCard } from "@/components/product";

/**
 * Handles companies load error behavior for this part of the Stoa application.
 *
 * @param retryHref - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function CompaniesLoadError({ retryHref }: { retryHref: string }) {
  return (
    <div className="mx-auto max-w-lg px-6 py-16">
      <ProductCard className="space-y-4 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-mkt-ink">
          Could not load companies
        </h1>
        <p className="text-sm leading-relaxed text-mkt-muted">
          The workspace could not reach the companies API. You were not redirected because your session is valid—try
          again shortly instead of creating a duplicate company.
        </p>
        <Link href={retryHref} className="inline-block">
          <ProductButton>Retry</ProductButton>
        </Link>
      </ProductCard>
    </div>
  );
}
