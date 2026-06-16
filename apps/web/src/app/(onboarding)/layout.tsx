import Link from "next/link";
import { redirect } from "next/navigation";
import { ProductButton, ProductShellFrame } from "@/components/product";
import { BRAND_LOGO_LETTER, BRAND_NAME } from "@/lib/brand";
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
    <ProductShellFrame>
      <header className="border-b border-mkt-ink/[0.06] bg-mkt-surface/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 md:px-6">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-sm border border-mkt-accent/35 bg-mkt-accent/[0.08] font-mono text-sm font-black text-mkt-accent">
              {BRAND_LOGO_LETTER}
            </span>
            <span className="font-syne text-lg font-extrabold uppercase tracking-[0.1em] text-mkt-ink">
              {BRAND_NAME}
            </span>
          </Link>
          <form action="/api/auth/signout" method="post">
            <ProductButton variant="secondary" type="submit">
              Sign out
            </ProductButton>
          </form>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8 md:px-6 md:py-12">{children}</main>
    </ProductShellFrame>
  );
}
