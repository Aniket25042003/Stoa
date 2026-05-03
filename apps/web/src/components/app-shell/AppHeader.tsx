"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function AppHeader({ email }: { email: string }) {
  const router = useRouter();

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-40 border-b border-mist bg-cream/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-4 py-4 md:px-6">
        <Link href="/dashboard" className="text-lg font-semibold tracking-tight text-ink">
          GTM Agent
        </Link>
        <div className="flex flex-wrap items-center gap-3 md:gap-4">
          <span className="hidden max-w-[200px] truncate text-sm text-ink/70 sm:inline md:max-w-xs" title={email}>
            {email}
          </span>
          <Link
            href="/runs/new"
            className="rounded-lg bg-slate px-3 py-2 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90"
          >
            New run
          </Link>
          <button
            type="button"
            onClick={() => void signOut()}
            className="rounded-lg border border-mist px-3 py-2 text-sm font-semibold text-ink transition-colors hover:border-slate/50"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
