"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";

type OrgEntry = {
  org_id: string;
  role_name?: string;
  role_key?: string;
  org?: { id: string; name: string };
};

export function OrgSwitcher() {
  const router = useRouter();
  const [orgs, setOrgs] = useState<OrgEntry[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      const res = await apiFetch("/v1/orgs");
      if (res.ok) {
        const body = await res.json();
        const list = (body.organizations ?? []) as OrgEntry[];
        setOrgs(list);
        const cookieMatch = document.cookie.match(new RegExp(`(?:^|; )${ACTIVE_ORG_COOKIE}=([^;]*)`));
        const cookieOrg = cookieMatch ? decodeURIComponent(cookieMatch[1]) : null;
        setActiveId(cookieOrg ?? list[0]?.org_id ?? null);
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
        className="max-w-[200px] truncate rounded-full border border-outline-variant/60 bg-surface-container-low/80 px-3 py-2 text-sm"
        aria-label="Switch organization"
      >
        {orgs.length === 0 ? <option value="">No organization</option> : null}
        {orgs.map((org) => (
          <option key={org.org_id} value={org.org_id}>
            {org.org?.name ?? org.org_id} ({org.role_name ?? org.role_key})
          </option>
        ))}
      </select>
      <a href="/onboarding?mode=create" className="btn-secondary px-3 py-2 text-xs whitespace-nowrap">
        Create org
      </a>
    </div>
  );
}
