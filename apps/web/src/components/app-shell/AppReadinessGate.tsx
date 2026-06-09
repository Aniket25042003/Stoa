"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { SessionState } from "@/lib/auth-workflow";

const ALLOWED_WHILE_INCOMPLETE = new Set(["/onboarding"]);

export function AppReadinessGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const res = await apiFetch("/v1/auth/session-state");
      if (!res.ok) {
        if (!cancelled) setReady(true);
        return;
      }
      const state = (await res.json()) as SessionState;
      if (state.needs_email_verification) {
        router.replace(`/verify-email?next=${encodeURIComponent(pathname)}`);
        return;
      }
      if (state.needs_onboarding && !ALLOWED_WHILE_INCOMPLETE.has(pathname)) {
        router.replace("/onboarding");
        return;
      }
      if (!cancelled) setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  if (!ready) {
    return <div className="rounded-3xl p-8 card-glass text-center text-sm text-on-surface-variant">Preparing your workspace...</div>;
  }

  return <>{children}</>;
}
