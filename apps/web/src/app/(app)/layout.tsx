import { AppHeader } from "@/components/app-shell/AppHeader";
import { createClient } from "@/lib/supabase/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return (
    <div className="min-h-screen bg-cream text-ink">
      {session?.user?.email ? <AppHeader email={session.user.email} /> : null}
      <div className="mx-auto max-w-5xl px-4 py-8 md:px-6">{children}</div>
    </div>
  );
}
