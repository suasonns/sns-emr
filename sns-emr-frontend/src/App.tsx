import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import BillingDashboard from "./pages/BillingDashboard";
import TenantDashboard from "./pages/TenantDashboard";
import OwnerDashboard from "./pages/OwnerDashboard";

// ✅ ENTERPRISE ROUTER (FIXED JSX)
export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Default route */}
        <Route path="/" element={<Navigate to="/billing" replace />} />

        {/* Pages */}
        <Route path="/billing" element={<BillingDashboard />} />
        <Route path="/tenant" element={<TenantDashboard />} />
        <Route path="/owner" element={<OwnerDashboard />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/billing" replace />} />

      </Routes>
    </BrowserRouter>
  );
}