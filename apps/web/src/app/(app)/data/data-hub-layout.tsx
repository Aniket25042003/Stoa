"use client";

import { SectionSubnav } from "@/components/app-shell/SectionSubnav";
import { useAppPermissions } from "@/components/app-shell/useAppPermissions";
import { ProductPageHeader } from "@/components/product";
import { DATA_SUBNAV } from "@/lib/app-navigation";
import { DataHubProvider, useDataHub } from "./data-hub-context";
import { DataHubToast } from "./data-hub-toast";

function DataHubHeader() {
  const { completeness } = useDataHub();
  return (
    <ProductPageHeader
      eyebrow="Workspace"
      title="Data hub"
      lead="Collect company profile, customer documents, competitors, and brand voice once. Intelligence features consume this data."
      actions={
        completeness ? (
          <div className="text-right">
            <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-muted">Completeness</p>
            <p className="font-syne text-2xl font-extrabold text-mkt-accent">{completeness.percent}%</p>
          </div>
        ) : null
      }
    />
  );
}

function DataSubnav() {
  const { permissions, loaded } = useAppPermissions();
  return (
    <SectionSubnav
      items={DATA_SUBNAV}
      permissions={permissions}
      permissionsLoaded={loaded}
      ariaLabel="Data hub sections"
    />
  );
}

function DataHubToastBanner() {
  const { toast } = useDataHub();
  return <DataHubToast message={toast?.message ?? null} variant={toast?.variant} />;
}

export function DataHubLayout({ children }: { children: React.ReactNode }) {
  return (
    <DataHubProvider>
      <DataHubHeader />
      <DataSubnav />
      <DataHubToastBanner />
      {children}
    </DataHubProvider>
  );
}
