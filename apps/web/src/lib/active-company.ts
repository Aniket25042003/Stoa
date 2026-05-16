import { migrateLegacyActiveCompanyStorage } from "@/lib/brand";

export const ACTIVE_COMPANY_KEY = "stoa.activeCompanyId";
export const ACTIVE_COMPANY_EVENT = "stoa:active-company";

export type ActiveCompanyEventDetail = {
  companyId: string | null;
};

export function getStoredActiveCompanyId() {
  if (typeof window === "undefined") return null;
  migrateLegacyActiveCompanyStorage();
  return window.localStorage.getItem(ACTIVE_COMPANY_KEY);
}

export function setStoredActiveCompanyId(companyId: string | null) {
  if (typeof window === "undefined") return;
  if (companyId) {
    window.localStorage.setItem(ACTIVE_COMPANY_KEY, companyId);
  } else {
    window.localStorage.removeItem(ACTIVE_COMPANY_KEY);
  }
  window.dispatchEvent(new CustomEvent<ActiveCompanyEventDetail>(ACTIVE_COMPANY_EVENT, { detail: { companyId } }));
}
