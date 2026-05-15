import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { MarketingWorkspace } from "./marketing-workspace";

type Company = { id: string; name: string; description?: string | null };

export default async function MarketingPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  let companies: Company[] = [];
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

  return <MarketingWorkspace accessToken={session.access_token} companies={companies} />;
}
