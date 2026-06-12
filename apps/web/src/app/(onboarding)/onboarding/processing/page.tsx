"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function OnboardingProcessingPage() {
  const router = useRouter();
  const [message, setMessage] = useState("Indexing your company profile and seed documents...");

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      for (let i = 0; i < 30; i++) {
        const res = await apiFetch("/v1/onboarding/status");
        if (res.ok) {
          const body = await res.json();
          if (body.ready) {
            if (!cancelled) router.replace("/dashboard");
            return;
          }
          if (body.pending_ingestion_jobs) {
            setMessage(`Embedding ${body.pending_ingestion_jobs} seed document(s) into memory...`);
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
    <div className="rounded-3xl p-8 card-glass text-center space-y-4">
      <h1 className="font-display text-2xl font-bold">Preparing your workspace</h1>
      <p className="text-sm text-on-surface-variant">{message}</p>
      <button type="button" className="btn-primary px-5 py-3 text-sm" onClick={() => router.replace("/dashboard")}>
        Go to dashboard
      </button>
    </div>
  );
}
