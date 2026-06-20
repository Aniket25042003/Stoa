/**
 * @file apps/web/src/components/product/BrandLogo.tsx
 * @layer Frontend Design System
 * @description Renders the Stoaai icon mark or horizontal wordmark.
 */
import Image from "next/image";
import {
  BRAND_ICON_SRC_48,
  BRAND_ICON_SRC_80,
  BRAND_LOGO_SRC,
  BRAND_LOGO_SRC_LG,
  BRAND_LOGO_SRC_MD,
  BRAND_LOGO_SRC_SM,
} from "@/lib/brand";
import { cn } from "@/lib/cn";

type BrandLogoVariant = "icon" | "logo";
type BrandLogoSize = "sm" | "md" | "lg";

type BrandLogoProps = {
  variant?: BrandLogoVariant;
  size?: BrandLogoSize;
  className?: string;
  priority?: boolean;
};

/** CSS display height for icon variants. */
const ICON_HEIGHT: Record<BrandLogoSize, number> = {
  sm: 32,
  md: 40,
  lg: 80,
};

/** CSS display box for logo variants (sources are exported at 2× for retina). */
const LOGO_DISPLAY: Record<BrandLogoSize, { width: number; height: number }> = {
  sm: { width: 146, height: 36 },
  md: { width: 179, height: 44 },
  lg: { width: 228, height: 56 },
};

const ICON_SRC: Record<BrandLogoSize, string> = {
  sm: BRAND_ICON_SRC_48,
  md: BRAND_ICON_SRC_48,
  lg: BRAND_ICON_SRC_80,
};

const LOGO_SRC: Record<BrandLogoSize, string> = {
  sm: BRAND_LOGO_SRC_SM,
  md: BRAND_LOGO_SRC_MD,
  lg: BRAND_LOGO_SRC_LG,
};

/**
 * Renders the Stoaai brand icon or horizontal logo.
 */
export function BrandLogo({
  variant = "icon",
  size = "sm",
  className,
  priority = false,
}: BrandLogoProps) {
  if (variant === "icon") {
    const height = ICON_HEIGHT[size];
    return (
      <Image
        src={ICON_SRC[size]}
        alt="Stoaai icon"
        width={height}
        height={height}
        priority={priority}
        className={cn("h-auto w-auto shrink-0 object-contain", className)}
        style={{ height, width: height }}
      />
    );
  }

  const { width, height } = LOGO_DISPLAY[size];

  return (
    <Image
      src={LOGO_SRC[size]}
      alt="Stoaai"
      width={width}
      height={height}
      priority={priority}
      className={cn("h-auto w-auto shrink-0 object-contain object-left", className)}
      style={{ height, width }}
    />
  );
}
