import { Suspense } from "react";
import { AgentWorkspace } from "./agent-workspace";

export default function AgentPage() {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-mkt-muted">Loading agent…</p>}>
      <AgentWorkspace />
    </Suspense>
  );
}
