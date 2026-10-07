import React, { useEffect, useMemo, useState } from "react";
import { emitRnIcaTelemetry } from "../../features/rnIcaTelemetry";
import {
  ClinicalCommandContextBar,
  ClinicalCommandHeader,
  ClinicalCommandLayout,
  ClinicalCommandWorkspace,
} from "../clinical-command/ClinicalCommandWorkspace";
import {
  validateRnIcaClinicalNavigation,
} from "./rnIcaClinicalNavigation";
import { RNICA_THIRTEEN_SCREENS, groupRoutesIntoScreens, screenForModuleKey } from "./rnicaThirteenScreenTaxonomy";
import { RnicaWorkflowRail, RnicaWorkflowSheet } from "./RnicaWorkflowRail";
import PatientStoryShadcn from "./patient-story/PatientStoryShadcn";
import EvidenceIntakeOverview from "./evidence-intake/EvidenceIntakeOverview";
import HopeAdministrativeReview from "./hope-admin-review/HopeAdministrativeReview";
import PainSymptomBurdenOverview from "./pain-symptom-burden/PainSymptomBurdenOverview";
import DiagnosisLcdOverview from "./diagnosis-lcd/DiagnosisLcdOverview";
import {
  PrimaryCard,
  SourceLink,
  StatusChip,
  DocumentedValue,
  notYetDocumented,
} from "./design-system/RnicaDesignSystem";
import { listBenefitPeriods } from "../../api/benefitPeriods";
import { fetchFacesheet } from "../../api/facesheet";
import { Card as ShadcnCard, CardHeader as ShadcnCardHeader, CardTitle as ShadcnCardTitle, CardContent as ShadcnCardContent } from "../ui/card";
import { Badge as ShadcnBadge } from "../ui/badge";
import { Progress as ShadcnProgress } from "../ui/progress";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "../ui/accordion";
import "./RNICACommandWorkspace.css";

const DENSITY_KEY = "sns-clinical-command-workspace-density";
const LEGACY_DENSITY_KEY = "sns-rnica-workspace-density";
const DENSITIES = ["compact", "comfortable", "large"];
function storedDensity() {
  const value = window.localStorage.getItem(DENSITY_KEY) || window.localStorage.getItem(LEGACY_DENSITY_KEY);
  return DENSITIES.includes(value) ? value : "compact";
}

// Shared, read-only formatters for the persistent clinical context bar
// (used by both the new RnicaScreenShell admission-facts bar and the
// legacy ClinicalCommandContextBar) so every screen presents allergies and
// vitals the same way. `patient` here is the object assembled in
// RNICA.jsx -- nothing is computed or fabricated, only formatted.
function formatAllergies(patient) {
  if (patient?.hasAllergies === false) return "NKA";
  if (patient?.allergiesText) return patient.allergiesText;
  if (patient?.hasAllergies === true) return "Present (see Face Sheet)";
  return null;
}

// Individual vitals facts (owner direction 2026-09-25: the context strip
// must be a single dense row, not a paragraph -- each vital is its own
// short fact so the strip can wrap per-item on narrow viewports instead of
// hiding everything behind one combined sentence).
function vitalsFacts(vitals) {
  if (!vitals) return [];
  return [
    (vitals.bpSystolic && vitals.bpDiastolic) ? { label: "BP", value: `${vitals.bpSystolic}/${vitals.bpDiastolic}` } : null,
    vitals.pulse ? { label: "P", value: vitals.pulse } : null,
    vitals.respirations ? { label: "RR", value: vitals.respirations } : null,
    vitals.temperature ? { label: "Temp", value: `${vitals.temperature}\u00b0${vitals.temperatureUnit || "F"}` } : null,
    vitals.oxygenSaturation ? { label: "O2", value: `${vitals.oxygenSaturation}%` } : null,
    vitals.weight ? { label: "Wt", value: `${vitals.weight} lbs` } : null,
  ].filter(Boolean);
}

function ScrollRegion({ name, className, children }) {
  const [lastBucket, setLastBucket] = useState(-1);
  const handleScroll = (event) => {
    const element = event.currentTarget;
    const max = element.scrollHeight - element.clientHeight;
    const percent = max <= 0 ? 100 : Math.round((element.scrollTop / max) * 100);
    const bucket = percent >= 95 ? 100 : percent >= 75 ? 75 : percent >= 50 ? 50 : percent >= 25 ? 25 : 0;
    if (bucket !== lastBucket) {
      setLastBucket(bucket);
      emitRnIcaTelemetry({ name: "workspace_scroll", region: name, depthBucket: bucket });
    }
  };
  return <div className={`clinical-command-region clinical-command-region--${name} ${className}`} onScroll={handleScroll}>{children}</div>;
}

// Screen 1 -- Patient Story. Read-only, source-linked orientation summary.
// Per RNICA_REDESIGN_SOURCE_OF_TRUTH.md Screen 1: "Owns: Nothing" -- every
// value here is read from data already owned/edited elsewhere (the `patient`
// summary object, existing validation state, and the existing RNICA
// Intelligence output). Nothing is entered or persisted from this panel;
// every item links back to its authoritative screen. Missing source data
// renders "NOT YET DOCUMENTED" rather than being fabricated -- see
// design-system/RnicaDesignSystem.jsx `notYetDocumented()`.
const PATIENT_STORY_RISK_DEFINITIONS = [
  { moduleKey: "safety", label: "Fall Risk Factors", tone: "warning" },
  { moduleKey: "pain", label: "Pain Control", tone: "warning" },
  { moduleKey: "psychosocial", label: "Respiratory / Symptom Concerns", tone: "critical" },
  { moduleKey: "caregiverAssessment", label: "Caregiver Overview", tone: "info" },
];

function PatientStoryPanel({ patient, intelligence, errorKeys, warningKeys, routeForRequirement, saveStatus, saving, onNavigate }) {
  const findings = intelligence?.findings || [];
  const recommendations = intelligence?.recommendations || [];
  const missingEvidence = intelligence?.missing_evidence || intelligence?.summary?.missing_evidence || [];
  const missingCount = errorKeys.length + warningKeys.length;

  const documentedRiskRows = useMemo(() => PATIENT_STORY_RISK_DEFINITIONS
    .map((definition) => {
      const flaggedErrors = errorKeys.filter((key) => routeForRequirement(key)?.key === definition.moduleKey);
      const flaggedWarnings = warningKeys.filter((key) => routeForRequirement(key)?.key === definition.moduleKey);
      const count = flaggedErrors.length + flaggedWarnings.length;
      if (count === 0) return null;
      return {
        ...definition,
        detail: `${count} documented item(s) require review on this screen.`,
      };
    })
    .filter(Boolean), [errorKeys, warningKeys, routeForRequirement]);

  const missingItems = [
    ...missingEvidence.map((item, index) => ({
      key: `evidence-${index}`,
      label: typeof item === "string" ? item : item?.label || item?.text,
    })),
    ...(missingCount > 0
      ? [{ key: "validation", label: `${missingCount} requirement(s) remain across the assessment`, route: "finalization" }]
      : []),
  ];

  const caregiver = patient.caregiver || {};
  const caregiverSummary = caregiver.noPcg
    ? "No primary caregiver identified"
    : [caregiver.name, caregiver.relationship].filter(Boolean).join(" \u2014 ");

  const functionalDecline = patient.functionalDeclineNarrative;

  return (
    <PatientStoryShadcn
      patient={patient}
      intelligence={intelligence}
      findings={findings}
      recommendations={recommendations}
      missingItems={missingItems}
      documentedRiskRows={documentedRiskRows}
      caregiver={caregiver}
      caregiverSummary={caregiverSummary}
      functionalDecline={functionalDecline}
      saveStatus={saveStatus}
      saving={saving}
      onNavigate={onNavigate}
    />
  );
}

// Screen 2 -- Evidence & Intake. Per RNICA_REDESIGN_SOURCE_OF_TRUTH.md
// Screen 2: "Conditionally visible: Missing-source alerts ... appear only
// when applicable" and "Required actions: Review intake evidence and
// resolve missing required intake/referral documentation." This reuses the
// existing validation state already computed for the workspace -- it adds
// no new field, rule, or data source -- and only surfaces items already
// scoped to this screen's three legacy modules (demographics, vitals,
// referrals), e.g. the existing `referrals.reviewed` requirement.
function EvidenceIntakeAlertBanner({ errorKeys, warningKeys, routeForRequirement, onNavigate }) {
  // `referrals` (discipline referrals) moved to Orders & POC -- see
  // rnicaThirteenScreenTaxonomy.js. This banner only scopes to modules this
  // screen still owns.
  const screenModuleKeys = new Set(["demographics", "vitals"]);
  const scoped = [...errorKeys, ...warningKeys]
    .map((key) => ({ key, route: routeForRequirement(key) }))
    .filter(({ route }) => route && screenModuleKeys.has(route.key));
  if (scoped.length === 0) return null;
  return (
    <PrimaryCard
      title="Missing Intake Evidence"
      subtitle="Resolve missing required intake/referral documentation for this screen."
      actions={<StatusChip tone="warning">{scoped.length} item(s)</StatusChip>}
      aria-live="polite"
    >
      {scoped.slice(0, 8).map(({ key, route }) => (
        <SourceLink key={key} onClick={() => onNavigate(route.key)}>{route.label}: {key}</SourceLink>
      ))}
    </PrimaryCard>
  );
}

function NarrativeFinalReviewPanel({ completedSections, totalSections, missingCount }) {
  const [draftState, setDraftState] = useState("not prepared");
  const focusClinicalNarrative = () => {
    document.querySelector("#rnica-clinical-narrative textarea")?.focus();
  };
  return (
    <section className="clinical-command-card rnica-command-card rnica-command-narrative" aria-labelledby="narrative-final-review-title">
      <div className="rnica-command-card__heading">
        <h2 id="narrative-final-review-title">Narrative &amp; final review</h2>
        <span className="rnica-command-state">{draftState}</span>
      </div>
      <p>
        Synthesize the completed assessment and source-linked encounter capture only after bedside documentation is complete.
        Missing documentation is not interpreted as a negative finding. The authoritative Clinical narrative field is directly below this review.
      </p>
      <div className="rnica-command-review">
        <strong>Source set</strong>
        <span>{completedSections} of {totalSections} assessment sections documented · {missingCount} requirement(s) remain</span>
      </div>
      {draftState === "not prepared" ? (
        <button type="button" onClick={() => setDraftState("review required")}>Prepare structured draft</button>
      ) : (
        <div className="rnica-command-review" role="status">
          <strong>Structured draft review required</strong>
          <span>Review source links and uncertainty items, then accept, edit, or reject before attestation. This action never signs, locks, or finalizes the assessment.</span>
          <div className="rnica-command-actions">
            <button type="button" onClick={() => setDraftState("accepted")}>Accept draft</button>
            <button type="button" onClick={() => setDraftState("editing")}>Edit draft</button>
            <button type="button" onClick={() => setDraftState("rejected")}>Reject draft</button>
          </div>
        </div>
      )}
      <button type="button" className="is-secondary" onClick={focusClinicalNarrative}>Review Clinical narrative field</button>
    </section>
  );
}

// True standalone RNICA screen shell -- replaces the legacy Clinical Command
// Workspace chrome entirely (patient bar eyebrow, context-prep bar, module
// navigator, quick-access grid, Validation/Intelligence rail) for screens
// that have been rebuilt into the approved 13-screen redesign. It renders
// only: a compact identity/status bar, the 13-screen tab strip, the screen's
// own content, and the save/lock controls -- there is no old-workspace
// content behind it.
function RnicaScreenShell({ patient, locked, completedSections, totalRoutes, activeScreenKey, onSelectScreenTab, onExitPilot, saving, saveStatus, onSave, onLock, canLock, statusContext, density, onChangeDensity, updateAssessmentContext, children }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  return (
    <div className={`rnica-screen rnica-screen--${density || "compact"}`}>
      <header className="rnica-screen__bar">
        <div className="rnica-screen__identity">
          <span className="rnica-command-eyebrow">RNICA</span>
          <strong>{patient.name}</strong>
          <span>MRN {patient.mrn}</span>
          {!notYetDocumented(patient.assessmentStage) && <StatusChip tone="warning">{patient.assessmentStage}</StatusChip>}
        </div>
        <div className="rnica-screen__admission-facts" aria-label="Persistent clinical context (read-only)">
          <span><em>Dx</em> <DocumentedValue value={patient.primaryDiagnosis} /></span>
          <span><em>2nd Dx</em> <DocumentedValue value={patient.secondaryDiagnoses} /></span>
          <span><em>Allergies</em> <DocumentedValue value={formatAllergies(patient)} /></span>
          <span><em>PPS</em> <DocumentedValue value={patient.currentPps ? `${patient.currentPps}%` : null} /></span>
          {vitalsFacts(patient.vitals).map((fact) => (
            <span key={fact.label}><em>{fact.label}</em> {fact.value}</span>
          ))}
          <span><em>Decline</em> <DocumentedValue value={patient.functionalDeclineNarrative} /></span>
          <span><em>Admit</em> <DocumentedValue value={patient.admissionDate} /></span>
          <span><em>BP#</em> <DocumentedValue value={patient.benefitPeriodNumber ? `${patient.benefitPeriodNumber} (${patient.benefitPeriodStart || "?"}\u2013${patient.benefitPeriodEnd || "?"})` : null} /></span>
          <span><em>Recert</em> <DocumentedValue value={patient.recertDueDate} /></span>
          <span><em>F2F</em> <DocumentedValue value={patient.faceToFaceDueDate} /></span>
        </div>
        <div className="rnica-screen__status">
          <span className={`clinical-command-status rnica-command-badge ${locked ? "is-complete" : "is-active"}`}>{locked ? "Locked" : "In progress"}</span>
          <span>{completedSections.length}/{totalRoutes} sections</span>
          <button
            type="button"
            className="rnica-screen__mobile-nav-trigger"
            aria-haspopup="dialog"
            onClick={() => setMobileNavOpen(true)}
          >
            Workflow
          </button>
          <button type="button" onClick={onExitPilot}>Use classic view</button>
        </div>
      </header>

      <div className="rnica-screen__body">
        <RnicaWorkflowRail
          activeScreenKey={activeScreenKey}
          onSelectScreen={onSelectScreenTab}
          statusContext={statusContext}
          density={density}
          onChangeDensity={onChangeDensity}
        />
        <main className="rnica-screen__content">
          {/* R3 Command Workspace parity repair: the 6 dedicated RNICA
              screens (Patient Story, HOPE Administrative Review, Evidence
              & Intake, Pain/Symptom Burden, Diagnosis & LCD, Body Systems)
              each early-return their own <RnicaScreenShell> tree, bypassing
              the generic detail layout below where updateAssessmentContext
              was originally wired. Rendering it once here, in the one
              shell every dedicated screen shares, restores true parity
              without duplicating the banner/POC JSX at each call site. */}
          {updateAssessmentContext}
          {children}
        </main>
      </div>

      <RnicaWorkflowSheet
        open={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        activeScreenKey={activeScreenKey}
        onSelectScreen={onSelectScreenTab}
        statusContext={statusContext}
      />

      <footer className="rnica-screen__footer">
        <span>{saveStatus === "saved" ? "Saved" : saving ? "Saving\u2026" : "Autosave active"}</span>
        <div className="rnica-screen__footer-actions">
          <button type="button" disabled={saving || locked} onClick={onSave}>{saving ? "Saving\u2026" : "Save assessment"}</button>
          {canLock && !locked && <button type="button" className="is-secondary" onClick={onLock}>Validate &amp; lock</button>}
        </div>
      </footer>
    </div>
  );
}

export default function RNICACommandWorkspace({
  patient,
  routes,
  formSections,
  activeSection,
  completedSections,
  validation,
  locked,
  saving,
  saveStatus,
  intelligence,
  renderWorkspaceSections,
  bodySystemsAccordionItems,
  bodySystemsStructuredFindings,
  visitRecorder,
  alerts,
  // R3 Command Workspace parity repair (Owner Directive): pre-built JSX
  // (UpdateAssessmentContextBanner + PlanOfCareReviewPanel from RNICA.jsx)
  // giving this view the same Update Assessment change-of-condition
  // context and assessment-scoped Plan of Care review gate the classic
  // view already has. Same pass-a-built-node pattern as `alerts`/
  // `visitRecorder` above -- no second implementation lives here.
  updateAssessmentContext,
  onSelect,
  onSave,
  onLock,
  onPrevious,
  onNext,
  onExitPilot,
  canLock,
  isOngoingAssessment = false,
  isUpdateAssessment = false,
  onUpdateField,
  painData,
  symptomImpactData,
  patientAge,
  renderPainStepCards,
  diagnosesData,
  renderDiagnosisStepCards,
}) {
  // Persistent admission/benefit-period reference facts (benefit period #,
  // dates, recert due, allergies, F2F due). Read-only -- sourced live from
  // the Benefit Period API and the Face Sheet facesheet endpoint, never
  // copied into RNICA form state, per owner direction that RNICA must not
  // duplicate other modules' data or touch the Face Sheet. Recert Due is
  // the current benefit period's end date (the date recertification must
  // be completed by), not a separately fabricated field. Allergies: the
  // Face Sheet (`clinical.has_allergies`/`clinical.allergies`) is the
  // authoritative, already-live source for this read-only display --
  // resolves the prior "two conflicting ownership claims" note in
  // PATIENT_CHART_AUTHORITY_MAP.md pragmatically for display purposes only
  // (this does not settle Medications-module write ownership, which is a
  // separate concern from showing the current value here).
  const [admissionFacts, setAdmissionFacts] = useState({
    benefitPeriodLabel: null,
    benefitPeriodStart: null,
    benefitPeriodEnd: null,
    benefitPeriodNumber: null,
    recertDueDate: null,
    allergiesText: null,
    hasAllergies: null,
    faceToFaceDueDate: null,
  });
  useEffect(() => {
    let cancelled = false;
    if (!patient?.id) return undefined;
    Promise.all([
      listBenefitPeriods(patient.id).catch(() => []),
      fetchFacesheet(patient.id).catch(() => null),
    ]).then(([benefitPeriods, facesheet]) => {
      if (cancelled) return;
      const current = (benefitPeriods || []).find((bp) => bp.is_current) || (benefitPeriods || [])[0] || null;
      setAdmissionFacts({
        benefitPeriodLabel: current
          ? `#${current.period_number} (${current.benefit_type === "RECERT" ? "Recert" : "Initial"}) \u00b7 ${current.start_date || "?"} \u2013 ${current.end_date || "?"}`
          : null,
        benefitPeriodStart: current?.start_date || null,
        benefitPeriodEnd: current?.end_date || null,
        benefitPeriodNumber: current?.period_number ?? null,
        recertDueDate: current?.end_date || null,
        allergiesText: facesheet?.clinical?.allergies || null,
        hasAllergies: facesheet?.clinical?.has_allergies ?? null,
        faceToFaceDueDate: facesheet?.service_dates?.face_to_face_due_date || null,
      });
    });
    return () => { cancelled = true; };
  }, [patient?.id]);
  const patientWithAdmissionFacts = useMemo(() => ({ ...patient, ...admissionFacts }), [patient, admissionFacts]);

  const [density, setDensity] = useState(storedDensity);
  const [viewMode, setViewMode] = useState("screen");
  const [genericNavOpen, setGenericNavOpen] = useState(false);
  // GitHub Directive (2026-09-28) "Final Neurological Density and
  // Space-Utilization Plan" Section 4/32/41 -- Structured Findings must
  // collapse to a compact rail (reclaiming width for the central
  // workspace) whenever it has no findings, and remain user-expandable at
  // any time. `null` means "no explicit user choice yet" so the rail
  // auto-tracks whether findings exist; once the user manually toggles it
  // that explicit choice is respected until they toggle again.
  const [findingsRailExpanded, setFindingsRailExpanded] = useState(null);
  // 13-screen presentation grouping (Phase B). This groups the same,
  // unchanged module routes under the approved 13-screen taxonomy -- it
  // does not add, remove, or reorder any module's content, validation, or
  // data. See rnicaThirteenScreenTaxonomy.js.
  const screenGroups = useMemo(() => groupRoutesIntoScreens(routes), [routes]);
  const activeScreen = useMemo(() => screenForModuleKey(activeSection), [activeSection]);
  const activeScreenIndex = activeScreen
    ? RNICA_THIRTEEN_SCREENS.findIndex((screen) => screen.key === activeScreen.key)
    : -1;
  const selectCrossCuttingScreen = (screen) => {
    if (screen.key === "patientStory") {
      setViewMode("patientStory");
      emitRnIcaTelemetry({ name: "section_jump", section: "patientStory", source: "screen:patientStory" });
      return;
    }
    setViewMode("screen");
    onSelect(screen.landingModuleKey);
    emitRnIcaTelemetry({ name: "section_jump", section: screen.landingModuleKey, source: `screen:${screen.key}` });
    if (screen.railTarget === "validation") setValidationOpen(true);
    requestAnimationFrame(() => {
      document.querySelector(`[data-rnica-rail-target="${screen.railTarget}"]`)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };
  const errorKeys = Object.keys(validation.errors);
  const warningKeys = Object.keys(validation.warnings);
  const routeForRequirement = (key) => [...routes]
    .sort((a, b) => (b.validationPrefix || b.formSection).length - (a.validationPrefix || a.formSection).length)
    .find((route) => key === (route.validationPrefix || route.formSection)
      || key.startsWith(`${route.validationPrefix || route.formSection}.`));
  const navigationAudit = useMemo(
    () => validateRnIcaClinicalNavigation(routes, formSections, isOngoingAssessment, isUpdateAssessment),
    [formSections, routes, isOngoingAssessment, isUpdateAssessment],
  );
  if (import.meta.env.DEV && !navigationAudit.valid) {
    throw new Error(`Invalid RNICA clinical navigation: ${navigationAudit.errors.join("; ")}`);
  }
  const scrollDetailTop = () => {
    requestAnimationFrame(() => document.querySelector(".rnica-command-detail")?.scrollTo({ top: 0, behavior: "smooth" }));
  };

  useEffect(() => {
    emitRnIcaTelemetry({ name: "completion_viewed", completed: completedSections.length, total: routes.length });
  }, [completedSections.length, routes.length]);

  const select = (key, source = "navigator") => {
    setViewMode("screen");
    onSelect(key);
    scrollDetailTop();
    emitRnIcaTelemetry({ name: "section_jump", section: key, source });
  };

  const changeDensity = (nextDensity) => {
    setDensity(nextDensity);
    window.localStorage.setItem(DENSITY_KEY, nextDensity);
    emitRnIcaTelemetry({ name: "density_changed", density: nextDensity });
  };

  // RNICA Diagnosis & LCD Workspace Optimization (owner directive FR-002):
  // global workspace toolbar. "Voice Documentation" toggles the Visit
  // Recording drawer (previously rendered permanently at the top of every
  // screen -- see visitRecorderOpen below); "AI Assist" and "HOPE Report"
  // reuse the existing cross-cutting screen navigation to the real
  // AI Action Center / Compliance & Readiness rail panels (no new
  // panels/data -- those are the only working surfaces for this content);
  // "Classic View" reuses the existing exitPilot confirm-and-switch flow.
  const [visitRecorderOpen, setVisitRecorderOpen] = useState(false);
  // FR-011: the persistent Validation drawer is collapsed by default so
  // it doesn't dominate the rail; the RN expands it deliberately, same
  // pattern as the LCD groups and HOPE Comorbidities category groups.
  const [validationOpen, setValidationOpen] = useState(false);
  const aiActionCenterScreen = RNICA_THIRTEEN_SCREENS.find((screen) => screen.key === "aiActionCenter");
  const complianceReadinessScreen = RNICA_THIRTEEN_SCREENS.find((screen) => screen.key === "complianceReadiness");

  const exitPilot = () => {
    if (window.confirm("Switch to the classic RN ICA view? Save or finish any open tool drafts before switching presentations.")) {
      onExitPilot?.();
    }
  };

  // Screen-tab navigation used by the standalone RnicaScreenShell (below).
  // Cross-cutting screens (Patient Story, Compliance & Readiness, AI Action
  // Center) keep their existing selectCrossCuttingScreen behavior; module
  // screens jump into the legacy workspace at their first module, exactly
  // like the old navigator did, until each screen is rebuilt in its own
  // implementation-order turn.
  const selectScreenTab = (screen) => {
    if (screen.crossCutting) {
      selectCrossCuttingScreen(screen);
      return;
    }
    setViewMode("screen");
    const landing = screen.moduleKeys[0];
    onSelect(landing);
    emitRnIcaTelemetry({ name: "section_jump", section: landing, source: `screen_tab:${screen.key}` });
  };

  const evidenceIntakeGroup = useMemo(
    () => screenGroups.find((group) => group.key === "evidenceIntake"),
    [screenGroups],
  );

  // Shared status data for the RNICA workflow rail/sheet -- reuses the same
  // completedSections/validation state already computed above; introduces
  // no new clinical rule or source of truth (presentation only).
  const railStatusContext = { completedSections, errorKeys, warningKeys, routeForRequirement };

  if (viewMode === "patientStory") {
    // Patient Story is a true standalone RNICA screen: no legacy Clinical
    // Command Workspace chrome renders behind it (no eyebrow/context bar,
    // no module navigator, no quick-access grid, no generic
    // Validation/Intelligence rail -- those all live inside PatientStoryPanel
    // itself, sourced from the same data).
    return (
      <RnicaScreenShell
        patient={patientWithAdmissionFacts}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="patientStory"
        updateAssessmentContext={updateAssessmentContext}
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
        statusContext={railStatusContext}
        density={density}
        onChangeDensity={changeDensity}
      >
        <PatientStoryPanel
          patient={patient}
          intelligence={intelligence}
          errorKeys={errorKeys}
          warningKeys={warningKeys}
          routeForRequirement={routeForRequirement}
          saveStatus={saveStatus}
          saving={saving}
          onNavigate={(key) => select(key, "patient_story")}
        />
      </RnicaScreenShell>
    );
  }

  if (viewMode === "screen" && activeScreen?.key === "hopeAdministrativeReview") {
    // [OWNER DESIGN DECISION -- 2026-09-25, RESTORED] HOPE Administrative
    // Review is restored as its own standalone RNICA screen (owner
    // rejected the 2026-09-25 consolidation into Evidence & Intake --
    // "RESTORE THIS ONE" / "THATS WHAT YOU DESTROYED", referring to the
    // original 14-screen navigation). It is NOT a duplicate Face Sheet and
    // NOT part of Evidence & Intake or Psychosocial. It renders the CMS
    // Section A administrative items (A1005/A1010/A1110 x2/A1905/A1910)
    // via HopeAdministrativeReview, reading/writing the same
    // `formData.demographics` / `formData.livingSituation` state as
    // before -- no persistence path change, no schema change.
    return (
      <RnicaScreenShell
        patient={patientWithAdmissionFacts}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="hopeAdministrativeReview"
        updateAssessmentContext={updateAssessmentContext}
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
        statusContext={railStatusContext}
        density={density}
        onChangeDensity={changeDensity}
      >
        <HopeAdministrativeReview
          value={patient.administrativeDemographics}
          onUpdateField={onUpdateField}
          locked={locked}
        />
        <nav className="rnica-command-stepnav rnica-screen__stepnav" aria-label="Section navigation">
          <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
          <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
        </nav>
      </RnicaScreenShell>
    );
  }

  if (viewMode === "screen" && activeScreen?.key === "evidenceIntake" && evidenceIntakeGroup) {
    // Evidence & Intake is the first substantive RNICA screen after Patient
    // Story. Per owner direction: vitals are continuous clinical context,
    // not a sub-navigation tab -- they render inline, always visible, as
    // the Clinical Snapshot leading the screen, above the evidence review
    // content (2026-09-25 owner correction: "Do not bury vitals beneath
    // evidence sections."). Discipline referrals (social work/spiritual
    // care/volunteer/etc.) live under Orders & POC -- see
    // rnicaThirteenScreenTaxonomy.js. The former "Patient Demographics" tab
    // is replaced by EvidenceIntakeOverview -- per owner direction, RNICA
    // must not store or edit a second copy of Face Sheet demographics. It
    // shows the real intake evidence pipeline (referral evidence, imported
    // clinical documents, AI-extracted structured findings), sourced live
    // -- nothing here is captured or persisted by RNICA.
    return (
      <RnicaScreenShell
        patient={patientWithAdmissionFacts}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="evidenceIntake"
        updateAssessmentContext={updateAssessmentContext}
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
        statusContext={railStatusContext}
        density={density}
        onChangeDensity={changeDensity}
      >
        {/* Clinical Snapshot (vitals) renders first -- 2026-09-25 owner
            direction: "Do not bury vitals beneath evidence sections."
            Vitals are continuous clinical context and must lead the
            screen, not trail the AI/evidence review content below. */}
        <section className="rnica-screen__inline-vitals" aria-label="Vitals & measurements">
          {renderWorkspaceSections(["vitals"])}
        </section>
        <EvidenceIntakeAlertBanner
          errorKeys={errorKeys}
          warningKeys={warningKeys}
          routeForRequirement={routeForRequirement}
          onNavigate={(key) => select(key, "evidence_intake_banner")}
        />
        <EvidenceIntakeOverview
          patientId={patient.id}
          intelligence={intelligence}
          onNavigate={(key) => select(key, "evidence_intake_overview")}
        />
        <nav className="rnica-command-stepnav rnica-screen__stepnav" aria-label="Section navigation">
          <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
          <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
        </nav>
      </RnicaScreenShell>
    );
  }

  if (viewMode === "screen" && activeScreen?.key === "painSymptomBurden") {
    // Pain Assessment is its own standalone RNICA screen. Owner
    // correction 2026-09-25: Symptom Impact Screening ("J2051 A-H") is
    // NOT rendered here as its own RN-facing section -- pain, dyspnea,
    // nausea/vomiting/diarrhea/constipation, and anxiety/agitation are
    // each documented exactly once, in their true owning section (Pain
    // Assessment, Respiratory, GI, Neuro/Mental Status). HOPE J2051
    // derivation/export/SFV/reporting logic still runs silently in the
    // background off those source fields (see the symptomImpact sync
    // effect) -- there is simply no duplicate RN-facing entry surface.
    return (
      <RnicaScreenShell
        patient={patientWithAdmissionFacts}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="painSymptomBurden"
        updateAssessmentContext={updateAssessmentContext}
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
        statusContext={railStatusContext}
        density={density}
        onChangeDensity={changeDensity}
      >
        <PainSymptomBurdenOverview
          painData={painData}
          symptomImpactData={symptomImpactData}
          patientAge={patientAge}
          renderPainStepCards={renderPainStepCards}
          onNavigateToSymptom={(moduleKey) => select(moduleKey, "pain_symptom_burden_matrix")}
          onContinue={() => { onNext(); scrollDetailTop(); }}
        />
        <nav className="rnica-command-stepnav rnica-screen__stepnav" aria-label="Section navigation">
          <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
          <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
        </nav>
      </RnicaScreenShell>
    );
  }

  if (viewMode === "screen" && activeScreen?.key === "diagnosisLcd") {
    // "Diagnosis & LCD" screen, presentation-only Pain/Neuro interaction-
    // model pass (owner directive, 2026-10): "Do not redesign Diagnosis &
    // LCD... change presentation only." Same renderGenericSection /
    // SECTION_CONFIGS.diagnoses fields, HOPE mappings (I0010, I0100-I8005),
    // and LCD validation as before -- only how much is permanently visible
    // vs. behind a focused Edit action changed. See
    // DiagnosisLcdOverview.jsx for the full rationale.
    return (
      <RnicaScreenShell
        patient={patientWithAdmissionFacts}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="diagnosisLcd"
        updateAssessmentContext={updateAssessmentContext}
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
        statusContext={railStatusContext}
        density={density}
        onChangeDensity={changeDensity}
      >
        <DiagnosisLcdOverview
          diagnosesData={diagnosesData}
          renderDiagnosisStepCards={renderDiagnosisStepCards}
          onContinue={() => { onNext(); scrollDetailTop(); }}
        />
        <nav className="rnica-command-stepnav rnica-screen__stepnav" aria-label="Section navigation">
          <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
          <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
        </nav>
      </RnicaScreenShell>
    );
  }

  if (viewMode === "screen" && activeScreen?.key === "bodySystems") {
    // Body Systems is a presentation-only consolidation of the 10 body
    // system modules (Neuro, CV, Respiratory, Infection, GI, Nutrition,
    // Endocrine, GU, Musculoskeletal, Skin) into ONE compact accordion
    // screen instead of a one-at-a-time wizard, per 2026 owner directive
    // ("Body Systems Review — Preserve HOPE + Preserve SFV + Do Not Move
    // Safety Content Into Body Systems"). Every accordion item reuses the
    // exact same field config / HOPE mapping / POC controls as legacy,
    // non-grouped rendering (see bodySystemsAccordionItems in RNICA.jsx) --
    // nothing about matching, validation, or data is changed here. Falls,
    // Safety, and Disaster Triage remain their own independent screen
    // (safetyClinicalRisk) and are never rendered here, per the owner's
    // explicit "do not move Safety/Falls into Body Systems" warning. Skin
    // stays a full body-system accordion item (not reduced to a checkbox)
    // since it is already its own module with its own field depth.
    const reviewedCount = (bodySystemsAccordionItems || []).filter((item) => item.reviewed).length;
    const totalSystems = (bodySystemsAccordionItems || []).length;
    // OWNER DIRECTIVE (2026-10-04) Density Optimization Pass item #9 --
    // bodySystemsStructuredFindings is now an array of per-system groups
    // ({ key, label, icon, findings: [...] }), not a flat string array;
    // total count is the sum of each group's findings.
    const findingsGroups = bodySystemsStructuredFindings || [];
    const findingsCount = findingsGroups.reduce((sum, group) => sum + (group.findings?.length || 0), 0);
    // Auto-collapse when empty unless the user has explicitly expanded it;
    // once findings appear, auto-expand unless the user explicitly
    // collapsed it. `findingsRailExpanded` (state) is the explicit
    // override; `null` defers to this auto behavior.
    const railExpanded = findingsRailExpanded === null ? findingsCount > 0 : findingsRailExpanded;
    return (
      <RnicaScreenShell
        patient={patientWithAdmissionFacts}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="bodySystems"
        updateAssessmentContext={updateAssessmentContext}
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
        statusContext={railStatusContext}
        density={density}
        onChangeDensity={changeDensity}
      >
        <div className={`rnica-bodysystems${railExpanded ? "" : " rnica-bodysystems--rail-collapsed"}`}>
          <div className="rnica-bodysystems__main">
            <div className="rnica-bodysystems__status">
              <span className="rnica-bodysystems__status-label">System Assessment Status</span>
              <ShadcnProgress
                value={totalSystems ? (reviewedCount / totalSystems) * 100 : 0}
                className="rnica-bodysystems__progress"
              />
              <span className="rnica-bodysystems__status-count">{reviewedCount} of {totalSystems} Systems Reviewed</span>
            </div>
            <Accordion type="multiple" className="rnica-bodysystems__accordion">
              {(bodySystemsAccordionItems || []).map((item) => (
                <AccordionItem key={item.key} value={item.key} className="rnica-bodysystems__item">
                  <AccordionTrigger className="rnica-bodysystems__trigger">
                    <span className="rnica-bodysystems__trigger-label">
                      <span aria-hidden="true">{item.icon}</span> {item.label}
                    </span>
                    {/* Bounded Compatibility Increment (2026-09-28) Section 5 --
                        Neurological supplies its own richer statusLabel/
                        statusVariant (Not Started / In Progress / Review
                        Required / Ready for Review) computed in RNICA.jsx's
                        computeNeurologicalWorkflowStatus. Every other body
                        system leaves these undefined and keeps the exact
                        original Reviewed/Not-started boolean badge. */}
                    <ShadcnBadge variant={item.statusVariant || (item.reviewed ? "success" : "neutral")}>
                      {item.statusLabel || (item.reviewed ? "Reviewed" : "Not started")}
                    </ShadcnBadge>
                  </AccordionTrigger>
                  <AccordionContent className="rnica-bodysystems__content">{item.content}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
          {/* GitHub Directive (2026-09-28) Section 4/32 -- when empty,
              collapse to a narrow rail with a compact count instead of
              reserving a large blank card; reclaim that width for the
              central workspace. Always user-expandable/collapsible. */}
          {railExpanded ? (
            <aside className="rnica-bodysystems__rail">
              <ShadcnCard className="rnica-bodysystems__findings">
                <ShadcnCardHeader className="rnica-bodysystems__findings-header">
                  <ShadcnCardTitle>
                    Structured Findings{findingsCount ? ` (${findingsCount})` : ""}
                  </ShadcnCardTitle>
                  <button
                    type="button"
                    className="rnica-bodysystems__rail-toggle"
                    onClick={() => setFindingsRailExpanded(false)}
                    aria-label="Collapse Structured Findings panel"
                  >
                    Collapse
                  </button>
                </ShadcnCardHeader>
                <ShadcnCardContent>
                  {/* Deterministic restatement of already-charted fields only
                      -- never generated/inferred/predicted. See
                      bodySystemsStructuredFindings in RNICA.jsx.
                      OWNER DIRECTIVE (2026-10-04) Density Optimization Pass
                      item #9 -- "true reviewer workspace": grouped by body
                      system (icon + label + count) instead of one flat,
                      unattributed bullet list, so a reviewer can tell at a
                      glance which system each finding came from. Same
                      strings, same source fields -- grouping/labels only. */}
                  {findingsGroups.length ? (
                    <div className="rnica-bodysystems__findings-groups">
                      {findingsGroups.map((group) => (
                        <div key={group.key} className="rnica-bodysystems__findings-group">
                          <div className="rnica-bodysystems__findings-group-header">
                            <span aria-hidden="true">{group.icon}</span>
                            <span className="rnica-bodysystems__findings-group-label">{group.label}</span>
                            <ShadcnBadge variant="neutral" className="rnica-bodysystems__findings-group-count">
                              {group.findings.length}
                            </ShadcnBadge>
                          </div>
                          <ul className="rnica-bodysystems__findings-list">
                            {group.findings.map((finding, idx) => (
                              <li key={idx}>{finding}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="rnica-bodysystems__findings-empty">No structured findings documented yet.</p>
                  )}
                </ShadcnCardContent>
              </ShadcnCard>
            </aside>
          ) : (
            <button
              type="button"
              className="rnica-bodysystems__rail-collapsed-toggle"
              onClick={() => setFindingsRailExpanded(true)}
              aria-label="Expand Structured Findings panel"
              title="Structured Findings"
            >
              <span className="rnica-bodysystems__rail-collapsed-count">{findingsCount}</span>
              <span className="rnica-bodysystems__rail-collapsed-label">Structured Findings</span>
            </button>
          )}
        </div>
        <nav className="rnica-command-stepnav rnica-screen__stepnav" aria-label="Section navigation">
          <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
          <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
        </nav>
      </RnicaScreenShell>
    );
  }

  return (
    <ClinicalCommandWorkspace density={density} ariaLabel="RN ICA Clinical Command Workspace" className="rnica-command">
      <ClinicalCommandHeader className="rnica-command-patientbar">
        <div className="rnica-command-patientbar__identity">
          <span className="rnica-command-eyebrow">RN ICA · Clinical Command Workspace pilot</span>
          <strong>{patient.name}</strong>
          <span>MRN {patient.mrn} · {patient.primaryDiagnosis || "Primary diagnosis not documented"}</span>
        </div>
        <div className="rnica-command-patientbar__status">
          <span className={`clinical-command-status rnica-command-badge ${locked ? "is-complete" : "is-active"}`}>{locked ? "Locked" : "In progress"}</span>
          <span>{completedSections.length}/{routes.length} sections</span>
          {activeScreenIndex >= 0 && <span>Screen {activeScreenIndex + 1} of {RNICA_THIRTEEN_SCREENS.length}</span>}
          {/* Same mobile workflow-nav trigger pattern as RnicaScreenShell
              (owner correction 2026-09-26: RnicaWorkflowRail must work for
              every RNICA screen, not just the 4 dedicated-shell ones). */}
          <button
            type="button"
            className="rnica-screen__mobile-nav-trigger"
            aria-haspopup="dialog"
            onClick={() => setGenericNavOpen(true)}
          >
            Workflow
          </button>
        </div>
      </ClinicalCommandHeader>

      {/* RNICA Workspace toolbar (owner directive FR-002) -- global, so it
          applies to every screen using this shared layout, not only
          Diagnosis & LCD. Each button reuses existing, already-working
          surfaces; nothing here is a new panel or data source. */}
      <div className="rnica-command-toolbar" role="toolbar" aria-label="RNICA Workspace">
        <button
          type="button"
          className={`rnica-command-toolbar__btn ${visitRecorderOpen ? "is-active" : ""}`}
          aria-pressed={visitRecorderOpen}
          onClick={() => setVisitRecorderOpen((current) => !current)}
        >
          Voice Documentation
        </button>
        <button
          type="button"
          className="rnica-command-toolbar__btn"
          onClick={() => aiActionCenterScreen && selectCrossCuttingScreen(aiActionCenterScreen)}
        >
          AI Assist
        </button>
        <button
          type="button"
          className="rnica-command-toolbar__btn"
          onClick={() => complianceReadinessScreen && selectCrossCuttingScreen(complianceReadinessScreen)}
        >
          HOPE Report
        </button>
        <button type="button" className="rnica-command-toolbar__btn" onClick={exitPilot}>
          Classic View
        </button>
        {/* Compact "Jump To" replacement for the removed Bedside Quick
            Access / Assessment Modules panel (owner directive
            2026-09-26): RNICA Workflow Navigation (left navigator) remains
            the single source of workflow navigation -- this is a
            secondary, space-neutral shortcut, not a second nav system. */}
        <label className="rnica-command-toolbar__jump">
          <span>Jump to</span>
          <select value={activeSection} onChange={(event) => select(event.target.value, "jump_to")}>
            {routes.map((route) => (
              <option key={route.key} value={route.key}>{route.label}</option>
            ))}
          </select>
        </label>
      </div>

      <ClinicalCommandContextBar className="rnica-command-prep" ariaLabel="Before visit patient context">
        <div><span>Primary</span><strong>{patient.primaryDiagnosis || "Not documented"}</strong></div>
        <div><span>Secondary</span><strong>{patient.secondaryDiagnoses || "None documented"}</strong></div>
        <div><span>Comorbidities</span><strong>{patient.comorbidities || "None verified"}</strong></div>
        <div><span>Prior issues</span><strong>{patient.priorIssues}</strong></div>
        <div><span>Expected symptoms</span><strong>Review disease-process prompts; document only observed findings</strong></div>
      </ClinicalCommandContextBar>

      <ClinicalCommandLayout className="rnica-command-layout">
        <RnicaWorkflowRail
          activeScreenKey={activeScreen?.key}
          onSelectScreen={selectScreenTab}
          statusContext={railStatusContext}
          density={density}
          onChangeDensity={changeDensity}
        />
        <ScrollRegion name="detail" className="rnica-command-detail">
          <>
              {/* FR-002/FR-005: Visit Recording is no longer a permanent
                  card -- it renders only inside the toolbar-controlled
                  drawer, same VisitRecorderCard/props as before. */}
              {visitRecorderOpen && (
                <div className="rnica-command-voice-drawer" data-rnica-rail-target="voice-documentation">
                  {visitRecorder}
                </div>
              )}
              {alerts}
              {updateAssessmentContext}
              {activeScreen?.key === "evidenceIntake" && (
                <EvidenceIntakeAlertBanner
                  errorKeys={errorKeys}
                  warningKeys={warningKeys}
                  routeForRequirement={routeForRequirement}
                  onNavigate={(key) => select(key, "evidence_intake_banner")}
                />
              )}
              <section className="clinical-command-card rnica-command-active" aria-live="polite">
                {activeSection === "finalization" && (
                  <NarrativeFinalReviewPanel
                    completedSections={completedSections.length}
                    totalSections={routes.length}
                    missingCount={errorKeys.length + warningKeys.length}
                  />
                )}
                {renderWorkspaceSections()}
              </section>
              <nav className="rnica-command-stepnav" aria-label="Section navigation">
                <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
                <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
              </nav>
            </>
        </ScrollRegion>

        <ScrollRegion name="rail" className="rnica-command-rail">
          <button type="button" className="rnica-command-final-shortcut rnica-command-final-shortcut--desktop" onClick={() => select("finalization")}>
            Narrative &amp; final review
          </button>
          <section className="clinical-command-card rnica-command-card" data-rnica-rail-target="validation">
              <button
                type="button"
                className="rnica-command-card__heading rnica-command-card__heading--toggle"
                aria-expanded={validationOpen}
                onClick={() => setValidationOpen((current) => !current)}
              >
                <h2>{validationOpen ? "▾" : "▸"} Validation</h2>
                <span>{errorKeys.length + warningKeys.length} items</span>
              </button>
              {validationOpen && (
                <>
                  {errorKeys.length === 0 && warningKeys.length === 0 && <p>No current validation blockers.</p>}
                  {errorKeys.slice(0, 5).map((key) => (
                    <button type="button" className="rnica-command-requirement" key={key} onClick={() => {
                      select(routeForRequirement(key)?.key || "finalization", "requirement");
                    }}>
                      <strong>Required</strong><span>{validation.errors[key]}</span>
                    </button>
                  ))}
                  {warningKeys.slice(0, 3).map((key) => (
                    <button type="button" className="rnica-command-requirement is-warning" key={key} onClick={() => select(routeForRequirement(key)?.key || "finalization", "requirement")}>
                      <strong>Review</strong><span>{validation.warnings[key]}</span>
                    </button>
                  ))}
                </>
              )}
            </section>
          <section className="clinical-command-card rnica-command-card" data-rnica-rail-target="intelligence">
              <div className="rnica-command-card__heading"><h2>RN ICA intelligence</h2><span>{intelligence?.summary?.finding_count || 0} findings</span></div>
              {(intelligence?.findings || []).slice(0, 4).map((finding, index) => <div className="rnica-command-signal" key={`${finding.category}-${index}`}><strong>{finding.title}</strong><span>{finding.details}</span></div>)}
              {!intelligence && <p>Save the assessment to refresh aggregate clinical signals.</p>}
            </section>
          <section className="clinical-command-card rnica-command-card rnica-command-save">
            <div><strong>Save &amp; sync</strong><span>{saveStatus === "saved" ? "Saved" : saving ? "Saving…" : "Autosave active"}</span></div>
            <button type="button" disabled={saving || locked} onClick={onSave}>{saving ? "Saving…" : "Save assessment"}</button>
            {canLock && !locked && <button type="button" className="is-secondary" onClick={onLock}>Validate &amp; lock</button>}
          </section>
        </ScrollRegion>
      </ClinicalCommandLayout>

      <RnicaWorkflowSheet
        open={genericNavOpen}
        onClose={() => setGenericNavOpen(false)}
        activeScreenKey={activeScreen?.key}
        onSelectScreen={selectScreenTab}
        statusContext={railStatusContext}
      />
    </ClinicalCommandWorkspace>
  );
}
