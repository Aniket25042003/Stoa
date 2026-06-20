/**
 * @file apps/web/src/app/(marketing)/page.tsx
 * @layer Frontend Marketing UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies React
 */
"use client";

import { LoadingGate } from "@/components/marketing/immersive/LoadingGate";
import { ScrollProgress } from "@/components/marketing/immersive/ScrollProgress";
import { ScrollLinkedLanding } from "@/components/marketing/immersive/ScrollLinkedLanding";

/**
 * Handles landing page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function LandingPage() {
  return (
    <>
      <LoadingGate />
      <ScrollProgress />
      <ScrollLinkedLanding />
    </>
  );
}
