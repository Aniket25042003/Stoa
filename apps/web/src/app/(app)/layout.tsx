import { AppHeader } from "@/components/app-shell/AppHeader";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { getServerApiBase } from "@/lib/server-api";
import { getServerActiveOrgId } from "@/lib/active-org-server";
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

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <div className="pointer-events-none fixed inset-0 -z-10 grid-bg dark:starfield" />
      {user?.email ? <AppHeader email={user.email} /> : null}
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10">{children}</div>
    </div>
  );
}
