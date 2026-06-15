export const BRAND_NAME = "Stoa";

export const BRAND_TAGLINE = "Know your market. Ship faster.";

/** Supporting subhead — hero body, section leads, footer blurb */
export const BRAND_SUBHEAD =
  "From customer signals to campaign-ready output - in one place.";

export const BRAND_LOGO_LETTER = "S";

const LEGACY_ACTIVE_COMPANY_KEY = "nexara.activeCompanyId";

export function migrateLegacyActiveCompanyStorage() {
  if (typeof window === "undefined") return;
  const legacy = window.localStorage.getItem(LEGACY_ACTIVE_COMPANY_KEY);
  if (legacy && !window.localStorage.getItem("stoa.activeCompanyId")) {
    window.localStorage.setItem("stoa.activeCompanyId", legacy);
    window.localStorage.removeItem(LEGACY_ACTIVE_COMPANY_KEY);
  }
}
