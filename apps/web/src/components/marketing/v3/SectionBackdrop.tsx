import { cn } from "@/lib/cn";

export type SectionBackdropVariant =
  | "hero-grid"
  | "plain"
  | "dark-grid"
  | "dots"
  | "warm"
  | "cta";

const VARIANT_CLASS: Record<SectionBackdropVariant, string> = {
  "hero-grid": "mkt-section-bg-hero",
  plain: "mkt-section-bg-plain",
  "dark-grid": "mkt-section-bg-dark",
  dots: "mkt-section-bg-dots",
  warm: "mkt-section-bg-warm",
  cta: "mkt-section-bg-cta",
};

export function SectionBackdrop({ variant }: { variant: SectionBackdropVariant }) {
  return (
    <div className={cn("pointer-events-none absolute inset-0", VARIANT_CLASS[variant])} aria-hidden />
  );
}

export type SectionTone = "light" | "dark";

export function sectionToneClasses(tone: SectionTone) {
  if (tone === "dark") {
    return {
      eyebrow: "text-mkt-dark-ink/45",
      body: "text-mkt-dark-ink/65",
      headlinePrimary: "text-mkt-dark-ink",
      headlineSecondary: "text-mkt-dark-ink/55",
    };
  }

  return {
    eyebrow: "text-mkt-subtle",
    body: "text-mkt-muted",
    headlinePrimary: "text-mkt-ink",
    headlineSecondary: "text-mkt-ink-secondary",
  };
}
