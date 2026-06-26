/**
 * @file apps/web/src/lib/integration-connect.ts
 * @layer Frontend Shared Utilities
 * @description Connect-flow helpers for integration providers (credential vs OAuth routing).
 */

export type IntegrationProvider = {
  id: string;
  name: string;
  auth_type: string;
  description: string;
  connection_mode?: string;
  supports_credential_auth?: boolean;
  oauth_available?: boolean;
  connectable?: boolean;
  missing_env?: string[];
};

/** Providers that expose an API-key / token form in the UI. */
export const API_KEY_PROVIDER_IDS = new Set([
  "intercom",
  "zendesk",
  "reviews",
  "slack",
  "notion",
  "jira",
  "posthog",
  "reddit",
  "gong",
  "ga4",
  "google_drive",
]);

export const DUAL_AUTH_PROVIDER_IDS = new Set(["slack", "zendesk", "gong"]);

export function supportsCredentialForm(provider: IntegrationProvider): boolean {
  if (provider.auth_type === "api_key") return true;
  if (provider.supports_credential_auth) return true;
  return API_KEY_PROVIDER_IDS.has(provider.id);
}

export function supportsOAuthConnect(provider: IntegrationProvider): boolean {
  return provider.auth_type === "oauth" || Boolean(provider.oauth_available);
}

export function isPlatformManaged(provider: IntegrationProvider): boolean {
  return provider.connection_mode === "platform";
}

export function defaultAuthMode(provider: IntegrationProvider): "oauth" | "token" {
  if (DUAL_AUTH_PROVIDER_IDS.has(provider.id) && provider.oauth_available) {
    return "oauth";
  }
  if (supportsCredentialForm(provider) && !provider.oauth_available) {
    return "token";
  }
  if (provider.auth_type === "oauth" && provider.oauth_available) {
    return "oauth";
  }
  return "token";
}

export function integrationConnectBlockedMessage(provider: IntegrationProvider): string | null {
  if (provider.connectable !== false) return null;
  if (isPlatformManaged(provider)) {
    return "Configured by your Stoa administrator — platform credentials are not set up yet.";
  }
  if (provider.missing_env?.length) {
    return `OAuth is not configured on the server (${provider.missing_env.join(", ")}).`;
  }
  return "This integration is not available to connect yet.";
}
