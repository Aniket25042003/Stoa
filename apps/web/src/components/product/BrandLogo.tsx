/**
 * @file apps/web/src/components/product/BrandLogo.tsx
 * @layer Frontend Design System
 * @description Renders the Stoa icon mark or horizontal wordmark.
 */
import Image from "next/image";
import {
  BRAND_ICON_ON_DARK_SRC_48,
  BRAND_ICON_ON_DARK_SRC_80,
  BRAND_ICON_SRC_48,
  BRAND_ICON_SRC_80,
  BRAND_LOGO_ASPECT,
  BRAND_LOGO_ON_DARK_SRC_LG,
  BRAND_LOGO_ON_DARK_SRC_MD,
  BRAND_LOGO_ON_DARK_SRC_SM,
  BRAND_LOGO_SRC_LG,
  BRAND_LOGO_SRC_MD,
  BRAND_LOGO_SRC_SM,
  BRAND_NAME,
} from "@/lib/brand";
import { cn } from "@/lib/cn";

type BrandLogoVariant = "icon" | "logo";
type BrandLogoSize = "sm" | "md" | "lg";
type BrandLogoTone = "default" | "on-dark";

type BrandLogoProps = {
  variant?: BrandLogoVariant;
  size?: BrandLogoSize;
  /** Use `on-dark` on dark surfaces (e.g. marketing footer). */
  tone?: BrandLogoTone;
  className?: string;
  priority?: boolean;
};

/** CSS display height for icon variants. */
const ICON_HEIGHT: Record<BrandLogoSize, number> = {
  sm: 32,
  md: 40,
  lg: 80,
};

/** CSS display height for logo variants (sources are exported at 2× for retina). */
const LOGO_HEIGHT: Record<BrandLogoSize, number> = {
  sm: 36,
  md: 44,
  lg: 56,
};

const ICON_SRC: Record<BrandLogoTone, Record<BrandLogoSize, string>> = {
  default: {
    sm: BRAND_ICON_SRC_48,
    md: BRAND_ICON_SRC_48,
    lg: BRAND_ICON_SRC_80,
  },
  "on-dark": {
    sm: BRAND_ICON_ON_DARK_SRC_48,
    md: BRAND_ICON_ON_DARK_SRC_48,
    lg: BRAND_ICON_ON_DARK_SRC_80,
  },
};

const LOGO_SRC: Record<BrandLogoTone, Record<BrandLogoSize, string>> = {
  default: {
    sm: BRAND_LOGO_SRC_SM,
    md: BRAND_LOGO_SRC_MD,
    lg: BRAND_LOGO_SRC_LG,
  },
  "on-dark": {
    sm: BRAND_LOGO_ON_DARK_SRC_SM,
    md: BRAND_LOGO_ON_DARK_SRC_MD,
    lg: BRAND_LOGO_ON_DARK_SRC_LG,
  },
};

/**
 * Renders the Stoa brand icon or horizontal logo.
 */
export function BrandLogo({
  variant = "icon",
  size = "sm",
  tone = "default",
  className,
  priority = false,
}: BrandLogoProps) {
  if (variant === "icon") {
    const height = ICON_HEIGHT[size];
    return (
      <Image
        src={ICON_SRC[tone][size]}
        alt={`${BRAND_NAME} icon`}
        width={height}
        height={height}
        priority={priority}
        className={cn("h-auto w-auto shrink-0 object-contain", className)}
        style={{ height, width: height }}
      />
    );
  }

  const height = LOGO_HEIGHT[size];
  const width = Math.round(height * BRAND_LOGO_ASPECT);

  return (
    <Image
      src={LOGO_SRC[tone][size]}
      alt={BRAND_NAME}
      width={width}
      height={height}
      priority={priority}
      className={cn("h-auto w-auto shrink-0 object-contain object-left", className)}
      style={{ height, width }}
    />
  );
}
