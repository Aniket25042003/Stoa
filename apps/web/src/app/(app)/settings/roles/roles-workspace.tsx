/**
 * @file apps/web/src/app/(app)/settings/roles/roles-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements roles workspace behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { productLabelClass } from "@/lib/product-typography";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductPageHeader,
} from "@/components/product";

type Role = {
  id: string;
  name: string;
  role_key: string;
  description?: string;
  permissions: string[];
  is_system: boolean;
};

type CatalogGroup = {
  resource: string;
  label: string;
  permissions: { key: string; label: string }[];
};

const labelClass = productLabelClass;

/**
 * Handles roles workspace behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function RolesWorkspace() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [catalog, setCatalog] = useState<CatalogGroup[]>([]);
  const [grantable, setGrantable] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [permissions, setPermissions] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const selected = useMemo(() => roles.find((r) => r.id === selectedId) ?? null, [roles, selectedId]);

  async function load() {
    const [rolesRes, catalogRes] = await Promise.all([apiFetch("/v1/roles"), apiFetch("/v1/roles/catalog")]);
    if (rolesRes.ok) {
      const body = await rolesRes.json();
      setRoles(body.roles ?? []);
    }
    if (catalogRes.ok) {
      const body = await catalogRes.json();
      setCatalog(body.groups ?? []);
      setGrantable(body.grantable ?? []);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function resetEditor(role?: Role | null) {
    if (!role) {
      setSelectedId(null);
      setName("");
      setDescription("");
      setPermissions([]);
      return;
    }
    setSelectedId(role.id);
    setName(role.name);
    setDescription(role.description ?? "");
    setPermissions(role.permissions ?? []);
  }

  function togglePermission(key: string) {
    setPermissions((cur) => (cur.includes(key) ? cur.filter((p) => p !== key) : [...cur, key]));
  }

  async function saveRole() {
    setMessage(null);
    setLoading(true);
    const payload = { name: name.trim(), description: description.trim() || null, permissions };
    const res = selected
      ? await apiFetch(`/v1/roles/${selected.id}`, { method: "PATCH", body: JSON.stringify(payload) })
      : await apiFetch("/v1/roles", { method: "POST", body: JSON.stringify(payload) });
    const body = await res.json().catch(() => null);
    setLoading(false);
    if (!res.ok) {
      setMessage(body?.detail?.message ?? body?.detail ?? "Could not save role.");
      return;
    }
    await load();
    resetEditor(body.role ?? null);
    setMessage("Role saved.");
  }

  async function deleteRole(role: Role) {
    if (role.is_system) return;
    const reassign = roles.find((r) => r.role_key === "viewer");
    if (!reassign) return;
    setLoading(true);
    const res = await apiFetch(`/v1/roles/${role.id}`, {
      method: "DELETE",
      body: JSON.stringify({ reassign_to_role_id: reassign.id }),
    });
    setLoading(false);
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      setMessage(body?.detail ?? "Could not delete role.");
      return;
    }
    resetEditor(null);
    await load();
    setMessage("Role deleted.");
  }

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Organization"
        title="Roles & permissions"
        lead="System roles are immutable defaults. Create custom roles with explicit resource:action permissions."
      />

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <ProductCard className="space-y-2 !p-4">
          <ProductButton className="w-full" onClick={() => resetEditor(null)}>
            New custom role
          </ProductButton>
          {roles.map((role) => (
            <button
              key={role.id}
              type="button"
              onClick={() => resetEditor(role)}
              className={cn(
                "w-full rounded-sm px-4 py-3 text-left transition-colors",
                selectedId === role.id
                  ? "border-l-2 border-mkt-accent bg-mkt-accent/[0.08]"
                  : "border-l-2 border-transparent bg-mkt-ink/[0.02] hover:bg-mkt-ink/[0.04]"
              )}
            >
              <p className="text-sm font-semibold text-mkt-ink">{role.name}</p>
              <p className="text-xs text-mkt-muted">
                {role.is_system ? "System" : "Custom"} · {role.permissions.length} permissions
              </p>
            </button>
          ))}
        </ProductCard>

        <ProductCard className="space-y-5">
          <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
            {selected?.is_system ? "View role" : selected ? "Edit role" : "Create role"}
          </h2>
          <div>
            <label className={labelClass}>Name</label>
            <ProductInput
              value={name}
              disabled={selected?.is_system}
              onChange={(e) => setName(e.target.value)}
              className="mt-1.5 disabled:opacity-60"
            />
          </div>
          <div>
            <label className={labelClass}>Description</label>
            <ProductInput
              value={description}
              disabled={selected?.is_system}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1.5 disabled:opacity-60"
            />
          </div>
          <div className="space-y-4">
            {catalog.map((group) => (
              <div key={group.resource}>
                <p className="text-sm font-semibold text-mkt-ink">{group.label}</p>
                <div className="mt-2 flex flex-wrap gap-3">
                  {group.permissions.map((perm) => {
                    const allowed = grantable.includes(perm.key);
                    const checked = permissions.includes(perm.key);
                    return (
                      <label
                        key={perm.key}
                        className={cn(
                          "flex items-center gap-2 text-sm text-mkt-ink",
                          !allowed && "opacity-50"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={selected?.is_system || !allowed}
                          onChange={() => togglePermission(perm.key)}
                          className="accent-mkt-accent"
                        />
                        {perm.label}
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3">
            {!selected?.is_system ? (
              <ProductButton
                disabled={loading || !name.trim() || permissions.length === 0}
                onClick={() => void saveRole()}
              >
                {loading ? "Saving..." : "Save role"}
              </ProductButton>
            ) : null}
            {selected && !selected.is_system ? (
              <ProductButton variant="secondary" disabled={loading} onClick={() => void deleteRole(selected)}>
                Delete role
              </ProductButton>
            ) : null}
          </div>
          {message ? <p className="text-sm text-mkt-muted">{message}</p> : null}
        </ProductCard>
      </div>
    </div>
  );
}
