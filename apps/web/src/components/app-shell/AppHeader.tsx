"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { OrgSwitcher } from "@/components/app-shell/OrgSwitcher";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { BRAND_NAME } from "@/lib/brand";
import { canRead } from "@/lib/auth-workflow";

const navItems = [
  { href: "/dashboard", label: "Dashboard", perm: "intelligence:read" },
  { href: "/data", label: "Data", perm: "data_sources:read" },
  { href: "/intelligence", label: "Intelligence", perm: "intelligence:read" },
  { href: "/competitive", label: "Competitive", perm: "competitive:read" },
  { href: "/campaigns", label: "Campaigns", perm: "campaigns:read" },
  { href: "/settings/team", label: "Team", perm: "team:read" },
  { href: "/settings/roles", label: "Roles", perm: "roles:manage" },
];

export function AppHeader({ email }: { email: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const [permissions, setPermissions] = useState<string[]>([]);

  useEffect(() => {
    void (async () => {
      const res = await fetch("/api/auth/session");
      if (res.ok) {
        const state = await res.json();
        setPermissions(state.permissions ?? []);
      }
    })();
  }, []);

  async function signOut() {
    await fetch("/api/auth/signout", { method: "POST" });
    router.push(getAuthEntryPath());
    router.refresh();
  }

  const visibleNav = navItems.filter((item) => canRead(permissions, item.perm));

  return (
    <header className="sticky top-0 z-40 border-b border-outline-variant/70 bg-surface-container-low/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 md:px-6">
        <Link href="/dashboard" className="inline-flex items-center gap-3">
          <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-secondary shadow-glow" />
          <span className="font-display text-lg font-extrabold tracking-[-0.03em] text-on-surface">{BRAND_NAME}</span>
        </Link>
        <OrgSwitcher />
        <nav className="order-3 flex w-full items-center gap-2 overflow-x-auto md:order-none md:w-auto" aria-label="App sections">
          {visibleNav.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={active ? "btn-primary px-4 py-2 text-sm" : "btn-secondary px-4 py-2 text-sm"}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex flex-wrap items-center gap-3 md:gap-4">
          <span className="hidden max-w-[200px] truncate rounded-full border border-outline-variant/60 bg-surface-container-low/80 px-3 py-2 text-sm text-on-surface-variant sm:inline md:max-w-xs" title={email}>
            {email}
          </span>
          <ThemeToggle />
          <button type="button" onClick={() => void signOut()} className="btn-secondary px-4 py-2 text-sm">
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
