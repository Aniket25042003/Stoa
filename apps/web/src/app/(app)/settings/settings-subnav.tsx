/**
 * @file apps/web/src/app/(app)/settings/settings-subnav.tsx
 * @layer Frontend Product UI
 * @description Implements settings subnav behavior for the frontend product ui.
 * @dependencies React
 */
"use client";

import { SectionSubnav } from "@/components/app-shell/SectionSubnav";
import { useAppPermissions } from "@/components/app-shell/useAppPermissions";
import { SETTINGS_SUBNAV } from "@/lib/app-navigation";

/**
 * Handles settings subnav behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function SettingsSubnav() {
  const { permissions, loaded } = useAppPermissions();
  return (
    <SectionSubnav
      items={SETTINGS_SUBNAV}
      permissions={permissions}
      permissionsLoaded={loaded}
      ariaLabel="Settings sections"
    />
  );
}
