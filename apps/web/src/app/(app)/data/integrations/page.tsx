/**
 * @file apps/web/src/app/(app)/data/integrations/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies React
 */
"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { ConnectionsPanel } from "../connections-panel";
import { CsvImportPanel } from "../csv-import-panel";
import { useDataHub } from "../data-hub-context";

function DataIntegrationsContent() {
  const { refresh } = useDataHub();
  const searchParams = useSearchParams();

  const oauthReturn = useMemo(
    () => ({
      connected: searchParams.get("connected") ?? undefined,
      connectionId: searchParams.get("connection_id") ?? undefined,
      error: searchParams.get("error") ?? undefined,
      provider: searchParams.get("provider") ?? undefined,
      configureScope: searchParams.get("configure_scope") === "1",
    }),
    [searchParams]
  );

  return (
    <div className="space-y-8">
      <ConnectionsPanel onConnected={() => void refresh()} oauthReturn={oauthReturn} />
      <div className="border-t border-mkt-ink/[0.06] pt-8">
        <CsvImportPanel onImported={() => void refresh()} />
      </div>
    </div>
  );
}

export default function DataIntegrationsPage() {
  return (
    <Suspense fallback={<div className="text-sm text-mkt-muted">Loading integrations…</div>}>
      <DataIntegrationsContent />
    </Suspense>
  );
}
