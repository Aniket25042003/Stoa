export const BRAND_NAME = "Stoa";

/** Primary tagline — hero headlines, metadata, footer */
export const BRAND_TAGLINE = "Where GTM strategy and marketing share one shelter.";

/** Supporting subhead — hero body, section leads, footer blurb */
export const BRAND_SUBHEAD =
  "Build and refine your go-to-market plan, then turn it into campaign-ready copy and creative—without switching tools.";

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
