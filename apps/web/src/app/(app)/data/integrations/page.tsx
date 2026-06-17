"use client";

import { ConnectionsPanel } from "../connections-panel";
import { CsvImportPanel } from "../csv-import-panel";
import { useDataHub } from "../data-hub-context";

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
