import { AppHeader } from "@/components/app-shell/AppHeader";
import { createClient } from "@/lib/supabase/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <div className="pointer-events-none fixed inset-0 -z-10 grid-bg dark:starfield" />
      {session?.user?.email && session.access_token ? <AppHeader email={session.user.email} accessToken={session.access_token} /> : null}
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10">{children}</div>
    </div>
  );
}
