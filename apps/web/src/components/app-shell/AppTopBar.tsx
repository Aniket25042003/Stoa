/**
 * @file apps/web/src/components/app-shell/AppTopBar.tsx
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { OrgSwitcher } from "@/components/app-shell/OrgSwitcher";
import { AppUserMenu } from "@/components/app-shell/AppUserMenu";
import { BrandLogo } from "@/components/product/BrandLogo";
import { pageTitleForPath } from "@/lib/app-navigation";

export function AppTopBar({ email, displayName }: { email: string; displayName?: string | null }) {
  const pathname = usePathname();
  const title = pageTitleForPath(pathname);

  return (
    <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-mkt-ink/[0.06] bg-mkt-surface/90 px-4 backdrop-blur-xl md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <Link href="/dashboard" className="inline-flex shrink-0 items-center lg:hidden">
          <BrandLogo variant="icon" size="sm" />
        </Link>
        <h1 className="truncate font-syne text-sm font-semibold uppercase tracking-wider text-mkt-ink">
          {title}
        </h1>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <OrgSwitcher />
        <AppUserMenu email={email} displayName={displayName} />
      </div>
    </header>
  );
}
