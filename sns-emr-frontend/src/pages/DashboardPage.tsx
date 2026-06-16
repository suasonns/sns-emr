import { Box } from "@mui/material";

import Sidebar from "../components/layout/Sidebar";
import Header from "../components/layout/Header";

import BillingDashboard from "./BillingDashboard";
import TenantDashboard from "./TenantDashboard";
import OwnerDashboard from "./OwnerDashboard";

// =========================================================
// COMPONENT
// =========================================================

export default function DashboardPage({ role }: { role: string }) {
  const user = {
    name: "Admin User", // ✅ replace later with real auth
    role,
    tenant_name: role === "OWNER" ? "All Tenants" : "Love & Faith Hospice",
  };

  // =========================================================
  // ROLE-BASED CONTENT
  // =========================================================

  let content: React.ReactNode;

  if (role === "BILLER") {
    content = <BillingDashboard />;
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