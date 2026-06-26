/**
 * @file apps/web/src/app/(app)/alignment/page.tsx
 */
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { AlignmentWorkspace } from "./alignment-workspace";

export default async function AlignmentPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return <AlignmentWorkspace />;
}
