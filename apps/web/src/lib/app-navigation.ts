/**
 * @file apps/web/src/lib/app-navigation.ts
 * @layer Frontend Shared Utilities
 * @description Single source of truth for icon rail, mobile nav, and section subnavs.
 */
import type { LucideIcon } from "lucide-react";
import {
  Archive,
  Building2,
  Cable,
  FileUp,
  LayoutDashboard,
  Radar,
  Settings,
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

export type IconRailItem = {
  id: string;
  href: string;
  label: string;
  perm: string;
  icon: LucideIcon;
  /** Match pathname prefix for active state (defaults to href). */
  matchPrefix?: string;
  /** Show rail item if user has any of these permissions. */
  altPerms?: string[];
};

/** Primary icon rail — Home, Agent, Assets, Data, Settings. */
export const ICON_RAIL_NAV: IconRailItem[] = [
  {
    id: "home",
    href: "/dashboard",
    label: "Home",
    perm: "intelligence:read",
    icon: LayoutDashboard,
  },
  {
    id: "agent",
    href: "/agent",
    label: "Agent",
    perm: "conversations:ask",
    icon: Sparkles,
    matchPrefix: "/agent",
  },
  {
    id: "assets",
    href: "/assets",
    label: "Assets",
    perm: "campaigns:read",
    icon: Archive,
    altPerms: ["content:read"],
    matchPrefix: "/assets",
  },
  {
    id: "data",
    href: "/data/profile",
    label: "Data",
    perm: "data_sources:read",
    icon: Building2,
    matchPrefix: "/data",
  },
  {
    id: "settings",
    href: "/settings/team",
    label: "Settings",
    perm: "team:read",
    icon: Settings,
    altPerms: ["roles:manage"],
    matchPrefix: "/settings",
  },
];

export const MOBILE_PRIMARY_TABS = [
  { id: "home", href: "/dashboard", label: "Home", icon: LayoutDashboard, perm: "intelligence:read" },
  { id: "agent", href: "/agent", label: "Agent", icon: Sparkles, perm: "conversations:ask" },
  { id: "assets", href: "/assets", label: "Assets", icon: Archive, perm: "campaigns:read", altPerms: ["content:read"] as const },
  { id: "data", href: "/data/profile", label: "Data", icon: Building2, perm: "data_sources:read" },
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

/** @deprecated Use ICON_RAIL_NAV — kept for breadcrumbs during migration. */
export const APP_NAVIGATION = ICON_RAIL_NAV.map((item) => ({
  type: "link" as const,
  href: item.href,
  label: item.label,
  perm: item.perm,
  icon: item.icon,
}));

/**
 * Handles is nav item active behavior for this part of the Stoa application.
 */
export function isNavItemActive(pathname: string, href: string, matchPrefix?: string): boolean {
  const prefix = matchPrefix ?? href;
  if (pathname === href) return true;
  if (href === "/data/profile" && pathname === "/data") return true;
  if (prefix === "/data" && pathname.startsWith("/data")) return true;
  if (prefix === "/settings" && pathname.startsWith("/settings")) return true;
  return pathname.startsWith(`${prefix}/`);
}

/**
 * Returns page title for top bar from pathname.
 */
export function pageTitleForPath(pathname: string): string {
  if (pathname.startsWith("/agent")) return "GTM Agent";
  if (pathname.startsWith("/assets")) return "Assets";
  if (pathname.startsWith("/data")) return "Data hub";
  if (pathname.startsWith("/settings")) return "Settings";
  if (pathname.startsWith("/dashboard")) return "Home";
  return "Stoa";
}

/**
 * Layout variant for route-aware shell width and height.
 */
export function layoutVariantForPath(pathname: string): "agent" | "assets" | "standard" {
  if (pathname.startsWith("/agent")) return "agent";
  if (pathname.startsWith("/assets")) return "assets";
  return "standard";
}

export function flattenNavItems(): NavItem[] {
  return [...DATA_SUBNAV, ...SETTINGS_SUBNAV];
}

/** @deprecated */
export function groupIdForPath(pathname: string): string | null {
  if (pathname.startsWith("/data")) return "workspace";
  if (pathname.startsWith("/settings")) return "organization";
  return null;
}
