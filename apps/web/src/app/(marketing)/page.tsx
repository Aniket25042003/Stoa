"use client";

import { LoadingGate } from "@/components/marketing/immersive/LoadingGate";
import { ScrollProgress } from "@/components/marketing/immersive/ScrollProgress";
import { ScrollLinkedLanding } from "@/components/marketing/immersive/ScrollLinkedLanding";

export default function LandingPage() {
  return (
    <>
      <LoadingGate />
      <ScrollProgress />
      <ScrollLinkedLanding />
    </>
  );
}
