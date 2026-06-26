/**
 * @file apps/web/src/components/app-shell/AppShell.tsx
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { AppIconRail } from "./AppIconRail";
import { AppMobileNav } from "./AppMobileNav";
import { AppTopBar } from "./AppTopBar";
import { useAppPermissions } from "./useAppPermissions";
import { ProductShellFrame } from "@/components/product";
import { BrandLogo } from "@/components/product/BrandLogo";
import { layoutVariantForPath } from "@/lib/app-navigation";
import { cn } from "@/lib/cn";

export function AppShell({
  email,
  displayName,
  children,
}: {
  email: string;
  displayName?: string | null;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const { permissions, loaded } = useAppPermissions();
  const variant = layoutVariantForPath(pathname);

  return (
    <ProductShellFrame>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-sm focus:bg-mkt-accent focus:px-3 focus:py-2 focus:text-mkt-dark-ink"
      >
        Skip to content
      </a>

      <div className="flex min-h-screen flex-col">
        <AppTopBar email={email} displayName={displayName} />

        <div className="flex min-h-0 flex-1">
          <div className="hidden shrink-0 flex-col border-r border-mkt-ink/[0.06] lg:flex">
            <Link
              href="/dashboard"
              className="flex h-14 shrink-0 items-center justify-center border-b border-mkt-ink/[0.06]"
            >
              <BrandLogo variant="icon" size="sm" />
            </Link>
            <AppIconRail permissions={permissions} permissionsLoaded={loaded} />
          </div>

          <main
            id="main-content"
            className={cn(
              "mx-auto w-full min-w-0 flex-1 pb-16 lg:pb-0",
              variant === "agent" && "agent-canvas flex flex-col px-0 py-0",
              variant === "assets" && "max-w-7xl px-4 py-6 md:px-6 md:py-8",
              variant === "standard" && "max-w-6xl px-4 py-6 md:px-6 md:py-8",
            )}
          >
            {children}
          </main>
        </div>
      </div>

      <AppMobileNav permissions={permissions} permissionsLoaded={loaded} />
    </ProductShellFrame>
  );
}
