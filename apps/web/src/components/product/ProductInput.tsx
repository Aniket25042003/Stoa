import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function ProductInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-3 font-dm-sans text-sm text-mkt-ink transition-all placeholder:text-mkt-muted/70 focus:border-mkt-accent focus:outline-none focus:ring-1 focus:ring-mkt-accent disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

export function ProductSelect({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "w-full rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-3 font-dm-sans text-sm text-mkt-ink transition-all focus:border-mkt-accent focus:outline-none focus:ring-1 focus:ring-mkt-accent disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

export function ProductTextarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-3 font-dm-sans text-sm text-mkt-ink transition-all placeholder:text-mkt-muted/70 focus:border-mkt-accent focus:outline-none focus:ring-1 focus:ring-mkt-accent disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}
