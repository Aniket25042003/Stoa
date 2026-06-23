/**
 * @file apps/web/src/app/(app)/data/profile/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies React
 */
"use client";

import { productLabelClass } from "@/lib/product-typography";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductTextarea,
} from "@/components/product";
import { useDataHub } from "../data-hub-context";

const labelClass = productLabelClass;

/**
 * Handles data profile page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function DataProfilePage() {
  const { profile, saving } = useDataHub();
  const {
    name,
    setName,
    websiteUrl,
    setWebsiteUrl,
    industry,
    setIndustry,
    targetCustomers,
    setTargetCustomers,
    businessModel,
    setBusinessModel,
    stage,
    setStage,
    goals,
    setGoals,
    brandVoice,
    setBrandVoice,
    competitorNotes,
    setCompetitorNotes,
    saveProfile,
  } = profile;

  return (
    <ProductCard>
      <form onSubmit={(e) => void saveProfile(e)} className="space-y-4">
        <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Company profile</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className={labelClass}>Company name</label>
            <ProductInput value={name} onChange={(e) => setName(e.target.value)} required className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Website URL</label>
            <ProductInput value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)} className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Industry</label>
            <ProductInput value={industry} onChange={(e) => setIndustry(e.target.value)} className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Business model</label>
            <ProductInput value={businessModel} onChange={(e) => setBusinessModel(e.target.value)} className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Stage</label>
            <ProductInput value={stage} onChange={(e) => setStage(e.target.value)} placeholder="seed, growth, etc." className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Target customers</label>
            <ProductInput value={targetCustomers} onChange={(e) => setTargetCustomers(e.target.value)} className="mt-1.5" />
          </div>
        </div>
        <div>
          <label className={labelClass}>Goals</label>
          <ProductTextarea value={goals} onChange={(e) => setGoals(e.target.value)} className="mt-1.5 min-h-[80px]" />
        </div>
        <div>
          <label className={labelClass}>Brand voice guidelines</label>
          <ProductTextarea value={brandVoice} onChange={(e) => setBrandVoice(e.target.value)} className="mt-1.5 min-h-[80px]" />
        </div>
        <div>
          <label className={labelClass}>Known competitors (notes)</label>
          <ProductTextarea value={competitorNotes} onChange={(e) => setCompetitorNotes(e.target.value)} className="mt-1.5 min-h-[60px]" />
        </div>
        <ProductButton type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save profile"}
        </ProductButton>
      </form>
    </ProductCard>
  );
}
