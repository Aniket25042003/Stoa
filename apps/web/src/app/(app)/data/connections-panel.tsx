/**
 * @file apps/web/src/app/(app)/data/connections-panel.tsx
 * @layer Frontend Product UI
 * @description Implements connections panel behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  DUAL_AUTH_PROVIDER_IDS,
  defaultAuthMode,
  integrationConnectBlockedMessage,
  isPlatformManaged,
  supportsCredentialForm,
  supportsOAuthConnect,
  type IntegrationProvider,
} from "@/lib/integration-connect";
import { isAllowedOAuthAuthorizeUrl } from "@/lib/integration-oauth-url";
import { consumeSse } from "@/lib/sse";
import { INTEGRATION_BENEFITS, groupProvidersByCategory } from "@/lib/integration-catalog";
import { formatIntegrationError } from "@/lib/user-facing-copy";
import { IntegrationScopeEditor } from "@/components/data/integration-scope-editor";
import { SCOPE_CONFIG } from "@/lib/integration-scope-config";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductStatusPill,
} from "@/components/product";
import { useDataHub } from "./data-hub-context";

type Connection = {
  id: string;
  provider: string;
  label: string;
  status: string;
  last_sync_at?: string | null;
  last_error?: string | null;
  scope_configured?: boolean;
  scope_summary?: string | null;
};

type AuthMode = "oauth" | "token";

const API_KEY_PROVIDERS: Record<string, { fields: { key: string; label: string; type?: string }[] }> = {
  intercom: {
    fields: [
      { key: "access_token", label: "Access Token", type: "password" },
      { key: "region", label: "Region (us, eu, or au)" },
    ],
  },
  zendesk: {
    fields: [
      { key: "subdomain", label: "Subdomain" },
      { key: "email", label: "Agent Email" },
      { key: "api_token", label: "API Token", type: "password" },
    ],
  },
  slack: {
    fields: [{ key: "access_token", label: "Bot Token", type: "password" }],
  },
  notion: {
    fields: [{ key: "access_token", label: "Integration Token", type: "password" }],
  },
  jira: {
    fields: [
      { key: "domain", label: "Domain (e.g. acme.atlassian.net)" },
      { key: "email", label: "Email" },
      { key: "api_token", label: "API Token", type: "password" },
    ],
  },
  posthog: {
    fields: [
      { key: "api_key", label: "Personal API Key", type: "password" },
      { key: "host", label: "Host (optional, default app.posthog.com)" },
    ],
  },
  gong: {
    fields: [
      { key: "access_key", label: "Access Key" },
      { key: "access_key_secret", label: "Access Key Secret", type: "password" },
      { key: "api_base_url", label: "API base URL (optional)" },
    ],
  },
  ga4: {
    fields: [{ key: "access_token", label: "Access Token", type: "password" }],
  },
  google_drive: {
    fields: [{ key: "access_token", label: "Access Token", type: "password" }],
  },
};

const OAUTH_EXTRA_FIELDS: Record<string, { key: string; label: string }[]> = {
  zendesk: [{ key: "subdomain", label: "Zendesk subdomain" }],
  salesforce: [{ key: "environment", label: "Environment (production or sandbox)" }],
};

function benefitFor(provider: IntegrationProvider): string {
  return INTEGRATION_BENEFITS[provider.id] ?? provider.description;
}

async function watchSyncEvents(
  connectionId: string,
  providerName: string,
  onDone: () => void,
  showToast: (message: string, variant?: "error" | "success") => void
) {
  const ctrl = new AbortController();
  try {
    await consumeSse(
      `/v1/integrations/sources/${connectionId}/events`,
      (data) => {
        if (data.status === "completed") {
          showToast(`${providerName} sync complete`);
          ctrl.abort();
          onDone();
        }
        if (data.status === "failed") {
          const err = formatIntegrationError(String(data.error ?? ""));
          showToast(err ? `${providerName}: ${err}` : `${providerName} sync failed`, "error");
          ctrl.abort();
          onDone();
        }
      },
      ctrl.signal
    );
  } catch {
    /* stream ended */
  }
}

export function ConnectionsPanel({
  onConnected,
  oauthReturn,
}: {
  onConnected?: () => void;
  oauthReturn?: {
    connected?: string;
    connectionId?: string;
    error?: string;
    provider?: string;
    configureScope?: boolean;
  };
}) {
  const { showToast } = useDataHub();
  const [providers, setProviders] = useState<IntegrationProvider[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [authModes, setAuthModes] = useState<Record<string, AuthMode>>({});
  const [credForm, setCredForm] = useState<Record<string, string>>({});
  const [oauthExtras, setOauthExtras] = useState<Record<string, string>>({});
  const [scopeEditor, setScopeEditor] = useState<{ connectionId: string; provider: string; name: string } | null>(null);

  const openScopeEditor = useCallback((connectionId: string, providerId: string) => {
    setScopeEditor({
      connectionId,
      provider: providerId,
      name: providers.find((p) => p.id === providerId)?.name ?? providerId,
    });
  }, [providers]);

  const refresh = useCallback(async () => {
    const [pRes, cRes] = await Promise.all([
      apiFetch("/v1/integrations/providers"),
      apiFetch("/v1/integrations/sources"),
    ]);
    if (pRes.ok) {
      const listed = ((await pRes.json()).providers ?? []) as IntegrationProvider[];
      setProviders(listed.filter((p) => p.auth_type !== "upload"));
    } else {
      showToast("Could not load integrations", "error");
    }
    if (cRes.ok) setConnections((await cRes.json()).connections ?? []);
  }, [showToast]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!oauthReturn) return;
    if (oauthReturn.error) {
      const name = oauthReturn.provider
        ? providers.find((p) => p.id === oauthReturn.provider)?.name ?? oauthReturn.provider
        : "Integration";
      showToast(`${name}: ${formatIntegrationError(oauthReturn.error) ?? oauthReturn.error}`, "error");
      return;
    }
    if (oauthReturn.connected) {
      const name =
        providers.find((p) => p.id === oauthReturn.connected)?.name ?? oauthReturn.connected;
      showToast(`${name} connected`);
      void refresh();
      onConnected?.();
      if (oauthReturn.configureScope && oauthReturn.connectionId && oauthReturn.connected) {
        openScopeEditor(oauthReturn.connectionId, oauthReturn.connected);
      } else if (oauthReturn.connectionId && SCOPE_CONFIG[oauthReturn.connected ?? ""]) {
        openScopeEditor(oauthReturn.connectionId, oauthReturn.connected);
      } else if (oauthReturn.connectionId) {
        void watchSyncEvents(oauthReturn.connectionId, name, () => void refresh(), showToast);
      }
    }
  }, [oauthReturn, onConnected, providers, refresh, showToast, openScopeEditor]);

  const connectionsByProvider = new Map(connections.map((c) => [c.provider, c]));
  const categories = groupProvidersByCategory(providers);

  function providerLabel(providerId: string) {
    return providers.find((p) => p.id === providerId)?.name ?? providerId;
  }

  function authModeFor(provider: IntegrationProvider): AuthMode {
    return authModes[provider.id] ?? defaultAuthMode(provider);
  }

  function setAuthMode(providerId: string, mode: AuthMode) {
    setAuthModes((prev) => ({ ...prev, [providerId]: mode }));
  }

  async function connectOAuth(provider: IntegrationProvider) {
    const params = new URLSearchParams();
    for (const field of OAUTH_EXTRA_FIELDS[provider.id] ?? []) {
      const value = oauthExtras[field.key]?.trim();
      if (value) params.set(field.key, value);
    }
    if (provider.id === "zendesk" && !params.get("subdomain")) {
      showToast("Enter your Zendesk subdomain first", "error");
      return;
    }
    const qs = params.toString();
    const res = await apiFetch(`/v1/integrations/connect/${provider.id}${qs ? `?${qs}` : ""}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = typeof body.detail === "string" ? body.detail : null;
      showToast(detail ?? `Could not connect ${provider.name}`, "error");
      return;
    }
    const body = await res.json();
    if (body.authorize_url && isAllowedOAuthAuthorizeUrl(body.authorize_url)) {
      window.location.href = body.authorize_url;
    } else if (body.authorize_url) {
      showToast(`Invalid OAuth redirect for ${provider.name}`, "error");
    }
  }

  async function connectPlatform(providerId: string) {
    const res = await apiFetch(`/v1/integrations/sources/${providerId}/connect`, {
      method: "POST",
      body: JSON.stringify({ credentials: {} }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = typeof body.detail === "string" ? body.detail : null;
      showToast(detail ?? `Could not connect ${providerLabel(providerId)}`, "error");
      return;
    }
    const body = await res.json();
    const connId = body.connection?.id as string | undefined;
    showToast(`${providerLabel(providerId)} connected`);
    void refresh();
    onConnected?.();
    if (connId) {
      openScopeEditor(connId, providerId);
    }
  }

  async function connectApiKey(providerId: string) {
    const schema = API_KEY_PROVIDERS[providerId];
    if (!schema) return;
    const credentials: Record<string, unknown> = { ...credForm };
    if (providerId === "reviews" || providerId === "reddit") {
      /* scope configured in editor */
    }
    const res = await apiFetch(`/v1/integrations/sources/${providerId}/connect`, {
      method: "POST",
      body: JSON.stringify({ credentials }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = typeof body.detail === "string" ? body.detail : null;
      showToast(detail ?? `Could not connect ${providerLabel(providerId)}`, "error");
      return;
    }
    const body = await res.json();
    const connId = body.connection?.id as string | undefined;
    const needsScope = body.needs_scope_configuration || Boolean(SCOPE_CONFIG[providerId]);
    showToast(`${providerLabel(providerId)} connected`);
    setActiveProvider(null);
    setCredForm({});
    void refresh();
    onConnected?.();
    if (connId && needsScope) {
      openScopeEditor(connId, providerId);
      return;
    }
    if (connId) {
      void watchSyncEvents(connId, providerLabel(providerId), () => void refresh(), showToast);
    }
  }

  async function syncNow(connection: Connection) {
    if (connection.scope_configured === false) {
      showToast("Configure access before syncing", "error");
      openScopeEditor(connection.id, connection.provider);
      return;
    }
    const res = await apiFetch(`/v1/integrations/sources/${connection.id}/sync`, { method: "POST" });
    if (!res.ok) {
      showToast("Could not start sync", "error");
      return;
    }
    showToast("Sync started");
    void watchSyncEvents(connection.id, connection.label, () => void refresh(), showToast);
  }

  async function disconnect(connection: Connection) {
    const res = await apiFetch(`/v1/integrations/sources/${connection.id}`, { method: "DELETE" });
    if (!res.ok) {
      showToast(`Could not disconnect ${connection.label}`, "error");
      return;
    }
    showToast(`${connection.label} disconnected`);
    void refresh();
  }

  function handleConnect(provider: IntegrationProvider) {
    const blocked = integrationConnectBlockedMessage(provider);
    if (blocked) {
      showToast(blocked, "error");
      return;
    }
    if (isPlatformManaged(provider) && SCOPE_CONFIG[provider.id] && !API_KEY_PROVIDERS[provider.id]) {
      void connectPlatform(provider.id);
      return;
    }
    const mode = authModeFor(provider);
    const needsOAuthForm =
      mode === "oauth" &&
      supportsOAuthConnect(provider) &&
      (OAUTH_EXTRA_FIELDS[provider.id]?.length ?? 0) > 0;
    if (needsOAuthForm && activeProvider !== provider.id) {
      setActiveProvider(provider.id);
      return;
    }
    if (mode === "token" && supportsCredentialForm(provider)) {
      setActiveProvider(activeProvider === provider.id ? null : provider.id);
      setCredForm({});
      return;
    }
    if (supportsOAuthConnect(provider)) {
      void connectOAuth(provider);
      return;
    }
    if (supportsCredentialForm(provider)) {
      setActiveProvider(activeProvider === provider.id ? null : provider.id);
      setCredForm({});
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Integrations</p>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mkt-muted">
          Connect your stack by category. Data syncs in the background and feeds Customer Intelligence, competitive
          monitoring, and campaign generation.
        </p>
      </div>

      {categories.map((category) => (
        <ProductCard key={category.id} className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">{category.label}</h2>
            <p className="mt-1 text-sm leading-relaxed text-mkt-muted">{category.description}</p>
          </div>

          <div className="space-y-3">
            {category.providers.map((provider) => {
              const connection = connectionsByProvider.get(provider.id);
              const isConnected = Boolean(connection);
              const isExpanded = activeProvider === provider.id;
              const blocked = integrationConnectBlockedMessage(provider);
              const mode = authModeFor(provider);
              const showDualAuth =
                DUAL_AUTH_PROVIDER_IDS.has(provider.id) &&
                supportsCredentialForm(provider) &&
                supportsOAuthConnect(provider);

              return (
                <div key={provider.id} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02]">
                  <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-mkt-ink">{provider.name}</h3>
                        {isConnected ? <ProductStatusPill status={connection!.status} /> : null}
                        {isPlatformManaged(provider) ? (
                          <span className="rounded-sm bg-mkt-ink/[0.06] px-2 py-0.5 text-xs text-mkt-muted">
                            Platform-managed
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 text-sm leading-relaxed text-mkt-muted">{benefitFor(provider)}</p>
                      {blocked && !isConnected ? (
                        <p className="mt-1 text-xs text-mkt-muted">{blocked}</p>
                      ) : null}
                      {isConnected && connection?.scope_summary ? (
                        <p className="mt-1 text-xs text-mkt-muted">Access: {connection.scope_summary}</p>
                      ) : null}
                      {isConnected && connection?.scope_configured === false ? (
                        <p className="mt-1 text-xs font-medium text-mkt-accent-warm">
                          Configure access before syncing
                        </p>
                      ) : null}
                      {isConnected && connection?.last_sync_at ? (
                        <p className="mt-1 text-xs text-mkt-muted">
                          Last sync: {new Date(connection.last_sync_at).toLocaleString()}
                        </p>
                      ) : null}
                      {isConnected && connection?.last_error ? (
                        <p className="mt-1 text-xs text-mkt-accent-warm">
                          {formatIntegrationError(connection.last_error) ?? connection.last_error}
                        </p>
                      ) : null}
                    </div>

                    <div className="flex shrink-0 gap-2 sm:pl-4">
                      {isConnected ? (
                        <>
                          {connection?.scope_configured === false || SCOPE_CONFIG[provider.id] ? (
                            <ProductButton
                              variant="secondary"
                              onClick={() => openScopeEditor(connection!.id, provider.id)}
                            >
                              {connection?.scope_configured === false ? "Configure access" : "Edit access"}
                            </ProductButton>
                          ) : null}
                          <ProductButton variant="secondary" onClick={() => void syncNow(connection!)}>
                            Sync
                          </ProductButton>
                          <ProductButton variant="ghost" onClick={() => void disconnect(connection!)}>
                            Disconnect
                          </ProductButton>
                        </>
                      ) : (
                        <ProductButton onClick={() => handleConnect(provider)} disabled={Boolean(blocked)}>
                          {supportsCredentialForm(provider) && isExpanded ? "Cancel" : "Connect"}
                        </ProductButton>
                      )}
                    </div>
                  </div>

                  {isExpanded && !isConnected ? (
                    <div className="space-y-3 border-t border-mkt-ink/[0.06] p-4">
                      {showDualAuth ? (
                        <div className="flex gap-2">
                          <ProductButton
                            type="button"
                            variant={mode === "oauth" ? "primary" : "secondary"}
                            onClick={() => setAuthMode(provider.id, "oauth")}
                          >
                            OAuth
                          </ProductButton>
                          <ProductButton
                            type="button"
                            variant={mode === "token" ? "primary" : "secondary"}
                            onClick={() => setAuthMode(provider.id, "token")}
                          >
                            API token
                          </ProductButton>
                        </div>
                      ) : null}

                      {mode === "oauth" && supportsOAuthConnect(provider) ? (
                        <form
                          className="space-y-3"
                          onSubmit={(e) => {
                            e.preventDefault();
                            void connectOAuth(provider);
                          }}
                        >
                          {(OAUTH_EXTRA_FIELDS[provider.id] ?? []).map((f) => (
                            <ProductInput
                              key={f.key}
                              placeholder={f.label}
                              value={oauthExtras[f.key] ?? ""}
                              onChange={(ev) => setOauthExtras({ ...oauthExtras, [f.key]: ev.target.value })}
                            />
                          ))}
                          <ProductButton type="submit">Continue with OAuth</ProductButton>
                        </form>
                      ) : API_KEY_PROVIDERS[provider.id] ? (
                        <form
                          className="space-y-3"
                          onSubmit={(e) => {
                            e.preventDefault();
                            void connectApiKey(provider.id);
                          }}
                        >
                          {API_KEY_PROVIDERS[provider.id].fields.map((f) => (
                            <ProductInput
                              key={f.key}
                              placeholder={f.label}
                              type={f.type ?? "text"}
                              value={credForm[f.key] ?? ""}
                              onChange={(ev) => setCredForm({ ...credForm, [f.key]: ev.target.value })}
                            />
                          ))}
                          <ProductButton type="submit">
                            {isPlatformManaged(provider) ? "Save & configure" : "Save & connect"}
                          </ProductButton>
                        </form>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </ProductCard>
      ))}

      {scopeEditor ? (
        <IntegrationScopeEditor
          connectionId={scopeEditor.connectionId}
          provider={scopeEditor.provider}
          providerName={scopeEditor.name}
          open
          onClose={() => setScopeEditor(null)}
          onSaved={() => void refresh()}
          showToast={showToast}
        />
      ) : null}
    </div>
  );
}
