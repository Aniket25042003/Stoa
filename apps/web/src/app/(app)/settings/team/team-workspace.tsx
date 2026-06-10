"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Member = {
  id: string;
  user_id: string;
  role: string;
  profile?: { email?: string; full_name?: string };
};

type Invite = {
  id: string;
  email: string;
  role: string;
  expires_at: string;
  accepted_at?: string | null;
  revoked_at?: string | null;
};

export function TeamWorkspace() {
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    const [membersRes, invitesRes] = await Promise.all([
      apiFetch("/v1/team/members"),
      apiFetch("/v1/team/invites"),
    ]);
    if (membersRes.ok) setMembers((await membersRes.json()).members ?? []);
    if (invitesRes.ok) setInvites((await invitesRes.json()).invites ?? []);
  }

  useEffect(() => {
    void load();
  }, []);

  async function invite(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setInviteUrl(null);
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const res = await apiFetch("/v1/team/invites", {
      method: "POST",
      body: JSON.stringify({
        email: String(form.get("email") ?? "").trim(),
        role: String(form.get("role") ?? "viewer"),
      }),
    });
    const body = await res.json().catch(() => null);
    setLoading(false);
    if (!res.ok) {
      setMessage(body?.detail || "Could not send invite.");
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

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Team</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">Manage company access</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">Invite teammates into your single company workspace and control RBAC roles.</p>
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
            <select name="role" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" defaultValue="viewer">
              <option value="admin">Admin</option>
              <option value="analyst">Analyst</option>
              <option value="viewer">Viewer</option>
            </select>
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
                <div key={member.id} className="rounded-xl bg-surface-container-low p-4 text-sm">
                  <p className="font-semibold text-on-surface">{member.profile?.full_name || member.profile?.email || member.user_id}</p>
                  <p className="text-on-surface-variant">{member.profile?.email || "No profile email"} · {member.role}</p>
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
                  <p className="text-on-surface-variant">{invite.role} · expires {new Date(invite.expires_at).toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
