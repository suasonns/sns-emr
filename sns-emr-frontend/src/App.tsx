import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import SNSAnalytics from "./pages/SNSAnalytics";
import LoginPage from "./pages/LoginPage";
import CareOverviewPage from "./pages/CareOverviewPage";
import PlanOfCarePage from "./pages/PlanOfCarePage";
import RNICAPage from "./pages/RNICAPage";
import MSWICAPage from "./pages/MSWICAPage";
import SCICAPage from "./pages/SCICAPage";
import PatientLCDPage from "./pages/PatientLCDPage";
import BereavementDataPage from "./pages/BereavementDataPage";
import IncidentOccurrenceDataPage from "./pages/IncidentOccurrenceDataPage";
import ClinicalAlertsDataPage from "./pages/ClinicalAlertsDataPage";
import PhysicianDataPage from "./pages/PhysicianDataPage";
import CommunicationLogDataPage from "./pages/CommunicationLogDataPage";
import SecureInboxDataPage from "./pages/SecureInboxDataPage";
import ComplianceDataPage from "./pages/ComplianceDataPage";
import VolunteerSchedulingDataPage from "./pages/VolunteerSchedulingDataPage";
import MyProfilePage from "./pages/MyProfilePage";
import IDGWorkspacePage from "./pages/IDGWorkspacePage";
import OwnerDashboard from "./owner/OwnerDashboard";
import TenantDashboard from "./tenant/TenantDashboard";
import BillingDashboard from "./pages/BillingDashboard";
import PatientChart from "./charts/PatientChart";
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
        <Route path="/billing" element={<RequireAuth><BillingDashboard /></RequireAuth>} />
        <Route path="/analytics" element={<RequireAuth><SNSAnalytics /></RequireAuth>} />
        <Route path="/tenant" element={<RequireAuth><TenantDashboard /></RequireAuth>} />
        <Route path="/owner" element={<RequireAuth><OwnerDashboard /></RequireAuth>} />
        <Route path="/owner/:section" element={<RequireAuth><OwnerDashboard /></RequireAuth>} />
        <Route path="/rnica" element={<RequireAuth><RNICAPage /></RequireAuth>} />
        <Route path="/nursing-assessment" element={<RequireAuth><RNICAPage /></RequireAuth>} />
        <Route path="/admission" element={<RequireAuth><RNICAPage /></RequireAuth>} />
        <Route path="/assessment" element={<RequireAuth><RNICAPage /></RequireAuth>} />
        <Route path="/msw-ica" element={<RequireAuth><MSWICAPage /></RequireAuth>} />
        <Route path="/psychosocial" element={<RequireAuth><MSWICAPage /></RequireAuth>} />
        <Route path="/psychosocial-assessment" element={<RequireAuth><MSWICAPage /></RequireAuth>} />
        <Route path="/sc-ica" element={<RequireAuth><SCICAPage /></RequireAuth>} />
        <Route path="/spiritual" element={<RequireAuth><SCICAPage /></RequireAuth>} />
        <Route path="/spiritual-assessment" element={<RequireAuth><SCICAPage /></RequireAuth>} />
        <Route path="/patient-lcd" element={<RequireAuth><PatientLCDPage /></RequireAuth>} />
        <Route path="/care-overview" element={<RequireAuth><CareOverviewPage /></RequireAuth>} />
        <Route path="/plan-of-care" element={<RequireAuth><PlanOfCarePage /></RequireAuth>} />
        <Route path="/bereavement" element={<RequireAuth><BereavementDataPage /></RequireAuth>} />
        <Route path="/incident-occurrence" element={<RequireAuth><IncidentOccurrenceDataPage /></RequireAuth>} />
        <Route path="/clinical-alerts" element={<RequireAuth><ClinicalAlertsDataPage /></RequireAuth>} />
        <Route path="/physician" element={<RequireAuth><PhysicianDataPage /></RequireAuth>} />
        <Route path="/communication-log" element={<RequireAuth><CommunicationLogDataPage /></RequireAuth>} />
        <Route path="/secure-inbox" element={<RequireAuth><SecureInboxDataPage /></RequireAuth>} />
        <Route path="/messaging" element={<RequireAuth><SecureInboxDataPage /></RequireAuth>} />
        <Route path="/messenger" element={<RequireAuth><SecureInboxDataPage /></RequireAuth>} />
        <Route path="/compliance" element={<RequireAuth><ComplianceDataPage /></RequireAuth>} />
        <Route path="/volunteer-scheduling" element={<RequireAuth><VolunteerSchedulingDataPage /></RequireAuth>} />
        <Route path="/idg-workspace" element={<RequireAuth><IDGWorkspacePage /></RequireAuth>} />
        <Route path="/my-profile" element={<RequireAuth><MyProfilePage /></RequireAuth>} />
        <Route path="/portal" element={<RequireAuth><TenantDashboard /></RequireAuth>} />
        <Route path="/chart/:patientId" element={<RequireAuth><PatientChart /></RequireAuth>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/portal" replace />} />

      </Routes>
    </BrowserRouter>
  );
}