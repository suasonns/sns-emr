import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import type { ReactNode } from "react";

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
import BillingOverviewPage from "./pages/billing/BillingOverviewPage";
import BillerShell from "./components/billing/BillerShell";
import VisitsNotesPage from "./pages/billing/VisitsNotesPage";
import PocCertificationPage from "./pages/billing/PocCertificationPage";
import NoeTrackingPage from "./pages/billing/NoeTrackingPage";
import ComingSoonPage from "./pages/billing/ComingSoonPage";
import ClaimsManagementPage from "./pages/billing/ClaimsManagementPage";
import DenialsAppealsPage from "./pages/billing/DenialsAppealsPage";
import EligibilityVerificationPage from "./pages/billing/EligibilityVerificationPage";
import PaymentPostingPage from "./pages/billing/PaymentPostingPage";
import ReportsPage from "./pages/billing/ReportsPage";
import CapCalculationPage from "./pages/billing/CapCalculationPage";
import AgingReportPage from "./pages/billing/AgingReportPage";
import PatientChart from "./charts/PatientChart";
import RequireFeatureAccess from "./components/RequireFeatureAccess";
import RequireRoleAccess from "./components/RequireRoleAccess";
import { useEffect } from "react";
import OfflineStatusBadge from "./offline/OfflineStatusBadge";
import { startConnectivityMonitor } from "./offline/networkStatus";
import { startSyncManager } from "./offline/syncManager";

const tenantRoute = (element: ReactNode) => (
  <RequireRoleAccess access="tenant">{element}</RequireRoleAccess>
);

// ✅ ENTERPRISE ROUTER (FIXED JSX)
export default function App() {
  useEffect(() => {
    // Started once for the whole app: watches connectivity and drains any
    // durable offline queue (RN ICA saves/updates, document uploads) the
    // instant a signal is available again -- no per-page wiring needed.
    startConnectivityMonitor();
    startSyncManager();
  }, []);

  return (
    <BrowserRouter>
      <OfflineStatusBadge />
      <Routes>

        {/* Default route */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Pages */}
        <Route
          path="/billing"
          element={
            <RequireFeatureAccess feature="billing">
              <BillerShell />
            </RequireFeatureAccess>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<BillingOverviewPage />} />
          <Route path="readiness" element={<Navigate to="/billing/dashboard" replace />} />
          <Route path="settings" element={<ComingSoonPage title="Settings" />} />
          <Route path="visits-notes" element={<VisitsNotesPage />} />
          <Route path="poc-certification" element={<PocCertificationPage />} />
          <Route path="noe-tracking" element={<NoeTrackingPage />} />
          <Route path="claims" element={<ClaimsManagementPage />} />
          <Route path="denials" element={<DenialsAppealsPage />} />
          <Route path="eligibility" element={<EligibilityVerificationPage />} />
          <Route path="payment-posting" element={<PaymentPostingPage />} />
          <Route path="cap-calculation" element={<CapCalculationPage />} />
          <Route path="aging-report" element={<AgingReportPage />} />
          <Route path="reports" element={<ReportsPage />} />
        </Route>
        <Route path="/analytics" element={<RequireRoleAccess access="analytics"><SNSAnalytics /></RequireRoleAccess>} />
        <Route path="/tenant" element={tenantRoute(<TenantDashboard />)} />
        <Route path="/owner" element={<RequireRoleAccess access="owner"><OwnerDashboard /></RequireRoleAccess>} />
        <Route path="/owner/:section" element={<RequireRoleAccess access="owner"><OwnerDashboard /></RequireRoleAccess>} />
        <Route path="/rnica" element={tenantRoute(<RNICAPage />)} />
        <Route path="/nursing-assessment" element={tenantRoute(<RNICAPage />)} />
        <Route path="/admission" element={tenantRoute(<RNICAPage />)} />
        <Route path="/assessment" element={tenantRoute(<RNICAPage />)} />
        <Route path="/msw-ica" element={tenantRoute(<MSWICAPage />)} />
        <Route path="/psychosocial" element={tenantRoute(<MSWICAPage />)} />
        <Route path="/psychosocial-assessment" element={tenantRoute(<MSWICAPage />)} />
        <Route path="/sc-ica" element={tenantRoute(<SCICAPage />)} />
        <Route path="/spiritual" element={tenantRoute(<SCICAPage />)} />
        <Route path="/spiritual-assessment" element={tenantRoute(<SCICAPage />)} />
        <Route path="/patient-lcd" element={tenantRoute(<PatientLCDPage />)} />
        <Route path="/care-overview" element={tenantRoute(<CareOverviewPage />)} />
        <Route path="/plan-of-care" element={tenantRoute(<PlanOfCarePage />)} />
        <Route path="/bereavement" element={tenantRoute(<BereavementDataPage />)} />
        <Route path="/incident-occurrence" element={tenantRoute(<IncidentOccurrenceDataPage />)} />
        <Route path="/clinical-alerts" element={tenantRoute(<ClinicalAlertsDataPage />)} />
        <Route path="/physician" element={tenantRoute(<PhysicianDataPage />)} />
        <Route path="/communication-log" element={tenantRoute(<CommunicationLogDataPage />)} />
        <Route path="/secure-inbox" element={tenantRoute(<SecureInboxDataPage />)} />
        <Route path="/messaging" element={tenantRoute(<SecureInboxDataPage />)} />
        <Route path="/messenger" element={tenantRoute(<SecureInboxDataPage />)} />
        <Route path="/compliance" element={tenantRoute(<ComplianceDataPage />)} />
        <Route path="/volunteer-scheduling" element={tenantRoute(<VolunteerSchedulingDataPage />)} />
        <Route path="/idg-workspace" element={tenantRoute(<IDGWorkspacePage />)} />
        <Route path="/my-profile" element={tenantRoute(<MyProfilePage />)} />
        <Route path="/portal" element={tenantRoute(<TenantDashboard />)} />
        <Route path="/chart/:patientId" element={tenantRoute(<PatientChart />)} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
    </BrowserRouter>
  );
}