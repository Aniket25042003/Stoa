/**
 * @file apps/web/src/app/(app)/data/data-hub-layout.tsx
 * @layer Frontend Product UI
 * @description Implements data hub layout behavior for the frontend product ui.
 * @dependencies React
 */
"use client";

import { SectionSubnav } from "@/components/app-shell/SectionSubnav";
import { useAppPermissions } from "@/components/app-shell/useAppPermissions";
import { ProductPageHeader } from "@/components/product";
import { DATA_SUBNAV } from "@/lib/app-navigation";
import { DataHubProvider, useDataHub } from "./data-hub-context";
import { DataHubToast } from "./data-hub-toast";

/**
 * Handles data hub header behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
            <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Completeness</p>
            <p className="text-2xl font-semibold text-mkt-ink">{completeness.percent}%</p>
          </div>
        ) : null
      }
    />
  );
}

/**
 * Handles data subnav behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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

/**
 * Handles data hub toast banner behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function DataHubToastBanner() {
  const { toast } = useDataHub();
  return <DataHubToast message={toast?.message ?? null} variant={toast?.variant} />;
}

/**
 * Handles data hub layout behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
