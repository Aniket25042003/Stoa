"use client";

import { SectionSubnav } from "@/components/app-shell/SectionSubnav";
import { useAppPermissions } from "@/components/app-shell/useAppPermissions";
import { SETTINGS_SUBNAV } from "@/lib/app-navigation";

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
