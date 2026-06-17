import Link from "next/link";
import type { ReactNode } from "react";
import { ProductShellFrame } from "@/components/product";
import { BRAND_LOGO_LETTER, BRAND_NAME } from "@/lib/brand";

export function AuthPageShell({
  children,
  lead,
}: {
  children: ReactNode;
  lead?: ReactNode;
}) {
  return (
    <ProductShellFrame>
      <div className="relative min-h-screen px-4 py-10 md:px-6">
        <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col gap-10 lg:flex-row lg:items-center lg:gap-16">
          <div className="flex-1 space-y-6 lg:max-w-lg">{lead}</div>
          <div className="flex flex-1 justify-center lg:justify-end">{children}</div>
        </div>
      </div>
    </ProductShellFrame>
  );
}

export function AuthBrandMark() {
  return (
    <Link href="/" className="inline-flex items-center gap-3">
      <span className="flex h-10 w-10 items-center justify-center rounded-sm border border-mkt-accent/35 bg-mkt-accent/[0.08] font-mono text-sm font-black text-mkt-accent shadow-[0_4px_16px_rgba(79,70,229,0.12)]">
        {BRAND_LOGO_LETTER}
      </span>
      <span className="font-syne text-xl font-extrabold uppercase tracking-[0.1em] text-mkt-ink">
        {BRAND_NAME}
      </span>
    </Link>
  );
}

export function AuthCard({ children }: { children: ReactNode }) {
  return (
    <div className="w-full max-w-md rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface/90 p-7 shadow-[0_30px_70px_rgba(20,20,26,0.06)] backdrop-blur-xl md:p-8">
      {children}
    </div>
  );
}

export function AuthCardHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="mb-8">
      <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">{eyebrow}</p>
      <h1 className="mt-3 font-syne text-2xl font-extrabold uppercase tracking-tight text-mkt-ink">{title}</h1>
      <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-muted">{description}</p>
    </div>
  );
}
