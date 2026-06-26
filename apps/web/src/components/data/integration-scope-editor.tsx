/**
 * @file apps/web/src/components/data/integration-scope-editor.tsx
 * @description Post-connect resource scope picker for integrations.
 */
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { buildScopePayload, SCOPE_CONFIG } from "@/lib/integration-scope-config";
import { consumeSse } from "@/lib/sse";
import { ProductButton, ProductInput } from "@/components/product";

export type ScopeResource = {
  id: string;
  label: string;
  kind: string;
  description?: string | null;
};

type Props = {
  connectionId: string;
  provider: string;
  providerName: string;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  showToast: (message: string, variant?: "error" | "success") => void;
};

export function IntegrationScopeEditor({
  connectionId,
  provider,
  providerName,
  open,
  onClose,
  onSaved,
  showToast,
}: Props) {
  const config = SCOPE_CONFIG[provider];
  const [resources, setResources] = useState<ScopeResource[]>([]);
  const [selected, setSelected] = useState<ScopeResource[]>([]);
  const [guided, setGuided] = useState<Record<string, string>>({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return resources;
    return resources.filter(
      (r) => r.label.toLowerCase().includes(q) || r.id.toLowerCase().includes(q)
    );
  }, [resources, search]);

  const loadResources = useCallback(
    async (nextCursor?: string | null) => {
      if (!config) return;
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (nextCursor) params.set("cursor", nextCursor);
        if (search.trim()) params.set("q", search.trim());
        const qs = params.toString();
        const res = await apiFetch(
          `/v1/integrations/sources/${connectionId}/resources${qs ? `?${qs}` : ""}`
        );
        if (!res.ok) {
          showToast(`Could not load ${providerName} resources`, "error");
          return;
        }
        const body = await res.json();
        const listed = (body.resources ?? []) as ScopeResource[];
        setResources((prev) => (nextCursor ? [...prev, ...listed] : listed));
        setCursor(body.next_cursor ?? null);
      } finally {
        setLoading(false);
      }
    },
    [config, connectionId, providerName, search, showToast]
  );

  useEffect(() => {
    if (!open) return;
    setSelected([]);
    setGuided({});
    setResources([]);
    setCursor(null);
    void loadResources(null);
  }, [open, connectionId, loadResources]);

  function toggle(item: ScopeResource) {
    if (!config) return;
    if (!config.multi) {
      setSelected([item]);
      return;
    }
    setSelected((prev) => {
      const exists = prev.some((p) => p.id === item.id && p.kind === item.kind);
      if (exists) return prev.filter((p) => !(p.id === item.id && p.kind === item.kind));
      return [...prev, item];
    });
  }

  function isSelected(item: ScopeResource) {
    return selected.some((s) => s.id === item.id && s.kind === item.kind);
  }

  async function save() {
    if (!config) return;
    setSaving(true);
    try {
      const scope = buildScopePayload(provider, selected, guided);
      const res = await apiFetch(`/v1/integrations/sources/${connectionId}/scope`, {
        method: "PATCH",
        body: JSON.stringify({ scope, sync: true }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        showToast(typeof body.detail === "string" ? body.detail : "Could not save access scope", "error");
        return;
      }
      showToast(`${providerName} access configured`);
      onSaved();
      onClose();
      const ctrl = new AbortController();
      try {
        await consumeSse(
          `/v1/integrations/sources/${connectionId}/events`,
          (data) => {
            if (data.status === "completed") {
              showToast(`${providerName} sync complete`);
              ctrl.abort();
            }
            if (data.status === "failed") {
              showToast(`${providerName} sync failed`, "error");
              ctrl.abort();
            }
          },
          ctrl.signal
        );
      } catch {
        /* stream ended */
      }
    } finally {
      setSaving(false);
    }
  }

  if (!open || !config) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-mkt-ink/40 p-4">
      <div className="flex max-h-[85vh] w-full max-w-lg flex-col rounded-sm border border-mkt-ink/[0.08] bg-mkt-surface shadow-lg">
        <div className="border-b border-mkt-ink/[0.06] p-4">
          <h2 className="text-lg font-semibold text-mkt-ink">Configure {providerName} access</h2>
          <p className="mt-1 text-sm text-mkt-muted">
            Choose what Stoa can read. Only selected resources are synced into your Memory Layer.
          </p>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {config.guided ? (
            <>
              {config.guidedFields?.map((f) => (
                <ProductInput
                  key={f.key}
                  placeholder={f.label}
                  type={f.type ?? "text"}
                  value={guided[f.key] ?? ""}
                  onChange={(ev) => setGuided({ ...guided, [f.key]: ev.target.value })}
                />
              ))}
              {provider === "reviews" || provider === "reddit" ? (
                <div className="space-y-2">
                  <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                    {provider === "reviews" ? "Platforms" : "Suggested subreddits"}
                  </p>
                  {resources.map((item) => (
                    <label
                      key={item.id}
                      className="flex cursor-pointer items-center gap-2 rounded-sm border border-mkt-ink/[0.06] p-2 text-sm"
                    >
                      <input
                        type="checkbox"
                        checked={isSelected(item)}
                        onChange={() => toggle(item)}
                      />
                      <span>{item.label}</span>
                    </label>
                  ))}
                </div>
              ) : null}
            </>
          ) : (
            <>
              <ProductInput
                placeholder="Search resources…"
                value={search}
                onChange={(ev) => setSearch(ev.target.value)}
              />
              {loading && resources.length === 0 ? (
                <p className="text-sm text-mkt-muted">Loading resources…</p>
              ) : null}
              <div className="space-y-1">
                {filtered.map((item) => (
                  <label
                    key={`${item.kind}:${item.id}`}
                    className="flex cursor-pointer items-start gap-2 rounded-sm border border-mkt-ink/[0.06] p-2 text-sm hover:bg-mkt-ink/[0.02]"
                  >
                    <input
                      type={config.multi ? "checkbox" : "radio"}
                      name={`scope-${provider}`}
                      checked={isSelected(item)}
                      onChange={() => toggle(item)}
                      className="mt-0.5"
                    />
                    <span>
                      <span className="font-medium text-mkt-ink">{item.label}</span>
                      {item.description ? (
                        <span className="mt-0.5 block text-xs text-mkt-muted">{item.description}</span>
                      ) : null}
                      <span className="mt-0.5 block text-xs text-mkt-subtle">{item.kind}</span>
                    </span>
                  </label>
                ))}
              </div>
              {cursor ? (
                <ProductButton variant="secondary" onClick={() => void loadResources(cursor)} disabled={loading}>
                  Load more
                </ProductButton>
              ) : null}
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t border-mkt-ink/[0.06] p-4">
          <ProductButton variant="ghost" onClick={onClose}>
            Cancel
          </ProductButton>
          <ProductButton onClick={() => void save()} disabled={saving}>
            {saving ? "Saving…" : "Save & sync"}
          </ProductButton>
        </div>
      </div>
    </div>
  );
}
