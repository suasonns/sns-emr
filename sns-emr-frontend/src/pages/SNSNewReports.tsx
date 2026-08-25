import { Box, Paper, Typography } from "@mui/material";
import type { ReactElement } from "react";

const NEW_REPORT_LABELS = [
  "IDG Management",
  "Quality Assurance",
  "Human Resource",
  "Print Patient Chart",
  "Infection Control",
  "Incident Rate",
  "Export CAHPS",
  "Admissions",
  "Discharge Trend",
  "Emergency Triage",
  "Patient Referral Source",
  "Employee Contact List",
  "Outbound Fax",
  "Standard Pack",
  "Re-Cert List",
  "Agency Announcements Hx",
  "HospiceMD Announcements Hx",
  "Bereavement Letter Template",
  "Bereavement Header/Footer",
] as const;

const LEGACY_REPORT_LABELS = [
  "All Visits Report",
  "Missed Visits Report",
  "Supervisory Visit Review",
  "On-Call Log",
  "Missing Consents",
  "SIA Patients/Visits",
  "Submission Log",
  "Pending Prescription",
  "Commonly Used ICD-10 Codes",
  "Commonly Used Medications",
  "Bereavement Calendar",
  "Bereavement Risk Assessment",
  "Late Tracking",
  "Re-Cert List with Dates",
  "F2F Scheduling",
  "Create IDG Notes/Groups",
  "IDG Meetings",
  "Notes To Review",
  "Late Submission Tracking",
  "QA Management Dashboard",
  "Comfortable Dying Measure",
  "Unwanted Hospitalization",
  "Census Integrity Report",
  "Wound Tracking Report",
  "Antibiotics w/o Care Plan",
  "eMAR Report",
  "Patient Acuity Report",
  "Staff Utilization/Productivity",
  "Volunteer Savings Report",
  "Non-Converted Notifications",
  "ADC/ALOS/MLOS Report",
  "Age & Gender Demographics",
  "Patient Profile Report",
  "Diagnosis/Disease Report",
  "Visits By Discipline",
  "Place of Service Report",
  "Level of Care Report",
  "Daily Summary",
  "Medication/DME Orders",
  "Signed Physician Orders",
  "Patients by Zip/City/County",
  "Census Heatmap",
  "Patient Birthday Report",
  "NPI Lookup",
  "Employee Directory",
  "Vendor Management",
  "Payer Source Report",
  "Announcement System",
  "Claims Dashboard",
  "RA Reconciliation",
  "NOE/NOTR Management",
  "Monthly Billing Summary",
] as const;

type NewReportLabel = typeof NEW_REPORT_LABELS[number];
type LegacyReportLabel = typeof LEGACY_REPORT_LABELS[number];
type ReportLabel = NewReportLabel | LegacyReportLabel;

const REPORT_META: Record<NewReportLabel, { domain: string; frameId: string; summary: string }> = {
  "IDG Management": { domain: "Clinical", frameId: "267:6", summary: "IDG meetings, notes, and patient review coordination." },
  "Quality Assurance": { domain: "QAPI", frameId: "267:234", summary: "Notes review, QA tracking, and late submission monitoring." },
  "Human Resource": { domain: "Administrative", frameId: "267:518", summary: "Employee directory, credentials, and staffing records." },
  "Print Patient Chart": { domain: "Administrative", frameId: "267:819", summary: "Patient chart print set for chart exports and packet prep." },
  "Infection Control": { domain: "Clinical", frameId: "267:1019", summary: "Infection control review and prevention tracking." },
  "Incident Rate": { domain: "QAPI", frameId: "267:1252", summary: "Incident rate monitoring and quality trend analysis." },
  "Export CAHPS": { domain: "QAPI", frameId: "267:1479", summary: "CAHPS survey export and submission readiness." },
  "Admissions": { domain: "Administrative", frameId: "267:1695", summary: "Admissions tracking and census intake visibility." },
  "Discharge Trend": { domain: "Administrative", frameId: "267:1983", summary: "Discharge volume trends and operational movement." },
  "Emergency Triage": { domain: "Administrative", frameId: "267:2373", summary: "Emergency and disaster triage workflow." },
  "Patient Referral Source": { domain: "Administrative", frameId: "267:2628", summary: "Referral source reporting and patient origin analysis." },
  "Employee Contact List": { domain: "Administrative", frameId: "267:2874", summary: "Employee contacts, role visibility, and directory access." },
  "Outbound Fax": { domain: "Administrative", frameId: "267:3085", summary: "Outbound fax queue and fax transmission log." },
  "Standard Pack": { domain: "Administrative", frameId: "267:3343", summary: "Standard packet templates and document bundles." },
  "Re-Cert List": { domain: "Clinical", frameId: "267:3558", summary: "Recertification list and due-date tracking." },
  "Agency Announcements Hx": { domain: "Administrative", frameId: "267:3788", summary: "Historical agency announcement archive." },
  "HospiceMD Announcements Hx": { domain: "Administrative", frameId: "267:4017", summary: "HospiceMD announcement archive and history." },
  "Bereavement Letter Template": { domain: "Clinical", frameId: "267:4241", summary: "Bereavement letter template editor and defaults." },
  "Bereavement Header/Footer": { domain: "Clinical", frameId: "267:4432", summary: "Bereavement header and footer configuration." },
};

const LEGACY_REPORT_DOMAIN: Record<LegacyReportLabel, string> = {
  "All Visits Report": "Clinical",
  "Missed Visits Report": "Clinical",
  "Supervisory Visit Review": "Clinical",
  "On-Call Log": "Clinical",
  "Missing Consents": "Clinical",
  "SIA Patients/Visits": "Clinical",
  "Submission Log": "Clinical",
  "Pending Prescription": "Clinical",
  "Commonly Used ICD-10 Codes": "Clinical",
  "Commonly Used Medications": "Clinical",
  "Bereavement Calendar": "Clinical",
  "Bereavement Risk Assessment": "Clinical",
  "Late Tracking": "Clinical",
  "Re-Cert List with Dates": "Clinical",
  "F2F Scheduling": "Clinical",
  "Create IDG Notes/Groups": "Clinical",
  "IDG Meetings": "Clinical",
  "Notes To Review": "QAPI",
  "Late Submission Tracking": "QAPI",
  "QA Management Dashboard": "QAPI",
  "Comfortable Dying Measure": "QAPI",
  "Unwanted Hospitalization": "QAPI",
  "Census Integrity Report": "QAPI",
  "Wound Tracking Report": "QAPI",
  "Antibiotics w/o Care Plan": "QAPI",
  "eMAR Report": "QAPI",
  "Patient Acuity Report": "QAPI",
  "Staff Utilization/Productivity": "QAPI",
  "Volunteer Savings Report": "QAPI",
  "Non-Converted Notifications": "QAPI",
  "ADC/ALOS/MLOS Report": "Administrative",
  "Age & Gender Demographics": "Administrative",
  "Patient Profile Report": "Administrative",
  "Diagnosis/Disease Report": "Administrative",
  "Visits By Discipline": "Administrative",
  "Place of Service Report": "Administrative",
  "Level of Care Report": "Administrative",
  "Daily Summary": "Administrative",
  "Medication/DME Orders": "Administrative",
  "Signed Physician Orders": "Administrative",
  "Patients by Zip/City/County": "Administrative",
  "Census Heatmap": "Administrative",
  "Patient Birthday Report": "Administrative",
  "NPI Lookup": "Administrative",
  "Employee Directory": "Administrative",
  "Vendor Management": "Administrative",
  "Payer Source Report": "Administrative",
  "Announcement System": "Administrative",
  "Claims Dashboard": "Billing",
  "RA Reconciliation": "Billing",
  "NOE/NOTR Management": "Billing",
  "Monthly Billing Summary": "Billing",
};

function legacySummary(label: LegacyReportLabel, domain: string) {
  if (label.includes("Visit")) {
    return `${domain} visit workflow for ${label.toLowerCase()}.`;
  }
  if (label.includes("Compliance") || label.includes("Submission") || label.includes("QA") || label.includes("Measure") || label.includes("Wound") || label.includes("eMAR") || label.includes("Acuity") || label.includes("Non-Converted")) {
    return `${domain} quality and compliance view for ${label.toLowerCase()}.`;
  }
  if (label.includes("Billing") || label.includes("Claims") || label.includes("RA") || label.includes("NOE") || label.includes("NOTR")) {
    return `${domain} billing and claims workflow for ${label.toLowerCase()}.`;
  }
  if (label.includes("Employee") || label.includes("Vendor") || label.includes("NPI") || label.includes("Payer") || label.includes("Birthday") || label.includes("Zip") || label.includes("Age") || label.includes("Diagnosis") || label.includes("Patients by")) {
    return `${domain} operations and directory workflow for ${label.toLowerCase()}.`;
  }
  return `${domain} legacy report shell for ${label.toLowerCase()}.`;
}

function ReportShell({ label }: { label: NewReportLabel }) {
  const meta = REPORT_META[label];

  return (
    <Paper variant="outlined" sx={{ borderColor: "#dbe5ea", borderRadius: 2, p: 2, background: "#fff" }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, flexWrap: "wrap", alignItems: "flex-start" }}>
        <Box>
          <Typography sx={{ fontSize: 15, fontWeight: 800, color: "#1f3552" }}>{label}</Typography>
          <Typography sx={{ fontSize: 11.5, color: "#64748b", mt: 0.4 }}>{meta.summary}</Typography>
        </Box>
        <Box sx={{ textAlign: "right" }}>
          <Typography sx={{ fontSize: 11, fontWeight: 800, color: "#0f766e" }}>{meta.domain}</Typography>
          <Typography sx={{ fontSize: 11, color: "#64748b" }}>Figma Frame {meta.frameId}</Typography>
        </Box>
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, gap: 1.25, mt: 2 }}>
        {[
          ["Status", "Navigation only"],
          ["Route Label", label],
          ["Frame ID", meta.frameId],
        ].map(([title, value]) => (
          <Box key={title} sx={{ border: "1px solid #e5edf3", borderRadius: 1.5, p: 1.25, background: "#f8fafc" }}>
            <Typography sx={{ fontSize: 10.5, fontWeight: 800, color: "#64748b", textTransform: "uppercase" }}>{title}</Typography>
            <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: "#1f2937", mt: 0.5 }}>{value}</Typography>
          </Box>
        ))}
      </Box>
      <Typography sx={{ fontSize: 12, color: "#64748b", mt: 2 }}>
        Structured report content is not available yet for this route. This shell now honestly preserves only the report label, domain, and design reference.
      </Typography>
    </Paper>
  );
}

function LegacyReportShell({ label }: { label: LegacyReportLabel }) {
  const domain = LEGACY_REPORT_DOMAIN[label];
  const summary = legacySummary(label, domain);

  return (
    <Paper variant="outlined" sx={{ borderColor: "#dbe5ea", borderRadius: 2, p: 2, background: "#fff" }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, flexWrap: "wrap", alignItems: "flex-start" }}>
        <Box>
          <Typography sx={{ fontSize: 15, fontWeight: 800, color: "#1f3552" }}>{label}</Typography>
          <Typography sx={{ fontSize: 11.5, color: "#64748b", mt: 0.4 }}>{summary}</Typography>
        </Box>
        <Box sx={{ textAlign: "right" }}>
          <Typography sx={{ fontSize: 11, fontWeight: 800, color: "#0f766e" }}>{domain}</Typography>
          <Typography sx={{ fontSize: 11, color: "#64748b" }}>Legacy report shell</Typography>
        </Box>
      </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, gap: 1.25, mt: 2 }}>
        {[
          ["Status", "Navigation only"],
          ["Route Label", label],
          ["Domain", domain],
        ].map(([title, value]) => (
          <Box key={title} sx={{ border: "1px solid #e5edf3", borderRadius: 1.5, p: 1.25, background: "#f8fafc" }}>
            <Typography sx={{ fontSize: 10.5, fontWeight: 800, color: "#64748b", textTransform: "uppercase" }}>{title}</Typography>
            <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: "#1f2937", mt: 0.5 }}>{value}</Typography>
          </Box>
        ))}
      </Box>
      <Typography sx={{ fontSize: 12, color: "#64748b", mt: 2 }}>
        This legacy report route does not currently render a real data-backed report. The old “Live” label has been removed to avoid implying otherwise.
      </Typography>
    </Paper>
  );
}

function shell(label: ReportLabel) {
  if (Object.prototype.hasOwnProperty.call(REPORT_META, label)) {
    return <ReportShell label={label as NewReportLabel} />;
  }

  return <LegacyReportShell label={label as LegacyReportLabel} />;
}

export function IDGManagement() { return shell("IDG Management"); }
export function QualityAssurance() { return shell("Quality Assurance"); }
export function HumanResource() { return shell("Human Resource"); }
export function PrintPatientChart() { return shell("Print Patient Chart"); }
export function InfectionControl() { return shell("Infection Control"); }
export function IncidentRate() { return shell("Incident Rate"); }
export function ExportCAHPS() { return shell("Export CAHPS"); }
export function AdmissionsReport() { return shell("Admissions"); }
export function DischargeTrend() { return shell("Discharge Trend"); }
export function EmergencyTriage() { return shell("Emergency Triage"); }
export function PatientReferralSource() { return shell("Patient Referral Source"); }
export function EmployeeContactList() { return shell("Employee Contact List"); }
export function OutboundFax() { return shell("Outbound Fax"); }
export function StandardPack() { return shell("Standard Pack"); }
export function ReCertList() { return shell("Re-Cert List"); }
export function AgencyAnnouncementsHx() { return shell("Agency Announcements Hx"); }
export function HospiceMDAnnouncementsHx() { return shell("HospiceMD Announcements Hx"); }
export function BereavementLetterTemplate() { return shell("Bereavement Letter Template"); }
export function BereavementHeaderFooter() { return shell("Bereavement Header/Footer"); }

const LEGACY_REPORT_COMPONENTS = LEGACY_REPORT_LABELS.reduce<Record<LegacyReportLabel, () => ReactElement>>((acc, label) => {
  acc[label] = () => shell(label);
  return acc;
}, {} as Record<LegacyReportLabel, () => ReactElement>);

const REPORT_COMPONENTS: Record<ReportLabel, () => ReactElement> = {
  "IDG Management": IDGManagement,
  "Quality Assurance": QualityAssurance,
  "Human Resource": HumanResource,
  "Print Patient Chart": PrintPatientChart,
  "Infection Control": InfectionControl,
  "Incident Rate": IncidentRate,
  "Export CAHPS": ExportCAHPS,
  "Admissions": AdmissionsReport,
  "Discharge Trend": DischargeTrend,
  "Emergency Triage": EmergencyTriage,
  "Patient Referral Source": PatientReferralSource,
  "Employee Contact List": EmployeeContactList,
  "Outbound Fax": OutboundFax,
  "Standard Pack": StandardPack,
  "Re-Cert List": ReCertList,
  "Agency Announcements Hx": AgencyAnnouncementsHx,
  "HospiceMD Announcements Hx": HospiceMDAnnouncementsHx,
  "Bereavement Letter Template": BereavementLetterTemplate,
  "Bereavement Header/Footer": BereavementHeaderFooter,
  ...LEGACY_REPORT_COMPONENTS,
};

function isReportLabel(value: string): value is ReportLabel {
  return Object.prototype.hasOwnProperty.call(REPORT_COMPONENTS, value);
}

export default function SNSNewReports({ activeReport }: { activeReport: string | null }) {
  if (!activeReport || !isReportLabel(activeReport)) return null;

  const Report = REPORT_COMPONENTS[activeReport];
  return <Report />;
}
