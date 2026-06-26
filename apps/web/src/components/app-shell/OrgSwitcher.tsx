/**
 * @file apps/web/src/components/app-shell/OrgSwitcher.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React, BFF apiFetch
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { formatRoleLabel } from "@/lib/user-facing-copy";

type OrgEntry = {
  org_id: string;
  role_name?: string;
  role_key?: string;
  org?: { id: string; name: string };
};

/**
 * Handles org switcher behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function OrgSwitcher() {
  const router = useRouter();
  const [orgs, setOrgs] = useState<OrgEntry[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      const res = await apiFetch("/v1/orgs");
      if (res.ok) {
        const body = (await res.json()) as { organizations?: OrgEntry[]; active_org_id?: string | null };
        const list = body.organizations ?? [];
        setOrgs(list);
        setActiveId(body.active_org_id ?? list[0]?.org_id ?? null);
      }
      setLoading(false);
    })();
  }, []);

  async function switchOrg(orgId: string) {
    const res = await fetch("/api/orgs/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ org_id: orgId }),
    });
    if (res.ok) {
      setActiveId(orgId);
      router.refresh();
    }
  }

  const active = orgs.find((o) => o.org_id === activeId) ?? orgs[0];

  return (
    <div className="flex items-center gap-2">
      <select
        value={active?.org_id ?? ""}
        onChange={(e) => void switchOrg(e.target.value)}
        disabled={loading || orgs.length === 0}
        className="max-w-[200px] truncate rounded-xl border border-mkt-border bg-mkt-surface-elevated px-3 py-2 text-xs text-mkt-ink"
        aria-label="Switch organization"
      >
        {orgs.length === 0 ? <option value="">No organization</option> : null}
        {orgs.map((org) => (
          <option key={org.org_id} value={org.org_id}>
            {org.org?.name ?? "Workspace"} ({formatRoleLabel(org.role_name ?? org.role_key)})
          </option>
        ))}
      </select>
      <Link
        href="/onboarding?mode=create"
        className="whitespace-nowrap rounded-full border border-mkt-border px-3 py-2 text-xs font-medium text-mkt-muted transition-colors hover:border-mkt-ink/20 hover:text-mkt-ink"
      >
        Create org
      </Link>
    </div>
  );
}
