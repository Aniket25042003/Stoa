"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeToggle";
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
    <header className="sticky top-0 z-40 border-b border-outline-variant/70 bg-surface-container-low/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 md:px-6">
        <Link href="/dashboard" className="inline-flex items-center gap-3">
          <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-violet-pulse shadow-glow" />
          <span className="font-display text-lg font-extrabold tracking-[-0.03em] text-on-surface">GTM Agent</span>
        </Link>
        <div className="flex flex-wrap items-center gap-3 md:gap-4">
          <span className="hidden max-w-[200px] truncate rounded-full border border-outline-variant/60 bg-surface-container-low/80 px-3 py-2 text-sm text-on-surface-variant sm:inline md:max-w-xs" title={email}>
            {email}
          </span>
          <ThemeToggle />
          <Link href="/marketing" className="btn-secondary px-4 py-2 text-sm">
            Marketing
          </Link>
          <Link href="/runs/new" className="btn-primary px-4 py-2 text-sm">
            New run
          </Link>
          <button type="button" onClick={() => void signOut()} className="btn-secondary px-4 py-2 text-sm">
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
