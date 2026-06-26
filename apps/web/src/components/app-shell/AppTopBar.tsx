/**
 * @file apps/web/src/components/app-shell/AppTopBar.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { OrgSwitcher } from "@/components/app-shell/OrgSwitcher";
import { AppUserMenu } from "@/components/app-shell/AppUserMenu";
import { BrandLogo } from "@/components/product/BrandLogo";

export function AppTopBar({ email, displayName }: { email: string; displayName?: string | null }) {
  return (
    <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-mkt-ink/[0.06] bg-mkt-surface/85 px-4 backdrop-blur-xl md:px-6">
      <Link href="/dashboard" className="inline-flex min-w-0 items-center lg:hidden">
        <BrandLogo variant="icon" size="sm" />
      </Link>

      <div className="hidden lg:block" />

      <div className="flex min-w-0 flex-1 items-center justify-end gap-3 md:gap-4">
        <OrgSwitcher />
        <AppUserMenu email={email} displayName={displayName} />
      </div>
    </header>
  );
}
