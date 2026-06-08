import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { MarketingChat } from "./marketing-chat";

export default async function MarketingChatPage({
  params,
}: {
  params: Promise<{ companyId: string; chatId: string }>;
}) {
  const { companyId, chatId } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  return (
    <div className="space-y-6">
      <div className="rounded-[2rem] bg-slate-deep p-6 text-white shadow-card md:p-8">
        <Link
          href={`/marketing/${companyId}`}
          className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-inverse-primary hover:text-white"
        >
          ← Workspace
        </Link>
        <h1 className="mt-4 font-display text-3xl font-extrabold tracking-[-0.04em]">Marketing chat</h1>
        <p className="mt-2 font-mono text-xs text-white/60">{chatId}</p>
      </div>
      <MarketingChat chatId={chatId} companyId={companyId} />
    </div>
  );
}
