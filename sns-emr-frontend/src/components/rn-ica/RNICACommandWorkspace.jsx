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
import {
  AiAdvisoryCard,
  AutosaveFooter,
  ClinicalRiskRow,
  ContinueAction,
  DocumentedValue,
  MissingInfoCard,
  PrimaryCard,
  RnicaNarrative,
  RnicaPageHeader,
  RnicaPatientHeader,
  SecondaryCard,
  SourceLink,
  StatusChip,
  TwoColumnGrid,
  notYetDocumented,
} from "./design-system/RnicaDesignSystem";
import "./RNICACommandWorkspace.css";

const DENSITY_KEY = "sns-clinical-command-workspace-density";
const LEGACY_DENSITY_KEY = "sns-rnica-workspace-density";
const DENSITIES = ["compact", "comfortable", "large"];
function storedDensity() {
  const value = window.localStorage.getItem(DENSITY_KEY) || window.localStorage.getItem(LEGACY_DENSITY_KEY);
  return DENSITIES.includes(value) ? value : "compact";
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

  return (
    <div className="rnica-ds-patient-story" aria-labelledby="patient-story-title">
      <RnicaPageHeader
        crumbs={[{ label: "RNICA Dashboard" }, { label: "Patient Story" }]}
        title={<span id="patient-story-title">Patient Story</span>}
      />

      <RnicaPatientHeader patient={patient} />

      <p className="rnica-ds-patient-story__intro">
        This is a read-only summary of information already documented elsewhere in RNICA. It does
        not store data and is not a certification, eligibility, or prognosis determination.
      </p>

      <TwoColumnGrid
        main={(
          <>
            <PrimaryCard title="Why Hospice" subtitle="Clinical narrative, owned by Diagnoses & LCD">
              <RnicaNarrative
                text={patient.whyHospiceNarrative}
                source="Diagnosis & LCD"
                onNavigateToSource={() => onNavigate("diagnoses")}
              />
            </PrimaryCard>

            <PrimaryCard title="Recent Hospitalization" subtitle="Owned by Diagnoses & LCD">
              <RnicaNarrative
                text={patient.recentHospitalization}
                source="Diagnosis & LCD"
                onNavigateToSource={() => onNavigate("diagnoses")}
              />
            </PrimaryCard>

            <PrimaryCard title="Current Clinical Concerns" subtitle="Documented findings requiring review -- no derived risk scoring engine is applied">
              {documentedRiskRows.length === 0 && (
                <p className="rnica-ds-muted">No documented clinical concerns currently flagged across Safety, Pain, Psychosocial, or Caregiver screens.</p>
              )}
              {documentedRiskRows.map((row) => (
                <ClinicalRiskRow key={row.moduleKey} label={row.label} detail={row.detail} tone={row.tone} />
              ))}
            </PrimaryCard>

            <SecondaryCard title="Caregiver Overview">
              {notYetDocumented(caregiverSummary) ? (
                <SourceLink onClick={() => onNavigate("caregiverAssessment")}>
                  <DocumentedValue value={caregiverSummary} />
                </SourceLink>
              ) : (
                <>
                  <p>
                    <SourceLink onClick={() => onNavigate("caregiverAssessment")}>{caregiverSummary}</SourceLink>
                  </p>
                  {caregiver.anxietyLevel && <p className="rnica-ds-muted">Anxiety level: {caregiver.anxietyLevel}</p>}
                  {caregiver.willingToProvideCare === false && (
                    <StatusChip tone="warning">Not willing to provide care</StatusChip>
                  )}
                </>
              )}
            </SecondaryCard>

            <ContinueAction
              label="Continue to Evidence & Intake"
              sublabel="Review available intake docs next"
              onClick={() => onNavigate("demographics")}
            />
          </>
        )}
        rail={(
          <>
            <AiAdvisoryCard>
              {!intelligence && <p className="rnica-ds-muted">Save the assessment to generate the clinical signal summary.</p>}
              {intelligence && findings.length === 0 && recommendations.length === 0 && (
                <p className="rnica-ds-muted">No current findings or recommendations.</p>
              )}
              {findings.slice(0, 5).map((finding, index) => (
                <SourceLink key={`story-finding-${index}`} onClick={() => onNavigate("finalization")}>
                  {finding.title}{finding.details ? ` \u2014 ${finding.details}` : ""}
                </SourceLink>
              ))}
              {recommendations.slice(0, 3).map((rec, index) => (
                <p key={`story-rec-${index}`}>{typeof rec === "string" ? rec : rec?.text || rec?.title}</p>
              ))}
            </AiAdvisoryCard>

            <MissingInfoCard items={missingItems} onNavigate={onNavigate} />
          </>
        )}
      />

      <AutosaveFooter active={saveStatus === "saved" || saving} lastSaved={saveStatus === "saved" ? "Just now" : undefined} version="RNICA v1.2" />
    </div>
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
  const screenModuleKeys = new Set(["demographics", "vitals", "referrals"]);
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
function RnicaScreenShell({ patient, locked, completedSections, totalRoutes, activeScreenKey, onSelectScreenTab, onExitPilot, saving, saveStatus, onSave, onLock, canLock, children }) {
  return (
    <div className="rnica-screen">
      <header className="rnica-screen__bar">
        <div className="rnica-screen__identity">
          <span className="rnica-command-eyebrow">RNICA</span>
          <strong>{patient.name}</strong>
          <span>MRN {patient.mrn}</span>
        </div>
        <div className="rnica-screen__status">
          <span className={`clinical-command-status rnica-command-badge ${locked ? "is-complete" : "is-active"}`}>{locked ? "Locked" : "In progress"}</span>
          <span>{completedSections.length}/{totalRoutes} sections</span>
          <button type="button" onClick={onExitPilot}>Use classic view</button>
        </div>
      </header>

      <nav className="rnica-screen__tabs" aria-label="RN ICA 13-screen navigator">
        {RNICA_THIRTEEN_SCREENS.map((screen, index) => (
          <button
            type="button"
            key={screen.key}
            className={activeScreenKey === screen.key ? "is-active" : ""}
            onClick={() => onSelectScreenTab(screen)}
          >
            <span className="rnica-screen__tab-index">{index + 1}</span>
            {screen.label}
          </button>
        ))}
      </nav>

      <main className="rnica-screen__content">{children}</main>

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
  visitRecorder,
  alerts,
  onSelect,
  onSave,
  onLock,
  onPrevious,
  onNext,
  onExitPilot,
  canLock,
  isOngoingAssessment = false,
}) {
  const [query, setQuery] = useState("");
  const [density, setDensity] = useState(storedDensity);
  const [searchStartedAt, setSearchStartedAt] = useState(0);
  const [showAllQuickAccess, setShowAllQuickAccess] = useState(false);
  const [collapsedScreens, setCollapsedScreens] = useState({});
  const [viewMode, setViewMode] = useState("screen");
  const filteredRoutes = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return normalized ? routes.filter((route) => route.label.toLowerCase().includes(normalized)) : routes;
  }, [query, routes]);
  // 13-screen presentation grouping (Phase B). This groups the same,
  // unchanged module routes under the approved 13-screen taxonomy -- it
  // does not add, remove, or reorder any module's content, validation, or
  // data. See rnicaThirteenScreenTaxonomy.js.
  const screenGroups = useMemo(() => groupRoutesIntoScreens(filteredRoutes), [filteredRoutes]);
  const activeScreen = useMemo(() => screenForModuleKey(activeSection), [activeSection]);
  const activeScreenIndex = activeScreen
    ? RNICA_THIRTEEN_SCREENS.findIndex((screen) => screen.key === activeScreen.key)
    : -1;
  const isScreenCollapsed = (screenKey) => {
    if (screenKey in collapsedScreens) return collapsedScreens[screenKey];
    return activeScreen?.key !== screenKey;
  };
  const toggleScreen = (screenKey) => {
    setCollapsedScreens((prev) => ({ ...prev, [screenKey]: !isScreenCollapsed(screenKey) }));
  };
  const selectCrossCuttingScreen = (screen) => {
    if (screen.key === "patientStory") {
      setViewMode("patientStory");
      emitRnIcaTelemetry({ name: "section_jump", section: "patientStory", source: "screen:patientStory" });
      return;
    }
    setViewMode("screen");
    onSelect(screen.landingModuleKey);
    emitRnIcaTelemetry({ name: "section_jump", section: screen.landingModuleKey, source: `screen:${screen.key}` });
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
    () => validateRnIcaClinicalNavigation(routes, formSections, isOngoingAssessment),
    [formSections, routes, isOngoingAssessment],
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

  const changeSearch = (event) => {
    if (!searchStartedAt) setSearchStartedAt(performance.now());
    const next = event.target.value;
    setQuery(next);
    if (next.length > 1) {
      const normalized = next.toLowerCase();
      const resultCount = routes.filter((route) => route.label.toLowerCase().includes(normalized)).length;
      emitRnIcaTelemetry({ name: "section_find", elapsedMs: Math.round(performance.now() - (searchStartedAt || performance.now())), resultCount });
    }
  };

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

  if (viewMode === "patientStory") {
    // Patient Story is a true standalone RNICA screen: no legacy Clinical
    // Command Workspace chrome renders behind it (no eyebrow/context bar,
    // no module navigator, no quick-access grid, no generic
    // Validation/Intelligence rail -- those all live inside PatientStoryPanel
    // itself, sourced from the same data).
    return (
      <RnicaScreenShell
        patient={patient}
        locked={locked}
        completedSections={completedSections}
        totalRoutes={routes.length}
        activeScreenKey="patientStory"
        onSelectScreenTab={selectScreenTab}
        onExitPilot={exitPilot}
        saving={saving}
        saveStatus={saveStatus}
        onSave={onSave}
        onLock={onLock}
        canLock={canLock}
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
          <button type="button" onClick={exitPilot}>Use classic view</button>
        </div>
      </ClinicalCommandHeader>

      <ClinicalCommandContextBar className="rnica-command-prep" ariaLabel="Before visit patient context">
        <div><span>Primary</span><strong>{patient.primaryDiagnosis || "Not documented"}</strong></div>
        <div><span>Secondary</span><strong>{patient.secondaryDiagnoses || "None documented"}</strong></div>
        <div><span>Comorbidities</span><strong>{patient.comorbidities || "None verified"}</strong></div>
        <div><span>Prior issues</span><strong>{patient.priorIssues}</strong></div>
        <div><span>Expected symptoms</span><strong>Review disease-process prompts; document only observed findings</strong></div>
      </ClinicalCommandContextBar>

      <ClinicalCommandLayout className="rnica-command-layout">
        <ScrollRegion name="navigator" className="rnica-command-nav">
          <label className="rnica-command-search">
            <span>Find section</span>
            <input type="search" value={query} onChange={changeSearch} placeholder={`Search ${routes.length} sections`} />
          </label>
          <div className="rnica-command-density" role="group" aria-label="Workspace density">
            {DENSITIES.map((item) => (
              <button type="button" key={item} aria-pressed={density === item} onClick={() => changeDensity(item)}>
                {item === "large" ? "Large text" : item[0].toUpperCase() + item.slice(1)}
              </button>
            ))}
          </div>
          <button type="button" className="rnica-command-final-shortcut rnica-command-final-shortcut--mobile" onClick={() => select("finalization")}>
            Narrative &amp; final review
          </button>
          <div className="rnica-command-screens" aria-label="RN ICA 13-screen navigator">
            {screenGroups.map((screen, screenIndex) => {
              if (screen.crossCutting) {
                return (
                  <div className="rnica-command-screen-group rnica-command-screen-group--crosscutting" key={screen.key}>
                    <button
                      type="button"
                      className={`rnica-command-screen-group__header ${activeScreen?.key === screen.key ? "is-active" : ""}`}
                      onClick={() => selectCrossCuttingScreen(screen)}
                    >
                      <span className="rnica-command-screen-group__index">{screenIndex + 1}</span>
                      <span className="rnica-command-screen-group__label">{screen.label}</span>
                    </button>
                  </div>
                );
              }
              if (screen.routes.length === 0) return null;
              const collapsed = isScreenCollapsed(screen.key);
              const screenComplete = screen.routes.filter((route) => completedSections.includes(route.key)).length;
              return (
                <div className="rnica-command-screen-group" key={screen.key}>
                  <button
                    type="button"
                    className={`rnica-command-screen-group__header ${activeScreen?.key === screen.key ? "is-active" : ""}`}
                    onClick={() => toggleScreen(screen.key)}
                    aria-expanded={!collapsed}
                  >
                    <span className="rnica-command-screen-group__caret">{collapsed ? "▸" : "▾"}</span>
                    <span className="rnica-command-screen-group__index">{screenIndex + 1}</span>
                    <span className="rnica-command-screen-group__label">{screen.label}</span>
                    <span className="rnica-command-screen-group__progress">{screenComplete}/{screen.routes.length}</span>
                  </button>
                  {!collapsed && (
                    <div className="rnica-command-matrix" aria-label={`${screen.label} sections`}>
                      {screen.routes.map((route) => {
                        const complete = completedSections.includes(route.key);
                        const missing = errorKeys.filter((key) => routeForRequirement(key)?.key === route.key).length;
                        const changed = complete && !locked;
                        return (
                          <button type="button" key={route.key} className={activeSection === route.key ? "is-active" : ""} onClick={() => select(route.key)}>
                            <span className="rnica-command-matrix__module">
                              <span className="rnica-command-matrix__title">{route.label}</span>
                              {route.regulator && <span className="rnica-command-matrix__regulator">{route.regulator}</span>}
                            </span>
                            <span className="rnica-command-matrix__signals">
                              <span title="Completion">{complete ? "Done" : "Open"}</span>
                              <span title="Risk">{missing ? "Risk" : "—"}</span>
                              <span title="Changed">{changed ? "Changed" : "—"}</span>
                              <span title="Missing requirements">{missing || "—"}</span>
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollRegion>

        <ScrollRegion name="detail" className="rnica-command-detail">
          <>
              {visitRecorder}
              {alerts}
              {activeScreen?.key === "evidenceIntake" && (
                <EvidenceIntakeAlertBanner
                  errorKeys={errorKeys}
                  warningKeys={warningKeys}
                  routeForRequirement={routeForRequirement}
                  onNavigate={(key) => select(key, "evidence_intake_banner")}
                />
              )}
              <section className="clinical-command-card rnica-command-sticky-note" aria-labelledby="quick-capture-title">
                <div>
                  <span className="rnica-command-eyebrow">Bedside quick access</span>
                  <h2 id="quick-capture-title">Assessment modules</h2>
                  <p>Use the same ordered RN workflow as the navigator. Missing documentation is never treated as a negative finding.</p>
                </div>
                <div className="rnica-command-quick-grid" aria-label="Ordered assessment module shortcuts">
                  {(showAllQuickAccess ? routes : routes.slice(0, 16)).map((route, index) => (
                    <button type="button" key={route.key} onClick={() => select(route.key, "quick_capture")}>
                      <span>{index + 1}</span> {route.label}
                    </button>
                  ))}
                </div>
                {routes.length > 16 && (
                  <button type="button" className="rnica-command-quick-toggle" onClick={() => setShowAllQuickAccess((current) => !current)}>
                    {showAllQuickAccess ? "Show first 16 modules" : `Show all ${routes.length} modules`}
                  </button>
                )}
                <div className="rnica-command-provenance" aria-label="Finding provenance">
                  <span>Observed / tapped</span><span>Spoken / extracted</span><span>Carried forward / verified</span>
                </div>
              </section>
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
              <div className="rnica-command-card__heading"><h2>Validation</h2><span>{errorKeys.length + warningKeys.length} items</span></div>
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
    </ClinicalCommandWorkspace>
  );
}
