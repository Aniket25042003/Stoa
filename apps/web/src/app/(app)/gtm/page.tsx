import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { CompaniesLoadError } from "../companies-load-error";
import { GtmWorkspace } from "./gtm-workspace";

export default async function GtmPage({ searchParams }: { searchParams: Promise<{ company_id?: string }> }) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  const sp = await searchParams;
  const initialCompanyId = typeof sp.company_id === "string" && sp.company_id.trim() ? sp.company_id.trim() : undefined;

  let companies: { id: string; name: string; description?: string | null }[] = [];
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

  if (companiesRequestFailed) return <CompaniesLoadError retryHref="/gtm" />;

  if (companies.length === 0) redirect("/onboarding");

  return <GtmWorkspace accessToken={session.access_token} companies={companies} initialCompanyId={initialCompanyId} />;
}
