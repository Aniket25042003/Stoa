"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ICON_RAIL_NAV, isNavItemActive, type IconRailItem } from "@/lib/app-navigation";
import { canReadNav } from "@/lib/auth-workflow";
import { cn } from "@/lib/cn";

type AppIconRailProps = {
  permissions: string[] | null;
  permissionsLoaded: boolean;
};

function canSeeRailItem(
  item: IconRailItem,
  permissions: string[] | null,
  permissionsLoaded: boolean,
): boolean {
  if (canReadNav(permissions, item.perm, permissionsLoaded)) return true;
  if (!item.altPerms?.length) return false;
  return item.altPerms.some((p) => canReadNav(permissions, p, permissionsLoaded));
}

export function AppIconRail({ permissions, permissionsLoaded }: AppIconRailProps) {
  const pathname = usePathname();

  return (
    <nav
      className="hidden w-[var(--app-rail-width)] shrink-0 flex-col items-center gap-1 border-r border-mkt-ink/[0.06] bg-mkt-surface-elevated py-3 lg:flex"
      aria-label="Primary navigation"
    >
      {ICON_RAIL_NAV.filter((item) => canSeeRailItem(item, permissions, permissionsLoaded)).map(
        (item) => {
          const Icon = item.icon;
          const active = isNavItemActive(pathname, item.href, item.matchPrefix);
          return (
            <Link
              key={item.id}
              href={item.href}
              title={item.label}
              className={cn(
                "icon-rail-item flex h-10 w-10 items-center justify-center rounded-sm transition-colors",
                active
                  ? "bg-mkt-accent/[0.1] text-mkt-accent"
                  : "text-mkt-muted hover:bg-mkt-ink/[0.04] hover:text-mkt-ink",
              )}
              aria-current={active ? "page" : undefined}
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={1.75} aria-hidden />
              <span className="sr-only">{item.label}</span>
            </Link>
          );
        },
      )}
    </nav>
  );
}
