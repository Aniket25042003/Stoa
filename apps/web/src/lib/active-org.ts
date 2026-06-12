export const ACTIVE_ORG_COOKIE = "stoa-active-org";

export function readActiveOrgCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${ACTIVE_ORG_COOKIE}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}
