/**
 * @file apps/web/src/app/(app)/data/integrations/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies React
 */
"use client";

import { ConnectionsPanel } from "../connections-panel";
import { CsvImportPanel } from "../csv-import-panel";
import { useDataHub } from "../data-hub-context";

/**
 * Handles data integrations page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function DataIntegrationsPage() {
  const { refresh } = useDataHub();
  return (
    <div className="space-y-8">
      <ConnectionsPanel onConnected={() => void refresh()} />
      <div className="border-t border-mkt-ink/[0.06] pt-8">
        <CsvImportPanel onImported={() => void refresh()} />
      </div>
    </div>
  );
}
