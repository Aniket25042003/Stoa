"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

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
        : "Invite created. Supabase will email the teammate when SMTP is configured.",
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
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Team</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">Manage organization access</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Invite teammates into the active organization and assign system or custom roles.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <form onSubmit={(event) => void invite(event)} className="rounded-3xl p-6 card-glass space-y-4">
          <h2 className="font-display text-xl font-bold">Invite teammate</h2>
          <div>
            <label className="text-sm font-medium">Work email</label>
            <input name="email" type="email" required className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="teammate@company.com" />
          </div>
          <div>
            <label className="text-sm font-medium">Role</label>
            <select name="role_id" defaultValue={defaultRoleId} className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm">
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name} {role.is_system ? "" : "(custom)"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Profile hint: job title (optional)</label>
            <input name="job_title" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
          </div>
          <div>
            <label className="text-sm font-medium">Profile hint: role type (optional)</label>
            <input name="role_type" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="marketer" />
          </div>
          <div>
            <label className="text-sm font-medium">Profile hint: department (optional)</label>
            <input name="department" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" />
          </div>
          <button disabled={loading} className="btn-primary px-5 py-3 text-sm disabled:opacity-50">
            {loading ? "Creating..." : "Create invite"}
          </button>
          {message ? <p className="text-sm text-on-surface-variant">{message}</p> : null}
          {inviteUrl ? <p className="break-all text-xs text-on-surface-variant">Fallback link: {inviteUrl}</p> : null}
        </form>

        <div className="space-y-6">
          <div className="rounded-3xl p-6 card-glass">
            <h2 className="font-display text-xl font-bold">Members</h2>
            <div className="mt-4 space-y-3">
              {members.map((member) => (
                <div key={member.id} className="rounded-xl bg-surface-container-low p-4 text-sm space-y-2">
                  <p className="font-semibold text-on-surface">{member.profile?.full_name || member.profile?.email || member.user_id}</p>
                  <p className="text-on-surface-variant">{member.profile?.email || "No profile email"}</p>
                  <select
                    value={member.role_id ?? ""}
                    onChange={(e) => void changeMemberRole(member.id, e.target.value)}
                    className="w-full rounded-lg border border-outline-variant/60 bg-surface px-3 py-2 text-sm"
                  >
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-3xl p-6 card-glass">
            <h2 className="font-display text-xl font-bold">Pending invites</h2>
            <div className="mt-4 space-y-3">
              {invites.filter((invite) => !invite.accepted_at && !invite.revoked_at).map((invite) => (
                <div key={invite.id} className="rounded-xl bg-surface-container-low p-4 text-sm">
                  <p className="font-semibold text-on-surface">{invite.email}</p>
                  <p className="text-on-surface-variant">
                    {(invite.org_roles?.name ?? invite.role)} · expires {new Date(invite.expires_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
