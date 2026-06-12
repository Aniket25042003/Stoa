"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";

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
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Roles</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">IAM-style access</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          System roles are immutable defaults. Create custom roles with explicit resource:action permissions.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="rounded-3xl p-4 card-glass space-y-2">
          <button type="button" className="btn-primary w-full px-4 py-2 text-sm" onClick={() => resetEditor(null)}>
            New custom role
          </button>
          {roles.map((role) => (
            <button
              key={role.id}
              type="button"
              onClick={() => resetEditor(role)}
              className={`w-full rounded-xl px-4 py-3 text-left text-sm ${selectedId === role.id ? "bg-primary/10 text-primary" : "bg-surface-container-low"}`}
            >
              <p className="font-semibold">{role.name}</p>
              <p className="text-xs text-on-surface-variant">
                {role.is_system ? "System" : "Custom"} · {role.permissions.length} permissions
              </p>
            </button>
          ))}
        </div>

        <div className="rounded-3xl p-6 card-glass space-y-5">
          <h2 className="font-display text-xl font-bold">{selected?.is_system ? "View role" : selected ? "Edit role" : "Create role"}</h2>
          <div>
            <label className="text-sm font-medium">Name</label>
            <input
              value={name}
              disabled={selected?.is_system}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm disabled:opacity-60"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <input
              value={description}
              disabled={selected?.is_system}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm disabled:opacity-60"
            />
          </div>
          <div className="space-y-4">
            {catalog.map((group) => (
              <div key={group.resource}>
                <p className="text-sm font-semibold">{group.label}</p>
                <div className="mt-2 flex flex-wrap gap-3">
                  {group.permissions.map((perm) => {
                    const allowed = grantable.includes(perm.key);
                    const checked = permissions.includes(perm.key);
                    return (
                      <label key={perm.key} className={`flex items-center gap-2 text-sm ${!allowed ? "opacity-50" : ""}`}>
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={selected?.is_system || !allowed}
                          onChange={() => togglePermission(perm.key)}
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
              <button type="button" disabled={loading || !name.trim() || permissions.length === 0} className="btn-primary px-5 py-3 text-sm disabled:opacity-50" onClick={() => void saveRole()}>
                {loading ? "Saving..." : "Save role"}
              </button>
            ) : null}
            {selected && !selected.is_system ? (
              <button type="button" disabled={loading} className="btn-secondary px-5 py-3 text-sm" onClick={() => void deleteRole(selected)}>
                Delete role
              </button>
            ) : null}
          </div>
          {message ? <p className="text-sm text-on-surface-variant">{message}</p> : null}
        </div>
      </div>
    </div>
  );
}
