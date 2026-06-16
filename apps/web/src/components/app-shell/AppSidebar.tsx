"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useEffect, useState } from "react";
import {
  APP_NAVIGATION,
  groupIdForPath,
  isNavItemActive,
  type NavGroup,
  type NavItem,
} from "@/lib/app-navigation";
import { canReadNav } from "@/lib/auth-workflow";
import { cn } from "@/lib/cn";
import { useSidebarCollapsed } from "./useSidebarCollapsed";

type AppSidebarProps = {
  permissions: string[];
  permissionsLoaded: boolean;
};

function NavLink({
  item,
  collapsed,
  active,
}: {
  item: { href: string; label: string; icon?: NavItem["icon"] };
  collapsed: boolean;
  active: boolean;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      title={collapsed ? item.label : undefined}
      className={cn(
        "flex items-center gap-3 rounded-sm px-3 py-2.5 font-dm-sans text-[11px] font-semibold transition-colors",
        active
          ? "border-l-2 border-mkt-accent bg-mkt-accent/[0.08] text-mkt-accent"
          : "border-l-2 border-transparent text-mkt-muted hover:bg-mkt-ink/[0.03] hover:text-mkt-ink"
      )}
    >
      {Icon ? <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} /> : null}
      {!collapsed ? <span className="truncate">{item.label}</span> : null}
    </Link>
  );
}

function NavGroupSection({
  group,
  collapsed,
  permissions,
  permissionsLoaded,
  pathname,
  expanded,
  onToggle,
}: {
  group: NavGroup;
  collapsed: boolean;
  permissions: string[];
  permissionsLoaded: boolean;
  pathname: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  const visibleItems = group.items.filter((item) => canReadNav(permissions, item.perm, permissionsLoaded));
  if (visibleItems.length === 0) return null;

  const GroupIcon = group.icon;
  const groupActive = visibleItems.some((item) => isNavItemActive(pathname, item.href));

  if (collapsed) {
    return (
      <div className="space-y-1">
        {visibleItems.map((item) => {
          const Icon = item.icon ?? group.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={cn(
                "flex items-center justify-center rounded-sm p-2.5 transition-colors",
                isNavItemActive(pathname, item.href)
                  ? "bg-mkt-accent/[0.08] text-mkt-accent"
                  : "text-mkt-muted hover:bg-mkt-ink/[0.03] hover:text-mkt-ink"
              )}
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={1.75} />
            </Link>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className={cn(
          "flex w-full items-center justify-between rounded-sm px-3 py-2 font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] transition-colors",
          groupActive ? "text-mkt-accent" : "text-mkt-muted hover:text-mkt-ink"
        )}
      >
        <span className="flex items-center gap-2">
          <GroupIcon className="h-3.5 w-3.5" strokeWidth={1.75} />
          {group.label}
        </span>
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", expanded ? "rotate-180" : "")} />
      </button>
      {expanded ? (
        <div className="ml-2 space-y-0.5 border-l border-mkt-ink/[0.06] pl-2">
          {visibleItems.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              collapsed={false}
              active={isNavItemActive(pathname, item.href)}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function AppSidebar({ permissions, permissionsLoaded }: AppSidebarProps) {
  const pathname = usePathname();
  const { collapsed, toggle, hydrated } = useSidebarCollapsed();
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const activeGroup = groupIdForPath(pathname);
    if (activeGroup) {
      setExpandedGroups((prev) => ({ ...prev, [activeGroup]: true }));
    }
  }, [pathname]);

  function toggleGroup(id: string) {
    setExpandedGroups((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  const width = !hydrated ? "w-60" : collapsed ? "w-16" : "w-60";

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-r border-mkt-ink/[0.06] bg-mkt-surface/90 backdrop-blur-xl transition-[width] duration-200 lg:flex",
        width
      )}
    >
      <div className="flex items-center justify-end border-b border-mkt-ink/[0.06] px-2 py-3">
        <button
          type="button"
          onClick={toggle}
          className="rounded-sm p-2 text-mkt-muted transition-colors hover:bg-mkt-ink/[0.04] hover:text-mkt-ink"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 space-y-4 overflow-y-auto p-3" aria-label="App navigation">
        {APP_NAVIGATION.map((entry) => {
          if (entry.type === "link") {
            if (!canReadNav(permissions, entry.perm, permissionsLoaded)) return null;
            return (
              <NavLink
                key={entry.href}
                item={entry}
                collapsed={collapsed}
                active={isNavItemActive(pathname, entry.href)}
              />
            );
          }

          return (
            <NavGroupSection
              key={entry.group.id}
              group={entry.group}
              collapsed={collapsed}
              permissions={permissions}
              permissionsLoaded={permissionsLoaded}
              pathname={pathname}
              expanded={expandedGroups[entry.group.id] ?? false}
              onToggle={() => toggleGroup(entry.group.id)}
            />
          );
        })}
      </nav>
    </aside>
  );
}
