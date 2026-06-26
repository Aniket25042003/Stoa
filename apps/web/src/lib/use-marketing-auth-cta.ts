"use client";

import { useEffect, useState } from "react";
import { getAuthEntryPath, getMarketingCta, type MarketingCta } from "@/lib/auth-entry";
import { routeForSessionState, type SessionState } from "@/lib/auth-workflow";

type MarketingAuthCta = Omit<MarketingCta, "href"> & {
  href: string;
  authenticated: boolean;
  loading: boolean;
};

const signedOutCta = getMarketingCta();

/**
 * Resolves marketing CTA targets: signed-in users go to the app, others to login/waitlist.
 */
export function useMarketingAuthCta(): MarketingAuthCta {
  const [cta, setCta] = useState<MarketingAuthCta>({
    ...signedOutCta,
    authenticated: false,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const res = await fetch("/api/auth/session", { cache: "no-store" });
        if (!res.ok) {
          if (!cancelled) {
            setCta({ ...signedOutCta, authenticated: false, loading: false });
          }
          return;
        }

        const state = (await res.json()) as SessionState & { authenticated?: boolean };
        if (cancelled) return;

        if (state.authenticated) {
          const appHref = routeForSessionState(state);
          setCta({
            href: appHref,
            navLabel: "Open app",
            buttonLabel: "Open app",
            heroLabel: "Open app",
            footerDescription: "Return to your marketing intelligence workspace.",
            bandTitle: "Welcome back",
            bandDescription: "Pick up where you left off in your workspace.",
            authenticated: true,
            loading: false,
          });
          return;
        }

        setCta({ ...getMarketingCta(), authenticated: false, loading: false });
      } catch {
        if (!cancelled) {
          setCta({
            ...getMarketingCta({ hostname: window.location.hostname }),
            authenticated: false,
            loading: false,
          });
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return cta;
}

export function marketingAuthEntryPath(): string {
  return getAuthEntryPath(
    typeof window !== "undefined" ? { hostname: window.location.hostname } : undefined,
  );
}
