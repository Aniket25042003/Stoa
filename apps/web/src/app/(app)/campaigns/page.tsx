/**
 * @file apps/web/src/app/(app)/campaigns/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Supabase, Next.js, React
 */
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { CampaignsWorkspace } from "./campaigns-workspace";

export default async function CampaignsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return <CampaignsWorkspace />;
}
