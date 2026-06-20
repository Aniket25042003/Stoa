/**
 * @file apps/web/src/lib/active-company.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
import { migrateLegacyActiveCompanyStorage } from "@/lib/brand";

export const ACTIVE_COMPANY_KEY = "stoa.activeCompanyId";
export const ACTIVE_COMPANY_EVENT = "stoa:active-company";

export type ActiveCompanyEventDetail = {
  companyId: string | null;
};

/**
 * Handles get stored active company id behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function getStoredActiveCompanyId() {
  if (typeof window === "undefined") return null;
  migrateLegacyActiveCompanyStorage();
  return window.localStorage.getItem(ACTIVE_COMPANY_KEY);
}

/**
 * Handles set stored active company id behavior for this part of the Stoa application.
 *
 * @param companyId - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function setStoredActiveCompanyId(companyId: string | null) {
  if (typeof window === "undefined") return;
  if (companyId) {
    window.localStorage.setItem(ACTIVE_COMPANY_KEY, companyId);
  } else {
    window.localStorage.removeItem(ACTIVE_COMPANY_KEY);
  }
  window.dispatchEvent(new CustomEvent<ActiveCompanyEventDetail>(ACTIVE_COMPANY_EVENT, { detail: { companyId } }));
}
