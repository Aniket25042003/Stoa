"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

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
        className="max-w-[200px] truncate rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-3 py-2 font-dm-sans text-xs text-mkt-ink"
        aria-label="Switch organization"
      >
        {orgs.length === 0 ? <option value="">No organization</option> : null}
        {orgs.map((org) => (
          <option key={org.org_id} value={org.org_id}>
            {org.org?.name ?? org.org_id} ({org.role_name ?? org.role_key})
          </option>
        ))}
      </select>
      <Link
        href="/onboarding?mode=create"
        className="whitespace-nowrap rounded-sm border border-mkt-ink/10 px-3 py-2 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-muted transition-colors hover:border-mkt-accent/30 hover:text-mkt-accent"
      >
        Create org
      </Link>
    </div>
  );
}
