"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, LogOut, User } from "lucide-react";
import { ProductButton } from "@/components/product";
import { signOutClient } from "@/lib/auth-client";
import { cn } from "@/lib/cn";
import { resolveDisplayName } from "@/lib/user-facing-copy";

type AppUserMenuProps = {
  email: string;
  displayName?: string | null;
};

export function AppUserMenu({ email, displayName }: AppUserMenuProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const name = resolveDisplayName(displayName, email);
  const initial = name.trim().charAt(0).toUpperCase() || "U";

  async function signOut() {
    await signOutClient(router);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center gap-2 rounded-sm border border-mkt-ink/[0.08] bg-mkt-surface-elevated px-2 py-1.5 text-sm transition-colors hover:bg-mkt-ink/[0.03]",
          open && "border-mkt-accent/20",
        )}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-mkt-accent text-xs font-semibold text-mkt-dark-ink">
          {initial}
        </span>
        <ChevronDown className="hidden h-3.5 w-3.5 text-mkt-muted sm:block" />
      </button>

      {open ? (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-2 w-56 rounded-sm border border-mkt-ink/[0.08] bg-mkt-surface-elevated p-2 shadow-lg"
        >
          <div className="flex items-start gap-2 border-b border-mkt-ink/[0.06] px-2 pb-2">
            <User className="mt-0.5 h-4 w-4 shrink-0 text-mkt-muted" />
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-mkt-ink">{name}</p>
              <p className="truncate text-[11px] text-mkt-subtle">{email}</p>
            </div>
          </div>
          <ProductButton
            variant="ghost"
            className="mt-2 w-full justify-start !px-2"
            onClick={() => void signOut()}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </ProductButton>
        </div>
      ) : null}
    </div>
  );
}
