"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { OrgSwitcher } from "@/components/app-shell/OrgSwitcher";
import { ProductButton } from "@/components/product";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { BRAND_LOGO_LETTER, BRAND_NAME } from "@/lib/brand";

export function AppTopBar({ email }: { email: string }) {
  const router = useRouter();

  async function signOut() {
    await fetch("/api/auth/signout", { method: "POST" });
    router.push(getAuthEntryPath());
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-mkt-ink/[0.06] bg-mkt-surface/85 px-4 backdrop-blur-xl md:px-6">
      <Link href="/dashboard" className="inline-flex min-w-0 items-center gap-3 lg:hidden">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-mkt-accent/35 bg-mkt-accent/[0.08] font-mono text-sm font-black text-mkt-accent">
          {BRAND_LOGO_LETTER}
        </span>
        <span className="truncate font-syne text-sm font-extrabold uppercase tracking-[0.1em] text-mkt-ink">
          {BRAND_NAME}
        </span>
      </Link>

      <div className="hidden lg:block" />

      <div className="flex min-w-0 flex-1 items-center justify-end gap-3 md:gap-4">
        <OrgSwitcher />
        <span
          className="hidden max-w-[180px] truncate font-dm-sans text-xs text-mkt-muted md:inline"
          title={email}
        >
          {email}
        </span>
        <ProductButton variant="ghost" className="!px-2 !py-2" onClick={() => void signOut()} aria-label="Sign out">
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Sign out</span>
        </ProductButton>
      </div>
    </header>
  );
}
