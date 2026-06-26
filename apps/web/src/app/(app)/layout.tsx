/**
 * @file apps/web/src/app/(app)/layout.tsx
 * @layer Frontend Product UI
 * @description Defines shared route layout structure, metadata, and navigation boundaries.
 * @dependencies Supabase, Next.js, React
 */
import { AppShell } from "@/components/app-shell/AppShell";
import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { createClient } from "@/lib/supabase/server";
import { getServerApiBase } from "@/lib/server-api";
import { getServerActiveOrgId } from "@/lib/active-org-server";
import { trustedProxyHeadersFromHeaders } from "@/lib/proxy-headers";
import { type SessionState } from "@/lib/auth-workflow";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    const apiBase = getServerApiBase();
    if (apiBase && session?.access_token) {
      const activeOrg = await getServerActiveOrgId();
      try {
        const res = await fetch(`${apiBase}/v1/auth/session-state`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            ...(activeOrg ? { "X-Org-Id": activeOrg } : {}),
            ...trustedProxyHeadersFromHeaders(await headers()),
          },
          cache: "no-store",
        });
        if (res.ok) {
          const state = (await res.json()) as SessionState;
          if (state.needs_email_verification) {
            redirect("/verify-email");
          }
          if (state.needs_onboarding) {
            redirect("/onboarding");
          }
        }
      } catch {
        // Allow render when API unavailable in local dev.
      }
    }
  }

  const displayName = user
    ? ((user.user_metadata?.full_name as string | undefined) ??
        (user.user_metadata?.name as string | undefined) ??
        null)
    : null;

  return user?.email ? (
    <AppShell email={user.email} displayName={displayName}>
      {children}
    </AppShell>
  ) : (
    <div className="product-v2 min-h-screen">{children}</div>
  );
}
