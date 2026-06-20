/**
 * @file apps/web/src/components/app-shell/SectionSubnav.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { NavItem } from "@/lib/app-navigation";
import { canReadNav } from "@/lib/auth-workflow";
import { cn } from "@/lib/cn";
import { isNavItemActive } from "@/lib/app-navigation";

/**
 * Handles section subnav behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function SectionSubnav({
  items,
  permissions,
  permissionsLoaded,
  ariaLabel,
}: {
  items: NavItem[];
  permissions: string[] | null;
  permissionsLoaded: boolean;
  ariaLabel: string;
}) {
  const pathname = usePathname();
  const visible = items.filter((item) => canReadNav(permissions, item.perm, permissionsLoaded));
  if (visible.length === 0) return null;

  return (
    <nav aria-label={ariaLabel} className="mb-8 flex flex-wrap gap-2 border-b border-mkt-ink/[0.06] pb-4">
      {visible.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "rounded-sm px-3 py-2 font-dm-sans text-[10px] font-bold uppercase tracking-[0.14em] transition-colors",
            isNavItemActive(pathname, item.href)
              ? "bg-mkt-accent/[0.08] text-mkt-accent"
              : "text-mkt-muted hover:bg-mkt-ink/[0.03] hover:text-mkt-ink"
          )}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
