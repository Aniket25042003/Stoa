import { Suspense } from "react";
import { AssetsWorkspace } from "./assets-workspace";

export default function AssetsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-mkt-muted">Loading assets…</p>}>
      <AssetsWorkspace />
    </Suspense>
  );
}
