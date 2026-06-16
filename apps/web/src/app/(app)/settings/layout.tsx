import { SettingsSubnav } from "./settings-subnav";

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <SettingsSubnav />
      {children}
    </div>
  );
}
