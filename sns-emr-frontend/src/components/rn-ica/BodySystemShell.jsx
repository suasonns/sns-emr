import React from "react";
import "./BodySystemShell.css";

// OWNER DECISION (2026-10-06) "Body Systems Architecture Review" -- the
// five remediated Body Systems (Neurological, Cardiovascular, Respiratory,
// Infection, Gastrointestinal) each implement their own independent JSX
// structure inside `renderGenericSection` (RNICA.jsx), and those
// structures have drifted: different section order, different Assessment
// State option counts, inconsistent progressive disclosure. The owner's
// directive is to stop maintaining five unrelated structures and instead
// have ONE shared presentational shell that enforces the canonical
// 7-part order below for every body system.
//
// Pass 1 scope (this file): the shell itself, with NO clinical field
// changes and NO production wiring yet -- `renderGenericSection` and the
// live Body Systems accordion in RNICACommandWorkspace.jsx are untouched.
// `BodySystemShellDemo` below renders one synthetic demonstration using
// Cardiovascular's real, already-existing card content so the shell's
// slot architecture can be proven against real clinical structure before
// any system is migrated onto it (Pass 2+).
//
// The canonical order is enforced BY CONSTRUCTION: `BodySystemShell`
// always renders its seven slots in the same fixed sequence regardless of
// the order props are passed in, and it has no "Summary" slot at all --
// so a caller cannot reintroduce a large duplicate Summary card inside an
// open system (Owner Decision 2: "Remove the separate full Summary card
// from each open body system").
//
// Slots:
//   1. header            -- icon, name, one status, finding count, one
//                            concise summary line (NOT a large Summary
//                            card -- see BodySystemShellHeader below).
//   2. assessmentState    -- the single 4-state gate (No Current Concern /
//                            Existing Findings Review / New or Worsening
//                            Findings / Unable to Assess).
//   3. essentialFindings  -- the minimal always-visible fields for the
//                            selected state.
//   4. changeSincePrior   -- one authoritative trend control, rendered
//                            after Assessment State + Essential Findings.
//   5. triggeredDetail    -- closed/absent until a finding, device, or
//                            explicit "open detail" action triggers it.
//   6. notes              -- one Notes area.
//   7. pocAction          -- one POC action area, always last.
export function BodySystemShell({
  header,
  assessmentState,
  essentialFindings,
  changeSincePrior,
  triggeredDetail,
  notes,
  pocAction,
  className = "",
}) {
  return (
    <div className={`body-system-shell ${className}`.trim()}>
      {header ? <div className="body-system-shell__header">{header}</div> : null}
      <div className="body-system-shell__assessment-state">{assessmentState}</div>
      {essentialFindings ? (
        <div className="body-system-shell__essential-findings">{essentialFindings}</div>
      ) : null}
      {changeSincePrior ? (
        <div className="body-system-shell__change-since-prior">{changeSincePrior}</div>
      ) : null}
      {triggeredDetail ? (
        <div className="body-system-shell__triggered-detail">{triggeredDetail}</div>
      ) : null}
      {notes ? <div className="body-system-shell__notes">{notes}</div> : null}
      {pocAction ? <div className="body-system-shell__poc-action">{pocAction}</div> : null}
    </div>
  );
}

// Header sub-component enforcing "exactly one workflow status" + "one
// concise summary line" (Owner Decision: no large Summary card, no
// duplicate status). `summaryLine` is display-only text the caller
// derives from existing structured fields -- this component does not
// compute or infer anything itself.
export function BodySystemShellHeader({ icon, name, status, findingCount, summaryLine }) {
  return (
    <div className="body-system-shell__header-row">
      <span className="body-system-shell__header-icon" aria-hidden="true">{icon}</span>
      <span className="body-system-shell__header-name">{name}</span>
      {status ? <span className="body-system-shell__header-status">{status}</span> : null}
      {findingCount ? (
        <span className="body-system-shell__header-count">{findingCount} finding{findingCount === 1 ? "" : "s"}</span>
      ) : null}
      {summaryLine ? <p className="body-system-shell__header-summary">{summaryLine}</p> : null}
    </div>
  );
}

// Synthetic Pass-1 demonstration only -- NOT wired to live formData, NOT
// rendered anywhere in the production Body Systems screen. Content below
// mirrors the real, already-existing Cardiovascular card structure
// (SECTION_CONFIGS.cardiovascular in RNICA.jsx: "Cardiovascular Overview",
// "Circulation & Perfusion", Clinical Status Change, Cardiovascular
// Notes, + Add to POC) so the shell can be evaluated against real
// clinical shape rather than placeholder text, per the owner's explicit
// "Render one synthetic demonstration using Cardiovascular" instruction.
export function BodySystemShellCardiovascularDemo() {
  return (
    <BodySystemShell
      header={
        <BodySystemShellHeader
          icon="❤️"
          name="Cardiovascular"
          status="Review Required"
          findingCount={1}
          summaryLine="Peripheral edema documented."
        />
      }
      assessmentState={
        <fieldset className="body-system-shell__demo-fieldset">
          <legend>Cardiovascular Overview</legend>
          <label><input type="radio" name="cv-demo-overview" defaultChecked /> No Current Cardiovascular Concern</label>
          <label><input type="radio" name="cv-demo-overview" /> Existing Cardiovascular Findings Review</label>
          <label><input type="radio" name="cv-demo-overview" /> New or Worsening Cardiovascular Findings</label>
          <label><input type="radio" name="cv-demo-overview" /> Unable to Assess</label>
        </fieldset>
      }
      essentialFindings={
        <p className="body-system-shell__demo-text">Edema documented. (essential-finding summary line, not a duplicate Summary card)</p>
      }
      changeSincePrior={
        <fieldset className="body-system-shell__demo-fieldset">
          <legend>Clinical Status Change</legend>
          <label><input type="radio" name="cv-demo-change" defaultChecked /> No Significant Change</label>
          <label><input type="radio" name="cv-demo-change" /> New or Worsening Finding</label>
        </fieldset>
      }
      triggeredDetail={
        <details className="body-system-shell__demo-details">
          <summary>Circulation &amp; Perfusion (previously documented findings preserved, click to review)</summary>
          <p>Pulse Rhythm, Pulse Rate, Pulse Strength, Edema Location/Severity...</p>
        </details>
      }
      notes={
        <label className="body-system-shell__demo-label">
          Cardiovascular Notes
          <textarea rows={2} />
        </label>
      }
      pocAction={<button type="button">+ Add to POC</button>}
    />
  );
}
