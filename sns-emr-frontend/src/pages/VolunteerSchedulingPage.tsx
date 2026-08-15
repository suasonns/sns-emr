import { useMemo } from "react";

import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";

const C = {
  navy: "#1f4a78",
  teal: "#10b7a2",
  tealDark: "#0f766e",
  tealLight: "#ccfbf1",
  white: "#ffffff",
  slate200: "#dbe5ee",
  slate500: "#64748b",
  gray100: "#f3f4f6",
  gray200: "#e5e7eb",
  gray600: "#4b5563",
  gray800: "#1f2937",
  gray900: "#111827",
  blue: "#3b82f6",
  blueLight: "#dbeafe",
  green: "#059669",
  greenLight: "#dcfce7",
  amber: "#f59e0b",
  amberLight: "#fef3c7",
};

const modules = [
  ["My Schedule", "View and edit your personal hospice visit calendar.", C.teal],
  ["My Time Sheet", "Log shift details, travel hours, and clinical time.", C.green],
  ["Staff Route Sheet", "Map daily clinical patient route optimized by zip.", C.blue],
  ["Staff Schedule", "Master agency calendar for active field coordinators.", C.teal],
  ["Schedule by Discipline", "Coordinate nursing, social work, and chaplain schedules.", C.blue],
  ["Staff Assigned Patient List", "Quick patient list distribution across caregivers.", C.green],
  ["On-Call Assignment", "Manage 24/7 emergency dispatch and physician rotation.", C.teal],
  ["Staff Contact List", "Direct secure messaging and emergency contact directory.", C.green],
] as const;

const visits = [
  ["09:00 AM", "George Henderson", "Routine Visit", "Sarah Jenkins, RN", "Completed", C.greenLight, C.green],
  ["11:30 AM", "Mary Albright", "Routine Visit", "Mina Patel, LVN", "In Progress", C.amberLight, C.amber],
  ["02:00 PM", "Harold Finch", "Palliative Care", "Marcus Brody, RN", "Scheduled", C.blueLight, C.blue],
  ["04:30 PM", "Eleanor Vance", "Admission", "Maria Santos, RN", "Scheduled", C.blueLight, C.blue],
];

function Pill({ text, bg, fg }: { text: string; bg: string; fg: string }) {
  return <span style={{ padding: "4px 10px", borderRadius: 999, backgroundColor: bg, color: fg, fontSize: portalTypography.chip, fontWeight: 700 }}>{text}</span>;
}

function ModuleCard({ title, description, color }: { title: string; description: string; color: string }) {
  return (
    <div style={{ border: "1px solid #e3edf2", borderRadius: 12, background: C.white, padding: 16, boxShadow: "0 1px 2px rgba(15,23,42,0.04)" }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ width: 28, height: 28, borderRadius: 8, background: C.tealLight, color: color, display: "grid", placeItems: "center", fontWeight: 900, fontSize: portalTypography.subtitle }}>◫</div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: portalTypography.subtitle, fontWeight: 800, color: C.gray800 }}>{title}</div>
          <div style={{ fontSize: portalTypography.small, color: C.slate500, lineHeight: 1.4, marginTop: 6 }}>{description}</div>
          <div style={{ marginTop: 10, fontSize: portalTypography.small, fontWeight: 700, color: color }}>Open Module →</div>
        </div>
      </div>
    </div>
  );
}

export default function VolunteerSchedulingPage() {
  const workspaceName = useMemo(() => getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.", []);

  return (
    <PortalShell activeTab="Scheduling">
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div style={{ width: "min(1180px, 100%)" }}>
          <div style={{ backgroundColor: C.white, borderRadius: 12, padding: "16px 22px", boxShadow: "0 1px 3px rgba(0,0,0,0.08)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: portalTypography.title, fontWeight: 800, color: C.gray800 }}>Clinician Scheduling Hub Workspace</div>
              <div style={{ marginTop: 8, fontSize: portalTypography.subtitle, color: C.slate500 }}>
                Active Agency Workspace:{" "}
                <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: 999, background: C.tealLight, color: C.tealDark, fontSize: portalTypography.small, fontWeight: 700 }}>
                  {workspaceName}
                </span>
              </div>
            </div>
            <div style={{ fontSize: portalTypography.subtitle, color: C.slate500 }}>Last synced: Today at 08:30 AM</div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16, marginTop: 18 }}>
            {modules.map(([title, description, color]) => (
              <ModuleCard key={title} title={title} description={description} color={color} />
            ))}
          </div>

          <div style={{ marginTop: 18, backgroundColor: C.white, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", overflow: "hidden" }}>
            <div style={{ padding: "14px 18px", borderBottom: `1px solid ${C.gray200}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: portalTypography.subtitle, fontWeight: 800, color: C.gray800 }}>Today's Scheduled Visits Preview</div>
              <div style={{ fontSize: portalTypography.small, color: C.slate500 }}>Wednesday, Feb 12</div>
            </div>
            <div style={{ padding: 18 }}>
              {visits.map(([time, patient, type, clinician, status, bg, fg]) => (
                <div key={`${time}-${patient}`} style={{ display: "grid", gridTemplateColumns: "120px 1.2fr 1fr 1.4fr 120px", alignItems: "center", gap: 14, padding: "12px 0", borderBottom: `1px solid ${C.gray100}` }}>
                  <div>
                    <div style={{ fontSize: portalTypography.subtitle, fontWeight: 800, color: C.gray800 }}>{time}</div>
                    <div style={{ fontSize: portalTypography.chip, color: C.slate500, marginTop: 4 }}>{type}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: portalTypography.subtitle, fontWeight: 700, color: C.gray800 }}>{patient}</div>
                    <div style={{ fontSize: portalTypography.chip, color: C.slate500, marginTop: 4 }}>Scheduled patient</div>
                  </div>
                  <div style={{ fontSize: portalTypography.small, color: C.gray600 }}>{type}</div>
                  <div style={{ fontSize: portalTypography.small, color: C.gray600 }}>{clinician}</div>
                  <div style={{ justifySelf: "end" }}>
                    <Pill text={status} bg={bg as string} fg={fg as string} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
