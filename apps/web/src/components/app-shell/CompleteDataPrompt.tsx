import Link from "next/link";
import { ProductButton, ProductCard } from "@/components/product";

export function CompleteDataPrompt({
  title,
  message,
  missing,
}: {
  title: string;
  message: string;
  missing?: string[];
}) {
  return (
    <ProductCard className="border-mkt-accent/20 bg-mkt-accent/[0.04]">
      <h3 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">{title}</h3>
      <p className="mt-2 font-dm-sans text-sm leading-relaxed text-mkt-muted">{message}</p>
      {missing && missing.length > 0 ? (
        <p className="mt-2 font-dm-sans text-xs text-mkt-muted">Missing: {missing.join(", ")}</p>
      ) : null}
      <Link href="/data/profile" className="mt-4 inline-block">
        <ProductButton>Go to Data hub</ProductButton>
      </Link>
    </ProductCard>
  );
}
