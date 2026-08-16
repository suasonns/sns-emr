import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import SNSAnalytics from "./pages/SNSAnalytics";
import LoginPage from "./pages/LoginPage";
import OwnerDashboard from "./owner/OwnerDashboard";
import TenantDashboard from "./tenant/TenantDashboard";
import RequireAuth from "./components/RequireAuth";

// ✅ ENTERPRISE ROUTER (FIXED JSX)
export default function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* Default route */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Pages */}
        <Route path="/billing" element={<RequireAuth><Navigate to="/analytics" replace /></RequireAuth>} />
        <Route path="/analytics" element={<RequireAuth><SNSAnalytics /></RequireAuth>} />
        <Route path="/tenant" element={<RequireAuth><TenantDashboard /></RequireAuth>} />
        <Route path="/owner" element={<RequireAuth><OwnerDashboard /></RequireAuth>} />
        <Route path="/owner/:section" element={<RequireAuth><OwnerDashboard /></RequireAuth>} />
        <Route path="/rnica" element={<RequireAuth><Navigate to="/analytics?section=rnica" replace /></RequireAuth>} />
        <Route path="/msw-ica" element={<RequireAuth><Navigate to="/analytics?section=msw-ica" replace /></RequireAuth>} />
        <Route path="/sc-ica" element={<RequireAuth><Navigate to="/analytics?section=sc-ica" replace /></RequireAuth>} />
        <Route path="/patient-lcd" element={<RequireAuth><Navigate to="/analytics?section=patient-lcd" replace /></RequireAuth>} />
        <Route path="/care-overview" element={<RequireAuth><Navigate to="/analytics?section=care-overview" replace /></RequireAuth>} />
        <Route path="/bereavement" element={<RequireAuth><Navigate to="/analytics?section=bereavement" replace /></RequireAuth>} />
        <Route path="/incident-occurrence" element={<RequireAuth><Navigate to="/analytics?section=incident-occurrence" replace /></RequireAuth>} />
        <Route path="/clinical-alerts" element={<RequireAuth><Navigate to="/analytics?section=clinical-alerts" replace /></RequireAuth>} />
        <Route path="/physician" element={<RequireAuth><Navigate to="/analytics?section=physician" replace /></RequireAuth>} />
        <Route path="/communication-log" element={<RequireAuth><Navigate to="/analytics?section=communication-log" replace /></RequireAuth>} />
        <Route path="/secure-inbox" element={<RequireAuth><Navigate to="/analytics?section=secure-inbox" replace /></RequireAuth>} />
        <Route path="/messaging" element={<RequireAuth><Navigate to="/analytics?section=secure-inbox" replace /></RequireAuth>} />
        <Route path="/messenger" element={<RequireAuth><Navigate to="/analytics?section=secure-inbox" replace /></RequireAuth>} />
        <Route path="/compliance" element={<RequireAuth><Navigate to="/analytics?section=compliance" replace /></RequireAuth>} />
        <Route path="/volunteer-scheduling" element={<RequireAuth><Navigate to="/analytics?section=scheduling" replace /></RequireAuth>} />
        <Route path="/my-profile" element={<RequireAuth><Navigate to="/analytics?section=my-profile" replace /></RequireAuth>} />
        <Route path="/portal" element={<RequireAuth><TenantDashboard /></RequireAuth>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/portal" replace />} />

      </Routes>
    </BrowserRouter>
  );
}