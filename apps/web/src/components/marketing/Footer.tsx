"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { BrandLogo } from "@/components/product/BrandLogo";
import { SolidButton } from "@/components/marketing/v3/Buttons";
import { getMarketingCta } from "@/lib/auth-entry";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

const marketingCta = getMarketingCta();

const exploreLinks = [
  { href: "/#features", label: "Features" },
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#integrations", label: "Integrations" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/#faq", label: "FAQ" },
];

export function Footer() {
  return (
    <footer className="relative mt-8 overflow-hidden rounded-t-[2rem] bg-mkt-dark-band text-mkt-dark-ink">
      <div className="relative z-10 mx-auto max-w-7xl px-4 py-14 md:px-8 md:py-16">
        <div className="grid gap-12 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <BrandLogo variant="icon" size="sm" tone="on-dark" />
            <p className="mt-5 max-w-sm text-xl font-semibold leading-tight tracking-tight text-mkt-dark-ink">
              {BRAND_TAGLINE}
            </p>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-mkt-dark-ink/65">{BRAND_SUBHEAD}</p>
          </div>

          <div>
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-mkt-dark-ink/50">Explore</p>
            <ul className="mt-4 space-y-2.5">
              {exploreLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-mkt-dark-ink/70 transition-colors hover:text-mkt-dark-ink"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col justify-between gap-6">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-mkt-dark-ink/50">Get started</p>
              <p className="mt-3 text-sm leading-relaxed text-mkt-dark-ink/65">{marketingCta.footerDescription}</p>
            </div>
            <SolidButton href={marketingCta.href} variant="light" className="w-fit">
              {marketingCta.buttonLabel}
              <ArrowRight className="h-3.5 w-3.5" />
            </SolidButton>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-mkt-dark-ink/10 pt-8 md:flex-row">
          <p className="text-xs text-mkt-dark-ink/45">
            © {new Date().getFullYear()} {BRAND_NAME}. All rights reserved.
          </p>
          <p className="text-[10px] uppercase tracking-[0.15em] text-mkt-dark-ink/35">Connect. Retrieve. Ship.</p>
        </div>
      </div>
    </footer>
  );
}
