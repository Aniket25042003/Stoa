/**
 * @file apps/web/src/app/(app)/agent/page.tsx
 */
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { AgentWorkspace } from "./agent-workspace";

export default async function AgentPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return <AgentWorkspace />;
}
