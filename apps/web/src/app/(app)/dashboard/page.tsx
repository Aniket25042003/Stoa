import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { CompaniesLoadError } from "../companies-load-error";
import { DashboardWorkspace } from "./dashboard-workspace";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  let companies: { id: string; name: string; description?: string | null; industry?: string | null; onboarding_completed_at?: string | null }[] = [];
  let companiesRequestFailed = false;
  try {
    const res = await apiFetch("/v1/companies", { accessToken: session.access_token });
    if (res.ok) {
      const body = await res.json();
      companies = body.companies ?? [];
    } else {
      companiesRequestFailed = true;
    }
  } catch {
    companiesRequestFailed = true;
  }

  if (companiesRequestFailed) return <CompaniesLoadError retryHref="/dashboard" />;

  if (companies.length === 0) redirect("/onboarding");

  return <DashboardWorkspace accessToken={session.access_token} companies={companies} email={session.user.email ?? "your account"} />;
}
