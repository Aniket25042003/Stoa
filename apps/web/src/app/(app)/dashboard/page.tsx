import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { DashboardWorkspace } from "./dashboard-workspace";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect(getAuthEntryPath());

  let orgData: { org?: { id: string; name: string; industry?: string | null }; membership?: { role: string } } | null = null;
  let loadError = false;
  try {
    const res = await apiFetch("/v1/orgs/me", { accessToken: session.access_token });
    if (res.ok) {
      orgData = await res.json();
    } else if (res.status === 404) {
      redirect("/onboarding");
    } else {
      loadError = true;
    }
  } catch {
    loadError = true;
  }

  if (loadError) {
    return (
      <div className="rounded-3xl p-8 card-glass text-center">
        <p className="text-on-surface-variant">Could not load workspace. Check API connection and try again.</p>
      </div>
    );
  }

  return (
    <DashboardWorkspace
      email={session.user.email ?? "your account"}
      org={orgData?.org}
      role={orgData?.membership?.role ?? "viewer"}
    />
  );
}
