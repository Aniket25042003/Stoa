/**
 * @file apps/web/src/app/(app)/data/layout.tsx
 * @layer Frontend Product UI
 * @description Defines shared route layout structure, metadata, and navigation boundaries.
 * @dependencies React
 */
import { DataHubLayout } from "./data-hub-layout";

/**
 * Handles data layout behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function DataLayout({ children }: { children: React.ReactNode }) {
  return <DataHubLayout>{children}</DataHubLayout>;
}
