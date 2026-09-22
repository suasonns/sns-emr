import React from "react";
import { RNICA_THIRTEEN_SCREENS } from "./rnicaThirteenScreenTaxonomy";
import { Badge } from "../ui/badge";

// Dedicated RNICA workflow rail. Replaces the horizontal, scrolling
// 13-screen pill strip (`.rnica-screen__tabs`) that no longer scaled once
// the workflow reached 13 screens (RNICA_NAVIGATION_SPECIFICATION.md).
//
// This is presentation only: it renders the same, unchanged
// RNICA_THIRTEEN_SCREENS order/labels and reuses status data the workspace
// already computes (completedSections, validation error/warning keys). It
// introduces no new field, validation rule, readiness check, or source of
// truth -- see RNICA_SCREEN_AUTHORITY_MATRIX.md.

function screenStatus(screen, { completedSections, errorKeys, warningKeys, routeForRequirement }) {
  if (screen.moduleKeys.length === 0) {
    return { kind: "crossCutting" };
  }
  const total = screen.moduleKeys.length;
  const completed = screen.moduleKeys.filter((key) => completedSections.includes(key)).length;
  const hasErrors = errorKeys.some((key) => screen.moduleKeys.includes(routeForRequirement(key)?.key));
  const hasWarnings = warningKeys.some((key) => screen.moduleKeys.includes(routeForRequirement(key)?.key));
  return { kind: "module", total, completed, hasErrors, hasWarnings };
}

function RailStatusBadge({ status }) {
  if (status.kind === "crossCutting") return null;
  if (status.hasErrors) return <Badge variant="red">{status.completed}/{status.total}</Badge>;
  if (status.total > 0 && status.completed === status.total) return <Badge variant="teal">Done</Badge>;
  if (status.hasWarnings) return <Badge variant="orange">{status.completed}/{status.total}</Badge>;
  return <Badge variant="neutral">{status.completed}/{status.total}</Badge>;
}

export function RnicaWorkflowRailList({ activeScreenKey, onSelectScreen, statusContext, onItemSelected }) {
  return (
    <ol className="rnica-rail__list">
      {RNICA_THIRTEEN_SCREENS.map((screen, index) => {
        const isActive = activeScreenKey === screen.key;
        const status = screenStatus(screen, statusContext);
        return (
          <li key={screen.key}>
            <button
              type="button"
              className={`rnica-rail__item${isActive ? " is-active" : ""}`}
              aria-current={isActive ? "step" : undefined}
              onClick={() => {
                onSelectScreen(screen);
                onItemSelected?.();
              }}
            >
              <span className="rnica-rail__index">{index + 1}</span>
              <span className="rnica-rail__label">{screen.label}</span>
              <span className="rnica-rail__status"><RailStatusBadge status={status} /></span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

/** Desktop rail: fixed vertical column, always visible, no horizontal scroll. */
export function RnicaWorkflowRail({ activeScreenKey, onSelectScreen, statusContext }) {
  const eligible = RNICA_THIRTEEN_SCREENS.filter((screen) => screen.moduleKeys.length > 0);
  const completeCount = eligible.filter((screen) => {
    const status = screenStatus(screen, statusContext);
    return status.kind === "module" && status.completed === status.total;
  }).length;
  const progressPercent = eligible.length > 0 ? Math.round((completeCount / eligible.length) * 100) : 0;

  return (
    <nav className="rnica-rail" aria-label="RN ICA workflow navigator">
      <div className="rnica-rail__heading">
        <span>RNICA Workflow</span>
        <span className="rnica-rail__progress-text">{completeCount}/{eligible.length}</span>
      </div>
      <div
        className="rnica-rail__progress-track"
        role="progressbar"
        aria-valuenow={progressPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Assessment completion"
      >
        <div className="rnica-rail__progress-fill" style={{ width: `${progressPercent}%` }} />
      </div>
      <div className="rnica-rail__scroll">
        <RnicaWorkflowRailList
          activeScreenKey={activeScreenKey}
          onSelectScreen={onSelectScreen}
          statusContext={statusContext}
        />
      </div>
    </nav>
  );
}

/** Mobile workflow selector: sheet/drawer overlay, no horizontal scroll. */
export function RnicaWorkflowSheet({ open, onClose, activeScreenKey, onSelectScreen, statusContext }) {
  if (!open) return null;
  return (
    <div className="rnica-rail-sheet" role="dialog" aria-modal="true" aria-label="RN ICA workflow navigator">
      <button type="button" className="rnica-rail-sheet__backdrop" aria-label="Close workflow navigator" onClick={onClose} />
      <div className="rnica-rail-sheet__panel">
        <div className="rnica-rail-sheet__header">
          <span>RNICA Workflow</span>
          <button type="button" className="rnica-rail-sheet__close" onClick={onClose} aria-label="Close workflow navigator">✕</button>
        </div>
        <div className="rnica-rail-sheet__scroll">
          <RnicaWorkflowRailList
            activeScreenKey={activeScreenKey}
            onSelectScreen={onSelectScreen}
            statusContext={statusContext}
            onItemSelected={onClose}
          />
        </div>
      </div>
    </div>
  );
}
