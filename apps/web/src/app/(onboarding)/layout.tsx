import Link from "next/link";
import { redirect } from "next/navigation";
import { BRAND_NAME } from "@/lib/brand";
import { createClient } from "@/lib/supabase/server";
import { getServerApiBase } from "@/lib/server-api";
import { getServerActiveOrgId } from "@/lib/active-org-server";
import type { SessionState } from "@/lib/auth-workflow";

export default async function OnboardingLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

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
        if (state.needs_email_verification) redirect("/verify-email");
        if (!state.needs_onboarding) redirect("/dashboard");
      }
    } catch {
      // continue
    }
  }

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <div className="pointer-events-none fixed inset-0 -z-10 grid-bg dark:starfield" />
      <header className="border-b border-outline-variant/70 bg-surface-container-low/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 md:px-6">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-secondary shadow-glow" />
            <span className="font-display text-lg font-extrabold tracking-[-0.03em]">{BRAND_NAME}</span>
          </Link>
          <form action="/api/auth/signout" method="post">
            <button type="submit" className="btn-secondary px-4 py-2 text-sm">
              Sign out
            </button>
          </form>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8 md:px-6 md:py-12">{children}</main>
    </div>
  );
}
