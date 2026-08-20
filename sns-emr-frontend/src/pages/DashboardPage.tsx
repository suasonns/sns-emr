import { Box } from "@mui/material";

import Sidebar from "../components/layout/Sidebar";
import Header from "../components/layout/Header";

import SNSAnalytics from "./SNSAnalytics";
import TenantDashboard from "../tenant/TenantDashboard";
import OwnerDashboard from "./OwnerDashboard";
import { getCurrentUser } from "../api/session";

// =========================================================
// COMPONENT
// =========================================================

export default function DashboardPage({ role }: { role: string }) {
  const currentUser = getCurrentUser();
  const user = {
    name: "Admin User", // ✅ replace later with real auth
    role,
    tenant_name: role === "OWNER" ? "All Tenants" : currentUser?.tenant_name ?? "Love & Faith Hospice Services Inc.",
  };

  // =========================================================
  // ROLE-BASED CONTENT
  // =========================================================

  let content: React.ReactNode;

  if (role === "BILLER") {
    content = <SNSAnalytics />;
  } else if (role === "TENANT_ADMIN" || role === "CLINICIAN") {
    content = <TenantDashboard />;
  } else if (role === "OWNER") {
    content = <OwnerDashboard />;
  } else {
    content = <div>No access</div>;
  }

  // =========================================================
  // LAYOUT
  // =========================================================

  return (
    <Box sx={{ display: "flex" }}>
      {/* ✅ SIDEBAR */}
      <Sidebar role={role} user={user} />

      {/* ✅ MAIN CONTENT */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {/* ✅ HEADER */}
        <Header user={user} />

        {/* ✅ PAGE CONTENT */}
        <Box sx={{ p: 3 }}>
          {content}
        </Box>
      </Box>
    </Box>
  );
}