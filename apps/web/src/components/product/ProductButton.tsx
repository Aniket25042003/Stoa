import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type ProductButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
};

const variants = {
  primary:
    "bg-mkt-accent text-mkt-dark-ink shadow-[0_8px_20px_rgba(79,70,229,0.18)] hover:bg-[#4338CA] active:scale-[0.98]",
  secondary:
    "border border-mkt-ink/10 bg-mkt-surface text-mkt-ink hover:border-mkt-accent/30 hover:text-mkt-accent",
  ghost: "text-mkt-muted hover:bg-mkt-accent/[0.06] hover:text-mkt-ink",
};

export function ProductButton({
  variant = "primary",
  className,
  children,
  ...props
}: ProductButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-sm px-4 py-2.5 font-dm-sans text-[10px] font-bold uppercase tracking-widest transition-all disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
