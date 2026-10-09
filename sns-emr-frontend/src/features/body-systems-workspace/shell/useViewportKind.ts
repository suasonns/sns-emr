/**
 * SNS Body Systems Workspace — viewport-kind detection.
 *
 * Drives the choice between ResponsiveDesktopLayout and
 * ResponsiveMobileLayout. The breakpoint (767px) matches the existing
 * project convention (md: breakpoint) and the SNS Browser Width Validation
 * Standard's mobile/tablet boundary. This hook only classifies viewport
 * kind — it never hides or reorders the fixed ten-system registry; both
 * layouts render the exact same registry order.
 */
import { useEffect, useState } from "react";

export type ViewportKind = "desktop" | "mobile";

const MOBILE_QUERY = "(max-width: 767px)";

function resolveInitialViewportKind(): ViewportKind {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return "desktop";
  }
  return window.matchMedia(MOBILE_QUERY).matches ? "mobile" : "desktop";
}

export function useViewportKind(): ViewportKind {
  const [viewportKind, setViewportKind] = useState<ViewportKind>(resolveInitialViewportKind);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mediaQueryList = window.matchMedia(MOBILE_QUERY);
    const handleChange = (event: MediaQueryListEvent) => {
      setViewportKind(event.matches ? "mobile" : "desktop");
    };
    mediaQueryList.addEventListener("change", handleChange);
    return () => mediaQueryList.removeEventListener("change", handleChange);
  }, []);

  return viewportKind;
}
