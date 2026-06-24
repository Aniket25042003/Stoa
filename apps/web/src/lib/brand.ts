/**
 * @file apps/web/src/lib/brand.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export const BRAND_NAME = "Stoa";

export const BRAND_TAGLINE = "Know your market. Ship faster.";

/** Supporting subhead — hero body, section leads, footer blurb */
export const BRAND_SUBHEAD =
  "From customer signals to campaign-ready output - in one place.";

/** Trimmed light wordmark aspect ratio (width / height) from V3 source assets. */
export const BRAND_LOGO_ASPECT = 1787 / 424;

export const BRAND_ICON_SRC = "/images/logos/stoa-icon.webp";
export const BRAND_ICON_SRC_32 = "/images/logos/stoa-icon-32.webp";
export const BRAND_ICON_SRC_48 = "/images/logos/stoa-icon-48.webp";
export const BRAND_ICON_SRC_80 = "/images/logos/stoa-icon-80.webp";
export const BRAND_ICON_ON_DARK_SRC_48 = "/images/logos/stoa-icon-on-dark-48.webp";
export const BRAND_ICON_ON_DARK_SRC_80 = "/images/logos/stoa-icon-on-dark-80.webp";

export const BRAND_LOGO_SRC = "/images/logos/stoa-logo.webp";
export const BRAND_LOGO_SRC_SM = "/images/logos/stoa-logo-sm.webp";
export const BRAND_LOGO_SRC_MD = "/images/logos/stoa-logo-md.webp";
export const BRAND_LOGO_SRC_LG = "/images/logos/stoa-logo-lg.webp";
export const BRAND_LOGO_ON_DARK_SRC_SM = "/images/logos/stoa-logo-on-dark-sm.webp";
export const BRAND_LOGO_ON_DARK_SRC_MD = "/images/logos/stoa-logo-on-dark-md.webp";
export const BRAND_LOGO_ON_DARK_SRC_LG = "/images/logos/stoa-logo-on-dark-lg.webp";

export const BRAND_OG_SRC = "/images/logos/og-stoa.webp";

const LEGACY_ACTIVE_COMPANY_KEY = "nexara.activeCompanyId";

/**
 * Handles migrate legacy active company storage behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function migrateLegacyActiveCompanyStorage() {
  if (typeof window === "undefined") return;
  const legacy = window.localStorage.getItem(LEGACY_ACTIVE_COMPANY_KEY);
  if (legacy && !window.localStorage.getItem("stoa.activeCompanyId")) {
    window.localStorage.setItem("stoa.activeCompanyId", legacy);
    window.localStorage.removeItem(LEGACY_ACTIVE_COMPANY_KEY);
  }
}
