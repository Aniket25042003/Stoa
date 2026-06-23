/**
 * @file apps/web/src/app/(app)/settings/team/team-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements team workspace behavior for the frontend product ui.
 * @dependencies Supabase, React, BFF apiFetch
 */
"use client";

import { productLabelClass } from "@/lib/product-typography";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductPageHeader,
  ProductSelect,
} from "@/components/product";

type Role = {
  id: string;
  name: string;
  role_key: string;
  is_system: boolean;
};

type Member = {
  id: string;
  user_id: string;
  role: string;
  role_id?: string;
  role_name?: string;
  profile?: { email?: string; full_name?: string };
};

type Invite = {
  id: string;
  email: string;
  role: string;
  role_id?: string;
  expires_at: string;
  accepted_at?: string | null;
  revoked_at?: string | null;
  org_roles?: { name?: string; role_key?: string };
};

const labelClass = productLabelClass;

/**
 * Handles team workspace behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function TeamWorkspace() {
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    const [membersRes, invitesRes, rolesRes] = await Promise.all([
      apiFetch("/v1/team/members"),
      apiFetch("/v1/team/invites"),
      apiFetch("/v1/roles"),
    ]);
    if (membersRes.ok) setMembers((await membersRes.json()).members ?? []);
    if (invitesRes.ok) setInvites((await invitesRes.json()).invites ?? []);
    if (rolesRes.ok) setRoles((await rolesRes.json()).roles ?? []);
  }

  useEffect(() => {
    void load();
  }, []);

  const defaultRoleId = roles.find((r) => r.role_key === "viewer")?.id ?? roles[0]?.id ?? "";

  async function invite(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setInviteUrl(null);
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const roleId = String(form.get("role_id") ?? defaultRoleId);
    const profileHints: Record<string, string> = {};
    const jobTitle = String(form.get("job_title") ?? "").trim();
    const roleType = String(form.get("role_type") ?? "").trim();
    const department = String(form.get("department") ?? "").trim();
    if (jobTitle) profileHints.job_title = jobTitle;
    if (roleType) profileHints.role_type = roleType;
    if (department) profileHints.department = department;

    const res = await apiFetch("/v1/team/invites", {
      method: "POST",
      body: JSON.stringify({
        email: String(form.get("email") ?? "").trim(),
        role_id: roleId || undefined,
        profile_hints: Object.keys(profileHints).length ? profileHints : undefined,
      }),
    });
    const body = await res.json().catch(() => null);
    setLoading(false);
    if (!res.ok) {
      setMessage(body?.detail?.message ?? body?.detail ?? "Could not send invite.");
      return;
    }
    if (body.invite_url) setInviteUrl(body.invite_url);
    setMessage(
      body.invite_url
        ? "Invite created. Share the link below if email delivery is delayed."
        : "Invite created. Supabase will email the teammate when SMTP is configured."
    );
    await load();
    event.currentTarget.reset();
  }

  async function changeMemberRole(memberId: string, roleId: string) {
    const res = await apiFetch(`/v1/team/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify({ role_id: roleId }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      setMessage(body?.detail ?? "Could not update member role.");
      return;
    }
    await load();
  }

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Organization"
        title="Team"
        lead="Invite teammates into the active organization and assign system or custom roles."
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <ProductCard>
          <form onSubmit={(event) => void invite(event)} className="space-y-4">
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Invite teammate</h2>
            <div>
              <label className={labelClass}>Work email</label>
              <ProductInput name="email" type="email" required placeholder="teammate@company.com" className="mt-1.5" />
            </div>
            <div>
              <label className={labelClass}>Role</label>
              <ProductSelect name="role_id" defaultValue={defaultRoleId} className="mt-1.5">
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name} {role.is_system ? "" : "(custom)"}
                  </option>
                ))}
              </ProductSelect>
            </div>
            <div>
              <label className={labelClass}>Job title (optional)</label>
              <ProductInput name="job_title" className="mt-1.5" />
            </div>
            <div>
              <label className={labelClass}>Role type (optional)</label>
              <ProductInput name="role_type" placeholder="marketer" className="mt-1.5" />
            </div>
            <div>
              <label className={labelClass}>Department (optional)</label>
              <ProductInput name="department" className="mt-1.5" />
            </div>
            <ProductButton type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create invite"}
            </ProductButton>
            {message ? <p className="text-sm text-mkt-muted">{message}</p> : null}
            {inviteUrl ? <p className="break-all text-xs text-mkt-muted">Fallback link: {inviteUrl}</p> : null}
          </form>
        </ProductCard>

        <div className="space-y-6">
          <ProductCard>
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Members</h2>
            <div className="mt-4 space-y-3">
              {members.map((member) => (
                <div key={member.id} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 space-y-2">
                  <p className="text-sm font-semibold text-mkt-ink">
                    {member.profile?.full_name || member.profile?.email || member.user_id}
                  </p>
                  <p className="text-sm text-mkt-muted">{member.profile?.email || "No profile email"}</p>
                  <ProductSelect
                    value={member.role_id ?? ""}
                    onChange={(e) => void changeMemberRole(member.id, e.target.value)}
                  >
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.name}
                      </option>
                    ))}
                  </ProductSelect>
                </div>
              ))}
            </div>
          </ProductCard>
          <ProductCard>
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Pending invites</h2>
            <div className="mt-4 space-y-3">
              {invites
                .filter((invite) => !invite.accepted_at && !invite.revoked_at)
                .map((invite) => (
                  <div key={invite.id} className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4">
                    <p className="text-sm font-semibold text-mkt-ink">{invite.email}</p>
                    <p className="text-sm text-mkt-muted">
                      {(invite.org_roles?.name ?? invite.role)} · expires {new Date(invite.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
            </div>
          </ProductCard>
        </div>
      </div>
    </div>
  );
}
