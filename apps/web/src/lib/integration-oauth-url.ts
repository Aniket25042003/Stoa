/**
 * @file apps/web/src/lib/integration-oauth-url.ts
 * @layer Frontend Shared Utilities
 * @description Allowlist validation for integration OAuth authorize redirects.
 */

const OAUTH_AUTHORIZE_HOSTS = new Set([
  "app.hubspot.com",
  "login.salesforce.com",
  "app.gong.io",
]);

const ZENDESK_HOST_PATTERN = /^[a-z0-9-]+\.zendesk\.com$/i;

/** True when URL is an HTTPS authorize endpoint from a known integration provider. */
export function isAllowedOAuthAuthorizeUrl(raw: string): boolean {
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:") return false;
    const host = url.hostname.toLowerCase();
    if (OAUTH_AUTHORIZE_HOSTS.has(host)) return true;
    return ZENDESK_HOST_PATTERN.test(host) && url.pathname.startsWith("/oauth/");
  } catch {
    return false;
  }
}
