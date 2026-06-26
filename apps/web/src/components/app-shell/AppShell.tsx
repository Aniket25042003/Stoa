/**
 * @file apps/web/src/components/app-shell/AppShell.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { AppMobileNav } from "./AppMobileNav";
import { AppSidebar } from "./AppSidebar";
import { AppTopBar } from "./AppTopBar";
import { useAppPermissions } from "./useAppPermissions";
import { ProductShellFrame } from "@/components/product";
import { BrandLogo } from "@/components/product/BrandLogo";

/**
 * Handles app shell behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AppShell({
  email,
  displayName,
  children,
}: {
  email: string;
  displayName?: string | null;
  children: ReactNode;
}) {
  const { permissions, loaded } = useAppPermissions();

  return (
    <ProductShellFrame>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-sm focus:bg-mkt-accent focus:px-3 focus:py-2 focus:text-mkt-dark-ink"
      >
        Skip to content
      </a>

      <div className="flex min-h-screen flex-col lg:flex-row">
        <div className="hidden lg:flex lg:w-60 lg:shrink-0 lg:flex-col">
          <Link
            href="/dashboard"
            className="flex h-14 shrink-0 items-center border-b border-r border-mkt-ink/[0.06] px-4"
          >
            <BrandLogo variant="icon" size="sm" />
          </Link>
          <AppSidebar permissions={permissions} permissionsLoaded={loaded} />
        </div>

        <div className="flex min-h-screen min-w-0 flex-1 flex-col pb-16 lg:pb-0">
          <AppTopBar email={email} displayName={displayName} />
          <main id="main-content" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-6 md:py-8">
            {children}
          </main>
        </div>
      </div>

      <AppMobileNav permissions={permissions} permissionsLoaded={loaded} />
    </ProductShellFrame>
  );
}
