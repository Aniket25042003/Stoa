/**
 * @file apps/web/src/app/(app)/data/competitors/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies React
 */
"use client";

import { ProductButton, ProductCard, ProductInput } from "@/components/product";
import { CompetitorsList } from "../competitors-list";
import { useDataHub } from "../data-hub-context";

const labelClass = "font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-muted";

/**
 * Handles data competitors page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function DataCompetitorsPage() {
  const { competitors, competitorsForm, refresh, showToast } = useDataHub();
  const { compName, setCompName, compUrl, setCompUrl, handleAddCompetitor } = competitorsForm;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <ProductCard>
        <form onSubmit={(e) => void handleAddCompetitor(e)} className="space-y-4">
          <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Add competitor</h2>
          <div>
            <label className={labelClass}>Name</label>
            <ProductInput value={compName} onChange={(e) => setCompName(e.target.value)} required className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Website URL</label>
            <ProductInput value={compUrl} onChange={(e) => setCompUrl(e.target.value)} className="mt-1.5" />
          </div>
          <ProductButton type="submit">Add competitor</ProductButton>
        </form>
      </ProductCard>

      <CompetitorsList
        competitors={competitors}
        onUpdated={() => {
          showToast("Competitor updated");
          void refresh();
        }}
        onDeleted={() => {
          showToast("Competitor removed");
          void refresh();
        }}
        onError={(message) => showToast(message, "error")}
      />
    </div>
  );
}
