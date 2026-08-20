import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Avatar,
  Badge,
  Box,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";

import { useDashboardAlerts, severityForCount } from "../../hooks/useDashboardAlerts";
import { logout } from "../../api/auth";

type SidebarUser = {
  name: string;
  role: string;
  tenant_name?: string;
};

export default function Sidebar({
  role,
  user,
}: {
  role: string;
  user: SidebarUser;
}) {
  const location = useLocation();
  const navigate = useNavigate();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { counts, total, loading } = useDashboardAlerts(role, 30000);

  const isActive = (path: string) => location.pathname === path;
  const menuOpen = Boolean(anchorEl);

  // ✅ NAV ITEMS
  const navItems = useMemo(() => {
    if (role === "OWNER") {
      // Platform/vendor super-user: platform operations only (tenants,
      // licensing, platform health). Never combined with billing/financial
      // access, and never any tenant, patient, or clinical PHI.
      return [{ label: "Owner Dashboard", path: "/owner", badge: total }];
    }

    if (role === "BILLER" || role === "BILLING") {
      return [{ label: "Analytics Hub", path: "/billing", badge: counts.tasks }];
    }

    return [
      { label: "Tenant Dashboard", path: "/tenant", badge: total },
      { label: "IDG Meeting Workspace", path: "/idg-workspace", badge: counts.blockers },
      { label: "Portal Preview", path: "/portal", badge: 0 },
    ];
  }, [role, counts, total]);

  // ✅ CLICK HANDLERS (SMART NAVIGATION)

  const handleFilterNavigation = (filter: string) => {
    navigate(`/tenant?filter=${filter}`);
  };

  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    window.location.href = "/";
  };

  return (
    <Box
      sx={{
        width: 280,
        bgcolor: "#0f172a",
        color: "white",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* HEADER */}
      <Box sx={{ p: 2, borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "center" }}>
        <Box
          component="img"
          src="/brand/sns-logo-light.svg"
          alt="SNS logo"
          onError={(event) => {
            const target = event.currentTarget as HTMLImageElement;
            if (!target.src.endsWith("/brand/sns-logo-icon.svg")) {
              target.src = "/brand/sns-logo-icon.svg";
            }
          }}
          sx={{ width: 190, height: "auto", display: "block" }}
        />
      </Box>

      {/* NAVIGATION */}
      <List sx={{ px: 1 }}>
        {navItems.map((item) => {
          const color = severityForCount(item.badge);

          return (
            <ListItemButton
              key={item.path}
              component={Link}
              to={item.path}
              selected={isActive(item.path)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                "&.Mui-selected": {
                  bgcolor: "#1e293b",
                },
              }}
            >
              <Badge badgeContent={item.badge} color={color} sx={{ mr: 2 }}>
                <Box sx={{ width: 10, height: 10 }} />
              </Badge>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>

      {/* REAL-TIME ALERTS */}
      <Box sx={{ px: 2, mt: 2 }}>
        <Typography variant="caption" color="#94a3b8">
          Real-Time Alerts {loading ? "· refreshing…" : ""}
        </Typography>

        <Stack spacing={1} sx={{ mt: 1 }}>
          {/* TASKS */}
          <Tooltip title="Open workflow tasks">
            <Box
              onClick={() => handleFilterNavigation("TASKS")}
              sx={{
                display: "flex",
                justifyContent: "space-between",
                cursor: "pointer",
                ":hover": { opacity: 0.8 },
              }}
            >
              <Typography variant="body2">Tasks</Typography>
              <Badge badgeContent={counts.tasks} color={severityForCount(counts.tasks)}>
                <Box sx={{ width: 10, height: 10 }} />
              </Badge>
            </Box>
          </Tooltip>

          {/* INCIDENTS */}
          <Tooltip title="Pending incident reports">
            <Box
              onClick={() => handleFilterNavigation("INCIDENTS")}
              sx={{
                display: "flex",
                justifyContent: "space-between",
                cursor: "pointer",
                ":hover": { opacity: 0.8 },
              }}
            >
              <Typography variant="body2">Incidents</Typography>
              <Badge badgeContent={counts.incidents} color={severityForCount(counts.incidents)}>
                <Box sx={{ width: 10, height: 10 }} />
              </Badge>
            </Box>
          </Tooltip>

          {/* BLOCKERS */}
          <Tooltip title="Patients blocked for IDG readiness">
            <Box
              onClick={() => handleFilterNavigation("BLOCKED")}
              sx={{
                display: "flex",
                justifyContent: "space-between",
                cursor: "pointer",
                ":hover": { opacity: 0.8 },
              }}
            >
              <Typography variant="body2">IDG Blockers</Typography>
              <Badge badgeContent={counts.blockers} color={severityForCount(counts.blockers)}>
                <Box sx={{ width: 10, height: 10 }} />
              </Badge>
            </Box>
          </Tooltip>
        </Stack>
      </Box>

      <Box sx={{ flexGrow: 1 }} />

      <Divider sx={{ bgcolor: "#1e293b" }} />

      {/* USER */}
      <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 1 }}>
        <IconButton onClick={handleOpenMenu}>
          <Avatar>{user.name.charAt(0).toUpperCase()}</Avatar>
        </IconButton>

        <Box>
          <Typography variant="body2">{user.name}</Typography>
          <Typography variant="caption" color="#94a3b8">
            {user.role}
            {user.tenant_name ? ` · ${user.tenant_name}` : ""}
          </Typography>
        </Box>
      </Box>

      <Menu anchorEl={anchorEl} open={menuOpen} onClose={handleCloseMenu}>
        <MenuItem onClick={handleCloseMenu}>Profile</MenuItem>
        <MenuItem onClick={handleCloseMenu}>Settings</MenuItem>
        <MenuItem onClick={handleLogout}>Logout</MenuItem>
      </Menu>
    </Box>
  );
}
