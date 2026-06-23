/**
 * @file apps/web/src/app/(onboarding)/onboarding/page.tsx
 * @layer Frontend Onboarding UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies React
 */
import { Suspense } from "react";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";

/**
 * Handles onboarding page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function OnboardingPage() {
  return (
    <Suspense fallback={<p className="text-sm text-mkt-muted">Loading...</p>}>
      <OnboardingWizard />
    </Suspense>
  );
}
