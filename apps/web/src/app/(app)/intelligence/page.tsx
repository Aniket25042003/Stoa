/**
 * @file apps/web/src/app/(app)/intelligence/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Supabase, Next.js, React
 */
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { IntelligenceWorkspace } from "./intelligence-workspace";

export default async function IntelligencePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return <IntelligenceWorkspace />;
}
