import type { ReactNode } from "react";
import { Box, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { getCurrentUser } from "../api/session";
import { portalTypography } from "../styles/portalTypography";

type PortalShellProps = {
  activeTab: string;
  children: ReactNode;
};

const NAV_ITEMS = [
  { label: "Dashboard", route: "/analytics?section=dashboard" },
  { label: "Census", route: "/analytics?section=census" },
  { label: "Secure Inbox", route: "/analytics?section=secure-inbox" },
  { label: "Clinical Alerts", route: "/analytics?section=clinical-alerts" },
  { label: "Scheduling", route: "/analytics?section=scheduling" },
  { label: "Analytics", route: "/analytics" },
  { label: "Settings", route: "/analytics?section=settings" },
  { label: "My Profile", route: "/analytics?section=my-profile" },
];

const C = {
  navy: "#1E3A5F",
  teal: "#0D9488",
  tealDark: "#0f766e",
  tealLight: "#ccfbf1",
  white: "#ffffff",
  slate200: "#E2E8F0",
  slate500: "#64748b",
  gray50: "#F8FAFC",
  gray900: "#111827",
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

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: C.gray50, display: "flex", flexDirection: "column", fontFamily: "'Inter', sans-serif" }}>
      <Box sx={{ bgcolor: C.navy, color: C.white }}>
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
            <Box sx={{ lineHeight: 1.1 }}>
              <Typography component="span" sx={{ fontSize: 20, fontWeight: 800, color: C.white, letterSpacing: 0.5 }}>
                SNS{" "}
              </Typography>
              <Typography component="span" sx={{ fontSize: 20, fontWeight: 800, color: C.teal, letterSpacing: 0.5 }}>
                Hospice
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
              {NAV_ITEMS.map((tab) => {
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
                      backgroundColor: active ? C.teal : "transparent",
                      color: active ? C.white : "#c9d6e3",
                      fontSize: portalTypography.body,
                      fontWeight: 600,
                      textTransform: "none",
                      fontFamily: "'Inter', sans-serif",
                      "&:hover": { backgroundColor: active ? C.teal : "rgba(255,255,255,0.08)" },
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

      <Box sx={{ bgcolor: C.navy, color: C.white }}>
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
        <Typography sx={{ fontSize: 11, fontWeight: 500 }}>SNS Hospice Solutions Secure Portal | &copy; 2024-2025 | All Rights Reserved | SNS Tech Solutions</Typography>
        <Typography sx={{ fontSize: 10, color: "#6b7280", mt: 0.5 }}>
          This system contains Protected Health Information (PHI). Access is restricted to authorized personnel and subject to HIPAA regulations. Unauthorized access or disclosure is strictly prohibited and may result in civil and criminal penalties.
        </Typography>
      </Box>
    </Box>
  );
}
