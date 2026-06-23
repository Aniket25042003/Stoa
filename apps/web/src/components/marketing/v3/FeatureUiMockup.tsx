import { MiniCard } from "@/components/marketing/v3/Cards";
import { cn } from "@/lib/cn";

function MockShell({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <MiniCard className={cn("mt-4 overflow-hidden p-3", className)}>
      <div className="rounded-xl border border-mkt-border/60 bg-white p-3 shadow-sm">{children}</div>
    </MiniCard>
  );
}

function IcpMockup() {
  return (
    <MockShell>
      <p className="text-[9px] font-semibold uppercase tracking-wider text-mkt-subtle">ICP segments</p>
      <div className="mt-2 space-y-1.5">
        {[
          { label: "Technical founders", pct: "68%", color: "bg-violet-400" },
          { label: "Mid-market PMM", pct: "42%", color: "bg-sky-400" },
          { label: "Enterprise GTM", pct: "24%", color: "bg-amber-400" },
        ].map((row) => (
          <div key={row.label} className="flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-mkt-surface">
              <div className={cn("h-full rounded-full", row.color)} style={{ width: row.pct }} />
            </div>
            <span className="w-16 truncate text-[10px] text-mkt-muted">{row.label}</span>
          </div>
        ))}
      </div>
    </MockShell>
  );
}

function ContentMockup() {
  return (
    <MockShell>
      <div className="flex gap-2">
        {["Brief", "Blog", "Email"].map((tag, i) => (
          <div
            key={tag}
            className={cn(
              "flex-1 rounded-lg border border-mkt-border/50 p-2",
              i === 0 ? "bg-amber-50" : "bg-white"
            )}
          >
            <p className="text-[9px] font-medium text-mkt-subtle">{tag}</p>
            <div className="mt-1.5 space-y-1">
              <div className="h-1 w-full rounded bg-mkt-border/40" />
              <div className="h-1 w-4/5 rounded bg-mkt-border/30" />
            </div>
          </div>
        ))}
      </div>
    </MockShell>
  );
}

function CompetitiveMockup() {
  return (
    <MockShell>
      <p className="text-[9px] font-semibold uppercase tracking-wider text-mkt-subtle">Competitor radar</p>
      <div className="mt-2 grid grid-cols-3 gap-1.5 text-center">
        {[
          { name: "You", val: "47%", highlight: true },
          { name: "Rival A", val: "62%" },
          { name: "Rival B", val: "38%" },
        ].map((c) => (
          <div
            key={c.name}
            className={cn(
              "rounded-lg border px-1 py-2",
              c.highlight ? "border-sky-200 bg-sky-50" : "border-mkt-border/40 bg-mkt-surface"
            )}
          >
            <p className="text-[9px] font-medium text-mkt-muted">{c.name}</p>
            <p className="text-sm font-semibold text-mkt-ink">{c.val}</p>
          </div>
        ))}
      </div>
    </MockShell>
  );
}

function CampaignAnalysisMockup() {
  return (
    <MockShell>
      <div className="flex items-end justify-between gap-1 h-14">
        {[40, 65, 45, 80, 55, 72].map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-t bg-gradient-to-t from-rose-300 to-rose-200"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
      <div className="mt-2 flex justify-between text-[9px] text-mkt-subtle">
        <span>Channel A +24%</span>
        <span className="font-medium text-mkt-ink">Best: LinkedIn</span>
      </div>
    </MockShell>
  );
}

function AlignmentMockup() {
  return (
    <MockShell>
      <div className="grid grid-cols-2 gap-2 text-[10px]">
        <div className="rounded-lg bg-violet-50 p-2">
          <p className="font-medium text-violet-700">Marketing</p>
          <p className="mt-1 text-mkt-muted">ICP v3.2</p>
        </div>
        <div className="rounded-lg bg-orange-50 p-2">
          <p className="font-medium text-orange-700">Sales</p>
          <p className="mt-1 text-mkt-muted">Same proof</p>
        </div>
      </div>
      <div className="mt-2 flex items-center justify-center">
        <span className="rounded-full border border-mkt-border bg-white px-2 py-0.5 text-[9px] text-mkt-muted">
          Shared intelligence
        </span>
      </div>
    </MockShell>
  );
}

function LaunchMockup() {
  return (
    <MockShell>
      <div className="space-y-1.5">
        {[
          { step: "Strategy brief", done: true },
          { step: "Creative assets", done: true },
          { step: "Launch checklist", done: false },
        ].map((item) => (
          <div key={item.step} className="flex items-center gap-2">
            <span
              className={cn(
                "flex h-4 w-4 items-center justify-center rounded-full text-[8px]",
                item.done ? "bg-violet-400 text-white" : "border border-mkt-border"
              )}
            >
              {item.done ? "✓" : ""}
            </span>
            <span className="text-[10px] text-mkt-muted">{item.step}</span>
          </div>
        ))}
      </div>
    </MockShell>
  );
}

const MOCKUPS: Record<string, () => React.ReactNode> = {
  "icp-research": IcpMockup,
  "content-bottleneck": ContentMockup,
  "competitive-intel": CompetitiveMockup,
  "campaign-analysis": CampaignAnalysisMockup,
  "sales-marketing-align": AlignmentMockup,
  "launch-orchestration": LaunchMockup,
};

export function FeatureUiMockup({ featureId }: { featureId: string }) {
  const Mock = MOCKUPS[featureId];
  if (!Mock) return null;
  return <Mock />;
}
