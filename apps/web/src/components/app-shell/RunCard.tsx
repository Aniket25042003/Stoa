/**
 * @file apps/web/src/components/app-shell/RunCard.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
import Link from "next/link";
import { ProductCard } from "@/components/product/ProductCard";
import { StatusPill } from "./StatusPill";

/**
 * Handles run card behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function RunCard({ id, status, createdAt }: { id: string; status: string; createdAt: string }) {
  return (
    <Link href={`/runs/${id}`} className="group block transition-transform hover:-translate-y-0.5">
      <ProductCard className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-semibold text-mkt-ink">{id.slice(0, 8)}...</span>
          <StatusPill status={status} />
        </div>
        <p className="mt-3 text-xs text-mkt-muted">{createdAt}</p>
        <span className="mt-5 inline-flex text-sm font-medium text-mkt-ink underline-offset-4 group-hover:underline">
          View run
        </span>
      </ProductCard>
    </Link>
  );
}
