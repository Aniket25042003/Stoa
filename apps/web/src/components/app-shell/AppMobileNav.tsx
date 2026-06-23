/**
 * @file apps/web/src/components/app-shell/AppMobileNav.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { MoreHorizontal, X } from "lucide-react";
import {
  APP_NAVIGATION,
  MOBILE_PRIMARY_TABS,
  isNavItemActive,
} from "@/lib/app-navigation";
import { canReadNav } from "@/lib/auth-workflow";
import { signOutClient } from "@/lib/auth-client";
import { cn } from "@/lib/cn";
import { ProductButton } from "@/components/product";

type AppMobileNavProps = {
  permissions: string[] | null;
  permissionsLoaded: boolean;
};

/**
 * Handles app mobile nav behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AppMobileNav({ permissions, permissionsLoaded }: AppMobileNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    setSheetOpen(false);
  }, [pathname]);

  const visibleTabs = MOBILE_PRIMARY_TABS.filter((tab) =>
    canReadNav(permissions, tab.perm, permissionsLoaded)
  );

  const orgGroup = APP_NAVIGATION.find((e) => e.type === "group" && e.group.id === "organization");
  const intelGroup = APP_NAVIGATION.find((e) => e.type === "group" && e.group.id === "intelligence");

  async function signOut() {
    await signOutClient(router);
  }

  return (
    <>
      <nav
        className="fixed inset-x-0 bottom-0 z-40 flex items-stretch border-t border-mkt-ink/[0.06] bg-mkt-surface/95 backdrop-blur-xl lg:hidden"
        aria-label="Mobile navigation"
      >
        {visibleTabs.map((tab) => {
          const Icon = tab.icon;
          const active =
            tab.id === "data"
              ? pathname.startsWith("/data")
              : isNavItemActive(pathname, tab.href);
          return (
            <Link
              key={tab.id}
              href={tab.href}
              className={cn(
                "flex flex-1 flex-col items-center justify-center gap-1 py-2.5 text-[11px] font-medium transition-colors",
                active ? "text-mkt-accent" : "text-mkt-muted"
              )}
            >
              <Icon className="h-5 w-5" strokeWidth={1.75} />
              {tab.label}
            </Link>
          );
        })}
        <button
          type="button"
          onClick={() => setSheetOpen(true)}
          className={cn(
            "flex flex-1 flex-col items-center justify-center gap-1 py-2.5 text-[11px] font-medium transition-colors",
            sheetOpen ? "text-mkt-accent" : "text-mkt-muted"
          )}
          aria-label="More navigation"
        >
          <MoreHorizontal className="h-5 w-5" strokeWidth={1.75} />
          More
        </button>
      </nav>

      {sheetOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="More menu">
          <button
            type="button"
            className="absolute inset-0 bg-mkt-ink/20 backdrop-blur-sm"
            onClick={() => setSheetOpen(false)}
            aria-label="Close menu"
          />
          <div className="absolute inset-x-0 bottom-0 max-h-[70vh] overflow-y-auto rounded-t-lg border border-mkt-ink/[0.06] bg-mkt-surface p-5 shadow-[0_-12px_40px_rgba(20,20,26,0.12)]">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                Navigation
              </p>
              <button
                type="button"
                onClick={() => setSheetOpen(false)}
                className="rounded-sm p-1 text-mkt-muted hover:text-mkt-ink"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {intelGroup?.type === "group" ? (
              <div className="mb-6">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                  Intelligence
                </p>
                <div className="space-y-1">
                  {intelGroup.group.items
                    .filter((item) => canReadNav(permissions, item.perm, permissionsLoaded))
                    .map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          "block rounded-sm px-3 py-2.5 text-sm font-medium",
                          isNavItemActive(pathname, item.href)
                            ? "bg-mkt-accent/[0.08] text-mkt-accent"
                            : "text-mkt-ink hover:bg-mkt-ink/[0.03]"
                        )}
                      >
                        {item.label}
                      </Link>
                    ))}
                </div>
              </div>
            ) : null}

            {orgGroup?.type === "group" ? (
              <div className="mb-6">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                  Organization
                </p>
                <div className="space-y-1">
                  {orgGroup.group.items
                    .filter((item) => canReadNav(permissions, item.perm, permissionsLoaded))
                    .map((item) => (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          "block rounded-sm px-3 py-2.5 text-sm font-medium",
                          isNavItemActive(pathname, item.href)
                            ? "bg-mkt-accent/[0.08] text-mkt-accent"
                            : "text-mkt-ink hover:bg-mkt-ink/[0.03]"
                        )}
                      >
                        {item.label}
                      </Link>
                    ))}
                </div>
              </div>
            ) : null}

            <ProductButton variant="secondary" className="w-full" onClick={() => void signOut()}>
              Sign out
            </ProductButton>
          </div>
        </div>
      ) : null}
    </>
  );
}
