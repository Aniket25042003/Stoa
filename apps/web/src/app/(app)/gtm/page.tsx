import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { GtmWorkspace } from "./gtm-workspace";

export default async function GtmPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  let companies: { id: string; name: string; description?: string | null }[] = [];
  try {
    const res = await apiFetch("/v1/companies", { accessToken: session.access_token });
    if (res.ok) {
      const body = await res.json();
      companies = body.companies ?? [];
    }
  } catch {
    companies = [];
  }

  if (companies.length === 0) redirect("/onboarding");

  return <GtmWorkspace accessToken={session.access_token} companies={companies} />;
}
