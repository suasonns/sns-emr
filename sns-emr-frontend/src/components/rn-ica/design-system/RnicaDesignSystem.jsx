import React from "react";
import "./RnicaDesignSystem.css";

// Shared RNICA presentation primitives (Phase B reference implementation).
// These are theme-aware only via `--sns-*` CSS custom properties -- no
// component here ever hardcodes a color, and none of them own, validate,
// or persist clinical data. They are pure presentation wrappers around
// data callers already computed/fetched elsewhere in RNICA.

export const NOT_YET_DOCUMENTED = "NOT YET DOCUMENTED";

export function notYetDocumented(value) {
  if (value === null || value === undefined) return true;
  if (typeof value === "string" && value.trim() === "") return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
}

export function DocumentedValue({ value, render }) {
  if (notYetDocumented(value)) {
    return <span className="rnica-ds-undocumented">{NOT_YET_DOCUMENTED}</span>;
  }
  return render ? render(value) : <>{value}</>;
}

export function PrimaryCard({ title, subtitle, actions, className = "", children, ...rest }) {
  return (
    <section className={`rnica-ds-card rnica-ds-card--primary ${className}`} {...rest}>
      {(title || actions) && (
        <header className="rnica-ds-card__header">
          <div>
            {title && <h3 className="rnica-ds-card__title">{title}</h3>}
            {subtitle && <p className="rnica-ds-card__subtitle">{subtitle}</p>}
          </div>
          {actions && <div className="rnica-ds-card__actions">{actions}</div>}
        </header>
      )}
      <div className="rnica-ds-card__body">{children}</div>
    </section>
  );
}

export function SecondaryCard({ title, actions, className = "", children, ...rest }) {
  return (
    <section className={`rnica-ds-card rnica-ds-card--secondary ${className}`} {...rest}>
      {(title || actions) && (
        <header className="rnica-ds-card__header">
          {title && <h4 className="rnica-ds-card__title rnica-ds-card__title--secondary">{title}</h4>}
          {actions && <div className="rnica-ds-card__actions">{actions}</div>}
        </header>
      )}
      <div className="rnica-ds-card__body">{children}</div>
    </section>
  );
}

export function InsetPanel({ className = "", children, ...rest }) {
  return <div className={`rnica-ds-inset ${className}`} {...rest}>{children}</div>;
}

const CHIP_TONES = {
  neutral: "rnica-ds-chip--neutral",
  success: "rnica-ds-chip--success",
  warning: "rnica-ds-chip--warning",
  critical: "rnica-ds-chip--critical",
  info: "rnica-ds-chip--info",
  ai: "rnica-ds-chip--ai",
};

export function StatusChip({ tone = "neutral", children }) {
  return <span className={`rnica-ds-chip ${CHIP_TONES[tone] || CHIP_TONES.neutral}`}>{children}</span>;
}

export function WarningChip({ children }) {
  return <StatusChip tone="warning">{children}</StatusChip>;
}

export function BlockerChip({ children }) {
  return <StatusChip tone="critical">{children}</StatusChip>;
}

export function AiAdvisoryCard({ title = "RNICA Intelligence", timestamp, children, className = "" }) {
  return (
    <section className={`rnica-ds-card rnica-ds-card--ai ${className}`} aria-label={title}>
      <header className="rnica-ds-card__header">
        <h3 className="rnica-ds-card__title rnica-ds-card__title--ai">
          <span className="rnica-ds-ai-dot" aria-hidden="true" /> {title}
        </h3>
        {timestamp && <span className="rnica-ds-card__meta">Refreshed: {timestamp}</span>}
      </header>
      <div className="rnica-ds-card__body">{children}</div>
    </section>
  );
}

export function MissingInfoCard({ title = "Missing Information", items = [], emptyLabel = "No outstanding missing-information items recorded.", onNavigate }) {
  return (
    <section className="rnica-ds-card rnica-ds-card--warning" aria-label={title}>
      <header className="rnica-ds-card__header">
        <h3 className="rnica-ds-card__title rnica-ds-card__title--warning">{title}</h3>
      </header>
      <div className="rnica-ds-card__body">
        {items.length === 0 && <p className="rnica-ds-muted">{emptyLabel}</p>}
        {items.length > 0 && (
          <ul className="rnica-ds-missing-list">
            {items.map((item, index) => (
              <li key={item.key || index}>
                {item.route ? (
                  <SourceLink onClick={() => onNavigate?.(item.route)}>{item.label}</SourceLink>
                ) : (
                  <span>{item.label}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

export function ClinicalRiskRow({ label, detail, tone = "neutral" }) {
  return (
    <div className={`rnica-ds-risk-row rnica-ds-risk-row--${tone}`}>
      <span className="rnica-ds-risk-row__dot" aria-hidden="true" />
      <div>
        <strong>{label}</strong>
        {detail && <span className="rnica-ds-risk-row__detail">{detail}</span>}
      </div>
    </div>
  );
}

export function SourceLink({ onClick, children }) {
  return (
    <button type="button" className="rnica-ds-source-link" onClick={onClick}>
      {children}
    </button>
  );
}

export function ContinueAction({ label, sublabel, onClick }) {
  return (
    <button type="button" className="rnica-ds-continue" onClick={onClick}>
      <span>
        <strong>{label}</strong>
        {sublabel && <span className="rnica-ds-continue__sublabel">{sublabel}</span>}
      </span>
      <span className="rnica-ds-continue__arrow" aria-hidden="true">&rarr;</span>
    </button>
  );
}

export function AutosaveFooter({ active = true, lastSaved, version }) {
  return (
    <footer className="rnica-ds-autosave-footer">
      <span className={`rnica-ds-autosave-dot ${active ? "is-active" : ""}`} aria-hidden="true" />
      <span>{active ? "Autosave Active" : "Autosave paused"}{version ? ` \u2022 ${version}` : ""}</span>
      {lastSaved && <span className="rnica-ds-autosave-footer__saved">Last Saved: {lastSaved}</span>}
    </footer>
  );
}

export function EmptyState({ label }) {
  return <div className="rnica-ds-state rnica-ds-state--empty">{label}</div>;
}

export function LoadingState({ label = "Loading..." }) {
  return <div className="rnica-ds-state rnica-ds-state--loading">{label}</div>;
}

export function ErrorState({ label }) {
  return <div className="rnica-ds-state rnica-ds-state--error">{label}</div>;
}

export function TwoColumnGrid({ main, rail }) {
  return (
    <div className="rnica-ds-two-col">
      <div className="rnica-ds-two-col__main">{main}</div>
      <div className="rnica-ds-two-col__rail">{rail}</div>
    </div>
  );
}

// ------------------------------------------------------------------------
// Phase 1/2: page header + persistent patient-context header + metric/
// summary card variants. These are the reusable primitives every one of
// the 13 screens is expected to compose with -- not Patient-Story-only
// markup. All values are read-only projections of data already owned by
// another screen; nothing here edits or persists a clinical field.
// ------------------------------------------------------------------------

/** Breadcrumb + screen title, shared by every RNICA screen. */
export function RnicaPageHeader({ crumbs = [], title, actions }) {
  return (
    <div className="rnica-ds-page-header">
      {crumbs.length > 0 && (
        <nav className="rnica-ds-page-header__crumb" aria-label="Breadcrumb">
          {crumbs.map((crumb, index) => (
            <React.Fragment key={crumb.key || crumb.label || index}>
              {index > 0 && <span aria-hidden="true">&rsaquo;</span>}
              <span className={index === crumbs.length - 1 ? "rnica-ds-page-header__crumb-current" : ""}>
                {crumb.label}
              </span>
            </React.Fragment>
          ))}
        </nav>
      )}
      <div className="rnica-ds-page-header__row">
        {title && <h1 className="rnica-ds-page-header__title">{title}</h1>}
        {actions && <div className="rnica-ds-page-header__actions">{actions}</div>}
      </div>
    </div>
  );
}

/**
 * Persistent patient-context header (MRN / primary diagnosis / admission /
 * attending physician / current PPS / assessment-stage badge). Every field
 * is read-only and sourced from data already owned by another screen
 * (demographics, diagnoses, functional status) -- see the `patient` object
 * assembled in RNICA.jsx. Renders "NOT YET DOCUMENTED" for anything absent
 * rather than fabricating a value.
 */
export function RnicaPatientHeader({ patient = {}, actions }) {
  const {
    name,
    age,
    sex,
    mrn,
    primaryDiagnosis,
    admissionDate,
    attendingPhysician,
    currentPps,
    assessmentStage,
  } = patient;

  return (
    <header className="rnica-ds-patient-header" aria-label="Patient context">
      <div className="rnica-ds-patient-header__top">
        <div className="rnica-ds-patient-header__name-row">
          <h2 className="rnica-ds-patient-header__name">
            <DocumentedValue value={name} />
          </h2>
          {(age || sex) && (
            <span className="rnica-ds-patient-header__age">
              {[age ? `${age}` : null, sex ? sex[0]?.toUpperCase() : null].filter(Boolean).join("")}
            </span>
          )}
          {!notYetDocumented(assessmentStage) && <StatusChip tone="warning">{assessmentStage}</StatusChip>}
        </div>
        {actions}
      </div>
      <div className="rnica-ds-patient-header__facts">
        <div className="rnica-ds-patient-header__fact">
          <span className="rnica-ds-patient-header__fact-label">MRN Number</span>
          <span className="rnica-ds-patient-header__fact-value"><DocumentedValue value={mrn} /></span>
        </div>
        <div className="rnica-ds-patient-header__fact">
          <span className="rnica-ds-patient-header__fact-label">Primary Diagnosis</span>
          <span className="rnica-ds-patient-header__fact-value"><DocumentedValue value={primaryDiagnosis} /></span>
        </div>
        <div className="rnica-ds-patient-header__fact">
          <span className="rnica-ds-patient-header__fact-label">Hospice Admission</span>
          <span className="rnica-ds-patient-header__fact-value"><DocumentedValue value={admissionDate} /></span>
        </div>
        <div className="rnica-ds-patient-header__fact">
          <span className="rnica-ds-patient-header__fact-label">Attending Physician</span>
          <span className="rnica-ds-patient-header__fact-value"><DocumentedValue value={attendingPhysician} /></span>
        </div>
        <div className="rnica-ds-patient-header__fact">
          <span className="rnica-ds-patient-header__fact-label">Current PPS</span>
          <span className="rnica-ds-patient-header__fact-value rnica-ds-patient-header__pps">
            {notYetDocumented(currentPps) ? (
              <DocumentedValue value={currentPps} />
            ) : (
              <>
                <span className="rnica-ds-patient-header__pps-dot" aria-hidden="true" />
                {currentPps}%
              </>
            )}
          </span>
        </div>
      </div>
    </header>
  );
}

/** Metric tile (e.g. PPS / KPS score cards on Functional Status). */
export function RnicaMetricCard({ label, value, suffix, note, barPercent, className = "" }) {
  return (
    <div className={`rnica-ds-metric-card ${className}`}>
      <span className="rnica-ds-metric-card__label">{label}</span>
      <span className="rnica-ds-metric-card__value">
        <DocumentedValue value={value} />
        {!notYetDocumented(value) && suffix}
      </span>
      {typeof barPercent === "number" && (
        <div className="rnica-ds-metric-card__bar">
          <div className="rnica-ds-metric-card__bar-fill" style={{ width: `${Math.max(0, Math.min(100, barPercent))}%` }} />
        </div>
      )}
      {note && <span className="rnica-ds-metric-card__note">{note}</span>}
    </div>
  );
}

/** Label/value summary row list (read-only recap panels). */
export function RnicaSummaryCard({ title, rows = [], className = "" }) {
  return (
    <section className={`rnica-ds-summary-card ${className}`} aria-label={title}>
      {title && <h4 className="rnica-ds-card__title rnica-ds-card__title--secondary">{title}</h4>}
      {rows.map((row, index) => (
        <div className="rnica-ds-summary-card__row" key={row.key || index}>
          <span className="rnica-ds-summary-card__row-label">{row.label}</span>
          <span className="rnica-ds-summary-card__row-value">
            <DocumentedValue value={row.value} />
          </span>
        </div>
      ))}
    </section>
  );
}

/** Bounded long-narrative text with expand/collapse, per the redesign's
 * long-narrative handling rule -- never an unrestricted wall of text. */
export function RnicaNarrative({ text, source, onNavigateToSource }) {
  const [expanded, setExpanded] = React.useState(false);
  if (notYetDocumented(text)) {
    return (
      <div className="rnica-ds-narrative-empty">
        <span className="rnica-ds-undocumented">{NOT_YET_DOCUMENTED}</span>
        {source && (
          <SourceLink onClick={onNavigateToSource}>Add in {source}</SourceLink>
        )}
      </div>
    );
  }
  const isLong = text.length > 320;
  return (
    <div className="rnica-ds-narrative">
      <p className={`rnica-ds-narrative__text ${isLong && !expanded ? "rnica-ds-narrative__text--clamped" : ""}`}>{text}</p>
      {isLong && (
        <button type="button" className="rnica-ds-narrative__toggle" onClick={() => setExpanded((current) => !current)}>
          {expanded ? "Show less" : "Show full narrative"}
        </button>
      )}
      {source && <SourceLink onClick={onNavigateToSource}>View source: {source}</SourceLink>}
    </div>
  );
}
