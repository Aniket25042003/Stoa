/**
 * @file apps/web/src/components/app-shell/AppTopBar.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { OrgSwitcher } from "@/components/app-shell/OrgSwitcher";
import { ProductButton } from "@/components/product";
import { signOutClient } from "@/lib/auth-client";
import { BrandLogo } from "@/components/product/BrandLogo";

/**
 * Handles app top bar behavior for this part of the Stoa application.
 *
 * @param email - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AppTopBar({ email }: { email: string }) {
  const router = useRouter();

  async function signOut() {
    await signOutClient(router);
  }

  return (
    <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between gap-4 border-b border-mkt-ink/[0.06] bg-mkt-surface/85 px-4 backdrop-blur-xl md:px-6">
      <Link href="/dashboard" className="inline-flex min-w-0 items-center lg:hidden">
        <BrandLogo variant="icon" size="sm" />
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
