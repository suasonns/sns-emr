import type { CSSProperties } from "react";

/**
 * Single source of truth for the SNS Hospice Solutions logo.
 *
 * There are exactly four approved logo assets, all under
 * `public/brand/`: sns-logo-light.svg (used on dark-theme
 * backgrounds), sns-logo-dark.svg (used on light-theme backgrounds),
 * sns-logo-icon.svg (compact mark), and sns-logo-icon-dark-tile.svg
 * (compact mark for the small dark/teal sidebar tile). This component
 * is the ONLY place that should reference those file paths — every
 * page that renders the logo should render <BrandLogo variant="..." />
 * instead of hardcoding an <img src="/brand/..."> block, so a future
 * asset update only needs to happen once.
 *
 * These are the ONLY approved logo assets. Do not add, replace, or
 * regenerate them without an explicit request — see
 * public/brand/README.md.
 *
 * This does not introduce any new visual design: it reproduces the
 * exact markup/behavior (including the icon fallback on load error)
 * that was previously duplicated across 7 separate files.
 */
export type BrandLogoVariant = "light" | "dark" | "icon" | "icon-dark-tile";

const LOGO_PATHS: Record<BrandLogoVariant, string> = {
  light: "/brand/sns-logo-light.svg",
  dark: "/brand/sns-logo-dark.svg",
  icon: "/brand/sns-logo-icon.svg",
  "icon-dark-tile": "/brand/sns-logo-icon-dark-tile.svg",
};

export interface BrandLogoProps {
  /** Which approved asset to render.
   * - "dark" — dark color treatment, for LIGHT-theme backgrounds
   *   (e.g. the login page).
   * - "light" — light color treatment, for DARK-theme backgrounds
   *   (e.g. navy sidebars/headers).
   * - "icon" — compact mark, general use.
   * - "icon-dark-tile" — compact mark for the small dark/teal
   *   sidebar tile (Owner Platform collapsed sidebar). */
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
