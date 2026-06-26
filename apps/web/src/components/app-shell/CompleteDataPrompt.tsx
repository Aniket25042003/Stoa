/**
 * @file apps/web/src/components/app-shell/CompleteDataPrompt.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
import Link from "next/link";
import { ProductButton, ProductCard } from "@/components/product";
import { formatCompletenessMissingSentence } from "@/lib/user-facing-copy";

/**
 * Handles complete data prompt behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function CompleteDataPrompt({
  title,
  message,
  missing,
}: {
  title: string;
  message: string;
  missing?: string[];
}) {
  return (
    <ProductCard className="border-mkt-accent/20 bg-mkt-accent/[0.04]">
      <h3 className="text-lg font-semibold tracking-tight text-mkt-ink">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-mkt-muted">{message}</p>
      {missing && missing.length > 0 ? (
        <p className="mt-2 text-xs text-mkt-muted">{formatCompletenessMissingSentence(missing)}</p>
      ) : null}
      <Link href="/data/profile" className="mt-4 inline-block">
        <ProductButton>Go to Data hub</ProductButton>
      </Link>
    </ProductCard>
  );
}
