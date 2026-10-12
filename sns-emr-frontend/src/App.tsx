import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy, useEffect } from "react";
import type { ReactNode } from "react";
import RequireFeatureAccess from "./components/RequireFeatureAccess";
import RequireRoleAccess from "./components/RequireRoleAccess";
import { BodySystemsWorkspacePreview } from "./features/body-systems";
import OfflineStatusBadge from "./offline/OfflineStatusBadge";
import { startConnectivityMonitor } from "./offline/networkStatus";
import { startSyncManager } from "./offline/syncManager";

// HOPE-BUNDLE-SIZE-001: every route-level page is route-split via
// React.lazy() rather than statically imported. Before this change, the
// production build's main JS chunk was ~2.25 MB (every page for every
// discipline/billing/admin screen bundled into one file), exceeding the
// PWA service worker's 2 MiB precache limit and causing the production
// build to fail. This is a pure code-splitting change -- no behavior,
// route, or component changes -- so each page now loads its own chunk on
// first navigation instead of all being downloaded (and precached)
// up front. See the <Suspense> boundary around <Routes> below.
const SNSAnalytics = lazy(() => import("./pages/SNSAnalytics"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SetPasswordPage = lazy(() => import("./pages/SetPasswordPage"));
const CareOverviewPage = lazy(() => import("./pages/CareOverviewPage"));
const PlanOfCarePage = lazy(() => import("./pages/PlanOfCarePage"));
const RNICAPage = lazy(() => import("./pages/RNICAPage"));
const MSWICAPage = lazy(() => import("./pages/MSWICAPage"));
const SCICAPage = lazy(() => import("./pages/SCICAPage"));
const PatientLCDPage = lazy(() => import("./pages/PatientLCDPage"));
const BereavementDataPage = lazy(() => import("./pages/BereavementDataPage"));
const IncidentOccurrenceDataPage = lazy(() => import("./pages/IncidentOccurrenceDataPage"));
const ClinicalAlertsDataPage = lazy(() => import("./pages/ClinicalAlertsDataPage"));
const PhysicianDataPage = lazy(() => import("./pages/PhysicianDataPage"));
const CommunicationLogDataPage = lazy(() => import("./pages/CommunicationLogDataPage"));
const SecureInboxDataPage = lazy(() => import("./pages/SecureInboxDataPage"));
const ComplianceDataPage = lazy(() => import("./pages/ComplianceDataPage"));
const VolunteerSchedulingDataPage = lazy(() => import("./pages/VolunteerSchedulingDataPage"));
const MyProfilePage = lazy(() => import("./pages/MyProfilePage"));
const IDGWorkspacePage = lazy(() => import("./pages/IDGWorkspacePage"));
const OwnerDashboard = lazy(() => import("./owner/OwnerDashboard"));
const TenantDashboard = lazy(() => import("./tenant/TenantDashboard"));
const BillingOverviewPage = lazy(() => import("./pages/billing/BillingOverviewPage"));
const BillerShell = lazy(() => import("./components/billing/BillerShell"));
const VisitsNotesPage = lazy(() => import("./pages/billing/VisitsNotesPage"));
const PocCertificationPage = lazy(() => import("./pages/billing/PocCertificationPage"));
const NoeTrackingPage = lazy(() => import("./pages/billing/NoeTrackingPage"));
const ReadinessWorkflowPage = lazy(() => import("./pages/billing/ReadinessWorkflowPage"));
const ComingSoonPage = lazy(() => import("./pages/billing/ComingSoonPage"));
const ClaimsManagementPage = lazy(() => import("./pages/billing/ClaimsManagementPage"));
const DenialsAppealsPage = lazy(() => import("./pages/billing/DenialsAppealsPage"));
const EligibilityVerificationPage = lazy(() => import("./pages/billing/EligibilityVerificationPage"));
const PaymentPostingPage = lazy(() => import("./pages/billing/PaymentPostingPage"));
const ReportsPage = lazy(() => import("./pages/billing/ReportsPage"));
const CapCalculationPage = lazy(() => import("./pages/billing/CapCalculationPage"));
const AgingReportPage = lazy(() => import("./pages/billing/AgingReportPage"));
const CreditBalanceReportPage = lazy(() => import("./pages/billing/CreditBalanceReportPage"));
const FacilityCollectionsReportPage = lazy(() => import("./pages/billing/FacilityCollectionsReportPage"));
const PatientChart = lazy(() => import("./charts/PatientChart"));

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
      <Suspense fallback={null}>
      <Routes>

        {/* Default route */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/set-password" element={<SetPasswordPage />} />

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
          <Route path="readiness" element={<ReadinessWorkflowPage />} />
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
          <Route path="credit-balance-report" element={<CreditBalanceReportPage />} />
          <Route path="facility-collections" element={<FacilityCollectionsReportPage />} />
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
        {/*
          Development-only Body Systems preview route.
          Gated on `import.meta.env.DEV`, which Vite statically replaces
          with `false` in production builds — this Route is never
          registered (and therefore never reachable or linked from any
          production navigation) outside `npm run dev`. Renders only the
          synthetic, read-only `BodySystemsWorkspacePreview` shell; no
          authentication bypass, API, persistence, or RNICA coupling.
        */}
        {import.meta.env.DEV && (
          <Route path="/__dev-preview/body-systems" element={<BodySystemsWorkspacePreview />} />
        )}

        <Route path="*" element={<Navigate to="/login" replace />} />

      </Routes>
      </Suspense>
    </BrowserRouter>
  );
}