/**
 * @file apps/web/src/lib/app-navigation.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies React
 */
import type { LucideIcon } from "lucide-react";
import {
  Building2,
  Cable,
  FileUp,
  Image,
  LayoutDashboard,
  Megaphone,
  Radar,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  perm: string;
  icon?: LucideIcon;
};

export type NavGroup = {
  id: string;
  label: string;
  icon: LucideIcon;
  items: NavItem[];
};

export type AppNavEntry =
  | { type: "link"; href: string; label: string; perm: string; icon: LucideIcon }
  | { type: "group"; group: NavGroup };

/** Single source of truth for sidebar, mobile nav, and breadcrumbs. */
export const APP_NAVIGATION: AppNavEntry[] = [
  {
    type: "link",
    href: "/dashboard",
    label: "Dashboard",
    perm: "intelligence:read",
    icon: LayoutDashboard,
  },
  {
    type: "group",
    group: {
      id: "workspace",
      label: "Workspace",
      icon: Building2,
      items: [
        { href: "/data/profile", label: "Company profile", perm: "data_sources:read", icon: Building2 },
        { href: "/data/sources", label: "Sources & uploads", perm: "data_sources:read", icon: FileUp },
        { href: "/data/integrations", label: "Integrations", perm: "data_sources:read", icon: Cable },
        { href: "/data/competitors", label: "Competitors", perm: "data_sources:read", icon: Radar },
      ],
    },
  },
  {
    type: "group",
    group: {
      id: "intelligence",
      label: "Intelligence",
      icon: Sparkles,
      items: [
        { href: "/intelligence", label: "Customer intelligence", perm: "intelligence:read", icon: Sparkles },
        { href: "/competitive", label: "Competitive", perm: "competitive:read", icon: Radar },
        { href: "/campaigns", label: "Campaigns", perm: "campaigns:read", icon: Megaphone },
        { href: "/content", label: "Content studio", perm: "content:read", icon: Image },
      ],
    },
  },
  {
    type: "group",
    group: {
      id: "organization",
      label: "Organization",
      icon: Users,
      items: [
        { href: "/settings/team", label: "Team", perm: "team:read", icon: Users },
        { href: "/settings/roles", label: "Roles & permissions", perm: "roles:manage", icon: Shield },
      ],
    },
  },
];

export const MOBILE_PRIMARY_TABS = [
  { id: "home", href: "/dashboard", label: "Home", icon: LayoutDashboard, perm: "intelligence:read" },
  { id: "data", href: "/data/profile", label: "Data", icon: Building2, perm: "data_sources:read" },
  { id: "intel", href: "/intelligence", label: "Intel", icon: Sparkles, perm: "intelligence:read" },
] as const;

export const DATA_SUBNAV: NavItem[] = [
  { href: "/data/profile", label: "Company profile", perm: "data_sources:read", icon: Building2 },
  { href: "/data/sources", label: "Sources & uploads", perm: "data_sources:read", icon: FileUp },
  { href: "/data/integrations", label: "Integrations", perm: "data_sources:read", icon: Cable },
  { href: "/data/competitors", label: "Competitors", perm: "data_sources:read", icon: Radar },
];

export const SETTINGS_SUBNAV: NavItem[] = [
  { href: "/settings/team", label: "Team", perm: "team:read", icon: Users },
  { href: "/settings/roles", label: "Roles & permissions", perm: "roles:manage", icon: Shield },
];

/**
 * Handles flatten nav items behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
export function flattenNavItems(): NavItem[] {
  const items: NavItem[] = [];
  for (const entry of APP_NAVIGATION) {
    if (entry.type === "link") {
      items.push({
        href: entry.href,
        label: entry.label,
        perm: entry.perm,
        icon: entry.icon,
      });
    } else {
      items.push(...entry.group.items);
    }
  }
  return items;
}

/**
 * Handles group id for path behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function groupIdForPath(pathname: string): string | null {
  for (const entry of APP_NAVIGATION) {
    if (entry.type !== "group") continue;
    if (entry.group.items.some((item) => pathname === item.href || pathname.startsWith(`${item.href}/`))) {
      return entry.group.id;
    }
  }
  return null;
}

/**
 * Handles is nav item active behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @param href - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isNavItemActive(pathname: string, href: string): boolean {
  if (pathname === href) return true;
  if (href === "/data/profile" && pathname === "/data") return true;
  return pathname.startsWith(`${href}/`);
}
