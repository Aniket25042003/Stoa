/**
 * @file apps/web/src/app/(onboarding)/onboarding/processing/page.tsx
 * @layer Frontend Onboarding UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React, BFF apiFetch
 */
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ProductButton, ProductCard } from "@/components/product";

/**
 * Handles onboarding processing page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function OnboardingProcessingPage() {
  const router = useRouter();
  const [message, setMessage] = useState("Indexing your company profile and seed documents...");

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      for (let i = 0; i < 45; i++) {
        const res = await apiFetch("/v1/onboarding/status");
        if (res.ok) {
          const body = await res.json();
          if (body.ready) {
            if (!cancelled) router.replace("/agent");
            return;
          }
          if (body.pending_enrichment_jobs) {
            setMessage("Researching your company on the web…");
          } else if (body.pending_ingestion_jobs) {
            setMessage("Preparing your documents…");
          } else if (body.partial_ready) {
            setMessage("Company profile indexed. Finishing background research…");
          }
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
      if (!cancelled) {
        setMessage("Setup is taking longer than expected. You can continue to the dashboard.");
      }
    };
    void poll();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <ProductCard className="space-y-4 p-8 text-center">
      <h1 className="text-2xl font-semibold tracking-tight text-mkt-ink">
        Preparing your workspace
      </h1>
      <p className="text-sm text-mkt-muted">{message}</p>
      <ProductButton type="button" onClick={() => router.replace("/agent")}>
        Open STOA
      </ProductButton>
    </ProductCard>
  );
}
