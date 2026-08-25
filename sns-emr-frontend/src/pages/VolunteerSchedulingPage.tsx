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
            <div style={{ fontSize: portalTypography.subtitle, color: C.slate500 }}>Agency-wide live visit preview unavailable</div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 16, marginTop: 18 }}>
            {modules.map(([title, description, color]) => (
              <ModuleCard key={title} title={title} description={description} color={color} />
            ))}
          </div>

          <div style={{ marginTop: 18, backgroundColor: C.white, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", overflow: "hidden" }}>
            <div style={{ padding: "14px 18px", borderBottom: `1px solid ${C.gray200}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: portalTypography.subtitle, fontWeight: 800, color: C.gray800 }}>Today's Scheduled Visits Preview</div>
              <Pill text="Unavailable" bg={C.gray100} fg={C.gray600} />
            </div>
            <div style={{ padding: 18 }}>
              <div style={{ border: `1px dashed ${C.gray200}`, borderRadius: 12, background: "#f8fafc", padding: 24, textAlign: "center" }}>
                <div style={{ fontSize: portalTypography.subtitle, fontWeight: 800, color: C.gray800 }}>No live tenant-wide visit list</div>
                <div style={{ marginTop: 8, fontSize: portalTypography.small, color: C.slate500, lineHeight: 1.6 }}>
                  Agency-wide volunteer visit scheduling is not wired to a live backend yet.
                  <br />
                  Open a patient chart to review real volunteer visits and assignments from the existing patient summary APIs.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
