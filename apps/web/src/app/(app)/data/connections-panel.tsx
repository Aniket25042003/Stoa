"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/lib/sse";

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
  gong: {
    fields: [
      { key: "access_key", label: "Access Key" },
      { key: "access_key_secret", label: "Access Key Secret", type: "password" },
    ],
  },
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
};

export function ConnectionsPanel({ onConnected }: { onConnected?: () => void }) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);
  const [credForm, setCredForm] = useState<Record<string, string>>({});

  const refresh = useCallback(async () => {
    const [pRes, cRes] = await Promise.all([
      apiFetch("/v1/integrations/providers"),
      apiFetch("/v1/integrations/sources"),
    ]);
    if (pRes.ok) setProviders((await pRes.json()).providers ?? []);
    if (cRes.ok) setConnections((await cRes.json()).connections ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function connectOAuth(provider: string) {
    setStatus(`Opening ${provider} authorization...`);
    const res = await apiFetch(`/v1/integrations/connect/${provider}`);
    if (!res.ok) {
      setStatus(`Failed to start ${provider} OAuth`);
      return;
    }
    const body = await res.json();
    if (body.authorize_url) {
      window.location.href = body.authorize_url;
    }
  }

  async function connectApiKey(provider: string) {
    const schema = API_KEY_PROVIDERS[provider];
    if (!schema) return;
    const credentials: Record<string, unknown> = { ...credForm };
    if (provider === "slack" && typeof credentials.channel_ids === "string") {
      credentials.channel_ids = credentials.channel_ids.split(",").map((s) => s.trim()).filter(Boolean);
    }
    if (provider === "notion" && typeof credentials.page_ids === "string") {
      credentials.page_ids = credentials.page_ids.split(",").map((s) => s.trim()).filter(Boolean);
    }
    const res = await apiFetch(`/v1/integrations/sources/${provider}/connect`, {
      method: "POST",
      body: JSON.stringify({ credentials }),
    });
    if (!res.ok) {
      setStatus(`Failed to connect ${provider}`);
      return;
    }
    const body = await res.json();
    setStatus(`${provider} connected — syncing...`);
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
              setStatus(`${provider} sync completed (${data.records_written ?? 0} records)`);
              ctrl.abort();
              void refresh();
            }
            if (data.status === "failed") {
              setStatus(`${provider} sync failed`);
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
    await apiFetch(`/v1/integrations/sources/${connectionId}/sync`, { method: "POST" });
    setStatus("Sync queued");
    void refresh();
  }

  async function disconnect(connectionId: string) {
    await apiFetch(`/v1/integrations/sources/${connectionId}`, { method: "DELETE" });
    void refresh();
  }

  const oauthProviders = providers.filter((p) => p.auth_type === "oauth");
  const apiProviders = providers.filter((p) => p.auth_type === "api_key" || API_KEY_PROVIDERS[p.id]);

  return (
    <div className="rounded-3xl p-6 card-glass space-y-4">
      <h2 className="font-display text-xl font-bold">Data connections</h2>
      <p className="text-sm text-on-surface-variant">
        Connect CRM, call transcripts, support tools, and reviews. Data syncs in the background and feeds Customer Intelligence.
      </p>

      <div className="flex flex-wrap gap-2">
        {oauthProviders.map((p) => (
          <button
            key={p.id}
            type="button"
            className="btn-secondary px-3 py-2 text-sm"
            onClick={() => void connectOAuth(p.id)}
          >
            Connect {p.name}
          </button>
        ))}
        {apiProviders.map((p) => (
          <button
            key={p.id}
            type="button"
            className="btn-secondary px-3 py-2 text-sm"
            onClick={() => setActiveProvider(activeProvider === p.id ? null : p.id)}
          >
            {p.name}
          </button>
        ))}
      </div>

      {activeProvider && API_KEY_PROVIDERS[activeProvider] ? (
        <form
          className="space-y-3 rounded-xl bg-surface-container-low p-4"
          onSubmit={(e) => {
            e.preventDefault();
            void connectApiKey(activeProvider);
          }}
        >
          {API_KEY_PROVIDERS[activeProvider].fields.map((f) => (
            <input
              key={f.key}
              className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-2 text-sm"
              placeholder={f.label}
              type={f.type ?? "text"}
              value={credForm[f.key] ?? ""}
              onChange={(ev) => setCredForm({ ...credForm, [f.key]: ev.target.value })}
            />
          ))}
          <button type="submit" className="btn-primary px-4 py-2 text-sm">
            Connect
          </button>
        </form>
      ) : null}

      <ul className="space-y-2 text-sm">
        {connections.map((c) => (
          <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-container-low p-3">
            <div>
              <span className="font-semibold">{c.label}</span>
              <span className="ml-2 text-xs text-on-surface-variant">{c.status}</span>
              {c.last_sync_at ? (
                <p className="text-xs text-on-surface-variant">Last sync: {new Date(c.last_sync_at).toLocaleString()}</p>
              ) : null}
              {c.last_error ? <p className="text-xs text-red-600">{c.last_error}</p> : null}
            </div>
            <div className="flex gap-2">
              <button type="button" className="text-xs text-primary" onClick={() => void syncNow(c.id)}>
                Sync now
              </button>
              <button type="button" className="text-xs text-on-surface-variant" onClick={() => void disconnect(c.id)}>
                Disconnect
              </button>
            </div>
          </li>
        ))}
      </ul>

      {status ? <p className="text-sm text-on-surface-variant">{status}</p> : null}
    </div>
  );
}
