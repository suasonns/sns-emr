import { useEffect, useState, type CSSProperties } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import PortalShell from "../components/PortalShell";
import SNSNewReports from "./SNSNewReports";

import { getCurrentUser } from "../api/session";
import BillingDashboard from "./BillingDashboard";
import { canAccessBilling } from "../utils/featureAccess";

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
  "secure-inbox": "Reports Directory",
  "clinical-alerts": "QAPI",
  scheduling: "Administrative",
  settings: "Administrative",
  "my-profile": "Administrative",
  rnica: "Clinical",
  "msw-ica": "Clinical",
  "sc-ica": "Clinical",
  "patient-lcd": "Clinical",
  "care-overview": "Clinical",
  bereavement: "QAPI",
  "incident-occurrence": "QAPI",
  compliance: "QAPI",
  physician: "Administrative",
  "communication-log": "Reports Directory",
};

function resolveDomainFromSection(section: string | null | undefined, fallback: string) {
  if (!section) return fallback;
  return SECTION_TO_DOMAIN[section] ?? fallback;
}

const cardStyle: CSSProperties = { backgroundColor: C.white, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", padding: 24 };
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

function ShieldIcon({ size = 28, color = C.teal }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
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
          <ShieldIcon />
          <div>
            <div style={{ lineHeight: 1.1 }}>
              <span style={{ fontSize: 20, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.white }}>SNS </span>
              <span style={{ fontSize: 20, fontWeight: 300, fontFamily: "'Inter', sans-serif", color: C.white }}>HOSPICE</span>
            </div>
            <div style={{ fontSize: 9, fontWeight: 600, letterSpacing: 1.5, color: C.gray400, marginTop: 1 }}>SECURE CLINICAL SYSTEM</div>
          </div>
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

export function WelcomeBanner({ title }: { title: string }) {
  const workspaceName = getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.";
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
        Last synced: Today at 08:30 AM
      </div>
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
          SNS Hospice Solutions Secure Portal | © 2024-2025 | All Rights Reserved | SNS Tech Solutions
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
    "Quality & Compliance": "QAPI",
    "Operations & Workforce": "Administrative",
    "Financial & Billing": "Financial",
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
      title: "Quality & Compliance",
      subtitle: "QUALITY MEASURES, HOPE/HIS/HQRP, AND CLINICAL TRACKING",
      color: C.blue,
      groups: [
        { name: "QUALITY MEASURES", items: ["Comfortable Dying Measure", "Unwanted Hospitalization", "Infection Control", "Census Integrity Report", "Incident Rate"] },
        { name: "HOPE / HIS / HQRP", items: ["HOPE/HIS Submissions", "HQRP Quality Reporting", "Export CAHPS"] },
        { name: "CLINICAL TRACKING", items: ["Wound Tracking Report", "Antibiotics w/o Care Plan", "eMAR Report", "Patient Acuity Report"] },
        { name: "STAFF & RESOURCES", items: ["Staff Utilization/Productivity", "Volunteer Savings Report", "Non-Converted Notifications"] },
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
          placeholder="Search or filter reports directory..."
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
              ["Report Status", "Live"],
              ["Source Section", selectedDomain || "—"],
              ["Update Mode", "Interactive"],
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

function CommandCenter({ onNavigate }: { onNavigate: (domain: string) => void }) {
  const alerts = [
    { text: "Recertification due for 3 patients in 48 hours", priority: "Critical", bg: C.redLight, color: C.red },
    { text: "QAPI incident report pending review (Fall Incident #204)", priority: "High", bg: C.amberLight, color: C.amberDark },
    { text: "Staff credential renewal: 2 expiring in next 15 days", priority: "Medium", bg: C.blueLight, color: C.blue },
  ];

  return (
    <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={responsiveThreeGrid}>
        <div onClick={() => onNavigate("Clinical")} style={{ ...cardStyle, borderTop: `3px solid ${C.teal}`, cursor: "pointer", padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.gray800, marginBottom: 8 }}>Clinical</div>
          <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>47 Active Patients</div>
          <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>Patient census, recertification tracking, IDG notes, care quality metrics</div>
        </div>
        <div onClick={() => onNavigate("QAPI")} style={{ ...cardStyle, borderTop: `3px solid ${C.blue}`, cursor: "pointer", padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.gray800, marginBottom: 8 }}>QAPI</div>
          <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>94.2% QAPI Score</div>
          <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>Quality measures, HOPE/HIS tracking, clinical tracking, staff resources</div>
        </div>
        <div onClick={() => onNavigate("Administrative")} style={{ ...cardStyle, borderTop: `3px solid ${C.amber}`, cursor: "pointer", padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.gray800, marginBottom: 8 }}>Administrative</div>
          <div style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>38 Staff Active</div>
          <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>Census, HR, orders, NPI lookup, vendor management, ALIRTS</div>
        </div>
      </div>
      <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800 }}>Cross-Domain Insights</div>
      <div style={responsiveTwoGrid}>
        <div style={cardStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            <div style={{ position: "relative", width: 100, height: 100 }}>
              <svg width="100" height="100" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke={C.gray200} strokeWidth="10" />
                <circle cx="50" cy="50" r="40" fill="none" stroke={C.teal} strokeWidth="10" strokeDasharray={`${0.913 * 251.3} ${251.3}`} strokeLinecap="round" transform="rotate(-90 50 50)" />
              </svg>
              <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800, fontFamily: "'Inter', sans-serif", color: C.navy }}>91.3%</div>
                <div style={{ fontSize: 9, color: C.slate500 }}>Overall Health</div>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 12 }}>Domain Breakdown</div>
              {[
                { name: "Clinical Compliance", score: "94%", color: C.green },
                { name: "Quality Assessment", score: "92%", color: C.teal },
                { name: "Operations Efficiency", score: "88%", color: C.amber },
              ].map((s) => (
                <div key={s.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0" }}>
                  <span style={{ fontSize: 13, color: C.gray600 }}>{s.name}</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: s.color }}>{s.score}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={cardStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <span style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800 }}>Key Performance Alerts</span>
            <span style={{ fontSize: 12, color: C.slate500 }}>3 Alerts Pending</span>
          </div>
          {alerts.map((a, i) => (
            <div key={a.text} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: i < alerts.length - 1 ? `1px solid ${C.gray100}` : "none" }}>
              <span style={{ fontSize: 13, color: C.gray600, flex: 1 }}>{a.text}</span>
              {badge(a.priority, a.bg, a.color)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ClinicalTab() {
  const [activeTab, setActiveTab] = useState("Overview");
  const tabs = ["Overview", "Visit Management", "Compliance & Documentation", "Recertification Tracker", "Clinical Reference", "Bereavement Tracking"];

  const patientRows = [
    ["Robert Taylor", "847-194", "Oct 12, 2024", "RHC", "End-Stage COPD", "Dr. L. Vance", "1st Period", "93"],
    ["Evelyn Martinez", "522-385", "Nov 02, 2024", "CHC", "Alzheimer's Dementia", "Dr. A. Cole", "2nd Period", "72"],
    ["Thomas Wilson", "411-930", "Jan 08, 2025", "GIP", "Congestive Heart Failure", "Dr. L. Vance", "1st Period", "15"],
  ];

  const render = () => {
    if (activeTab === "Visit Management") {
      const visits = [
        ["Jan 20, 2025", "Robert Taylor", "847-194", "SN Visit", "Sarah Jenkins, RN", "1h 15m", "Completed"],
        ["Jan 20, 2025", "Evelyn Martinez", "522-385", "Aide Visit", "Elena Rostova, CHHA", "45m", "Completed"],
        ["Jan 18, 2025", "Thomas Wilson", "411-930", "SN Visit", "Sarah Jenkins, RN", "0m", "Missed"],
      ];
      return (
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>All Visits Log</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Visit Date", "Patient", "MRN", "Visit Type", "Clinician", "Duration", "Status"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {visits.map((r) => (
                <tr key={r.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {r.map((cell, idx) => <td key={idx} style={{ ...tdStyle, fontWeight: idx === 1 ? 600 : 400, color: idx === 1 ? C.gray800 : C.gray600 }}>{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    if (activeTab === "Compliance & Documentation") {
      const consents = [
        ["Thomas Wilson", "411-930", "Jan 12, 2025", "Election of Benefits", "8 days", "Marcus Brody, RN", "Critical"],
        ["James Fitzpatrick", "729-183", "Jan 15, 2025", "HIPAA Authorization", "5 days", "Sarah Jenkins, RN", "High"],
      ];
      return (
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Missing Consents Tracker</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient", "MRN", "Admission Date", "Missing Doc", "Days", "Assigned To", "Priority"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {consents.map((r) => (
                <tr key={r.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {r.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 6 ? badge(cell, cell === "Critical" ? C.redLight : C.amberLight, cell === "Critical" ? C.red : C.amberDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    if (activeTab === "Recertification Tracker") {
      const recerts = [
        ["Thomas Wilson", "411-930", "1st Period", "Nov 10, 2024", "Jan 25, 2025", "2 days", "Complete", "Signed"],
        ["James Fitzpatrick", "729-183", "1st Period", "Nov 15, 2024", "Jan 28, 2025", "5 days", "Scheduled", "Signed"],
      ];
      return (
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Recertification List</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient", "MRN", "Period", "Start", "End", "Days Left", "F2F", "Order"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {recerts.map((r) => (
                <tr key={r.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {r.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 6 ? badge(cell, cell === "Complete" ? C.greenLight : C.amberLight, cell === "Complete" ? C.greenDark : C.amberDark) : idx === 7 ? badge(cell, C.greenLight, C.greenDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    if (activeTab === "Bereavement Tracking") {
      const rows = [
        ["Mary Taylor", "Robert Taylor", "Oct 12, 2024", "Low", "Alisha Patel, LCSW"],
        ["John Chen", "Margaret Chen", "Dec 18, 2024", "High", "Sarah Jenkins, RN"],
      ];
      return (
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Bereavement Risk Assessment</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Contact", "Deceased", "Date of Death", "Risk", "Counselor"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {r.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 3 ? badge(cell, cell === "High" ? C.redLight : C.greenLight, cell === "High" ? C.red : C.greenDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    if (activeTab === "Clinical Reference") {
      const icdRows = [
        ["C34.9", "Lung Cancer", "18", "24.0%", "45 Days"],
        ["F03.9", "Dementia / Alzheimer's", "14", "18.0%", "125 Days"],
        ["I50.9", "Heart Failure (CHF)", "11", "15.0%", "92 Days"],
      ];
      const medsRows = [
        ["Morphine", "18"],
        ["Lorazepam", "16"],
        ["Haldol", "13"],
        ["Atropine", "12"],
      ];
      return (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div style={cardStyle}>
            <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Commonly Used ICD-10 Codes</div>
            <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
              <thead><tr>{["ICD-10 Code", "Disease Category", "Patient Count", "% of Census", "Avg LOS"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
              <tbody>
                {icdRows.map((row) => (
                  <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                    {row.map((cell, idx) => <td key={idx} style={{ ...tdStyle, fontWeight: idx === 0 ? 700 : 400, color: idx === 0 ? C.gray800 : C.gray600 }}>{cell}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Commonly Used Medications</div>
            {medsRows.map((row, idx) => (
              <div key={row[0]} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: idx < medsRows.length - 1 ? `1px solid ${C.gray100}` : "none" }}>
                <span style={{ fontSize: 13, color: C.gray600 }}>{row[0]}</span>
                <strong style={{ color: C.navy }}>{row[1]}</strong>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return (
      <>
        <div style={responsiveFourGrid}>
          {kpiCard("ACTIVE CENSUS", "47 Patients", "Target: 42", C.teal)}
          {kpiCard("AVG LENGTH OF STAY", "92.4 Days", "Median: 68 Days", C.blue)}
          {kpiCard("RECERTIFICATIONS DUE", "8 Patients", "3 within 48 hrs", C.amber)}
          {kpiCard("CLINICAL QA SCORE", "96.1%", "Target: 95%", C.green)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Patient Census Summary</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient Name", "MRN", "Admission Date", "Level of Care", "Primary Dx", "Attending MD", "Cert Period", "Days on Service"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {patientRows.map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={{ ...tdStyle, fontWeight: idx === 0 ? 600 : 400, color: idx === 0 ? C.gray800 : C.gray600 }}>{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div style={cardStyle}>
            <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Recertification Alert Queue</div>
            {[
              ["Thomas Wilson", "Congestive Heart Failure", "2 Days Left", C.redLight, C.red],
              ["James Fitzpatrick", "Renal Failure", "5 Days Left", C.amberLight, C.amberDark],
              ["Margaret Chen", "Lung Adenocarcinoma", "8 Days Left", C.greenLight, C.greenDark],
            ].map((row) => (
              <div key={row.join("-")} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: `1px solid ${C.gray100}` }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.gray800 }}>{row[0]}</div>
                  <div style={{ fontSize: 11, color: C.slate500 }}>{row[1]}</div>
                </div>
                {badge(row[2], row[3] as string, row[4] as string)}
              </div>
            ))}
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>IDG Review Schedule</div>
            {[
              ["IDG Team A Weekly", "Jan 22, 2025 at 09:00 AM • 16 Patients", "Active"],
              ["IDG Team B Weekly", "Jan 23, 2025 at 01:00 PM • 14 Patients", "Pending Prep"],
              ["IDG Monthly Compliance Review", "Jan 28, 2025 at 10:00 AM • 8 Patients", "Scheduled"],
            ].map((row, idx) => (
              <div key={row.join("-")} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: idx < 2 ? `1px solid ${C.gray100}` : "none" }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.gray800 }}>{row[0]}</div>
                  <div style={{ fontSize: 11, color: C.slate500 }}>{row[1]}</div>
                </div>
                {badge(row[2], row[2] === "Active" ? C.greenLight : row[2] === "Scheduled" ? C.blueLight : C.amberLight, row[2] === "Active" ? C.greenDark : row[2] === "Scheduled" ? C.blue : C.amberDark)}
              </div>
            ))}
          </div>
        </div>
      </>
    );
  };

  return (
    <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
      <SubNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      {render()}
    </div>
  );
}

function QAPITab() {
  const [activeTab, setActiveTab] = useState("Overview");
  const tabs = ["Overview", "Quality Measures", "HOPE/HIS Tracking", "Clinical Tracking", "Staff & Resources"];

  if (activeTab === "Quality Measures") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("COMFORTABLE DYING MEASURE", "89.2%", "National avg: 86.4%", C.teal)}
          {kpiCard("UNWANTED HOSPITALIZATION", "4.1%", "Target: <5.0%", C.blue)}
          {kpiCard("INFECTION CONTROL RATE", "97.3%", "1 active case", C.amber)}
          {kpiCard("CENSUS INTEGRITY SCORE", "99.1%", "0 discrepancies", C.green)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Census Integrity Report</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Check Type", "Last Run", "Checked", "Discrepancies", "Status"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Admission Verification", "Today 08:00 AM", "142", "0", "Clear"],
                ["LOC Accuracy Validation", "Jan 19, 2025", "140", "1", "Issues"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 4 ? badge(cell, cell === "Issues" ? C.redLight : C.greenLight, cell === "Issues" ? C.red : C.greenDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeTab === "HOPE/HIS Tracking") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("HOPE SUBMISSIONS (MTD)", "38 Records", "100% timely", C.teal)}
          {kpiCard("HIS ACCURACY RATE", "98.7%", "Target: 95%", C.blue)}
          {kpiCard("HQRP COMPLIANCE", "96.2%", "All measures met", C.green)}
          {kpiCard("PENDING SUBMISSIONS", "3 Records", "1 past due", C.amber)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>HOPE/HIS Submission Tracking</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient", "Assessment Type", "Assess Date", "Submit Date", "Timeliness", "QA Status"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Robert Taylor", "Admission Assessment", "Jan 12, 2025", "Jan 15, 2025", "On Time", "Approved"],
                ["Margaret Chen", "Admission Assessment", "Jan 03, 2025", "Jan 08, 2025", "Late", "Needs Review"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 4 ? badge(cell, cell === "On Time" ? C.greenLight : C.redLight, cell === "On Time" ? C.greenDark : C.red) : idx === 5 ? badge(cell, cell === "Approved" ? C.greenLight : C.amberLight, cell === "Approved" ? C.greenDark : C.amberDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeTab === "Clinical Tracking") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("ACTIVE WOUNDS", "14 Patients", "3 new this month", C.teal)}
          {kpiCard("ANTIBIOTICS W/O CARE PLAN", "2 Patients", "Action required", C.red)}
          {kpiCard("EMAR COMPLIANCE", "94.8%", "Target: 95%", C.amber)}
          {kpiCard("AVG ACUITY SCORE", "3.2 / 5.0", "High acuity: 8 patients", C.blue)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Patient Acuity Level Report</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient", "Acuity", "LOC", "Primary Dx", "Symptom Burden"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Thomas Wilson", "5/5", "GIP", "Lung Cancer", "High"],
                ["Robert Taylor", "4/5", "RHC", "Heart Failure", "High"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 1 ? <span style={{ padding: "2px 8px", borderRadius: 4, backgroundColor: C.redLight, color: C.red, fontWeight: 700, fontSize: 11 }}>{cell}</span> : idx === 4 ? badge(cell, cell === "High" ? C.redLight : C.greenLight, cell === "High" ? C.red : C.greenDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeTab === "Staff & Resources") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("STAFF UTILIZATION RATE", "87.3%", "vs target threshold", C.teal)}
          {kpiCard("AVG PRODUCTIVITY", "6.2 Visits/Day", "vs target threshold", C.blue)}
          {kpiCard("VOLUNTEER HOURS (MTD)", "142 Hours", "vs target threshold", C.amber)}
          {kpiCard("NON-COVERED COMPLIANCE", "96.7%", "vs target threshold", C.green)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Staff Utilization Report</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Staff", "Scheduled", "Actual", "Utilization", "Overtime"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Sarah Jenkins, RN", "160 hrs", "168 hrs", "105%", "+8 hrs"],
                ["Marcus Brody, RN", "160 hrs", "160 hrs", "100%", "0 hrs"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 4 ? <span style={{ color: cell.startsWith("+") ? C.red : C.green, fontWeight: 600 }}>{cell}</span> : idx === 3 ? <strong>{cell}</strong> : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 24px 40px" }}>
      <SubNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={{ ...responsiveFourGrid, padding: "0 0 24px" }}>
        {kpiCard("OVERALL QAPI SCORE", "94.2%", "Target: 90%", C.teal)}
        {kpiCard("OPEN INCIDENTS", "3 Active", "1 high severity", C.red)}
        {kpiCard("SURVEY RESPONSE RATE", "87.3%", "+5.2% vs last quarter", C.blue)}
        {kpiCard("CORRECTIVE ACTIONS", "2 Open", "1 overdue", C.amber)}
      </div>
      {activeTab === "Overview" ? (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1fr", gap: 20 }}>
            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Customer Survey Results</div>
              {[
                ["Overall Care", "4.8 / 5.0"],
                ["Pain Management", "4.6 / 5.0"],
                ["Communication", "4.7 / 5.0"],
                ["Spiritual Support", "4.5 / 5.0"],
              ].map((row, idx) => (
                <div key={row[0]} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: idx < 3 ? `1px solid ${C.gray100}` : "none" }}>
                  <span style={{ fontSize: 13, color: C.gray600 }}>{row[0]}</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: C.navy }}>{row[1]}</span>
                </div>
              ))}
            </div>
            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Recent Incident Reports</div>
              <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
                <thead><tr>{["ID", "Type", "Patient", "Date", "Severity", "Status"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
                <tbody>
                  {[
                    ["INC-204", "Fall", "Evelyn Martinez", "Jan 18, 2025", "Moderate", "Under Review"],
                    ["INC-203", "Medication Error", "Robert Taylor", "Jan 15, 2025", "Low", "Resolved"],
                    ["INC-202", "Skin Breakdown", "Dorothy Henderson", "Jan 12, 2025", "High", "Corrective Action"],
                  ].map((row) => (
                    <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                      {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 4 ? badge(cell, cell === "Moderate" ? C.amberLight : cell === "High" ? C.redLight : C.greenLight, cell === "Moderate" ? C.amberDark : cell === "High" ? C.red : C.greenDark) : idx === 5 ? badge(cell, cell === "Resolved" ? C.greenLight : cell === "Corrective Action" ? C.blueLight : C.amberLight, cell === "Resolved" ? C.greenDark : cell === "Corrective Action" ? C.blue : C.amberDark) : cell}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div style={cardStyle}>
            <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>QAPI Performance Improvement Projects (PIPs)</div>
            {[
              ["Fall Prevention Initiative", "Reducing patient falls in GIP/RHC settings via targeted risk assessments and environmental modifications", 75, C.teal],
              ["IDG Documentation Audit", "Streamlining interdisciplinary notes alignment to meet 100% compliance for MAC fiscal reviews", 40, C.amber],
              ["Bereavement Outreach Escalation", "Implementing post-discharge customer feedback cycles to address caregiver satisfaction targets", 90, C.green],
            ].map((row, idx) => (
              <div key={row[0]} style={{ padding: 20, borderRadius: 8, border: `1px solid ${C.gray200}`, marginBottom: idx < 2 ? 16 : 0 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: C.navy }}>{row[0]}</div>
                    <div style={{ fontSize: 12, color: C.slate500, marginTop: 4 }}>{row[1]}</div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 16, minWidth: 300 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: C.slate500, marginBottom: 4 }}>Project Progress</div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ flex: 1, height: 8, backgroundColor: C.gray200, borderRadius: 4 }}>
                          <div style={{ height: 8, backgroundColor: row[3] as string, borderRadius: 4, width: `${row[2]}%` }} />
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 700, color: row[3] as string }}>{row[2]}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}
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

  return <BillingDashboard />;
}

export default function SNSAnalytics({ defaultDomain = "Reports Directory" }: { defaultDomain?: string }) {
  const [searchParams] = useSearchParams();
  const section = searchParams.get("section");
  const [activeDomain, setActiveDomain] = useState(() => resolveDomainFromSection(section, defaultDomain));
  const [activeReport, setActiveReport] = useState<string | null>(null);
  const currentUser = getCurrentUser();
  const workspaceName = currentUser?.tenant_name ?? "Love & Faith Hospice Services Inc.";

  useEffect(() => {
    setActiveDomain(resolveDomainFromSection(section, defaultDomain));
    setActiveReport(null);
  }, [defaultDomain, section]);

  const renderDomain = () => {
    switch (activeDomain) {
      case "Reports Directory":
        return <ReportsDirectory onOpenSection={setActiveDomain} onOpenReport={setActiveReport} />;
      case "Command Center":
        return <CommandCenter onNavigate={setActiveDomain} />;
      case "Clinical":
        return <ClinicalTab />;
      case "QAPI":
        return <QAPITab />;
      case "Administrative":
        return <AdministrativeTab />;
      case "Financial":
        return <FinancialTab />;
      default:
        return <ReportsDirectory onOpenSection={setActiveDomain} onOpenReport={setActiveReport} />;
    }
  };

  return (
    <PortalShell activeTab="Analytics">
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <WelcomeBanner title={activeDomain === "Reports Directory" ? "Reports Directory" : activeDomain === "Command Center" ? "Analytics Command Center" : `${activeDomain} Analytics`} />
        {activeDomain !== "Reports Directory" ? (
          <div style={{ width: "100%", boxSizing: "border-box" }}>
            <button
              onClick={() => {
                setActiveReport(null);
                setActiveDomain("Reports Directory");
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
              Back to Reports Directory
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

function AdministrativeTab() {
  const [activeTab, setActiveTab] = useState("Overview");
  const tabs = ["Overview", "Census & Demographics", "Service Operations", "Orders & Rx", "Staffing & HR"];

  if (activeTab === "Census & Demographics") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("AVERAGE DAILY CENSUS", "45.3 Patients", "Target: 42", C.teal)}
          {kpiCard("AVERAGE LOS", "92.4 Days", "National avg: 71 days", C.blue)}
          {kpiCard("MEDIAN LOS", "68 Days", "Median benchmark", C.amber)}
          {kpiCard("ACTIVE PAYER MIX", "Medicare 78%", "Medicaid 12%, Private 10%", C.green)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Patient Profile Summary</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient", "MRN", "Age/Sex", "Primary Dx", "LOC", "Payer", "Days on Svc"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Robert Taylor", "847-194", "78 / M", "COPD", "ROUTINE", "MEDICARE", "70 Days"],
                ["Evelyn Martinez", "522-385", "84 / F", "Dementia", "ROUTINE", "MEDICAID", "108 Days"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={{ ...tdStyle, fontWeight: idx === 0 ? 600 : 400, color: idx === 0 ? C.gray800 : C.gray600 }}>{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeTab === "Service Operations") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("TOTAL VISITS (MTD)", "342 Visits", "By 38 active staff", C.teal)}
          {kpiCard("VISITS BY DISCIPLINE", "RN 45%", "LVN 20%, MSW 15%", C.blue)}
          {kpiCard("PLACE OF SERVICE", "Home 82%", "Facility 14%, Inpatient 4%", C.amber)}
          {kpiCard("DAILY SUMMARY ACTIVE", "47 Patients", "23 visits scheduled today", C.green)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Visits By Discipline</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Discipline", "Total Visits", "% of Total", "Avg Duration", "Billable Rate"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Skilled Nursing (RN)", "154", "45%", "1h 15m", "100%"],
                ["Hospice Aide (CHHA)", "68", "20%", "45m", "100%"],
                ["Social Work (MSW)", "51", "15%", "1h 00m", "100%"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 0 ? <strong style={{ color: C.gray800 }}>{cell}</strong> : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (activeTab === "Orders & Rx") {
    return (
      <div style={{ padding: "24px 24px 40px", display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={responsiveFourGrid}>
          {kpiCard("ACTIVE MEDICATION ORDERS", "312 Orders", "24 unique medications", C.teal)}
          {kpiCard("DME ORDERS ACTIVE", "48 Items", "8 pending delivery", C.blue)}
          {kpiCard("SIGNED ORDERS RATE", "97.2%", "Target: 95%", C.green)}
          {kpiCard("PENDING SIGNATURES", "6 Orders", "2 past 72hrs", C.amber)}
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Medication & DME Orders Summary</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Order Date", "Patient", "Order Type", "Description", "Prescriber", "Status"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Jan 24, 2025", "Robert Taylor", "Medication", "Morphine Sulfate", "Dr. J. Vance", "Active"],
                ["Jan 24, 2025", "Evelyn Martinez", "DME", "Hospital Bed Full Electric", "Dr. A. Sterling", "Active"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 2 ? badge(cell, C.tealLight, C.tealDark) : idx === 5 ? badge(cell, C.greenLight, C.greenDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 24px 40px" }}>
      <SubNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={responsiveFourGrid}>
        {kpiCard("ACTIVE CENSUS", "47 Patients", "Target: 42", C.teal)}
        {kpiCard("ADMISSIONS (MTD)", "8 New", "+3 vs last month", C.green)}
        {kpiCard("DISCHARGES (MTD)", "5 Patients", "3 deceased, 2 revocation", C.amber)}
        {kpiCard("AVG LENGTH OF STAY", "92.4 Days", "Median: 68 days", C.blue)}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Recent Admissions</div>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead><tr>{["Patient", "MRN", "Admit Date", "Source", "LOC", "Status"].map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
            <tbody>
              {[
                ["Robert Taylor", "847-194", "Oct 12, 2024", "Hospital", "RHC", "Active"],
                ["Evelyn Martinez", "522-385", "Nov 02, 2024", "Physician", "CHC", "Active"],
                ["Thomas Wilson", "411-930", "Jan 08, 2025", "Referral", "GIP", "Pending"],
              ].map((row) => (
                <tr key={row.join("-")} style={{ borderBottom: `1px solid ${C.gray100}` }}>
                  {row.map((cell, idx) => <td key={idx} style={tdStyle}>{idx === 4 ? badge(cell, C.blueLight, C.blue) : idx === 5 ? badge(cell, cell === "Active" ? C.greenLight : C.amberLight, cell === "Active" ? C.greenDark : C.amberDark) : cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Inter', sans-serif", color: C.gray800, marginBottom: 16 }}>Operational Snapshot</div>
          {[
            ["Pending Physician Orders", "12"],
            ["Unsigned Hospice Certs", "4"],
            ["Open HR Compliance Tasks", "6"],
            ["Medicare Pending Follow-Up", "9"],
          ].map((row, idx) => (
            <div key={row[0]} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: idx < 3 ? `1px solid ${C.gray100}` : "none" }}>
              <span style={{ fontSize: 13, color: C.gray600 }}>{row[0]}</span>
              <strong style={{ color: C.navy }}>{row[1]}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
