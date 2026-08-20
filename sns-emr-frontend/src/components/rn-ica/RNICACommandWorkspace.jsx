import React, { useEffect, useMemo, useState } from "react";
import { emitRnIcaTelemetry } from "../../features/rnIcaTelemetry";
import "./RNICACommandWorkspace.css";

const DENSITY_KEY = "sns-rnica-workspace-density";
const DENSITIES = ["compact", "comfortable", "large"];
const HEAD_TO_TOE = [
  ["General", "demographics"],
  ["Vitals", "vitals"],
  ["Pain", "pain"],
  ["Neurological", "neurological"],
  ["Cardiovascular", "cardiovascular"],
  ["Respiratory", "respiratory"],
  ["Infection", "infection"],
  ["Gastrointestinal", "gastrointestinal"],
  ["Nutrition", "nutrition"],
  ["Endocrine", "endocrine"],
  ["Genitourinary", "genitourinary"],
  ["Musculoskeletal", "musculoskeletal"],
  ["Skin / wounds", "skin"],
  ["Safety", "safety"],
  ["Personal care", "personalCare"],
  ["Imminent decline", "imminentDeath"],
];

function storedDensity() {
  const value = window.localStorage.getItem(DENSITY_KEY);
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
  return <div className={className} onScroll={handleScroll}>{children}</div>;
}

function VoiceDraftPanel() {
  const [consented, setConsented] = useState(false);
  const [recordingState, setRecordingState] = useState("idle");
  const [bookmarks, setBookmarks] = useState(0);
  const start = () => {
    if (consented) setRecordingState("recording");
  };

  return (
    <section className="rnica-command-card" aria-labelledby="voice-draft-title">
      <div className="rnica-command-card__heading">
        <h2 id="voice-draft-title">Voice draft</h2>
        <span className={`rnica-command-state rnica-command-state--${recordingState}`}>{recordingState}</span>
      </div>
      <label className="rnica-command-check">
        <input type="checkbox" checked={consented} onChange={(event) => setConsented(event.target.checked)} />
        Patient consent confirmed
      </label>
      <div className="rnica-command-actions">
        {recordingState === "idle" && <button type="button" disabled={!consented} onClick={start}>Start capture</button>}
        {recordingState === "recording" && <button type="button" onClick={() => setRecordingState("paused")}>Pause</button>}
        {recordingState === "paused" && <button type="button" onClick={() => setRecordingState("recording")}>Resume</button>}
        {recordingState !== "idle" && (
          <>
            <button type="button" onClick={() => setBookmarks((count) => count + 1)}>Bookmark ({bookmarks})</button>
            <button type="button" onClick={() => setRecordingState("review")}>Stop &amp; review</button>
          </>
        )}
      </div>
      <p className="rnica-command-help">Draft extraction requires accept, edit, or reject review. It never finalizes the assessment.</p>
      {recordingState === "review" && (
        <div className="rnica-command-review" role="status">
          <strong>Extraction queue ready</strong>
          <span>No findings are applied until reviewed. Uncertain statements remain in the missing queue with source links.</span>
        </div>
      )}
    </section>
  );
}

export default function RNICACommandWorkspace({
  patient,
  routes,
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
}) {
  const [query, setQuery] = useState("");
  const [density, setDensity] = useState(storedDensity);
  const [searchStartedAt, setSearchStartedAt] = useState(0);
  const filteredRoutes = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return normalized ? routes.filter((route) => route.label.toLowerCase().includes(normalized)) : routes;
  }, [query, routes]);
  const errorKeys = Object.keys(validation.errors);
  const warningKeys = Object.keys(validation.warnings);
  const scrollDetailTop = () => {
    requestAnimationFrame(() => document.querySelector(".rnica-command-detail")?.scrollTo({ top: 0, behavior: "smooth" }));
  };

  useEffect(() => {
    emitRnIcaTelemetry({ name: "completion_viewed", completed: completedSections.length, total: routes.length });
  }, [completedSections.length, routes.length]);

  const select = (key, source = "navigator") => {
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

  return (
    <main className={`rnica-command rnica-command--${density}`} aria-label="RN ICA Clinical Command Workspace">
      <header className="rnica-command-patientbar">
        <div className="rnica-command-patientbar__identity">
          <span className="rnica-command-eyebrow">RN ICA · Clinical Command Workspace pilot</span>
          <strong>{patient.name}</strong>
          <span>MRN {patient.mrn} · {patient.primaryDiagnosis || "Primary diagnosis not documented"}</span>
        </div>
        <div className="rnica-command-patientbar__status">
          <span className={`rnica-command-badge ${locked ? "is-complete" : "is-active"}`}>{locked ? "Locked" : "In progress"}</span>
          <span>{completedSections.length}/{routes.length} sections</span>
          <button type="button" onClick={exitPilot}>Use classic view</button>
        </div>
      </header>

      <section className="rnica-command-prep" aria-label="Before visit patient context">
        <div><span>Primary</span><strong>{patient.primaryDiagnosis || "Not documented"}</strong></div>
        <div><span>Secondary</span><strong>{patient.secondaryDiagnoses || "None documented"}</strong></div>
        <div><span>Comorbidities</span><strong>{patient.comorbidities || "None verified"}</strong></div>
        <div><span>Prior issues</span><strong>{patient.priorIssues}</strong></div>
        <div><span>Expected symptoms</span><strong>Review disease-process prompts; document only observed findings</strong></div>
      </section>

      <div className="rnica-command-layout">
        <ScrollRegion name="navigator" className="rnica-command-nav">
          <label className="rnica-command-search">
            <span>Find section</span>
            <input type="search" value={query} onChange={changeSearch} placeholder="Search 28 sections" />
          </label>
          <div className="rnica-command-density" role="group" aria-label="Workspace density">
            {DENSITIES.map((item) => (
              <button type="button" key={item} aria-pressed={density === item} onClick={() => changeDensity(item)}>
                {item === "large" ? "Large text" : item[0].toUpperCase() + item.slice(1)}
              </button>
            ))}
          </div>
          <div className="rnica-command-matrix" aria-label="Assessment section status">
            {filteredRoutes.map((route) => {
              const complete = completedSections.includes(route.key);
              const missing = errorKeys.filter((key) => key.startsWith(`${route.formSection}.`)).length;
              const changed = complete && !locked;
              return (
                <button type="button" key={route.key} className={activeSection === route.key ? "is-active" : ""} onClick={() => select(route.key)}>
                  <span className="rnica-command-matrix__title">{route.label}</span>
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
        </ScrollRegion>

        <ScrollRegion name="detail" className="rnica-command-detail">
          <div className="rnica-command-mobile-tools">
            <VoiceDraftPanel />
          </div>
          {visitRecorder}
          {alerts}
          <section className="rnica-command-sticky-note" aria-labelledby="quick-capture-title">
            <div>
              <span className="rnica-command-eyebrow">Bedside quick capture</span>
              <h2 id="quick-capture-title">Head-to-toe ledger</h2>
              <p>Capture concise +/- observed findings. Missing documentation is never treated as negative.</p>
            </div>
            <div className="rnica-command-quick-grid">
              {HEAD_TO_TOE.map(([label, key]) => (
                <button type="button" key={key} onClick={() => select(key, "quick_capture")}>{label}</button>
              ))}
            </div>
            <div className="rnica-command-provenance" aria-label="Finding provenance">
              <span>Observed / tapped</span><span>Spoken / extracted</span><span>Carried forward / verified</span>
            </div>
          </section>
          <section className="rnica-command-active" aria-live="polite">
            {renderWorkspaceSections()}
          </section>
          <nav className="rnica-command-stepnav" aria-label="Section navigation">
            <button type="button" onClick={() => { onPrevious(); scrollDetailTop(); }}>Previous section</button>
            <button type="button" onClick={() => { onNext(); scrollDetailTop(); }}>Next section</button>
          </nav>
        </ScrollRegion>

        <ScrollRegion name="rail" className="rnica-command-rail">
          <div className="rnica-command-desktop-tools"><VoiceDraftPanel /></div>
          <section className="rnica-command-card">
            <div className="rnica-command-card__heading"><h2>Requirements</h2><span>{errorKeys.length + warningKeys.length}</span></div>
            {errorKeys.length === 0 && warningKeys.length === 0 && <p>No current validation blockers.</p>}
            {errorKeys.slice(0, 5).map((key) => (
              <button type="button" className="rnica-command-requirement" key={key} onClick={() => select(routes.find((route) => key.startsWith(`${route.formSection}.`))?.key || "finalization", "requirement")}>
                <strong>Required</strong><span>{validation.errors[key]}</span>
              </button>
            ))}
            {warningKeys.slice(0, 3).map((key) => <div className="rnica-command-requirement is-warning" key={key}><strong>Review</strong><span>{validation.warnings[key]}</span></div>)}
          </section>
          <section className="rnica-command-card">
            <div className="rnica-command-card__heading"><h2>Clinical signals</h2><span>{intelligence?.summary?.finding_count || 0}</span></div>
            {(intelligence?.findings || []).slice(0, 4).map((finding, index) => <div className="rnica-command-signal" key={`${finding.category}-${index}`}><strong>{finding.title}</strong><span>{finding.details}</span></div>)}
            {!intelligence && <p>Save the assessment to refresh aggregate clinical signals.</p>}
          </section>
          <section className="rnica-command-card rnica-command-save">
            <div><strong>Save &amp; sync</strong><span>{saveStatus === "saved" ? "Saved" : saving ? "Saving…" : "Autosave active"}</span></div>
            <button type="button" disabled={saving || locked} onClick={onSave}>{saving ? "Saving…" : "Save assessment"}</button>
            {canLock && !locked && <button type="button" className="is-secondary" onClick={onLock}>Validate &amp; lock</button>}
          </section>
        </ScrollRegion>
      </div>
    </main>
  );
}
