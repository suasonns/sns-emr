import type { CSSProperties } from "react";

/**
 * Single source of truth for the SNS Hospice Solutions logo.
 *
 * There are exactly three approved logo assets, all under
 * `public/brand/`: sns-logo-light.svg, sns-logo-dark.svg, and
 * sns-logo-icon.svg. This component is the ONLY place that should
 * reference those file paths — every page that renders the logo
 * should render <BrandLogo variant="..." /> instead of hardcoding
 * an <img src="/brand/..."> block, so a future asset update only
 * needs to happen once.
 *
 * This does not introduce any new visual design: it reproduces the
 * exact markup/behavior (including the icon fallback on load error)
 * that was previously duplicated across 7 separate files.
 */
export type BrandLogoVariant = "light" | "dark" | "icon";

const LOGO_PATHS: Record<BrandLogoVariant, string> = {
  light: "/brand/sns-logo-light.svg",
  dark: "/brand/sns-logo-dark.svg",
  icon: "/brand/sns-logo-icon.svg",
};

export interface BrandLogoProps {
  /** Which approved asset to render. "light"/"dark" refer to the logo's
   * own color treatment (a "light"-treatment logo is meant for dark
   * backgrounds, and vice versa); "icon" is the compact mark used in
   * tight navigation/collapsed spaces. */
  variant: BrandLogoVariant;
  alt?: string;
  style?: CSSProperties;
  className?: string;
}

export default function BrandLogo({
  variant,
  alt = "SNS Hospice Solutions",
  style,
  className,
}: BrandLogoProps) {
  return (
    <img
      src={LOGO_PATHS[variant]}
      alt={alt}
      className={className}
      style={style}
      onError={(event) => {
        const target = event.currentTarget;
        if (!target.src.endsWith(LOGO_PATHS.icon)) {
          target.src = LOGO_PATHS.icon;
        }
      }}
    />
  );
}
