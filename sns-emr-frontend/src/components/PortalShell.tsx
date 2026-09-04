import type { ReactNode } from "react";
import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { getCurrentUser } from "../api/session";
import { portalTypography } from "../styles/portalTypography";
import { hasFeatureAccess, hasRouteAccess } from "../utils/authorization";
import type { FeatureKey, RouteAccess } from "../utils/authorization";
import BrandLogo from "./BrandLogo";

type PortalShellProps = {
  activeTab: string;
  children: ReactNode;
};

type NavItem = {
  label: string;
  route: string;
  access?: RouteAccess;
  feature?: FeatureKey;
};

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", route: "/portal", access: "tenant" },
  { label: "Census", route: "/tenant", access: "tenant" },
  { label: "Secure Inbox", route: "/secure-inbox", access: "tenant" },
  { label: "Clinical Alerts", route: "/clinical-alerts", access: "tenant" },
  { label: "Analytics", route: "/analytics", access: "analytics" },
  { label: "Billing", route: "/billing", feature: "billing" },
  { label: "My Profile", route: "/my-profile", access: "tenant" },
];

const C = {
  navy: "var(--sns-bgAlt)",
  teal: "var(--sns-teal)",
  tealDark: "var(--sns-teal)",
  tealLight: "var(--sns-cardSoft)",
  white: "var(--sns-white)",
  slate200: "var(--sns-border)",
  slate500: "var(--sns-muted)",
  gray50: "var(--sns-bg)",
  gray900: "var(--sns-card)",
};

function formatRole(role?: string) {
  if (!role) return "";
  if (role === "RN" || role === "LVN" || role === "LPN" || role === "MD" || role === "NP" || role === "SW") {
    return role;
  }
  return role
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getInitials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export default function PortalShell({ activeTab, children }: PortalShellProps) {
  const navigate = useNavigate();
  const user = getCurrentUser();
  const displayName = user?.full_name ?? "Signed-in User";
  const displayRole = formatRole(user?.role) || "Clinical Staff";
  const initials = getInitials(displayName) || "US";
  const navItems = NAV_ITEMS.filter((item) => (
    item.feature
      ? hasFeatureAccess(user, item.feature)
      : item.access ? hasRouteAccess(user, item.access) : false
  ));

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: C.gray50, color: C.white, display: "flex", flexDirection: "column", fontFamily: "'Inter', sans-serif" }}>
      <Box sx={{ bgcolor: "var(--sns-card)", color: C.white }}>
        <Box
          sx={{
            width: "100%",
            px: 3.5,
            minHeight: 80,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            flexWrap: "wrap",
            boxSizing: "border-box",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 3, flexWrap: "wrap" }}>
            <BrandLogo
              variant="light"
              style={{ width: 180, height: "auto", display: "block" }}
            />
            <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
              {navItems.map((tab) => {
                const active = tab.label === activeTab;
                return (
                  <Button
                    key={tab.label}
                    onClick={() => navigate(tab.route)}
                    sx={{
                      minWidth: "auto",
                      px: 1.75,
                      py: 1,
                      borderRadius: 1,
                      border: "none",
                      backgroundColor: active ? "var(--sns-teal)" : "transparent",
                      color: active ? "var(--sns-white)" : "var(--sns-muted)",
                      fontSize: portalTypography.body,
                      fontWeight: 600,
                      textTransform: "none",
                      fontFamily: "'Inter', sans-serif",
                      "&:hover": { backgroundColor: active ? "var(--sns-teal)" : "rgba(255,255,255,0.08)" },
                    }}
                  >
                    {tab.label}
                  </Button>
                );
              })}
              </Box>
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexShrink: 0 }}>
            <Box sx={{ textAlign: "right" }}>
              <Typography sx={{ fontSize: portalTypography.subtitle, fontWeight: 600, color: C.white, lineHeight: 1.1 }}>{displayName}</Typography>
              <Typography sx={{ fontSize: portalTypography.chip, color: "#bfdbfe" }}>{displayRole}</Typography>
            </Box>
            <Box sx={{ width: 36, height: 36, borderRadius: "50%", bgcolor: C.white, color: C.navy, display: "grid", placeItems: "center", fontSize: portalTypography.chip, fontWeight: 800 }}>
              {initials}
            </Box>
          </Box>
        </Box>
      </Box>

      <Box sx={{ flex: 1, width: "100%" }}>
        <Box sx={{ width: "100%", px: 4, py: 3.5, boxSizing: "border-box" }}>{children}</Box>
      </Box>

      <Box sx={{ bgcolor: "var(--sns-card)", color: C.white }}>
        <Box
          sx={{
            width: "100%",
            px: 4,
            minHeight: 65,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            flexWrap: "wrap",
            boxSizing: "border-box",
          }}
        >
          <Box sx={{ display: "flex", gap: 2.5, flexWrap: "wrap", rowGap: 1 }}>
            {["Patient Care Hub", "Clinical Charting Validation", "Compliance Alerts & Logs", "Quality & QIES Reports", "Billing & HIS Tools"].map((item) => (
              <Typography key={item} sx={{ fontSize: portalTypography.subtitle, fontWeight: 500, color: C.white, whiteSpace: "nowrap" }}>
                {item}
              </Typography>
            ))}
          </Box>
          <Typography sx={{ fontSize: portalTypography.subtitle, fontWeight: 600, color: C.teal }}>Secure Support: 1-800-555-0199</Typography>
        </Box>
      </Box>

      <Box sx={{ bgcolor: C.gray900, color: "#9ca3af", textAlign: "center", py: 2.5, px: 3 }}>
        <Typography sx={{ fontSize: 11, fontWeight: 500 }}>Secure Portal | &copy; 2024-2025 | All Rights Reserved</Typography>
        <Typography sx={{ fontSize: 10, color: "#6b7280", mt: 0.5 }}>
          This system contains Protected Health Information (PHI). Access is restricted to authorized personnel and subject to HIPAA regulations. Unauthorized access or disclosure is strictly prohibited and may result in civil and criminal penalties.
        </Typography>
      </Box>
    </Box>
  );
}
