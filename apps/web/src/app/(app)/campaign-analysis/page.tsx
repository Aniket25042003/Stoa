/**
 * @file apps/web/src/app/(app)/campaign-analysis/page.tsx
 */
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { CampaignAnalysisWorkspace } from "./campaign-analysis-workspace";

export default async function CampaignAnalysisPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return <CampaignAnalysisWorkspace />;
}
