/**
 * @file apps/web/src/app/(app)/data/connections-panel.tsx
 * @layer Frontend Product UI
 * @description Implements connections panel behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/lib/sse";
import { INTEGRATION_BENEFITS, groupProvidersByCategory } from "@/lib/integration-catalog";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductStatusPill,
} from "@/components/product";
import { useDataHub } from "./data-hub-context";

type Provider = {
  id: string;
  name: string;
  auth_type: string;
  description: string;
};

type Connection = {
  id: string;
  provider: string;
  label: string;
  status: string;
  last_sync_at?: string | null;
  last_error?: string | null;
};

const API_KEY_PROVIDERS: Record<string, { fields: { key: string; label: string; type?: string }[] }> = {
  intercom: { fields: [{ key: "access_token", label: "Access Token", type: "password" }] },
  zendesk: {
    fields: [
      { key: "subdomain", label: "Subdomain" },
      { key: "email", label: "Agent Email" },
      { key: "api_token", label: "API Token", type: "password" },
    ],
  },
  reviews: {
    fields: [
      { key: "product_query", label: "G2/Capterra product URL or name" },
      { key: "max_results", label: "Max reviews (default 50)" },
    ],
  },
  slack: {
    fields: [
      { key: "access_token", label: "Bot Token", type: "password" },
      { key: "channel_ids", label: "Channel IDs (comma-separated)" },
    ],
  },
  notion: {
    fields: [
      { key: "access_token", label: "Integration Token", type: "password" },
      { key: "page_ids", label: "Page IDs (comma-separated)" },
    ],
  },
  jira: {
    fields: [
      { key: "domain", label: "Domain (e.g. acme.atlassian.net)" },
      { key: "email", label: "Email" },
      { key: "api_token", label: "API Token", type: "password" },
      { key: "jql", label: "JQL (optional)" },
    ],
  },
  posthog: {
    fields: [
      { key: "api_key", label: "Personal API Key", type: "password" },
      { key: "project_id", label: "Project ID" },
    ],
  },
  reddit: {
    fields: [
      { key: "search_query", label: "Brand or product search query" },
      { key: "subreddits", label: "Subreddits (comma-separated, optional)" },
    ],
  },
};

/**
 * Handles benefit for behavior for this part of the Stoa application.
 *
 * @param provider - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function benefitFor(provider: Provider): string {
  return INTEGRATION_BENEFITS[provider.id] ?? provider.description;
}

/**
 * Handles uses credential form behavior for this part of the Stoa application.
 *
 * @param provider - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function usesCredentialForm(provider: Provider): boolean {
  if (provider.auth_type === "oauth") return false;
  return provider.auth_type === "api_key" || Boolean(API_KEY_PROVIDERS[provider.id]);
}

export function ConnectionsPanel({ onConnected }: { onConnected?: () => void }) {
  const { showToast } = useDataHub();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [credForm, setCredForm] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    const [pRes, cRes] = await Promise.all([
      apiFetch("/v1/integrations/providers"),
      apiFetch("/v1/integrations/sources"),
    ]);
    if (pRes.ok) {
      const listed = ((await pRes.json()).providers ?? []) as Provider[];
      setProviders(listed.filter((p) => p.auth_type !== "upload"));
    }
    if (cRes.ok) setConnections((await cRes.json()).connections ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const connectionsByProvider = new Map(connections.map((c) => [c.provider, c]));
  const categories = groupProvidersByCategory(providers);

  function providerLabel(providerId: string) {
    return providers.find((p) => p.id === providerId)?.name ?? providerId;
  }

  async function connectOAuth(provider: Provider) {
    const res = await apiFetch(`/v1/integrations/connect/${provider.id}`);
    if (!res.ok) {
      showToast(`Could not connect ${provider.name}`, "error");
      return;
    }
    const body = await res.json();
    if (body.authorize_url) {
      window.location.href = body.authorize_url;
    }
  }

  async function connectApiKey(providerId: string) {
    const schema = API_KEY_PROVIDERS[providerId];
    if (!schema) return;
    const credentials: Record<string, unknown> = { ...credForm };
    if (providerId === "slack" && typeof credentials.channel_ids === "string") {
      credentials.channel_ids = credentials.channel_ids.split(",").map((s) => s.trim()).filter(Boolean);
    }
    if (providerId === "notion" && typeof credentials.page_ids === "string") {
      credentials.page_ids = credentials.page_ids.split(",").map((s) => s.trim()).filter(Boolean);
    }
    if (providerId === "reddit" && typeof credentials.subreddits === "string") {
      credentials.subreddits = credentials.subreddits.split(",").map((s) => s.trim()).filter(Boolean);
    }
    const res = await apiFetch(`/v1/integrations/sources/${providerId}/connect`, {
      method: "POST",
      body: JSON.stringify({ credentials }),
    });
    if (!res.ok) {
      showToast(`Could not connect ${providerLabel(providerId)}`, "error");
      return;
    }
    const body = await res.json();
    showToast(`${providerLabel(providerId)} connected`);
    setActiveProvider(null);
    setCredForm({});
    void refresh();
    onConnected?.();
    const connId = body.connection?.id;
    if (connId) {
      const ctrl = new AbortController();
      try {
        await consumeSse(
          `/v1/integrations/sources/${connId}/events`,
          (data) => {
            if (data.status === "completed") {
              showToast(`${providerLabel(providerId)} sync complete`);
              ctrl.abort();
              void refresh();
            }
            if (data.status === "failed") {
              showToast(`${providerLabel(providerId)} sync failed`, "error");
              ctrl.abort();
            }
          },
          ctrl.signal
        );
      } catch {
        /* stream ended */
      }
    }
  }

  async function syncNow(connectionId: string) {
    const res = await apiFetch(`/v1/integrations/sources/${connectionId}/sync`, { method: "POST" });
    if (!res.ok) {
      showToast("Could not start sync", "error");
      return;
    }
    showToast("Sync started");
    void refresh();
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

  function handleConnect(provider: Provider) {
    if (usesCredentialForm(provider)) {
      setActiveProvider(activeProvider === provider.id ? null : provider.id);
      setCredForm({});
      return;
    }
    void connectOAuth(provider);
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
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
              {category.label}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-mkt-muted">{category.description}</p>
          </div>

          <div className="space-y-3">
            {category.providers.map((provider) => {
              const connection = connectionsByProvider.get(provider.id);
              const isConnected = Boolean(connection);
              const isExpanded = activeProvider === provider.id;

              return (
                <div key={provider.id} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02]">
                  <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-mkt-ink">{provider.name}</h3>
                        {isConnected ? <ProductStatusPill status={connection!.status} /> : null}
                      </div>
                      <p className="mt-1 text-sm leading-relaxed text-mkt-muted">
                        {benefitFor(provider)}
                      </p>
                      {isConnected && connection?.last_sync_at ? (
                        <p className="mt-1 text-xs text-mkt-muted">
                          Last sync: {new Date(connection.last_sync_at).toLocaleString()}
                        </p>
                      ) : null}
                      {isConnected && connection?.last_error ? (
                        <p className="mt-1 text-xs text-mkt-accent-warm">{connection.last_error}</p>
                      ) : null}
                    </div>

                    <div className="flex shrink-0 gap-2 sm:pl-4">
                      {isConnected ? (
                        <>
                          <ProductButton variant="secondary" onClick={() => void syncNow(connection!.id)}>
                            Sync
                          </ProductButton>
                          <ProductButton variant="ghost" onClick={() => void disconnect(connection!)}>
                            Disconnect
                          </ProductButton>
                        </>
                      ) : (
                        <ProductButton onClick={() => handleConnect(provider)}>
                          {usesCredentialForm(provider) && isExpanded ? "Cancel" : "Connect"}
                        </ProductButton>
                      )}
                    </div>
                  </div>

                  {isExpanded && !isConnected && API_KEY_PROVIDERS[provider.id] ? (
                    <form
                      className="space-y-3 border-t border-mkt-ink/[0.06] p-4"
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
                      <ProductButton type="submit">Save & connect</ProductButton>
                    </form>
                  ) : null}
                </div>
              );
            })}
          </div>
        </ProductCard>
      ))}

    </div>
  );
}
