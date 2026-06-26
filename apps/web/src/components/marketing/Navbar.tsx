"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { BrandLogo } from "@/components/product/BrandLogo";
import { SolidButton } from "@/components/marketing/v3/Buttons";
import { isLoginEnabled } from "@/lib/auth-entry";
import { useMarketingAuthCta } from "@/lib/use-marketing-auth-cta";
import { BRAND_NAME } from "@/lib/brand";

const anchorNav = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#integrations", label: "Integrations" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export function Navbar() {
  const pathname = usePathname();
  const marketingCta = useMarketingAuthCta();
  const loginEnabled = isLoginEnabled();
  const isLanding = pathname === "/";
  const navLinks = isLanding ? anchorNav : [{ href: "/", label: "Home" }, ...anchorNav];

  return (
    <header className="sticky top-0 z-50 px-4 pt-4 md:px-8">
      <div className="mkt-nav-pill mx-auto max-w-5xl overflow-hidden">
        <div className="flex items-center justify-between gap-2 px-3 py-2.5 sm:px-4 md:px-6">
          <Link href="/" className="inline-flex min-w-0 shrink-0 items-center" aria-label={`${BRAND_NAME} home`}>
            <BrandLogo variant="logo" size="sm" priority />
          </Link>

          <nav className="hidden items-center gap-5 lg:flex" aria-label="Primary">
            {navLinks.map((item) => (
              <Link key={item.href} href={item.href} className="mkt-nav-link text-sm text-mkt-muted hover:text-mkt-ink">
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-2">
            {!loginEnabled && (
              <span className="hidden rounded-full border border-mkt-border bg-white/60 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-mkt-muted lg:inline-flex">
                Early access
              </span>
            )}
            {loginEnabled && !marketingCta.authenticated && !marketingCta.loading && (
              <Link href={marketingCta.href} className="hidden text-sm text-mkt-muted hover:text-mkt-ink sm:inline">
                Log in
              </Link>
            )}
            <SolidButton href={marketingCta.href} className="px-3 py-2 text-sm sm:px-4" variant="dark">
              <span className="hidden sm:inline">
                {marketingCta.loading ? "Loading..." : marketingCta.navLabel}
              </span>
              <span className="sm:hidden">{marketingCta.authenticated ? "App" : "Join"}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </SolidButton>
          </div>
        </div>

        {isLanding && (
          <nav
            className="mkt-scrollbar-none flex gap-4 overflow-x-auto border-t border-black/[0.06] px-3 py-2.5 sm:px-4 lg:hidden"
            aria-label="Primary mobile"
          >
            {anchorNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="mkt-nav-link shrink-0 text-xs font-medium text-mkt-muted hover:text-mkt-ink"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        )}
      </div>
    </header>
  );
}
