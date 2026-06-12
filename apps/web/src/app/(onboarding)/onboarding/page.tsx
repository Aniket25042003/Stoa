import { Suspense } from "react";
import { OnboardingWizard } from "@/components/onboarding/OnboardingWizard";

export default function OnboardingPage() {
  return (
    <Suspense fallback={<p className="text-sm text-on-surface-variant">Loading...</p>}>
      <OnboardingWizard />
    </Suspense>
  );
}
