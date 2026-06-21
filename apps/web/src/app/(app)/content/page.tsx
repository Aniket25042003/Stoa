/**
 * @file apps/web/src/app/(app)/content/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for the Content Studio.
 * @dependencies Supabase, Next.js, React
 */

import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { ContentWorkspace } from "./content-workspace";

export default async function ContentPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return <ContentWorkspace />;
}
