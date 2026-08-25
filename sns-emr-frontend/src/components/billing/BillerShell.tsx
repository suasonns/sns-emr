import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Avatar,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";

import { logout } from "../../api/auth";
import { getCurrentUser } from "../../api/session";
import { AgencyProvider, useAgency } from "./AgencyContext";

// Canonical 10-item sidebar nav reconciled from the SNS Hospice Solutions
// Figma "External Billing Services" portal screens (dark navy theme, left
// sidebar). Pages without real backend data yet render an honest
// "not available yet" state rather than fabricated numbers -- see each
// page component.
const NAV_ITEMS = [
  { label: "Dashboard", path: "/billing/dashboard" },
  { label: "Billing Readiness", path: "/billing/readiness" },
  { label: "Visits & Notes", path: "/billing/visits-notes" },
  { label: "POC & Certifications", path: "/billing/poc-certification" },
  { label: "Claims", path: "/billing/claims" },
  { label: "Denials & Appeals", path: "/billing/denials" },
  { label: "Eligibility", path: "/billing/eligibility" },
  { label: "Payment Posting", path: "/billing/payment-posting" },
  { label: "NOE Tracking", path: "/billing/noe-tracking" },
  { label: "Reports", path: "/billing/reports" },
];

const NAVY = "#0b1d33";
const NAVY_PANEL = "#132a47";
const NAVY_BORDER = "#1f3a5c";
const TEAL = "#14b8a6";

function ShellChrome() {
  const location = useLocation();
  const navigate = useNavigate();
  const user = getCurrentUser();
  const { agencies, selectedAgencyId, setSelectedAgencyId, loading: agenciesLoading } = useAgency();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const activeItem = NAV_ITEMS.find((item) => location.pathname.startsWith(item.path));

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "#0f1b2d" }}>
      {/* SIDEBAR */}
      <Box
        component="nav"
        sx={{
          width: 264,
          flexShrink: 0,
          bgcolor: NAVY,
          borderRight: `1px solid ${NAVY_BORDER}`,
          display: "flex",
          flexDirection: "column",
          minHeight: "100vh",
        }}
      >
        <Box sx={{ p: 2.5, borderBottom: `1px solid ${NAVY_BORDER}` }}>
          <Typography sx={{ color: "#fff", fontWeight: 800, fontSize: 15, letterSpacing: 0.2 }}>
            SNS Hospice Solutions
          </Typography>
          <Typography sx={{ color: "#7f97b3", fontWeight: 600, fontSize: 11.5, mt: 0.3 }}>
            External Billing Services
          </Typography>
        </Box>

        {/* AGENCY CONTEXT */}
        <Box sx={{ p: 2, borderBottom: `1px solid ${NAVY_BORDER}` }}>
          <Typography sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, mb: 0.6 }}>
            AGENCY CONTEXT
          </Typography>
          <Select
            size="small"
            fullWidth
            displayEmpty
            value={selectedAgencyId}
            onChange={(event) => setSelectedAgencyId(event.target.value)}
            disabled={agenciesLoading || agencies.length === 0}
            sx={{
              bgcolor: NAVY_PANEL,
              color: "#fff",
              fontSize: 13,
              borderRadius: 1.5,
              ".MuiOutlinedInput-notchedOutline": { borderColor: NAVY_BORDER },
              "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: TEAL },
              ".MuiSvgIcon-root": { color: "#7f97b3" },
            }}
          >
            {agencies.length === 0 ? (
              <MenuItem value="" disabled>
                {agenciesLoading ? "Loading agencies…" : "No billable agencies"}
              </MenuItem>
            ) : (
              agencies.map((agency) => (
                <MenuItem key={agency.tenant_id} value={agency.tenant_id}>
                  {agency.display_name || agency.legal_name}
                </MenuItem>
              ))
            )}
          </Select>
        </Box>

        {/* NAV */}
        <Stack sx={{ px: 1.5, py: 1.5, gap: 0.3, flexGrow: 1, overflowY: "auto" }}>
          {NAV_ITEMS.map((item) => {
            const active = activeItem?.path === item.path;
            return (
              <Box
                key={item.path}
                component={Link}
                to={item.path}
                sx={{
                  display: "block",
                  textDecoration: "none",
                  px: 1.5,
                  py: 1,
                  borderRadius: 1.5,
                  fontSize: 13.5,
                  fontWeight: active ? 700 : 500,
                  color: active ? "#fff" : "#a9bdd6",
                  bgcolor: active ? TEAL : "transparent",
                  "&:hover": { bgcolor: active ? TEAL : NAVY_PANEL },
                }}
              >
                {item.label}
              </Box>
            );
          })}
        </Stack>

        {/* USER / LOGOUT */}
        <Box sx={{ p: 2, borderTop: `1px solid ${NAVY_BORDER}`, display: "flex", alignItems: "center", gap: 1.2 }}>
          <IconButton size="small" onClick={(event) => setAnchorEl(event.currentTarget)} sx={{ p: 0 }}>
            <Avatar sx={{ width: 34, height: 34, bgcolor: TEAL, fontSize: 14, fontWeight: 700 }}>
              {(user?.full_name || user?.email || "?").charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>
          <Box sx={{ minWidth: 0, flexGrow: 1 }}>
            <Typography noWrap sx={{ color: "#fff", fontSize: 12.5, fontWeight: 700 }}>
              {user?.full_name || user?.email || "Biller"}
            </Typography>
            <Typography noWrap sx={{ color: "#7f97b3", fontSize: 11 }}>
              {user?.role || "Billing"}
            </Typography>
          </Box>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
            <MenuItem onClick={handleLogout}>Sign out</MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* MAIN AREA */}
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* HIPAA MINIMUM-NECESSARY-ACCESS BANNER */}
        <Box
          sx={{
            bgcolor: "#fef3c7",
            borderBottom: "1px solid #fde68a",
            px: 2.5,
            py: 0.8,
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          <Chip
            label="HIPAA"
            size="small"
            sx={{ bgcolor: "#f59e0b", color: "#fff", fontWeight: 800, fontSize: 10.5, height: 20 }}
          />
          <Typography sx={{ fontSize: 12, color: "#78350f", fontWeight: 600 }}>
            Minimum-necessary access: only billing-relevant fields for the selected agency are shown here. Clinical
            note content is never displayed.
          </Typography>
        </Box>

        <Box sx={{ flexGrow: 1, p: 3, bgcolor: "#f4f7fb", overflowY: "auto" }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}

export default function BillerShell() {
  return (
    <AgencyProvider>
      <ShellChrome />
    </AgencyProvider>
  );
}
