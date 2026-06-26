/**
 * @file apps/web/src/app/(onboarding)/layout.tsx
 * @layer Frontend Onboarding UI
 * @description Defines shared route layout structure, metadata, and navigation boundaries.
 * @dependencies Supabase, Next.js, React
 */
import Link from "next/link";
import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { ProductButton, ProductShellFrame } from "@/components/product";
import { BrandLogo } from "@/components/product/BrandLogo";
import { createClient } from "@/lib/supabase/server";
import { getServerApiBase } from "@/lib/server-api";
import { getServerActiveOrgId } from "@/lib/active-org-server";
import { trustedProxyHeadersFromHeaders } from "@/lib/proxy-headers";
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
          ...trustedProxyHeadersFromHeaders(await headers()),
        },
        cache: "no-store",
      });
      if (res.ok) {
        const state = (await res.json()) as SessionState;
        if (state.needs_email_verification) redirect("/verify-email");
        const onboardingMode = (await headers()).get("x-onboarding-mode");
        const isCreateMode = onboardingMode === "create";
        if (!state.needs_onboarding && !isCreateMode) redirect("/dashboard");
      }
    } catch {
      // continue
    }
  }

  const onboardingMode = (await headers()).get("x-onboarding-mode");
  const isCreateMode = onboardingMode === "create";

  return (
    <ProductShellFrame>
      <header className="border-b border-mkt-ink/[0.06] bg-mkt-surface/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 md:px-6">
          <Link href="/" className="inline-flex items-center">
            <BrandLogo variant="logo" size="md" />
          </Link>
          <div className="flex items-center gap-2">
            {isCreateMode ? (
              <Link href="/dashboard">
                <ProductButton variant="secondary" type="button">
                  Back to dashboard
                </ProductButton>
              </Link>
            ) : null}
            <form action="/api/auth/signout" method="post">
              <ProductButton variant="secondary" type="submit">
                Sign out
              </ProductButton>
            </form>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8 md:px-6 md:py-12">{children}</main>
    </ProductShellFrame>
  );
}
