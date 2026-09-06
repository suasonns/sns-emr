import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Avatar,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import EventNoteOutlinedIcon from "@mui/icons-material/EventNoteOutlined";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import ReceiptLongOutlinedIcon from "@mui/icons-material/ReceiptLongOutlined";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import VerifiedUserOutlinedIcon from "@mui/icons-material/VerifiedUserOutlined";
import PaymentsOutlinedIcon from "@mui/icons-material/PaymentsOutlined";
import NotificationsActiveOutlinedIcon from "@mui/icons-material/NotificationsActiveOutlined";
import BarChartOutlinedIcon from "@mui/icons-material/BarChartOutlined";
import GppMaybeOutlinedIcon from "@mui/icons-material/GppMaybeOutlined";
import TrendingDownOutlinedIcon from "@mui/icons-material/TrendingDownOutlined";
import AccountBalanceWalletOutlinedIcon from "@mui/icons-material/AccountBalanceWalletOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";

import { logout } from "../../api/auth";
import { getCurrentUser } from "../../api/session";
import { AgencyProvider, useAgency } from "./AgencyContext";

// Canonical 11-item sidebar nav reconciled from the SNS Hospice Solutions
// Figma "External Billing Services" portal screens (dark navy theme, left
// sidebar, per-item icon) -- see docs/design/biller-dashboard-figma/README.md
// for the full reconciliation notes. "Billing Readiness" is kept as its own
// item per explicit user direction (2026-08-24) even though the reference
// screenshot's most complete mockup only shows 10 items without it; "Settings"
// is added as an 11th item to match that same screenshot. Pages without real
// backend data yet render an honest "not available yet" state rather than
// fabricated numbers -- see each page component.
const NAV_ITEMS = [
  { label: "Dashboard", path: "/billing/dashboard", icon: DashboardOutlinedIcon },
  { label: "Billing Readiness", path: "/billing/readiness", icon: FactCheckOutlinedIcon },
  { label: "Visits & Notes", path: "/billing/visits-notes", icon: EventNoteOutlinedIcon },
  { label: "POC & Certifications", path: "/billing/poc-certification", icon: AssignmentOutlinedIcon },
  { label: "Claims", path: "/billing/claims", icon: ReceiptLongOutlinedIcon },
  { label: "Denials & Appeals", path: "/billing/denials", icon: GavelOutlinedIcon },
  { label: "Eligibility", path: "/billing/eligibility", icon: VerifiedUserOutlinedIcon },
  { label: "Payment Posting", path: "/billing/payment-posting", icon: PaymentsOutlinedIcon },
  { label: "NOE Tracking", path: "/billing/noe-tracking", icon: NotificationsActiveOutlinedIcon },
  { label: "CAP Calculation", path: "/billing/cap-calculation", icon: GppMaybeOutlinedIcon },
  { label: "Aging Report", path: "/billing/aging-report", icon: TrendingDownOutlinedIcon },
  { label: "Credit Balance Report", path: "/billing/credit-balance-report", icon: AccountBalanceWalletOutlinedIcon },
  { label: "Reports", path: "/billing/reports", icon: BarChartOutlinedIcon },
  { label: "Settings", path: "/billing/settings", icon: SettingsOutlinedIcon },
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
            const Icon = item.icon;
            return (
              <Box
                key={item.path}
                component={Link}
                to={item.path}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.2,
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
                <Icon sx={{ fontSize: 18 }} />
                {item.label}
              </Box>
            );
          })}
        </Stack>

        {/* USER / LOGOUT */}
        <Box sx={{ p: 2, borderTop: `1px solid ${NAVY_BORDER}` }}>
          <Typography sx={{ color: "#7f97b3", fontSize: 10.5, mb: 1 }}>
            External Billing Audit
            <br />
            HIPAA Audit Active
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.2 }}>
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
      </Box>

      {/* MAIN AREA */}
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <Box sx={{ flexGrow: 1, p: 3, bgcolor: "#0b1626", overflowY: "auto" }}>
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
