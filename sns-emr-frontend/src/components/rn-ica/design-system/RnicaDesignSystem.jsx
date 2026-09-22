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

export function SecondaryCard({ title, className = "", children, ...rest }) {
  return (
    <section className={`rnica-ds-card rnica-ds-card--secondary ${className}`} {...rest}>
      {title && <h4 className="rnica-ds-card__title rnica-ds-card__title--secondary">{title}</h4>}
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
