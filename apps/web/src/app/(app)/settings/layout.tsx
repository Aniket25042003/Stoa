/**
 * @file apps/web/src/app/(app)/settings/layout.tsx
 * @layer Frontend Product UI
 * @description Defines shared route layout structure, metadata, and navigation boundaries.
 * @dependencies React
 */
import { SettingsSubnav } from "./settings-subnav";

/**
 * Handles settings layout behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <SettingsSubnav />
      {children}
    </div>
  );
}
