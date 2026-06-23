import Link from "next/link";
import { cn } from "@/lib/cn";

type ButtonVariant = "dark" | "light" | "glass";

type ButtonProps = {
  children: React.ReactNode;
  className?: string;
  href?: string;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  variant?: ButtonVariant;
};

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  dark: "mkt-solid-btn",
  light: "mkt-glass-btn-light",
  glass: "mkt-glass-btn",
};

export function GlassButton({
  children,
  className,
  href,
  onClick,
  type = "button",
  disabled,
  variant = "glass",
}: ButtonProps) {
  const cls = cn(VARIANT_CLASS[variant], disabled && "pointer-events-none opacity-50", className);

  if (href) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} onClick={onClick} disabled={disabled} className={cls}>
      {children}
    </button>
  );
}

export function SolidButton({
  children,
  className,
  href,
  onClick,
  type = "button",
  disabled,
  variant = "dark",
}: ButtonProps) {
  return (
    <GlassButton
      variant={variant}
      className={className}
      href={href}
      onClick={onClick}
      type={type}
      disabled={disabled}
    >
      {children}
    </GlassButton>
  );
}
