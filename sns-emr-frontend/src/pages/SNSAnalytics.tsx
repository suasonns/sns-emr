import {
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
  fetchCensusWorkspace,
  type CensusPatientRow,
  type CensusWorkspaceResponse,
} from "../api/census";
import {
  fetchClinicalAlerts,
  fetchTenantDashboard,
  type ClinicalAlertsResponse,
  type DashboardIncidentItem,
  type DashboardNoteFlagItem,
  type DashboardOrderItem,
  type DashboardPatientBlocker,
  type DashboardTaskItem,
  type TenantDashboardResponse,
} from "../api/dashboard";
import { listIdgSessions, type IDGSessionSummary } from "../api/idgWorkspace";
import { getCurrentUser } from "../api/session";
import { listStaff, type StaffRecord } from "../api/staff";
import PortalShell from "../components/PortalShell";
import { canAccessBilling } from "../utils/featureAccess";
import SNSNewReports from "./SNSNewReports";
import TenantBillingOutcomes from "./TenantBillingOutcomes";

const C = {
  navy: "#1f4a78",
  teal: "#10b7a2",
  tealDark: "#0f766e",
  tealLight: "#ccfbf1",
  greenDark: "#065f46",
  greenLight: "#d1fae5",
  green: "#059669",
  amberDark: "#92400e",
  amberLight: "#fef3c7",
  amber: "#f59e0b",
  red: "#dc2626",
  redLight: "#fee2e2",
  blue: "#2563eb",
  blueLight: "#dbeafe",
  slate200: "#e2e8f0",
  slate500: "#64748b",
  gray100: "#f3f4f6",
  gray200: "#e5e7eb",
  gray400: "#9ca3af",
  gray500: "#6b7280",
  gray600: "#4b5563",
  gray800: "#1f2937",
  gray900: "#111827",
  white: "#ffffff",
};

const SECTION_TO_DOMAIN: Record<string, string> = {
  dashboard: "Command Center",
  census: "Clinical",
  "secure-inbox": "Analytics Directory",
  "clinical-alerts": "Analytics Directory",
  scheduling: "Analytics Directory",
  billing: "Analytics Directory",
  staff: "Analytics Directory",
  qapi: "QAPI",
  compliance: "Analytics Directory",
  settings: "Administrative",
  "my-profile": "Administrative",
  rnica: "Clinical",
  "msw-ica": "Clinical",
  "sc-ica": "Clinical",
  "patient-lcd": "Clinical",
  "care-overview": "Clinical",
  bereavement: "Analytics Directory",
  "incident-occurrence": "Analytics Directory",
  physician: "Administrative",
  "communication-log": "Analytics Directory",
};

const cardStyle: CSSProperties = {
  backgroundColor: C.white,
  borderRadius: 12,
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  padding: 24,
};
const pageShellStyle: CSSProperties = { width: "min(1180px, 100%)", margin: "0 auto", boxSizing: "border-box" };
const responsiveFourGrid: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, alignItems: "start" };
const responsiveThreeGrid: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20, alignItems: "start" };
const responsiveTwoGrid: CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20, alignItems: "start" };
const thStyle: CSSProperties = {
  textAlign: "left",
  padding: "12px 8px",
  fontSize: 11,
  fontWeight: 700,
  color: C.slate500,
  textTransform: "uppercase",
  letterSpacing: 0.5,
  whiteSpace: "normal",
  verticalAlign: "top",
};
const tdStyle: CSSProperties = { padding: "12px 8px", fontSize: 13, color: C.gray600, whiteSpace: "normal", verticalAlign: "top", overflowWrap: "anywhere" };

type SourceErrors = Partial<Record<"census" | "dashboard" | "alerts" | "staff" | "idg", string>>;

type AnalyticsDataState = {
  alerts: ClinicalAlertsResponse | null;
  census: CensusWorkspaceResponse | null;
  dashboard: TenantDashboardResponse | null;
  errors: SourceErrors;
  idgSessions: IDGSessionSummary[] | null;
  loading: boolean;
  staff: StaffRecord[] | null;
};

type AnalyticsViewModel = {
  activePatients: CensusPatientRow[];
  activeStaff: StaffRecord[];
  admissionsThisMonth: number;
  avgAge: number | null;
  avgDaysOnService: number | null;
  blockedPatients: DashboardPatientBlocker[];
  censusError: string | null;
  censusRows: CensusPatientRow[];
  clinicalStaffCount: number;
  dashboardError: string | null;
  dischargesThisMonth: number;
  flaggedNotes: DashboardNoteFlagItem[];
  idgError: string | null;
  idgSessions: IDGSessionSummary[];
  loading: boolean;
  medicationOrderCount: number;
  openIncidents: DashboardIncidentItem[];
  openTasks: DashboardTaskItem[];
  orderRows: DashboardOrderItem[];
  payerMix: Array<{ label: string; value: number }>;
  patientNameById: Map<string, string>;
  recentAdmissions: CensusPatientRow[];
  recentAlerts: ClinicalAlertsResponse["alerts"];
  recentVisitActivity: CensusPatientRow[];
  sourceWarnings: string[];
  staffError: string | null;
  staffRoleMix: Array<{ label: string; value: number }>;
  topDiagnoses: Array<{ label: string; value: number }>;
  topOrderCategories: Array<{ label: string; value: number }>;
  totalOrders: number;
  unsignedOrders: DashboardOrderItem[];
};

function resolveDomainFromSection(section: string | null | undefined, fallback: string) {
  if (!section) return fallback;
  return SECTION_TO_DOMAIN[section] ?? fallback;
}

function badge(text: string, bg: string, color: string) {
  return <span style={{ padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 600, backgroundColor: bg, color }}>{text}</span>;
}

function kpiCard(label: string, value: string, sub: string, borderColor: string) {
  return (
    <div style={{ ...cardStyle, borderTop: `3px solid ${borderColor}`, padding: 20 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.slate500, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>{value}</div>
      <div style={{ fontSize: 12, color: borderColor, fontWeight: 600, marginTop: 4 }}>{sub}</div>
    </div>
  );
}

function PhoneIcon({ size = 16, color = C.white }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" />
    </svg>
  );
}

function ChevronRight({ size = 14, color = C.gray400 }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function SearchIcon({ size = 16, color = C.gray400 }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function toDate(value: string | Date | null | undefined): Date | null {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDate(value: string | Date | null | undefined) {
  const date = toDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" }).format(date);
}

function formatDateTime(value: string | Date | null | undefined) {
  const date = toDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function daysBetweenNow(value: string | Date | null | undefined) {
  const date = toDate(value);
  if (!date) return null;
  const diff = Date.now() - date.getTime();
  return Math.max(0, Math.floor(diff / (1000 * 60 * 60 * 24)));
}

function isSameMonth(value: string | Date | null | undefined, now: Date) {
  const date = toDate(value);
  return !!date && date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
}

function average(values: number[]) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function ageFromDob(value: string | null | undefined) {
  const dob = toDate(value);
  if (!dob) return null;
  const now = new Date();
  let age = now.getFullYear() - dob.getFullYear();
  const monthDelta = now.getMonth() - dob.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && now.getDate() < dob.getDate())) {
    age -= 1;
  }
  return age >= 0 ? age : null;
}

function humanize(value: string | null | undefined) {
  const text = (value ?? "").toString().trim();
  if (!text) return "—";
  return text
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function pluralize(value: number, singular: string, plural = `${singular}s`) {
  return `${value.toLocaleString()} ${value === 1 ? singular : plural}`;
}

function countBy(items: Array<string | null | undefined>) {
  const counts = new Map<string, number>();
  items.forEach((item) => {
    const key = (item ?? "").trim();
    if (!key) return;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  });
  return [...counts.entries()]
    .sort((a, b) => (b[1] - a[1]) || a[0].localeCompare(b[0]))
    .map(([label, value]) => ({ label, value }));
}

function isActivePatient(row: CensusPatientRow) {
  const bucket = (row.census_bucket ?? "").toLowerCase();
  if (bucket) return bucket === "active";
  const patientStatus = (row.patient_status ?? "").toLowerCase();
  const admissionStatus = (row.admission_status ?? "").toLowerCase();
  return !["discharged", "deceased", "revoked"].includes(patientStatus) && !["discharged", "deceased", "revoked"].includes(admissionStatus);
}

function priorityColors(priority: string) {
  const normalized = priority.toLowerCase();
  if (normalized === "critical") return { bg: C.redLight, color: C.red };
  if (normalized === "high") return { bg: C.amberLight, color: C.amberDark };
  return { bg: C.blueLight, color: C.blue };
}

function buildViewModel(state: AnalyticsDataState): AnalyticsViewModel {
  const now = new Date();
  const censusRows = state.census?.patients ?? [];
  const activePatients = censusRows.filter(isActivePatient);
  const patientNameById = new Map(censusRows.map((row) => [row.patient_id, row.full_name]));
  const dashboardPayload = state.dashboard?.dashboard;
  const openTasks = dashboardPayload?.open_tasks ?? [];
  const openIncidents = dashboardPayload?.pending_incidents ?? [];
  const flaggedNotes = dashboardPayload?.flagged_notes ?? [];
  const blockedPatients = dashboardPayload?.blocked_patients ?? [];
  const unsignedOrders = dashboardPayload?.unsigned_orders ?? [];
  const orderRows = dashboardPayload?.all_orders ?? [];
  const alerts = state.alerts?.alerts ?? [];
  const activeStaff = state.staff ?? [];
  const staffRoleMix = countBy(activeStaff.map((member) => member.role)).slice(0, 6);
  const payerMix = countBy(activePatients.map((row) => row.payer_name)).slice(0, 5);
  const topDiagnoses = countBy(activePatients.map((row) => row.primary_diagnosis)).slice(0, 5);
  const topOrderCategories = countBy(orderRows.map((row) => row.order_category)).slice(0, 5);
  const recentAdmissions = [...censusRows]
    .filter((row) => !!toDate(row.admission_at))
    .sort((a, b) => (toDate(b.admission_at)?.getTime() ?? 0) - (toDate(a.admission_at)?.getTime() ?? 0))
    .slice(0, 6);
  const recentVisitActivity = [...activePatients]
    .filter((row) => !!toDate(row.last_visit_at))
    .sort((a, b) => (toDate(b.last_visit_at)?.getTime() ?? 0) - (toDate(a.last_visit_at)?.getTime() ?? 0))
    .slice(0, 8);
  const admissionsThisMonth = censusRows.filter((row) => isSameMonth(row.admission_at, now)).length;
  const dischargesThisMonth = censusRows.filter((row) => isSameMonth(row.discharge_date, now)).length;
  const avgDaysOnService = average(activePatients.map((row) => daysBetweenNow(row.admission_at)).filter((value): value is number => value !== null));
  const avgAge = average(activePatients.map((row) => ageFromDob(row.date_of_birth)).filter((value): value is number => value !== null));
  const medicationOrderCount = orderRows.filter((row) => /med/i.test(row.order_category ?? "") || /med/i.test(row.order_text ?? "")).length;
  const clinicalStaffCount = activeStaff.filter((member) => member.staff_type === "C").length;
  const sourceWarnings = Object.values(state.errors).filter((value): value is string => !!value);

  return {
    activePatients,
    activeStaff,
    admissionsThisMonth,
    avgAge,
    avgDaysOnService,
    blockedPatients,
    censusError: state.errors.census ?? null,
    censusRows,
    clinicalStaffCount,
    dashboardError: state.errors.dashboard ?? null,
    dischargesThisMonth,
    flaggedNotes,
    idgError: state.errors.idg ?? null,
    idgSessions: state.idgSessions ?? [],
    loading: state.loading,
    medicationOrderCount,
    openIncidents,
    openTasks,
    orderRows,
    payerMix,
    patientNameById,
    recentAdmissions,
    recentAlerts: alerts.filter((alert) => alert.status === "Open").slice(0, 6),
    recentVisitActivity,
    sourceWarnings,
    staffError: state.errors.staff ?? null,
    staffRoleMix,
    topDiagnoses,
    topOrderCategories,
    totalOrders: orderRows.length,
    unsignedOrders,
  };
}

function EmptyNotice({ title, description }: { title: string; description: string }) {
  return (
    <div style={{ ...cardStyle, border: `1px dashed ${C.gray200}`, boxShadow: "none" }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>{title}</div>
      <div style={{ marginTop: 8, fontSize: 13, color: C.slate500 }}>{description}</div>
    </div>
  );
}

function InlineInfoList({ rows }: { rows: Array<[string, string]> }) {
  return (
    <div style={cardStyle}>
      {rows.map(([label, value], index) => (
        <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, padding: "10px 0", borderBottom: index < rows.length - 1 ? `1px solid ${C.gray100}` : "none" }}>
          <span style={{ fontSize: 13, color: C.gray600 }}>{label}</span>
          <strong style={{ fontSize: 13, color: C.navy }}>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function StatusSummary({ warnings }: { warnings: string[] }) {
  if (!warnings.length) return null;
  return (
    <div style={{ ...cardStyle, padding: 16, borderLeft: `4px solid ${C.amber}`, backgroundColor: "#fffdf7" }}>
      <div style={{ fontSize: 12, fontWeight: 800, color: C.amberDark, textTransform: "uppercase", letterSpacing: 0.5 }}>Source notice</div>
      <div style={{ marginTop: 8, fontSize: 13, color: C.gray600 }}>
        Some widgets are showing “not available yet” because one or more live data sources could not be loaded for this user.
      </div>
    </div>
  );
}

function TableSection({
  title,
  headers,
  rows,
  emptyMessage,
}: {
  title: string;
  headers: string[];
  rows: Array<Array<ReactNode>>;
  emptyMessage: string;
}) {
  return (
    <div style={cardStyle}>
      <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>{title}</div>
      <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
        <thead>
          <tr>{headers.map((header) => <th key={header} style={thStyle}>{header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.length ? rows.map((row, rowIndex) => (
            <tr key={`${title}-${rowIndex}`} style={{ borderBottom: `1px solid ${C.gray100}` }}>
              {row.map((cell, cellIndex) => <td key={cellIndex} style={tdStyle}>{cell}</td>)}
            </tr>
          )) : (
            <tr>
              <td colSpan={headers.length} style={{ ...tdStyle, color: C.slate500 }}>{emptyMessage}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function MetricListCard({ title, items }: { title: string; items: Array<{ label: string; value: number }> }) {
  return (
    <div style={cardStyle}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800, marginBottom: 16 }}>{title}</div>
      {items.length ? items.map((item, index) => (
        <div key={item.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: index < items.length - 1 ? `1px solid ${C.gray100}` : "none" }}>
          <span style={{ fontSize: 13, color: C.gray600 }}>{item.label}</span>
          <strong style={{ color: C.navy }}>{item.value.toLocaleString()}</strong>
        </div>
      )) : <div style={{ fontSize: 13, color: C.slate500 }}>No live rows available.</div>}
    </div>
  );
}

function SubNav({ tabs, activeTab, onTabChange }: { tabs: string[]; activeTab: string; onTabChange: (tab: string) => void }) {
  return (
    <div style={{ padding: "12px 24px", display: "flex", flexWrap: "wrap", gap: 6 }}>
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab)}
          style={{
            padding: "6px 14px",
            borderRadius: 20,
            border: `1px solid ${activeTab === tab ? C.teal : C.slate200}`,
            backgroundColor: activeTab === tab ? C.teal : C.white,
            color: activeTab === tab ? C.white : C.gray600,
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "'Inter', sans-serif",
            whiteSpace: "nowrap",
          }}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

export function Navbar() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const displayName = currentUser?.full_name ?? "Signed-in User";
  const displayRole = currentUser?.role === "ADMINISTRATOR" ? "Administrator" : currentUser?.role ?? "Clinical Staff";
  const initials = (displayName.match(/\b\w/g) ?? []).slice(0, 2).join("").toUpperCase() || "SU";
  const mainTabs = ["Dashboard", "Census", "Secure Inbox", "Clinical Alerts", "Scheduling", "Analytics", "Settings", "My Profile"];
  const routes: Record<string, string> = {
    Dashboard: "/portal",
    Census: "/tenant",
    "Secure Inbox": "/secure-inbox",
    "Clinical Alerts": "/clinical-alerts",
    Scheduling: "/volunteer-scheduling",
    Analytics: "/analytics",
    Settings: "/owner",
    "My Profile": "/my-profile",
  };
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 16, backgroundColor: C.navy, padding: "12px 24px", minHeight: 80, boxSizing: "border-box" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <img
            src="/brand/sns-logo-light.svg"
            alt="SNS logo"
            onError={(event) => {
              const target = event.currentTarget as HTMLImageElement;
              if (!target.src.endsWith("/brand/sns-logo-icon.svg")) {
                target.src = "/brand/sns-logo-icon.svg";
              }
            }}
            style={{ width: 170, height: "auto", display: "block" }}
          />
        </div>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {mainTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => navigate(routes[tab])}
              style={{
                padding: "8px 12px",
                borderRadius: 4,
                border: "none",
                backgroundColor: tab === "Analytics" ? C.teal : "transparent",
                color: C.white,
                fontSize: 13,
                fontWeight: tab === "Analytics" ? 700 : 600,
                fontFamily: "'Inter', sans-serif",
                cursor: "pointer",
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginLeft: "auto" }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.white }}>{displayName}</div>
          <div style={{ fontSize: 11, color: C.gray400 }}>{displayRole}</div>
        </div>
        <div style={{ width: 38, height: 38, borderRadius: 99, backgroundColor: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: 13, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.white }}>{initials}</span>
        </div>
      </div>
    </div>
  );
}

export function WelcomeBanner({ title, syncedLabel }: { title: string; syncedLabel: string }) {
  const workspaceName = getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services";
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, backgroundColor: C.white, padding: "24px 24px", borderBottom: `1px solid ${C.gray200}` }}>
      <div>
        <h1 style={{ fontSize: 24, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, margin: "0 0 6px" }}>{title}</h1>
        <div style={{ fontSize: 14, color: C.slate500 }}>
          Active Agency Workspace:{" "}
          <span style={{ padding: "4px 12px", borderRadius: 99, fontSize: 12, fontWeight: 600, backgroundColor: C.tealLight, color: C.tealDark }}>
            {workspaceName}
          </span>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: C.gray400 }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={C.gray400} strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        Last loaded: {syncedLabel}
      </div>
    </div>
  );
}

export function Footer() {
  return (
    <div style={{ marginTop: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 16, backgroundColor: C.navy, padding: "18px 24px", minHeight: 65, boxSizing: "border-box" }}>
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", rowGap: 8 }}>
          {["Patient Care Hub", "Clinical Charting Validation", "Compliance Alerts & Logs", "Quality & QIES Reports", "Billing & HIS Tools"].map((t) => (
            <span key={t} style={{ fontSize: 14, fontWeight: 500, fontFamily: "'Inter', sans-serif", color: C.white, cursor: "pointer", whiteSpace: "nowrap" }}>
              {t}
            </span>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginLeft: "auto" }}>
          <PhoneIcon />
          <span style={{ fontSize: 14, fontWeight: 600, fontFamily: "'Inter', sans-serif", color: C.white }}>Secure Support: 1-800-555-0199</span>
        </div>
      </div>
      <div style={{ backgroundColor: C.gray900, padding: "20px 24px", textAlign: "center" }}>
        <div style={{ fontSize: 13, fontWeight: 400, fontFamily: "'Inter', sans-serif", color: C.gray400, marginBottom: 8 }}>
          Secure Portal | All Rights Reserved
        </div>
        <div style={{ fontSize: 11, fontWeight: 400, fontFamily: "'Inter', sans-serif", color: C.gray500 }}>
          Unauthorized access to this EMR dashboard is strictly prohibited. Activity is logged and monitored in compliance with federal healthcare data safety laws (HIPAA/HITECH).
        </div>
      </div>
    </div>
  );
}

function ReportsDirectory({
  onOpenSection,
  onOpenReport,
}: {
  onOpenSection: (domain: string) => void;
  onOpenReport: (report: string | null) => void;
}) {
  const [search, setSearch] = useState("");
  const [selectedReport, setSelectedReport] = useState<{ title: string; column: string } | null>(null);
  const sectionForColumn: Record<string, string> = {
    "Clinical Operations": "Clinical",
    "Quality & Compliance": "Analytics Directory",
    "Operations & Workforce": "Analytics Directory",
    "Scheduling & Staff": "Analytics Directory",
    "Billing & Revenue": "Analytics Directory",
    "QAPI & Compliance": "Analytics Directory",
    "Financial & Billing": "Analytics Directory",
  };

  const columns = [
    {
      title: "Clinical Operations",
      subtitle: "VISITS, COMPLIANCE, AND PATIENT CARE PLAN",
      color: C.teal,
      groups: [
        { name: "VISIT MANAGEMENT", items: ["All Visits Report", "Missed Visits Report", "Supervisory Visit Review", "On-Call Log"] },
        { name: "COMPLIANCE & DOCUMENTATION", items: ["Missing Consents", "SIA Patients/Visits", "Submission Log", "Pending Prescription"] },
        { name: "REFERENCE REPORTS", items: ["Commonly Used ICD-10 Codes", "Commonly Used Medications"] },
        { name: "BEREAVEMENT MANAGEMENT", items: ["Bereavement Calendar", "Bereavement Risk Assessment", "Late Tracking", "Bereavement Letter Template", "Bereavement Header/Footer"] },
        { name: "RECERTIFICATION", items: ["Re-Cert List with Dates", "F2F Scheduling", "Re-Cert List"] },
        { name: "IDG", items: ["IDG Management", "Create IDG Notes/Groups", "IDG Meetings"] },
        { name: "QUALITY ASSURANCE", items: ["Quality Assurance", "Notes To Review", "Late Submission Tracking"] },
      ],
    },
    {
      title: "Scheduling & Staff",
      subtitle: "VISIT SCHEDULING, COVERAGE, AND STAFFING OPERATIONS",
      color: C.amber,
      groups: [
        { name: "SCHEDULING", items: ["Visit Schedule", "Coverage Matrix", "Holiday Coverage", "Scheduling Summary", "Caseload Assignment"] },
        { name: "WORKFORCE", items: ["Staff Utilization/Productivity", "Employee Contact List", "Human Resource", "Staff Productivity Dashboard"] },
      ],
    },
    {
      title: "QAPI & Compliance",
      subtitle: "QUALITY, INCIDENT, COMPLIANCE, AND PERFORMANCE IMPROVEMENT",
      color: C.blue,
      groups: [
        { name: "QUALITY MEASURES", items: ["Comfortable Dying Measure", "Unwanted Hospitalization", "Infection Control", "Census Integrity Report", "Incident Rate"] },
        { name: "HOPE / HIS / HQRP", items: ["HOPE/HIS Submissions", "HQRP Quality Reporting", "Export CAHPS"] },
        { name: "COMPLIANCE TRACKING", items: ["Compliance Review", "Late Submission Tracking", "QA Management Dashboard", "Notes To Review", "Incident Review"] },
        { name: "CLINICAL TRACKING", items: ["Wound Tracking Report", "Antibiotics w/o Care Plan", "eMAR Report", "Patient Acuity Report"] },
      ],
    },
    {
      title: "Operations & Workforce",
      subtitle: "CENSUS, SERVICE OPERATIONS, ORDERS, GEO/CONTACT, AND HR",
      color: C.amber,
      groups: [
        { name: "CENSUS & DEMOGRAPHICS", items: ["ADC/ALOS/MLOS Report", "Age & Gender Demographics", "Patient Profile Report", "Diagnosis/Disease Report", "Admissions", "Discharge Trend"] },
        { name: "SERVICE OPERATIONS", items: ["Visits By Discipline", "Place of Service Report", "Level of Care Report", "Daily Summary", "Emergency Triage", "Patient Referral Source", "Print Patient Chart"] },
        { name: "ORDERS & PRESCRIPTIONS", items: ["Medication/DME Orders", "Signed Physician Orders", "Outbound Fax"] },
        { name: "GEOGRAPHIC & CONTACT", items: ["Patients by Zip/City/County", "Census Heatmap", "Patient Birthday Report", "NPI Lookup", "Employee Contact List"] },
        { name: "HR & VENDOR", items: ["Human Resource", "Vendor Management", "Payer Source Report", "Agency Announcements Hx", "HospiceMD Announcements Hx", "Outbound Fax", "Standard Pack"] },
      ],
    },
    {
      title: "Billing & Revenue",
      subtitle: "BILLING, CLAIMS, REVENUE, AND WORKSHEETS",
      color: C.green,
      groups: [
        { name: "BILLING & CLAIMS", items: ["Claims Dashboard", "RA Reconciliation", "NOE/NOTR Management", "Monthly Billing Summary", "Billing Summary Report"] },
        { name: "REVENUE & AGING", items: ["Revenue Report", "Aging Report", "Unbilled Revenue", "Submission & Collection", "Patient Billing Lookup"] },
        { name: "COLLECTIONS & FOLLOW-UP", items: ["Agency Follow-Up", "Uncollected/Unbilled Claims", "Credit Balance Report", "Collection Dashboard"] },
      ],
    },
    {
      title: "Financial & Billing",
      subtitle: "BILLING, CLAIMS, REVENUE, AND WORKSHEETS",
      color: C.green,
      groups: [
        { name: "BILLING & CLAIMS", items: ["Claims Dashboard", "RA Reconciliation", "NOE/NOTR Management", "Monthly Billing Summary"] },
        { name: "REVENUE & AGING", items: ["Revenue Report", "Aging Report", "Unbilled Revenue", "Submission & Collection"] },
        { name: "COLLECTIONS & FOLLOW-UP", items: ["Agency Follow-Up", "Patient Billing Lookup", "Uncollected/Unbilled Claims", "Credit Balance Report"] },
        { name: "COST ANALYSIS", items: ["Cost Per Patient", "Direct Patient Care Cost", "CAP Calculation"] },
        { name: "WORKSHEETS", items: ["Billing Issues Report", "Worksheet 1 - Part I", "Worksheet 1 - Part II"] },
      ],
    },
  ];

  const visibleColumns = canAccessBilling() ? columns : columns.filter((col) => col.title !== "Financial & Billing");
  const filteredColumns = columns.map((col) => ({
    ...col,
    groups: col.groups
      .map((group) => ({ ...group, items: group.items.filter((item) => item.toLowerCase().includes(search.toLowerCase())) }))
      .filter((group) => group.items.length > 0),
  }));

  const selectedDomain = selectedReport ? sectionForColumn[selectedReport.column] : null;
  const selectedGroup = selectedReport
    ? filteredColumns
        .find((column) => column.title === selectedReport.column)
        ?.groups.find((group) => group.items.includes(selectedReport.title)) || null
    : null;

  return (
    <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ position: "relative", maxWidth: 480 }}>
        <div style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)" }}>
          <SearchIcon />
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search or filter analytics directory..."
          style={{ width: "100%", padding: "10px 14px 10px 40px", borderRadius: 8, border: `1px solid ${C.gray200}`, fontSize: 13, fontFamily: "'Inter', sans-serif", color: C.gray800, outline: "none", boxSizing: "border-box" }}
        />
      </div>

      <div style={responsiveFourGrid}>
        {visibleColumns.map((col) => {
          const filtered = filteredColumns.find((item) => item.title === col.title);
          if (!filtered) return null;
          return (
            <div key={col.title} style={{ backgroundColor: C.white, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", overflow: "hidden" }}>
              <div style={{ borderTop: `4px solid ${col.color}`, padding: "16px 20px 12px" }}>
                <div style={{ fontSize: 15, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800 }}>{col.title}</div>
                <div style={{ fontSize: 10, fontWeight: 600, color: C.slate500, textTransform: "uppercase", letterSpacing: 0.5, marginTop: 2 }}>{col.subtitle}</div>
              </div>
              <div style={{ padding: "0 20px 20px" }}>
                {filtered.groups.map((group, gi) => (
                  <div key={group.name} style={{ marginTop: gi > 0 ? 16 : 8 }}>
                    <div style={{ fontSize: 10, fontWeight: 800, color: col.color, textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 6 }}>{group.name}</div>
                    {group.items.map((item) => (
                      <div
                        key={item}
                        onClick={() => {
                          setSelectedReport({ title: item, column: col.title });
                          onOpenReport(item);
                          onOpenSection(sectionForColumn[col.title] ?? "Reports Directory");
                        }}
                        style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "7px 0", cursor: "pointer", borderBottom: `1px solid ${C.gray100}` }}
                      >
                        <span style={{ fontSize: 13, color: C.gray600, fontWeight: 400 }}>{item}</span>
                        <ChevronRight />
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {selectedReport ? (
        <div style={{ backgroundColor: C.white, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 800, color: C.slate500, textTransform: "uppercase", letterSpacing: 0.8 }}>Selected report</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: C.gray800, marginTop: 6 }}>{selectedReport.title}</div>
              <div style={{ fontSize: 13, color: C.slate500, marginTop: 6 }}>
                Section: <strong style={{ color: C.gray800 }}>{selectedDomain}</strong>
                {selectedGroup ? ` · Group: ${selectedGroup.name}` : ""}
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
              <button
                onClick={() => {
                  onOpenSection(selectedDomain || "Reports Directory");
                }}
                style={{
                  padding: "8px 12px",
                  borderRadius: 8,
                  border: "none",
                  backgroundColor: C.teal,
                  color: C.white,
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Open full section
              </button>
              <button
                onClick={() => {
                  setSelectedReport(null);
                  onOpenReport(null);
                }}
                style={{
                  padding: "8px 12px",
                  borderRadius: 8,
                  border: `1px solid ${C.slate200}`,
                  backgroundColor: C.white,
                  color: C.gray600,
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Clear selection
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
            {[
              ["Directory Status", "Navigation only"],
              ["Source Section", selectedDomain || "—"],
              ["Structured Report", "Not available yet"],
              ["Action", "Open section"],
            ].map(([label, value]) => (
              <div key={label} style={{ border: `1px solid ${C.gray200}`, borderRadius: 10, padding: 14, backgroundColor: "#fafcff" }}>
                <div style={{ fontSize: 11, fontWeight: 800, color: C.slate500, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
                <div style={{ marginTop: 6, fontSize: 14, fontWeight: 700, color: C.gray800 }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function CommandCenter({ analytics, onNavigate }: { analytics: AnalyticsViewModel; onNavigate: (domain: string) => void }) {
  return (
    <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
      <StatusSummary warnings={analytics.sourceWarnings} />
      <div style={responsiveThreeGrid}>
        <div onClick={() => onNavigate("Clinical")} style={{ ...cardStyle, borderTop: `3px solid ${C.teal}`, cursor: "pointer", padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.gray800, marginBottom: 8 }}>Clinical</div>
          <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>{pluralize(analytics.activePatients.length, "active patient")}</div>
          <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>Live census rows from /audit-dashboard/census.</div>
        </div>
        <div onClick={() => onNavigate("QAPI")} style={{ ...cardStyle, borderTop: `3px solid ${C.blue}`, cursor: "pointer", padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.gray800, marginBottom: 8 }}>QAPI</div>
          <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>{pluralize(analytics.openIncidents.length, "open incident")}</div>
          <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>Live incident and alert counts from /api/dashboard/tenant and /api/dashboard/clinical-alerts.</div>
        </div>
        <div onClick={() => onNavigate("Administrative")} style={{ ...cardStyle, borderTop: `3px solid ${C.amber}`, cursor: "pointer", padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.gray800, marginBottom: 8 }}>Administrative</div>
          <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>{pluralize(analytics.activeStaff.length, "active staff member")}</div>
          <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>Live staff roster rows from /staff.</div>
        </div>
      </div>
      <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800 }}>Cross-Domain Insights</div>
      <div style={responsiveTwoGrid}>
        <InlineInfoList
          rows={[
            ["Open workflow tasks", analytics.openTasks.length.toLocaleString()],
            ["Open clinical alerts", analytics.recentAlerts.length.toLocaleString()],
            ["Orders awaiting signature", analytics.unsignedOrders.length.toLocaleString()],
            ["IDG sessions on file", analytics.idgSessions.length.toLocaleString()],
          ]}
        />
        <div style={cardStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <span style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800 }}>Key Performance Alerts</span>
            <span style={{ fontSize: 12, color: C.slate500 }}>{pluralize(analytics.recentAlerts.length, "open alert")}</span>
          </div>
          {analytics.recentAlerts.length ? analytics.recentAlerts.slice(0, 5).map((alert, index) => {
            const colors = priorityColors(alert.priority);
            return (
              <div key={alert.alert_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: index < Math.min(analytics.recentAlerts.length, 5) - 1 ? `1px solid ${C.gray100}` : "none" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: C.gray600 }}>{alert.description}</div>
                  <div style={{ fontSize: 11, color: C.slate500, marginTop: 4 }}>{alert.patient_name} • {formatDateTime(alert.generated)}</div>
                </div>
                {badge(alert.priority, colors.bg, colors.color)}
              </div>
            );
          }) : (
            <div style={{ fontSize: 13, color: C.slate500 }}>No live alerts are open for this workspace.</div>
          )}
        </div>
      </div>
      <EmptyNotice title="Composite scores are not available yet" description="This page no longer shows fabricated cross-domain health percentages or QAPI scorecards. Only live queue, census, alert, and roster counts are shown." />
    </div>
  );
}

function ClinicalTab({ analytics }: { analytics: AnalyticsViewModel }) {
  const [activeTab, setActiveTab] = useState("Overview");
  const tabs = ["Overview", "Visit Management", "Compliance & Documentation", "Recertification Tracker", "Clinical Reference", "Bereavement Tracking"];

  const overviewRows = analytics.activePatients.slice(0, 8).map((row) => ([
    <strong key={`${row.patient_id}-name`} style={{ color: C.gray800 }}>{row.full_name}</strong>,
    row.mrn || "—",
    formatDate(row.admission_at),
    humanize(row.admission_status || row.patient_status),
    row.primary_diagnosis || "—",
    row.payer_name || "—",
    daysBetweenNow(row.admission_at) !== null ? `${daysBetweenNow(row.admission_at)} days` : "—",
  ]));

  if (activeTab === "Visit Management") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <TableSection
          title="Recent Patient Visit Activity"
          headers={["Patient", "MRN", "Last Visit", "Last Visiting Clinician", "Payer", "Status"]}
          rows={analytics.recentVisitActivity.map((row) => ([
            <strong key={`${row.patient_id}-patient`} style={{ color: C.gray800 }}>{row.full_name}</strong>,
            row.mrn || "—",
            formatDateTime(row.last_visit_at),
            row.attending_physician || "—",
            row.payer_name || "—",
            humanize(row.census_bucket),
          ]))}
          emptyMessage={analytics.censusError ? "Unable to load live census activity." : "No recent visit timestamps are available in the live census feed."}
        />
      </div>
    );
  }

  if (activeTab === "Compliance & Documentation") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <TableSection
          title="Open Clinical Workflow Queue"
          headers={["Task Type", "Patient", "Status", "Due", "Linked Record"]}
          rows={analytics.openTasks.map((task) => ([
            humanize(task.task_type),
            analytics.patientNameById.get(task.patient_id) ?? task.patient_id,
            badge(humanize(task.status), C.amberLight, C.amberDark),
            task.due_at ? formatDateTime(task.due_at) : task.due_date ? formatDate(task.due_date) : "—",
            task.clinical_note_id ?? task.incident_id ?? "—",
          ]))}
          emptyMessage={analytics.dashboardError ? "Unable to load the live compliance queue." : "No live compliance tasks are currently open."}
        />
      </div>
    );
  }

  if (activeTab === "Recertification Tracker") {
    return (
      <div style={{ padding: "24px 24px 40px" }}>
        <EmptyNotice title="Structured recertification tracker is not available yet" description="Patient-level physician and compliance records exist, but this page does not have a tenant-wide recertification aggregate endpoint yet, so the old fabricated due-date table has been removed." />
      </div>
    );
  }

  if (activeTab === "Clinical Reference") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <MetricListCard title="Top Diagnoses in Active Census" items={analytics.topDiagnoses} />
        <MetricListCard title="Physician Order Categories" items={analytics.topOrderCategories} />
      </div>
    );
  }

  if (activeTab === "Bereavement Tracking") {
    return (
      <div style={{ padding: "24px 24px 40px" }}>
        <EmptyNotice title="Tenant-wide bereavement reporting is not available yet" description="The backend currently exposes bereavement aggregation per patient chart, not as a tenant-wide analytics report, so the fabricated bereavement names and risk rows were removed." />
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
      <SubNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={responsiveFourGrid}>
        {kpiCard("ACTIVE CENSUS", pluralize(analytics.activePatients.length, "patient"), analytics.censusError ? "Live census unavailable" : "Live rows from tenant census", C.teal)}
        {kpiCard("OPEN WORKFLOW TASKS", pluralize(analytics.openTasks.length, "task"), "Live compliance queue", C.blue)}
        {kpiCard("OPEN INCIDENTS", pluralize(analytics.openIncidents.length, "incident"), "Pending incident review", C.amber)}
        {kpiCard("UNSIGNED ORDERS", pluralize(analytics.unsignedOrders.length, "order"), "Awaiting signature", C.green)}
      </div>
      <TableSection title="Patient Census Summary" headers={["Patient", "MRN", "Admission Date", "Current Status", "Primary Dx", "Payer", "Days on Service"]} rows={overviewRows} emptyMessage={analytics.censusError ? "Unable to load live census rows." : "No active patients are available."} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <EmptyNotice title="Recertification alert queue is not available yet" description="The old patient-specific due dates and physician names were fabricated. This card stays empty until a real tenant-level recertification feed is exposed." />
        <TableSection
          title="IDG Meeting Schedule"
          headers={["Meeting Date", "Patient Count", "Status"]}
          rows={analytics.idgSessions.slice(0, 6).map((session) => ([formatDateTime(session.meeting_date), session.patient_count.toLocaleString(), badge("Live session", C.greenLight, C.greenDark)]))}
          emptyMessage={analytics.idgError ? "Unable to load IDG sessions for this user." : "No IDG sessions are scheduled yet."}
        />
      </div>
    </div>
  );
}

function QAPITab({ analytics }: { analytics: AnalyticsViewModel }) {
  const [activeTab, setActiveTab] = useState("Overview");
  const tabs = ["Overview", "Quality Measures", "HOPE/HIS Tracking", "Clinical Tracking", "Staff & Resources"];

  if (activeTab === "Quality Measures") {
    return (
      <div style={{ padding: "24px 24px 40px" }}>
        <EmptyNotice title="Structured quality-measure scoring is not available yet" description="No real tenant-level endpoint currently provides comfortable-dying, hospitalization, infection-control, or census-integrity percentages for this page, so the fabricated percentages were removed." />
      </div>
    );
  }

  if (activeTab === "HOPE/HIS Tracking") {
    return (
      <div style={{ padding: "24px 24px 40px" }}>
        <EmptyNotice title="Tenant-wide HOPE/HIS reporting is not available yet" description="Patient-level HOPE and compliance records exist in chart workflows, but this analytics page does not yet have a real tenant-wide submission tracker endpoint." />
      </div>
    );
  }

  if (activeTab === "Clinical Tracking") {
    return (
      <div style={{ padding: "24px 24px 40px" }}>
        <TableSection
          title="Documentation Flags Requiring Review"
          headers={["Patient", "Discipline", "Visit Type", "Red Flags", "Needs Clarification"]}
          rows={analytics.flaggedNotes.map((note) => ([
            analytics.patientNameById.get(note.patient_id) ?? note.patient_id,
            humanize(note.discipline),
            humanize(note.visit_type),
            note.red_flags.length ? note.red_flags.join(", ") : "—",
            note.needs_clarification.length ? note.needs_clarification.join(", ") : "—",
          ]))}
          emptyMessage={analytics.dashboardError ? "Unable to load live note flags." : "No live note flags are currently open."}
        />
      </div>
    );
  }

  if (activeTab === "Staff & Resources") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("ACTIVE STAFF", pluralize(analytics.activeStaff.length, "person"), "Live roster count", C.teal)}
          {kpiCard("CLINICAL STAFF", pluralize(analytics.clinicalStaffCount, "person"), "staff_type = C", C.blue)}
          {kpiCard("ROLE TYPES", analytics.staffRoleMix.length.toLocaleString(), "Distinct active roles", C.amber)}
          {kpiCard("OPEN ALERTS", pluralize(analytics.recentAlerts.length, "alert"), "Live alert queue", C.green)}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <MetricListCard title="Active Staff by Role" items={analytics.staffRoleMix} />
          <EmptyNotice title="Utilization and productivity metrics are not available yet" description="The old staff utilization percentages, volunteer hours, and overtime rows were fabricated. The live staff roster exists, but no real productivity/utilization aggregate model backs those metrics yet." />
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 24px 40px" }}>
      <SubNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={{ ...responsiveFourGrid, padding: "0 0 24px" }}>
        {kpiCard("OPEN ALERTS", pluralize(analytics.recentAlerts.length, "alert"), "Clinical alerts feed", C.teal)}
        {kpiCard("OPEN INCIDENTS", pluralize(analytics.openIncidents.length, "incident"), "Pending incident review", C.red)}
        {kpiCard("FLAGGED NOTES", pluralize(analytics.flaggedNotes.length, "note"), "Validation review queue", C.blue)}
        {kpiCard("IDG BLOCKERS", pluralize(analytics.blockedPatients.length, "patient"), "Readiness blockers", C.amber)}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1fr", gap: 20 }}>
        <TableSection
          title="Recent Incident Reports"
          headers={["Type", "Patient", "Incident Date", "Severity"]}
          rows={analytics.openIncidents.slice(0, 8).map((incident) => ([
            humanize(incident.incident_type),
            analytics.patientNameById.get(incident.patient_id) ?? incident.patient_id,
            formatDate(incident.incident_date),
            badge(humanize(incident.incident_severity), ...(incident.incident_severity || "").toLowerCase() === "high" ? [C.redLight, C.red] : [C.amberLight, C.amberDark]),
          ]))}
          emptyMessage={analytics.dashboardError ? "Unable to load live incident rows." : "No pending incidents are currently open."}
        />
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Live Alert Queue</div>
          {analytics.recentAlerts.length ? analytics.recentAlerts.map((alert, index) => {
            const colors = priorityColors(alert.priority);
            return (
              <div key={alert.alert_id} style={{ padding: "12px 0", borderBottom: index < analytics.recentAlerts.length - 1 ? `1px solid ${C.gray100}` : "none" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.gray800 }}>{alert.alert_type}</div>
                  {badge(alert.priority, colors.bg, colors.color)}
                </div>
                <div style={{ fontSize: 12, color: C.slate500, marginTop: 6 }}>{alert.patient_name} • {alert.description}</div>
              </div>
            );
          }) : <div style={{ fontSize: 13, color: C.slate500 }}>No live alerts are open.</div>}
        </div>
      </div>
      <div style={{ marginTop: 20 }}>
        <EmptyNotice title="Survey scores and PIP progress are not available yet" description="This page no longer shows fabricated CAHPS ratings or project progress percentages. Real incident, alert, and documentation-review queues are shown above instead." />
      </div>
    </div>
  );
}

function AdministrativeTab({ analytics }: { analytics: AnalyticsViewModel }) {
  const [activeTab, setActiveTab] = useState("Overview");
  const tabs = ["Overview", "Census & Demographics", "Service Operations", "Orders & Rx", "Staffing & HR"];

  if (activeTab === "Census & Demographics") {
    const topPayer = analytics.payerMix[0];
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("ACTIVE CENSUS", pluralize(analytics.activePatients.length, "patient"), "Live census feed", C.teal)}
          {kpiCard("AVERAGE AGE", analytics.avgAge !== null ? `${analytics.avgAge.toFixed(1)} yrs` : "—", analytics.avgAge !== null ? "Calculated from DOB on live census" : "DOB not available", C.blue)}
          {kpiCard("AVG DAYS ON SERVICE", analytics.avgDaysOnService !== null ? `${analytics.avgDaysOnService.toFixed(1)} days` : "—", analytics.avgDaysOnService !== null ? "Calculated from admission dates" : "Admission dates not available", C.amber)}
          {kpiCard("TOP PAYER", topPayer ? topPayer.label : "—", topPayer ? `${topPayer.value.toLocaleString()} active patients` : "No payer data available", C.green)}
        </div>
        <TableSection
          title="Active Patient Demographics"
          headers={["Patient", "MRN", "DOB / Age", "Primary Dx", "Payer", "Days on Service"]}
          rows={analytics.activePatients.slice(0, 10).map((row) => ([
            <strong key={`${row.patient_id}-full-name`} style={{ color: C.gray800 }}>{row.full_name}</strong>,
            row.mrn || "—",
            `${formatDate(row.date_of_birth)}${ageFromDob(row.date_of_birth) !== null ? ` / ${ageFromDob(row.date_of_birth)} yrs` : ""}`,
            row.primary_diagnosis || "—",
            row.payer_name || "—",
            daysBetweenNow(row.admission_at) !== null ? `${daysBetweenNow(row.admission_at)} days` : "—",
          ]))}
          emptyMessage={analytics.censusError ? "Unable to load live census demographics." : "No active patients are available."}
        />
      </div>
    );
  }

  if (activeTab === "Service Operations") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <TableSection
          title="Recent Service Activity"
          headers={["Patient", "MRN", "Last Visit", "Last Visiting Clinician", "Current Bucket"]}
          rows={analytics.recentVisitActivity.map((row) => ([
            row.full_name,
            row.mrn || "—",
            formatDateTime(row.last_visit_at),
            row.attending_physician || "—",
            humanize(row.census_bucket),
          ]))}
          emptyMessage={analytics.censusError ? "Unable to load live service activity." : "No recent visit activity is available."}
        />
        <EmptyNotice title="Place-of-service and discipline breakdowns are not available yet" description="The old visit totals, discipline percentages, and place-of-service percentages were fabricated. The live census feed only exposes each patient's most recent visit timestamp, which is shown above." />
      </div>
    );
  }

  if (activeTab === "Orders & Rx") {
    const dmeOrders = analytics.orderRows.filter((row) => /dme|equipment/i.test(row.order_category ?? "") || /dme|bed|walker|wheelchair|oxygen/i.test(row.order_text ?? ""));
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("TRACKED ORDERS", pluralize(analytics.totalOrders, "order"), "Live physician order feed", C.teal)}
          {kpiCard("MEDICATION ORDERS", pluralize(analytics.medicationOrderCount, "order"), "Category/text contains medication terms", C.blue)}
          {kpiCard("DME-RELATED ORDERS", pluralize(dmeOrders.length, "order"), "Detected from live order categories/text", C.green)}
          {kpiCard("PENDING SIGNATURES", pluralize(analytics.unsignedOrders.length, "order"), "Awaiting provider signature", C.amber)}
        </div>
        <TableSection
          title="Medication & DME Orders Summary"
          headers={["Ordered", "Patient", "Category", "Description", "Ordered By", "Status"]}
          rows={analytics.orderRows.slice(0, 10).map((row) => ([
            formatDateTime(row.ordered_at),
            row.patient_name,
            badge(humanize(row.order_category), C.tealLight, C.tealDark),
            row.order_text || "—",
            `${row.ordered_by_provider_name || "—"}${row.ordered_by_provider_role ? ` (${humanize(row.ordered_by_provider_role)})` : ""}`,
            badge(row.signed_at ? "Signed" : humanize(row.status), row.signed_at ? C.greenLight : C.amberLight, row.signed_at ? C.greenDark : C.amberDark),
          ]))}
          emptyMessage={analytics.dashboardError ? "Unable to load live physician orders." : "No physician orders are currently available."}
        />
      </div>
    );
  }

  if (activeTab === "Staffing & HR") {
    const adminCount = analytics.activeStaff.filter((member) => member.staff_type === "A").length;
    const contractedCount = analytics.activeStaff.filter((member) => member.staff_type === "X" || member.staff_type === "Y").length;
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("ACTIVE STAFF", pluralize(analytics.activeStaff.length, "person"), "Live roster feed", C.teal)}
          {kpiCard("CLINICAL STAFF", pluralize(analytics.clinicalStaffCount, "person"), "staff_type = C", C.blue)}
          {kpiCard("ADMINISTRATIVE STAFF", pluralize(adminCount, "person"), "staff_type = A", C.amber)}
          {kpiCard("CONTRACT / REFERRAL", pluralize(contractedCount, "person"), "staff_type = X or Y", C.green)}
        </div>
        <TableSection
          title="Active Staff Roster"
          headers={["Staff", "Role", "Job Title", "Discipline", "Email"]}
          rows={analytics.activeStaff.slice(0, 10).map((member) => ([
            <strong key={`${member.id}-staff`} style={{ color: C.gray800 }}>{member.full_name}</strong>,
            humanize(member.role),
            member.job_title || "—",
            member.discipline || "—",
            member.email,
          ]))}
          emptyMessage={analytics.staffError ? "Unable to load the live staff roster." : "No active staff rows are available."}
        />
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 24px 40px" }}>
      <SubNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={responsiveFourGrid}>
        {kpiCard("ACTIVE CENSUS", pluralize(analytics.activePatients.length, "patient"), "Live census feed", C.teal)}
        {kpiCard("ADMISSIONS (MTD)", pluralize(analytics.admissionsThisMonth, "admission"), "Derived from live admission dates", C.green)}
        {kpiCard("DISCHARGES (MTD)", pluralize(analytics.dischargesThisMonth, "discharge"), "Derived from live discharge dates", C.amber)}
        {kpiCard("ACTIVE STAFF", pluralize(analytics.activeStaff.length, "staff member"), "Live staff roster", C.blue)}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <TableSection
          title="Recent Admissions"
          headers={["Patient", "MRN", "Admit Date", "Status", "Payer"]}
          rows={analytics.recentAdmissions.map((row) => ([
            row.full_name,
            row.mrn || "—",
            formatDate(row.admission_at),
            badge(humanize(row.admission_status || row.patient_status), C.blueLight, C.blue),
            row.payer_name || "—",
          ]))}
          emptyMessage={analytics.censusError ? "Unable to load live admissions data." : "No admissions are available in the current census feed."}
        />
        <InlineInfoList
          rows={[
            ["Pending physician orders", analytics.unsignedOrders.length.toLocaleString()],
            ["Open workflow tasks", analytics.openTasks.length.toLocaleString()],
            ["Open incident reviews", analytics.openIncidents.length.toLocaleString()],
            ["Flagged note reviews", analytics.flaggedNotes.length.toLocaleString()],
          ]}
        />
      </div>
    </div>
  );
}

function FinancialTab() {
  if (!canAccessBilling()) {
    return (
      <div style={{ padding: "24px 24px 40px" }}>
        <div style={cardStyle}>
          <strong>Billing features are not enabled for this tenant.</strong>
        </div>
      </div>
    );
  }

  return <TenantBillingOutcomes />;
}

export default function SNSAnalytics({ defaultDomain = "Analytics Directory" }: { defaultDomain?: string }) {
  const [searchParams] = useSearchParams();
  const section = searchParams.get("section");
  const [activeDomain, setActiveDomain] = useState(() => resolveDomainFromSection(section, defaultDomain));
  const [activeReport, setActiveReport] = useState<string | null>(null);
  const currentUser = getCurrentUser();
  const workspaceName = currentUser?.tenant_name ?? "Love & Faith Hospice Services";
  const [dataState, setDataState] = useState<AnalyticsDataState>({
    alerts: null,
    census: null,
    dashboard: null,
    errors: {},
    idgSessions: null,
    loading: true,
    staff: null,
  });

  useEffect(() => {
    let mounted = true;

    setDataState((previous) => ({ ...previous, loading: true, errors: {} }));

    Promise.allSettled([
      fetchCensusWorkspace(),
      fetchTenantDashboard(),
      fetchClinicalAlerts(),
      listStaff({ status: "active" }),
      listIdgSessions(),
    ]).then((results) => {
      if (!mounted) return;
      const [censusResult, dashboardResult, alertsResult, staffResult, idgResult] = results;
      const errors: SourceErrors = {};
      if (censusResult.status === "rejected") errors.census = "Live census workspace unavailable.";
      if (dashboardResult.status === "rejected") errors.dashboard = "Live dashboard queue unavailable.";
      if (alertsResult.status === "rejected") errors.alerts = "Live clinical alerts unavailable.";
      if (staffResult.status === "rejected") errors.staff = "Live staff roster unavailable.";
      if (idgResult.status === "rejected") errors.idg = "Live IDG sessions unavailable.";
      setDataState({
        alerts: alertsResult.status === "fulfilled" ? alertsResult.value : null,
        census: censusResult.status === "fulfilled" ? censusResult.value : null,
        dashboard: dashboardResult.status === "fulfilled" ? dashboardResult.value : null,
        errors,
        idgSessions: idgResult.status === "fulfilled" ? idgResult.value : null,
        loading: false,
        staff: staffResult.status === "fulfilled" ? staffResult.value : null,
      });
    });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    setActiveDomain(resolveDomainFromSection(section, defaultDomain));
    setActiveReport(null);
  }, [defaultDomain, section]);

  const analytics = useMemo(() => buildViewModel(dataState), [dataState]);
  const syncedLabel = useMemo(() => formatDateTime(new Date()), []);

  const renderDomain = () => {
    switch (activeDomain) {
      case "Reports Directory":
      case "Analytics Directory":
        return <ReportsDirectory onOpenSection={setActiveDomain} onOpenReport={setActiveReport} />;
      case "Command Center":
        return <CommandCenter analytics={analytics} onNavigate={setActiveDomain} />;
      case "Clinical":
        return <ClinicalTab analytics={analytics} />;
      case "QAPI":
        return <QAPITab analytics={analytics} />;
      case "Administrative":
        return <AdministrativeTab analytics={analytics} />;
      case "Financial":
        return <FinancialTab />;
      default:
        return <ReportsDirectory onOpenSection={setActiveDomain} onOpenReport={setActiveReport} />;
    }
  };

  return (
    <PortalShell activeTab="Analytics">
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <WelcomeBanner title={activeDomain === "Reports Directory" || activeDomain === "Analytics Directory" ? "Analytics Directory" : activeDomain === "Command Center" ? "Analytics Command Center" : `${activeDomain} Analytics`} syncedLabel={syncedLabel} />
        {activeDomain !== "Reports Directory" && activeDomain !== "Analytics Directory" ? (
          <div style={{ width: "100%", boxSizing: "border-box" }}>
            <button
              onClick={() => {
                setActiveReport(null);
                setActiveDomain("Analytics Directory");
              }}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: `1px solid ${C.slate200}`,
                backgroundColor: C.white,
                color: C.gray600,
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Back to Analytics Directory
            </button>
            <div style={{ marginTop: 12, fontSize: 13, color: C.slate500 }}>
              Active Agency Workspace: <strong style={{ color: C.gray800 }}>{workspaceName}</strong>
            </div>
          </div>
        ) : null}
        {activeReport ? <SNSNewReports activeReport={activeReport} /> : <div style={pageShellStyle}>{renderDomain()}</div>}
      </div>
    </PortalShell>
  );
}
