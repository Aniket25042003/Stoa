/**
 * @file apps/web/src/components/marketing/Navbar.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { BrandLogo } from "@/components/product/BrandLogo";
import { getAuthEntryPath, getMarketingCta, isLoginEnabled } from "@/lib/auth-entry";
import { BRAND_NAME } from "@/lib/brand";
import { cn } from "@/lib/cn";
import { isMarketingV2Page } from "@/lib/marketing-v2";

const authEntry = getAuthEntryPath();
const marketingCta = getMarketingCta();
const loginEnabled = isLoginEnabled();

const nav = [
  { href: "/see-it-in-action", label: "See it in action" },
  { href: "/pricing", label: "Pricing" },
  { href: "/faq", label: "FAQ" },
];

const fullNav = [
  { href: "/see-it-in-action", label: "See it in action", index: "01" },
  { href: "/pricing", label: "Pricing", index: "02" },
  { href: "/faq", label: "FAQ", index: "03" },
];

/**
 * Handles navbar behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function Navbar() {
  const pathname = usePathname();
  const isV2 = isMarketingV2Page(pathname);

  if (isV2) {
    return (
      <header className="sticky top-0 z-50 w-full border-b border-mkt-ink/[0.06] bg-mkt-surface/75 backdrop-blur-xl">
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-mkt-accent/25 to-transparent" />

        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3.5 md:px-8">
          <Link
            href="/"
            className="group inline-flex min-w-0 items-center"
            aria-label={`${BRAND_NAME} home`}
          >
            <BrandLogo variant="logo" size="sm" priority />
          </Link>

          <nav className="hidden items-center gap-8 md:flex" aria-label="Primary">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "font-dm-sans text-[10px] font-bold uppercase tracking-[0.18em] transition-colors",
                  pathname === item.href
                    ? "text-mkt-accent"
                    : "text-mkt-muted hover:text-mkt-ink"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-3">
            {!loginEnabled && (
              <span className="hidden rounded-full border border-mkt-accent-warm/25 bg-mkt-accent-warm/[0.07] px-2.5 py-1 font-dm-sans text-[8px] font-bold uppercase tracking-[0.18em] text-mkt-accent-warm lg:inline-flex">
                Early access
              </span>
            )}
            <Link
              href={marketingCta.href}
              className="group inline-flex items-center gap-1.5 rounded-sm bg-mkt-accent px-4 py-2.5 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_6px_20px_rgba(79,70,229,0.18)] transition-all hover:bg-[#4338CA] active:scale-[0.97]"
            >
              {marketingCta.navLabel}
              <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>

        <nav
          className="flex items-center justify-center gap-6 border-t border-mkt-ink/[0.04] py-2.5 md:hidden"
          aria-label="Primary mobile"
        >
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.16em] text-mkt-muted transition-colors hover:text-mkt-accent"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-outline-variant bg-surface/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-6">
        <Link
          href="/"
          className="group inline-flex min-w-0 items-center"
          aria-label={`${BRAND_NAME} home`}
        >
          <BrandLogo variant="logo" size="sm" priority />
        </Link>

        <nav className="hidden items-center justify-center gap-8 md:flex" aria-label="Primary">
          {fullNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group relative shrink-0 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-on-surface-variant transition-colors hover:text-primary"
            >
              <span className="text-secondary/80 mr-1 transition-colors group-hover:text-primary">[{item.index}]</span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center justify-end gap-3">
          <ThemeToggle />
          <Link href={authEntry} className="btn-nav-purple px-3 py-1.5 text-xs uppercase tracking-wider font-mono">
            Sign in
          </Link>
          <Link href={authEntry} className="btn-primary hidden px-4 py-1.5 text-xs uppercase tracking-wider font-mono sm:inline-flex">
            Start free
          </Link>
        </div>
      </div>

      <nav
        className="flex items-center justify-center gap-6 border-t border-outline-variant/30 py-2.5 md:hidden"
        aria-label="Primary mobile"
      >
        {fullNav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="shrink-0 font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-on-surface-variant transition-colors hover:text-primary"
          >
            <span className="text-secondary/80 mr-1">[{item.index}]</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
