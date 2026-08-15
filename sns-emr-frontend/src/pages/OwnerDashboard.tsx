import { useMemo } from "react";

import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";

const C = {
  navy: "#1f4a78",
  teal: "#10b7a2",
  tealDark: "#0f766e",
  tealLight: "#ccfbf1",
  gray100: "#f3f4f6",
  gray200: "#e5e7eb",
  gray500: "#6b7280",
  gray600: "#4b5563",
  gray700: "#374151",
  gray800: "#1f2937",
  white: "#ffffff",
};

const settingsCards = [
  ["Practice Information", "Manage agency details, locations, and NPI numbers"],
  ["Letter Templates", "Bereavement, admission, and discharge letter templates"],
  ["Referring Physicians", "Add or edit referring MD directory"],
  ["Medication Tables", "Medication detail lookup tables"],
  ["Vendor Management", "DME suppliers, pharmacies, and lab vendors"],
  ["Staff Administration", "View staff activity logs and manage user roles"],
  ["Insurance & Payers", "Configure insurance companies and payer information"],
  ["System Configuration", "Portal preferences, security settings, audit logs"],
] as const;

function ChevronRight({ size = 14, color = C.gray500 }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function SettingsCard({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, backgroundColor: C.white, border: `1px solid ${C.gray200}`, borderRadius: 10, padding: "16px 18px", boxShadow: "0 1px 2px rgba(15,23,42,0.04)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, minWidth: 0 }}>
        <div style={{ width: 30, height: 30, borderRadius: 8, backgroundColor: C.tealLight, color: C.tealDark, display: "grid", placeItems: "center", flex: "0 0 auto" }}>
        <span style={{ fontSize: portalTypography.subtitle, fontWeight: 900 }}>▣</span>
        </div>
        <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: portalTypography.subtitle, fontWeight: 800, color: C.gray800 }}>{title}</div>
        <div style={{ fontSize: portalTypography.small, color: C.gray500, marginTop: 3 }}>{subtitle}</div>
        </div>
      </div>
      <ChevronRight />
    </div>
  );
}

export default function OwnerDashboard() {
  const workspaceName = useMemo(() => getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.", []);

  return (
    <PortalShell activeTab="Settings">
      <div style={{ width: "min(1180px, 100%)", margin: "0 auto", boxSizing: "border-box", padding: "0", flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, marginBottom: 18 }}>
          <div>
            <div style={{ fontSize: portalTypography.title, fontWeight: 800, color: C.gray800, lineHeight: 1.2 }}>System Settings &amp; Configuration</div>
            <div style={{ marginTop: 6, fontSize: portalTypography.subtitle, color: C.gray500 }}>
              Active Agency Workspace:{" "}
              <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: 999, backgroundColor: C.tealLight, color: C.tealDark, fontSize: portalTypography.small, fontWeight: 700 }}>
                {workspaceName}
              </span>
            </div>
          </div>
          <div style={{ fontSize: portalTypography.subtitle, color: C.gray500 }}>Last synced: Today at 08:30 AM</div>
        </div>

        <div style={{ backgroundColor: C.white, borderRadius: 12, padding: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(330px, 1fr))", gap: 16 }}>
            {settingsCards.map(([title, subtitle]) => (
              <SettingsCard key={title} title={title} subtitle={subtitle} />
            ))}
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
