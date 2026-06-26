"use client";

import type { DashboardSummary } from "@/components/dashboard/types";
import { cn } from "@/lib/cn";

type CrmPipelineMiniProps = {
  crmStats?: DashboardSummary["crm_stats"];
  className?: string;
};

export function CrmPipelineMini({ crmStats, className }: CrmPipelineMiniProps) {
  const accounts = crmStats?.total_accounts ?? 0;
  const deals = crmStats?.total_deals ?? 0;
  const won = crmStats?.won_deals ?? 0;
  const lost = crmStats?.lost_deals ?? 0;
  const decided = won + lost;

  if (accounts === 0 && deals === 0) return null;

  const winRate = decided > 0 ? Math.round((won / decided) * 100) : 0;

  return (
    <div className={cn("rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4", className)}>
      <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">CRM pipeline</p>
      <div className="mt-3 grid grid-cols-3 gap-3 text-center">
        <div>
          <p className="text-lg font-semibold tabular-nums text-mkt-ink">{accounts}</p>
          <p className="text-[10px] uppercase tracking-wider text-mkt-muted">Accounts</p>
        </div>
        <div>
          <p className="text-lg font-semibold tabular-nums text-mkt-ink">{deals}</p>
          <p className="text-[10px] uppercase tracking-wider text-mkt-muted">Deals</p>
        </div>
        <div>
          <p className="text-lg font-semibold tabular-nums text-mkt-ink">{decided > 0 ? `${winRate}%` : "—"}</p>
          <p className="text-[10px] uppercase tracking-wider text-mkt-muted">Win rate</p>
        </div>
      </div>
      {decided > 0 ? (
        <div className="mt-3 flex h-2 overflow-hidden rounded-sm">
          <div className="bg-emerald-600/80" style={{ width: `${(won / decided) * 100}%` }} title={`Won: ${won}`} />
          <div className="bg-mkt-ink/20" style={{ width: `${(lost / decided) * 100}%` }} title={`Lost: ${lost}`} />
        </div>
      ) : null}
    </div>
  );
}
