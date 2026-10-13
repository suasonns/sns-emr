/**
 * SNS Body Systems — Respiratory detail panel.
 *
 * Respiratory proof-of-pattern milestone (explicit product-authority
 * decision superseding the narrowed shell's "no detail panel / no API"
 * rule for Respiratory only — see BodySystemsWorkspace.tsx docstring).
 * Renders every verified field in `RESPIRATORY_FIELD_INVENTORY`, drives
 * conditional display from the situation selector, surfaces server-
 * derived review exceptions, and wires load/save to the Respiratory API
 * via `useRespiratoryAssessment`.
 *
 * No other Body System has (or may gain, via this file) a detail panel,
 * an API client, or draft persistence — that remains out of scope per the
 * milestone's "one system at a time" delivery rule.
 */
import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../components/ui/select";
import { Checkbox } from "../../../components/ui/checkbox";
import { Textarea } from "../../../components/ui/textarea";
import { Button } from "../../../components/ui/button";
import { Alert, AlertDescription } from "../../../components/ui/alert";
import {
  RESPIRATORY_NO_CURRENT_CONCERN_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD,
  RESPIRATORY_NOTES_FIELD,
  RESPIRATORY_ASSESSMENT_CONTEXT_FIELD,
  RESPIRATORY_CLINICAL_COMPARISON_FIELD,
  RESPIRATORY_CLINICAL_STATUS_CHANGE_DETAIL_FIELD,
  RESPIRATORY_FIELD_INVENTORY,
  type RespiratoryFieldDefinition,
} from "../../../domain/body-systems/respiratoryFieldInventory";
import {
  mapOxygenDeliveryDeviceToLegacyType,
  mapOxygenFlowValueToLegacyLitersPerMinute,
  mapOxygenFrequencyToLegacyDeliveryMode,
  mapOxygenUseToLegacyInUse,
  mapSpo2ConditionToLegacyRoomAir,
  mapSpo2ValueToLegacySatOnO2,
  mapTreatmentDecisionToLegacy,
  mapVentilatorDurationToLegacy,
} from "../../../domain/body-systems/respiratoryBackwardCompatibility";
import { useRespiratoryAssessment, type RespiratoryDraft } from "./useRespiratoryAssessment";

export interface RespiratoryPanelProps {
  patientId: string;
  /** RNICA episode id (`RnicaAssessment.id`) that scopes this Respiratory
   * record — required so two episodes for the same patient never read or
   * write each other's assessment. */
  assessmentId: string;
  /** True once the owning RNICA episode is locked/signed. Disables every
   * input and the Save/Complete actions as defense-in-depth alongside the
   * backend's own 409 rejection (`RnicaAssessment.status == "LOCKED"`) —
   * mirrors the same `locked` concept `renderGenericSection` already
   * respects for every other Body System. */
  readOnly?: boolean;
  /** The visit date for the RNICA episode this Respiratory assessment
   * belongs to (ongoing-visit date, or facesheet SOC date for an initial
   * admission). Hospice visit-based documentation directive: SOB Screening
   * Date and Comfort/Function Screening Date default to this value instead
   * of asking the nurse to re-enter a date for an assessment already being
   * performed during the current documented visit. The nurse may freely
   * edit/override the default — this is a one-time fill, never enforced. */
  visitDate?: string;
}

const INTERVENTION_FIELD_IDS = new Set([
  "respiratory_treatment_initiated",
  "respiratory_treatment_date",
  "respiratory_treatment_declined",
  "respiratory_treatment_decision",
  "respiratory_treatment_description",
  "respiratory_treatment_decline_reason",
  "respiratory_treatment_action_date",
  "respiratory_treatment_action_time",
  "respiratory_treatment_response_time",
  "respiratory_treatment_response",
  "respiratory_treatment_response_status",
  "respiratory_clinical_response",
  "respiratory_clinical_response_evidence",
]);
const FOLLOW_UP_FIELD_IDS = new Set([
  "respiratory_follow_up_need",
  "respiratory_follow_up_timing_plan",
  "respiratory_follow_up_responsible_clinician",
  "respiratory_poc_review_need",
  "respiratory_poc_review_reason",
  "respiratory_poc_source_reference",
  "respiratory_configured_requirement_response",
  "respiratory_configured_follow_up_status",
]);
const HANDLED_SEPARATELY_FIELD_IDS = new Set([
  RESPIRATORY_NO_CURRENT_CONCERN_FIELD.fieldId,
  RESPIRATORY_UNABLE_TO_ASSESS_FIELD.fieldId,
  RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD.fieldId,
  RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD.fieldId,
  RESPIRATORY_NOTES_FIELD.fieldId,
  "respiratory_assessment_context",
  "respiratory_clinical_comparison",
  "respiratory_clinical_status_change_detail",
  "respiratory_clinical_status_change",
]);

/** `legacySource` is always `respiratory.<path>`; this resolves that dotted
 * path against the flat/nested draft object used by `useRespiratoryAssessment`. */
function legacyPathSegments(legacySource: string): string[] {
  return legacySource.split(".").slice(1);
}

function getFieldValue(draft: RespiratoryDraft, field: RespiratoryFieldDefinition): unknown {
  const segments = legacyPathSegments(field.legacySource);
  let current: unknown = draft;
  for (const segment of segments) {
    if (current == null || typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[segment];
  }
  return current;
}

function setFieldValue(draft: RespiratoryDraft, field: RespiratoryFieldDefinition, value: unknown): RespiratoryDraft {
  const segments = legacyPathSegments(field.legacySource);
  if (segments.length === 1) {
    return { ...draft, [segments[0]]: value };
  }
  const [parentKey, childKey] = segments;
  const parent = (draft as Record<string, unknown>)[parentKey];
  const nextParent = { ...(typeof parent === "object" && parent ? (parent as Record<string, unknown>) : {}), [childKey]: value };
  return { ...draft, [parentKey]: nextParent };
}

/**
 * Keeps the retired legacy compatibility keys in sync whenever one of the
 * four canonical nurse-facing fields changes, so historical/audit
 * consumers of the legacy keys keep working even though their own visible
 * controls have been removed. Each mapping only sets a legacy value for a
 * deterministic canonical value (see `respiratoryBackwardCompatibility.ts`)
 * — an ambiguous canonical value leaves the legacy keys untouched rather
 * than fabricating one.
 */
function applyCanonicalLegacyMapping(
  field: RespiratoryFieldDefinition,
  draft: RespiratoryDraft,
  visitDate?: string,
): RespiratoryDraft {
  switch (field.fieldId) {
    case "respiratory_treatment_decision": {
      const legacy = mapTreatmentDecisionToLegacy(draft.treatmentDecision);
      const next = { ...draft, ...legacy };
      // respiratory_treatment_date ("SOB Treatment Date") is hidden from
      // the nurse-facing admission workflow (it is Reporting Support
      // only — its sole consumer is HOPE J2040-B; hospice admission does
      // not require the nurse to record an exact intervention date, see
      // hospice-admission Treatment section simplification). Since there
      // is no longer a nurse-facing control to set it, generate it
      // automatically — the RNICA visit date when available (RNICA is
      // visit-centric; see LEGACY_HIDDEN_FIELD_IDS doc comment below),
      // else today's date as a defensive fallback — the first time the
      // decision becomes Initiated, and cleared whenever the decision is
      // anything else, so it can never go stale from a decision the
      // nurse has since changed or cleared (same correctness concern as
      // the legacy treatmentInitiated/treatmentDeclined flags above).
      next.treatmentDate =
        legacy.treatmentInitiated === true
          ? next.treatmentDate ?? visitDate ?? new Date().toISOString().slice(0, 10)
          : undefined;
      return next;
    }
    case "respiratory_oxygen_use": {
      const inUse = mapOxygenUseToLegacyInUse(draft.oxygenUse);
      if (inUse === undefined) return draft;
      return { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, inUse } };
    }
    case "respiratory_spo2_measurement_condition": {
      const onRoomAir = mapSpo2ConditionToLegacyRoomAir(draft.spo2MeasurementCondition);
      const satOnO2 = mapSpo2ValueToLegacySatOnO2(draft.spo2Value, draft.spo2MeasurementCondition);
      let next = draft;
      if (onRoomAir !== undefined) next = { ...next, oxygenTherapy: { ...next.oxygenTherapy, onRoomAir } };
      if (satOnO2 !== undefined) next = { ...next, oxygenTherapy: { ...next.oxygenTherapy, satOnO2 } };
      return next;
    }
    case "respiratory_spo2_value": {
      const satOnO2 = mapSpo2ValueToLegacySatOnO2(draft.spo2Value, draft.spo2MeasurementCondition);
      if (satOnO2 === undefined) return draft;
      return { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, satOnO2 } };
    }
    case "respiratory_oxygen_delivery_device":
    case "respiratory_oxygen_other_device": {
      const type = mapOxygenDeliveryDeviceToLegacyType(draft.oxygenTherapy?.deliveryDevice, draft.oxygenTherapy?.otherDevice);
      let next = type !== undefined ? { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, type } } : draft;
      // PRODUCT-OWNER DIRECTIVE ("NASAL CANNULA / MASK ... Default: L/min.
      // Hidden from user."): these two devices always use L/min -- the
      // unit is auto-derived the moment Delivery Device is set, so the
      // nurse is never asked to choose it (see OxygenFlowRateField and
      // the "respiratory_oxygen_flow_unit" branch of
      // `isFieldCurrentlyRelevant`, which only shows a standalone unit
      // control when Delivery Device = OTHER). Re-derive litersPerMinute
      // too, in case Flow Value was already entered before the device was
      // chosen.
      const device = draft.oxygenTherapy?.deliveryDevice;
      if (device === "NASAL_CANNULA" || device === "MASK") {
        const flowUnit = "L_MIN";
        const litersPerMinute = mapOxygenFlowValueToLegacyLitersPerMinute(draft.oxygenTherapy?.flowValue, flowUnit);
        next = {
          ...next,
          oxygenTherapy: {
            ...next.oxygenTherapy,
            flowUnit,
            ...(litersPerMinute !== undefined ? { litersPerMinute } : {}),
          },
        };
      }
      return next;
    }
    case "respiratory_oxygen_flow_value":
    case "respiratory_oxygen_flow_unit": {
      const litersPerMinute = mapOxygenFlowValueToLegacyLitersPerMinute(draft.oxygenTherapy?.flowValue, draft.oxygenTherapy?.flowUnit);
      if (litersPerMinute === undefined) return draft;
      return { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, litersPerMinute } };
    }
    case "respiratory_oxygen_frequency": {
      const deliveryMode = mapOxygenFrequencyToLegacyDeliveryMode(draft.oxygenTherapy?.frequency);
      let next = deliveryMode !== undefined ? { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, deliveryMode } } : draft;
      // Ticket 3 (Continuous Hours/Day derivation): Continuous oxygen use is
      // by definition 24 hours/day — auto-derive and lock it the moment the
      // schedule becomes Continuous (see the disabled-prop check in the
      // Oxygen section render below). PRN has no "hours/day" concept at all
      // (its own detail field is hidden entirely, see
      // `isFieldCurrentlyRelevant`), so no value is forced for it here.
      if (draft.oxygenTherapy?.frequency === "CONTINUOUS") {
        next = { ...next, oxygenTherapy: { ...next.oxygenTherapy, hoursPerDay: "24" } };
      }
      return next;
    }
    case "respiratory_ventilator_duration": {
      const legacy = mapVentilatorDurationToLegacy(draft.ventilator?.duration);
      return Object.keys(legacy).length > 0 ? { ...draft, ventilator: { ...draft.ventilator, ...legacy } } : draft;
    }
    default:
      return draft;
  }
}

function FieldLabel({ children, htmlFor }: { children: ReactNode; htmlFor: string }) {
  return (
    <label htmlFor={htmlFor} className="text-xs font-medium text-rnica-textStrong">
      {children}
    </label>
  );
}

/**
 * Density Pass 2 — visual-hierarchy fix: ordinary clinical grouping
 * containers (Assessment Context, Comparison to Prior, Lung Sounds,
 * Respiratory Pattern, and any other multi-select/radio-group field) must
 * read as quiet structure, not as warnings. Replaces the browser's default
 * high-contrast `fieldset` border with the subtle slate tokens the
 * directive specified, scoped locally to this panel (no existing
 * equivalent design-system token covers this low-emphasis "ordinary group"
 * case, so these stay local rather than becoming a new global token).
 */
const GROUP_CONTAINER_CLASS =
  "rounded-lg border border-[rgba(148,163,184,0.16)] bg-[rgba(15,23,42,0.10)] px-2 py-1.5 focus-within:border-[rgba(45,212,191,0.58)]";

/**
 * Density Pass 2 — raw enum values (e.g. `CURRENT_CONCERNS_ASSESSED`,
 * `UNABLE_TO_VERIFY`) must never reach the nurse-facing label; only the
 * stored value is the enum constant. Display-only transform — does not
 * change `controlledValues`, persistence, or validation.
 */
function humanizeOption(option: string): string {
  return option
    .toLowerCase()
    .split("_")
    .map((word) => (word.length > 0 ? word[0].toUpperCase() + word.slice(1) : word))
    .join(" ");
}

/**
 * Usability-defect fix (product-owner directive, "L_MIN ... cannot add
 * the unit, just the flow"): a small set of controlled values are not
 * plain-English words `humanizeOption`'s underscore-splitting handles
 * correctly — "L_MIN" word-splits to the clinically-wrong "L Min" rather
 * than the standard clinical abbreviation "L/min". This is a display-only
 * override map; the stored/persisted value is always the raw enum
 * constant (`L_MIN`), never this label.
 */
const OPTION_LABEL_OVERRIDES: Record<string, string> = {
  L_MIN: "L/min",
};

function optionLabel(option: string): string {
  return OPTION_LABEL_OVERRIDES[option] ?? humanizeOption(option);
}

/**
 * Selected-state contrast fix: a live-screen defect report (and Playwright
 * computed-style diagnostics) confirmed the Tailwind `bg-rnica-teal` /
 * `border-rnica-teal` utility classes were being silently overridden by a
 * higher-specificity rule elsewhere in the app bundle — the "selected"
 * pill rendered with the exact same background/border as every
 * unselected sibling, with no color difference at all. Inline styles have
 * the highest CSS specificity short of `!important` and cannot be
 * silently shadowed the same way, so the checked/unchecked pill state is
 * now driven entirely by inline style rather than conditional utility
 * classes. Also adds a checkmark glyph so the selected option never
 * depends on color alone (color-blind / low-contrast displays).
 */
function pillStateStyle(checked: boolean): CSSProperties {
  return checked
    ? {
        backgroundColor: "var(--sns-teal)",
        borderColor: "var(--sns-teal)",
        color: "var(--sns-textInverse)",
        fontWeight: 700,
        boxShadow: "0 0 0 1px var(--sns-teal)",
      }
    : {
        backgroundColor: "var(--sns-bg)",
        borderColor: "var(--sns-border)",
        color: "var(--sns-white)",
        fontWeight: 500,
      };
}

/**
 * Layout-density pass: short, enumerated dropdowns should be sized to
 * their content, not stretched to the panel's full column width. Fields
 * not listed here fall back to a still-constrained default (never
 * full-width) rather than being enumerated one-by-one.
 */
const SELECT_WIDTH_CLASS: Record<string, string> = {
  respiratory_sob_severity: "w-[220px]",
  respiratory_exertion_level: "w-[220px]",
  respiratory_cough_type: "w-[220px]",
  respiratory_oxygen_delivery_type: "w-[220px]",
  respiratory_oxygen_delivery_mode: "w-[160px]",
  respiratory_clinical_status_change: "w-[300px]",
  respiratory_unable_to_assess_reason: "w-[280px]",
};
const DEFAULT_SELECT_WIDTH_CLASS = "w-[240px]";

function SingleSelectField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const widthClass = SELECT_WIDTH_CLASS[field.fieldId] ?? DEFAULT_SELECT_WIDTH_CLASS;
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <Select value={typeof value === "string" ? value : ""} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id={field.fieldId} aria-label={field.label} className={`h-8 ${widthClass} max-w-full px-2 py-1`}>
          <SelectValue placeholder="Select…" />
        </SelectTrigger>
        <SelectContent>
          {field.controlledValues?.map((option) => (
            <SelectItem key={option} value={option}>
              {optionLabel(option)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function MultiSelectField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string[]) => void;
  disabled?: boolean;
}) {
  const selected = Array.isArray(value) ? (value as string[]) : [];
  return (
    <fieldset className={`flex w-full flex-col gap-1 ${GROUP_CONTAINER_CLASS}`} data-testid={`respiratory-field-${field.fieldId}`}>
      <legend className="px-1 text-xs font-medium text-rnica-textStrong">{field.label}</legend>
      {/* Entire pill is clickable (no separate checkbox square) — same
          toggle-button pattern as SegmentedField, but multiple options may
          be active at once. */}
      <div className="flex flex-wrap gap-1.5">
        {field.controlledValues?.map((option) => {
          const checked = selected.includes(option);
          return (
            <button
              key={option}
              type="button"
              role="checkbox"
              aria-checked={checked}
              disabled={disabled}
              onClick={() =>
                onChange(checked ? selected.filter((item) => item !== option) : [...selected, option])
              }
              style={pillStateStyle(checked)}
              className="rounded-md border px-2.5 py-1.5 text-[11px] leading-none transition-colors disabled:cursor-not-allowed disabled:opacity-50"
            >
              {checked ? (
                <span aria-hidden="true" className="mr-1">
                  ✓
                </span>
              ) : null}
              {option}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

/**
 * Per the approved Respiratory production candidate: exclusive single-
 * choice fields render as a compact, content-width segmented button row
 * (not a native dropdown), with the selected option solid-filled. Only
 * applied to the short, enumerated fields the design explicitly shows this
 * way (see `SEGMENTED_FIELD_IDS`); other single-selects keep the dropdown
 * control.
 */
function SegmentedField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string | undefined) => void;
  disabled?: boolean;
}) {
  const selected = typeof value === "string" ? value : undefined;
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <div role="radiogroup" aria-label={field.label} className="flex flex-wrap gap-1.5">
        {field.controlledValues?.map((option) => {
          const checked = selected === option;
          return (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={checked}
              disabled={disabled}
              // Clearable segmented control (usability-defect fix,
              // product-owner directive: "Every segmented choice must
              // support Selected / Unselected / Changed / Cleared"):
              // clicking the already-selected option toggles it back to
              // unselected/null rather than being a one-way, un-undoable
              // choice. Clicking a different option still changes the
              // selection normally.
              onClick={() => onChange(checked ? undefined : option)}
              style={pillStateStyle(checked)}
              className="rounded-md border px-2.5 py-1.5 text-[11px] leading-none transition-colors disabled:cursor-not-allowed disabled:opacity-50"
              title={checked ? "Click again to clear this selection" : undefined}
            >
              {checked ? (
                <span aria-hidden="true" className="mr-1">
                  ✓
                </span>
              ) : null}
              {optionLabel(option)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Per the approved production candidate, Assessment Context and Clinical
 * Comparison render as true inline radio buttons (not a segmented button
 * row and not a dropdown) — these are longer, distinct one-time
 * declarations rather than repeated clinical scans. Density Pass 2: capped
 * to a shared-row width so both fields sit side by side instead of each
 * claiming a full line, with internal options wrapping into extra lines
 * as needed.
 */
function RadioGroupField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const selected = typeof value === "string" ? value : undefined;
  return (
    <fieldset
      className={`flex w-full max-w-[460px] flex-col gap-1 ${GROUP_CONTAINER_CLASS}`}
      data-testid={`respiratory-field-${field.fieldId}`}
    >
      <legend className="px-1 text-xs font-medium text-rnica-textStrong">{field.label}</legend>
      <div role="radiogroup" aria-label={field.label} className="flex flex-wrap gap-x-3 gap-y-0.5">
        {field.controlledValues?.map((option) => {
          const optionId = `${field.fieldId}-${option}`;
          return (
            <label key={option} htmlFor={optionId} className="flex items-center gap-1.5 text-[11px] leading-none text-rnica-text">
              <input
                id={optionId}
                type="radio"
                name={field.fieldId}
                checked={selected === option}
                disabled={disabled}
                onChange={() => onChange(option)}
                className="h-3.5 w-3.5 accent-[var(--sns-teal)]"
              />
              {optionLabel(option)}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function BooleanField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label htmlFor={field.fieldId} className="flex items-center gap-1.5 text-xs text-rnica-text" data-testid={`respiratory-field-${field.fieldId}`}>
      <Checkbox id={field.fieldId} checked={value === true} disabled={disabled} onCheckedChange={(next) => onChange(next === true)} />
      {field.label}
    </label>
  );
}

/**
 * Density pass: free-text/number fields are sized to the content they
 * actually hold (a tracheostomy size, a liters/min value) rather than
 * stretched full-width — this is what lets short fields share a row
 * instead of each claiming a full line. Only genuinely long narrative
 * fields (`WIDE_TEXT_FIELD_IDS`) keep a full-width input.
 */
const NUMBER_WIDTH_CLASS = "w-[110px]";
const TEXT_WIDTH_CLASS: Record<string, string> = {
  respiratory_tracheostomy_type: "w-[160px]",
  respiratory_tracheostomy_size: "w-[120px]",
  respiratory_oxygen_other_device: "w-[180px]",
  respiratory_oxygen_hours_per_day: "w-[110px]",
  respiratory_poc_source_reference: "w-[200px]",
  respiratory_follow_up_responsible_clinician: "w-[200px]",
  respiratory_cough_follow_up_responsible_clinician: "w-[200px]",
};
const DEFAULT_TEXT_WIDTH_CLASS = "w-[240px]";
/** Narrative/explanatory fields the approved candidate shows as a full
 * content-width line — these hold free prose, not a short value. */
const WIDE_TEXT_FIELD_IDS = new Set([
  "respiratory_treatment_description",
  "respiratory_treatment_decline_reason",
  "respiratory_treatment_response",
  "respiratory_follow_up_timing_plan",
  "respiratory_poc_review_reason",
  "respiratory_oxygen_effectiveness_response",
  "respiratory_cough_action_description",
  "respiratory_cough_decline_reason",
  "respiratory_cough_response",
  "respiratory_cough_follow_up_timing_plan",
  "respiratory_ventilator_type_and_settings",
  "respiratory_ventilator_settings_source",
  "respiratory_airway_site_findings",
  "respiratory_support_response",
  "respiratory_support_follow_up_plan",
]);

function NumberField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: number | undefined) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>
        {field.label}
        {field.units ? ` (${field.units})` : ""}
      </FieldLabel>
      <input
        id={field.fieldId}
        type="number"
        disabled={disabled}
        className={`h-8 ${NUMBER_WIDTH_CLASS} max-w-full rounded-lg border border-rnica-border bg-rnica-bg px-2 py-1 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50`}
        value={typeof value === "number" ? value : ""}
        onChange={(event) => onChange(event.target.value === "" ? undefined : Number(event.target.value))}
      />
    </div>
  );
}

/**
 * PRODUCT-OWNER DIRECTIVE ("REMOVE FLOW VALUE + FLOW UNIT SPLIT MODEL"):
 * one clinical fact ("3 L/min") was split across two controls. For Nasal
 * Cannula / Mask (anything other than OTHER) the unit is auto-derived
 * (see the "respiratory_oxygen_delivery_device" case in
 * `applyCanonicalLegacyMapping`) and shown as fixed, non-editable inline
 * text beside the value -- the nurse enters one number only. OTHER keeps
 * a standalone Flow Unit dropdown (rendered separately via the normal
 * field dispatch, since `isFieldCurrentlyRelevant` only makes it relevant
 * for OTHER) for the rare device that genuinely needs a different unit.
 */
function OxygenFlowRateField({
  field,
  value,
  onChange,
  disabled = false,
  unit,
  showUnitInline,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: number | undefined) => void;
  disabled?: boolean;
  unit?: string;
  showUnitInline: boolean;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <div className="flex items-center gap-1.5">
        <input
          id={field.fieldId}
          type="number"
          disabled={disabled}
          className={`h-8 ${NUMBER_WIDTH_CLASS} max-w-full rounded-lg border border-rnica-border bg-rnica-bg px-2 py-1 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50`}
          value={typeof value === "number" ? value : ""}
          onChange={(event) => onChange(event.target.value === "" ? undefined : Number(event.target.value))}
        />
        {showUnitInline && unit && (
          <span
            className="text-[11px] text-rnica-muted"
            data-testid="respiratory-oxygen-flow-rate-unit"
          >
            {optionLabel(unit)}
          </span>
        )}
      </div>
    </div>
  );
}

function TextField({
  field,
  value,
  onChange,
  disabled = false,
  labelOverride,
  placeholder,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
  disabled?: boolean;
  labelOverride?: string;
  placeholder?: string;
}) {
  const widthClass = WIDE_TEXT_FIELD_IDS.has(field.fieldId)
    ? "w-full"
    : (TEXT_WIDTH_CLASS[field.fieldId] ?? DEFAULT_TEXT_WIDTH_CLASS);
  return (
    <div
      className={`flex flex-col gap-1 ${WIDE_TEXT_FIELD_IDS.has(field.fieldId) ? "w-full" : ""}`}
      data-testid={`respiratory-field-${field.fieldId}`}
    >
      <FieldLabel htmlFor={field.fieldId}>{labelOverride ?? field.label}</FieldLabel>
      <input
        id={field.fieldId}
        type="text"
        disabled={disabled}
        placeholder={placeholder}
        className={`h-8 ${widthClass} max-w-full rounded-lg border border-rnica-border bg-rnica-bg px-2 py-1 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50`}
        value={typeof value === "string" ? value : ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function DateField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <input
        id={field.fieldId}
        type="date"
        disabled={disabled}
        className="h-8 w-[150px] rounded-lg border border-rnica-border bg-rnica-bg px-2 py-1 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50"
        value={typeof value === "string" ? value : ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function TimeField({
  field,
  value,
  onChange,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <input
        id={field.fieldId}
        type="time"
        disabled={disabled}
        className="h-8 w-[120px] rounded-lg border border-rnica-border bg-rnica-bg px-2 py-1 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50"
        value={typeof value === "string" ? value : ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

/**
 * Short, exclusive-choice fields the approved production candidate renders
 * as a segmented button row rather than a dropdown. Every other
 * `single_select` field keeps the standard dropdown control.
 */
const SEGMENTED_FIELD_IDS = new Set([
  "respiratory_sob_severity",
  "respiratory_comfort_function_impact",
  "respiratory_treatment_decision",
  "respiratory_follow_up_need",
  "respiratory_poc_review_need",
  "respiratory_oxygen_use",
  "respiratory_oxygen_delivery_device",
  "respiratory_spo2_measurement_condition",
  "respiratory_cough_type",
  "respiratory_cough_action_decision",
  "respiratory_support_status",
]);

/**
 * Treatment Description is reused as a single canonical field across all
 * four Treatment Decision contexts, including DECLINED (hospice-admission
 * simplification, product-owner directive: do not create a separate data
 * field for every concept — decline reason, clinical rationale, and the
 * "what was done" narrative all live in this one field). The nurse-facing
 * label and placeholder change by context; the persisted key
 * (`treatmentDescription`) never changes.
 */
function treatmentDescriptionContext(draft: RespiratoryDraft): { label: string; placeholder?: string } {
  if (draft.treatmentDecision === "DECLINED") {
    return {
      label: "Decline Reason",
      placeholder: "Record why the treatment/intervention was declined and by whom.",
    };
  }
  if (draft.treatmentDecision === "NOT_INDICATED") {
    return {
      label: "Clinical Rationale",
      placeholder: "Briefly document why no Respiratory intervention is indicated for the current finding.",
    };
  }
  // FINAL PRODUCT-OWNER DIRECTIVE: not reachable for INITIATED/
  // ALREADY_IN_PLACE — isFieldCurrentlyRelevant() no longer renders this
  // field's active control for those two values (see
  // LegacyTreatmentDocumentation for their read-only historical display
  // instead). This fallback only matters if the field is ever rendered
  // before treatmentDecision is set.
  return { label: "Decline Reason / Clinical Rationale" };
}

const CLINICAL_RESPONSE_EVIDENCE_PLACEHOLDER =
  "Document the patient's observed response. Medication and treatment-order details belong in Orders.";

function GenericField({
  field,
  draft,
  updateDraft,
  disabled = false,
  visitDate,
}: {
  field: RespiratoryFieldDefinition;
  draft: RespiratoryDraft;
  updateDraft: (patch: Partial<RespiratoryDraft>) => void;
  disabled?: boolean;
  visitDate?: string;
}) {
  const value = getFieldValue(draft, field);
  const onChange = (next: unknown) => {
    const updated = setFieldValue(draft, field, next);
    updateDraft(applyCanonicalLegacyMapping(field, updated, visitDate) as Partial<RespiratoryDraft>);
  };

  switch (field.responseType) {
    case "single_select":
      return SEGMENTED_FIELD_IDS.has(field.fieldId) ? (
        <SegmentedField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />
      ) : (
        <SingleSelectField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />
      );
    case "multi_select":
      return <MultiSelectField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "boolean":
      return <BooleanField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "number":
      // PRODUCT-OWNER DIRECTIVE ("REMOVE FLOW VALUE + FLOW UNIT SPLIT
      // MODEL"): Oxygen Flow Rate is rendered as a single composite
      // control (value + inline unit) instead of the plain NumberField --
      // see OxygenFlowRateField below.
      return field.fieldId === "respiratory_oxygen_flow_value" ? (
        <OxygenFlowRateField
          field={field}
          value={value}
          onChange={(v) => onChange(v)}
          disabled={disabled}
          unit={draft.oxygenTherapy?.flowUnit}
          showUnitInline={draft.oxygenTherapy?.deliveryDevice !== "OTHER"}
        />
      ) : (
        <NumberField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />
      );
    case "text": {
      const override =
        field.fieldId === "respiratory_treatment_description" ? treatmentDescriptionContext(draft) : undefined;
      const placeholder =
        field.fieldId === "respiratory_clinical_response_evidence"
          ? CLINICAL_RESPONSE_EVIDENCE_PLACEHOLDER
          : override?.placeholder;
      return (
        <TextField
          field={field}
          value={value}
          onChange={(v) => onChange(v)}
          disabled={disabled}
          labelOverride={override?.label}
          placeholder={placeholder}
        />
      );
    }
    case "date":
      return <DateField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "time":
      return <TimeField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "datetime":
      return <TextField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    default:
      return null;
  }
}

const OXYGEN_DETAIL_FIELD_IDS = new Set([
  "respiratory_oxygen_delivery_type",
  "respiratory_oxygen_liters_per_minute",
  "respiratory_oxygen_delivery_mode",
  "respiratory_oxygen_sat_on_o2",
]);
const NEW_OXYGEN_DETAIL_FIELD_IDS = new Set([
  "respiratory_oxygen_delivery_device",
  "respiratory_oxygen_frequency",
]);
const VENTILATOR_DETAIL_FIELD_IDS = new Set([
  "respiratory_ventilator_type_and_settings",
  "respiratory_tracheostomy_type",
  "respiratory_tracheostomy_size",
]);
const SPUTUM_CHARACTERISTIC_FIELD_IDS = new Set([
  "respiratory_sputum_character",
  "respiratory_sputum_amount",
  "respiratory_sputum_color",
]);
const COUGH_ACTION_FIELD_IDS = new Set(["respiratory_cough_action_decision"]);
const COUGH_ACTION_TAKEN_FIELD_IDS = new Set([
  "respiratory_cough_action_description",
  "respiratory_cough_response",
  "respiratory_cough_action_date_time",
]);

/**
 * Usability-first presentation layer (progressive disclosure). Contract v2
 * field requirements, blocking rules, and completion logic are unchanged —
 * this only controls which already-required fields are visible right now,
 * per Contract v2's own allowance for hiding fields the parent response
 * makes inapplicable (e.g. oxygen device/flow/SpO2-on-O2 only matter once
 * oxygen is actually in use; sputum character only matters for a
 * productive cough).
 */
function isFieldCurrentlyRelevant(field: RespiratoryFieldDefinition, draft: RespiratoryDraft): boolean {
  if (OXYGEN_DETAIL_FIELD_IDS.has(field.fieldId)) {
    return draft.oxygenTherapy?.inUse === true;
  }
  if (field.fieldId === "respiratory_oxygen_hours_per_day") {
    // Ticket 3: only relevant once oxygen is actually in use, and never for
    // PRN (as-needed use has no "hours/day" concept — see the PRN hide
    // rule in the directive). Continuous keeps it visible but locked to a
    // derived 24 (see the disabled-prop check on this field's render and
    // the "respiratory_oxygen_frequency" case in
    // `applyCanonicalLegacyMapping` above).
    return draft.oxygenUse === "YES" && draft.oxygenTherapy?.frequency !== "PRN";
  }
  if (NEW_OXYGEN_DETAIL_FIELD_IDS.has(field.fieldId)) {
    return draft.oxygenUse === "YES";
  }
  if (field.fieldId === "respiratory_oxygen_other_device") {
    return draft.oxygenUse === "YES" && draft.oxygenTherapy?.deliveryDevice === "OTHER";
  }
  if (field.fieldId === "respiratory_oxygen_flow_value") {
    // Relabeled "Oxygen Flow Rate" (OxygenFlowRateField) -- the single
    // nurse-facing flow control, relevant whenever oxygen is in use,
    // regardless of which device/unit is in effect.
    return draft.oxygenUse === "YES";
  }
  if (field.fieldId === "respiratory_oxygen_flow_unit") {
    // PRODUCT-OWNER DIRECTIVE ("NASAL CANNULA / MASK ... Hidden from
    // user." / "OTHER ... show advanced unit selection"): a standalone
    // Flow Unit control is shown only when Delivery Device = OTHER. For
    // Nasal Cannula / Mask the unit is auto-derived to L/min (see the
    // "respiratory_oxygen_delivery_device" case in
    // `applyCanonicalLegacyMapping`) and displayed as fixed inline text
    // next to Oxygen Flow Rate instead (OxygenFlowRateField).
    return draft.oxygenUse === "YES" && draft.oxygenTherapy?.deliveryDevice === "OTHER";
  }
  if (field.fieldId === "respiratory_oxygen_unable_to_verify_reason") {
    return draft.oxygenUse === "UNABLE_TO_VERIFY";
  }
  if (field.fieldId === "respiratory_spo2_not_obtained_reason") {
    return draft.spo2MeasurementCondition === "NOT_OBTAINED";
  }
  // respiratory_oxygen_measurement_date / _time, respiratory_measured_
  // oxygen_flow_or_concentration, respiratory_oxygen_effectiveness_
  // response: no longer reachable here -- all four are retired into
  // LEGACY_HIDDEN_FIELD_IDS (removed from the rendered field arrays
  // entirely, see that Set's doc comment), not merely conditionally
  // hidden. Duplicate/redundant oxygen-outcome documentation (product-
  // owner directives "REMOVE Measured Oxygen Flow / Concentration" and
  // "REMOVE O2 EFFECTIVENESS / RESPONSE").
  if (VENTILATOR_DETAIL_FIELD_IDS.has(field.fieldId)) {
    // Legacy visibility rule (src/components/RNICA.jsx, "Ventilator /
    // Airway Support" card): these three fields only render once a
    // Short-Term or Long-Term Ventilator is actually in use.
    return draft.ventilator?.shortTermVentilator === true || draft.ventilator?.longTermVentilator === true;
  }
  if (
    field.fieldId === "respiratory_ventilator_duration" ||
    field.fieldId === "respiratory_ventilator_settings_source" ||
    field.fieldId === "respiratory_ventilator_settings_date" ||
    field.fieldId === "respiratory_ventilator_settings_time"
  ) {
    return Boolean(draft.respiratorySupportTypes?.includes("VENTILATOR"));
  }
  if (field.fieldId === "respiratory_support_types") {
    return draft.respiratorySupportStatus === "IN_USE";
  }
  if (field.fieldId === "respiratory_airway_site_findings") {
    return Boolean(draft.respiratorySupportTypes?.includes("TRACHEOSTOMY"));
  }
  if (field.fieldId === "respiratory_support_response") {
    return draft.respiratorySupportStatus === "IN_USE";
  }
  if (field.fieldId === "respiratory_support_unable_to_verify_reason") {
    return draft.respiratorySupportStatus === "UNABLE_TO_VERIFY";
  }
  if (SPUTUM_CHARACTERISTIC_FIELD_IDS.has(field.fieldId)) {
    return draft.coughType === "Productive";
  }
  if (field.fieldId === "respiratory_sputum_other_specification") {
    return draft.sputumCharacter === "OTHER" || draft.sputumColor === "OTHER";
  }
  if (field.fieldId === "respiratory_cough_clinical_significance") {
    return draft.hemoptysisPresent === true;
  }
  if (COUGH_ACTION_FIELD_IDS.has(field.fieldId)) {
    return draft.coughType === "Productive" || draft.hemoptysisPresent === true;
  }
  if (COUGH_ACTION_TAKEN_FIELD_IDS.has(field.fieldId)) {
    return draft.coughActionDecision === "ACTION_TAKEN";
  }
  if (field.fieldId === "respiratory_cough_decline_reason") {
    return draft.coughActionDecision === "DECLINED";
  }
  if (field.fieldId === "respiratory_cough_follow_up_timing_plan" || field.fieldId === "respiratory_cough_follow_up_responsible_clinician") {
    return draft.coughActionDecision === "ACTION_TAKEN" || draft.coughActionDecision === "DECLINED";
  }
  if (field.fieldId === "respiratory_treatment_response_status") {
    return draft.treatmentDecision === "INITIATED" || draft.treatmentDecision === "ALREADY_IN_PLACE";
  }
  if (field.fieldId === "respiratory_treatment_description") {
    // FINAL PRODUCT-OWNER DIRECTIVE (clinical workflow / data-ownership
    // correction): no longer an active control for INITIATED or
    // ALREADY_IN_PLACE — that was an unrestricted free-text box letting a
    // nurse re-enter order/medication details that belong exclusively to
    // the authoritative Orders/Medications workflow. Historical values for
    // those two decisions are preserved and shown read-only (see
    // LegacyTreatmentDocumentation below), never through this editable
    // control. Still active, reused contextually, for DECLINED ("Decline
    // Reason") and NOT_INDICATED ("Clinical Rationale") — no
    // medication-order risk exists for either.
    return draft.treatmentDecision === "DECLINED" || draft.treatmentDecision === "NOT_INDICATED";
  }
  if (field.fieldId === "respiratory_clinical_response" || field.fieldId === "respiratory_clinical_response_evidence") {
    // FINAL PRODUCT-OWNER DIRECTIVE: documents the patient's observed
    // response for INITIATED/ALREADY_IN_PLACE, replacing the removed
    // free-text "Describe the treatment" control for those two values.
    return draft.treatmentDecision === "INITIATED" || draft.treatmentDecision === "ALREADY_IN_PLACE";
  }
  if (field.fieldId === "respiratory_treatment_decline_reason") {
    return draft.treatmentDecision === "DECLINED";
  }
  if (
    field.fieldId === "respiratory_treatment_action_date" ||
    field.fieldId === "respiratory_treatment_action_time" ||
    field.fieldId === "respiratory_treatment_response_time" ||
    field.fieldId === "respiratory_treatment_response"
  ) {
    return draft.treatmentDecision === "INITIATED" || draft.treatmentDecision === "ALREADY_IN_PLACE";
  }
  if (field.fieldId === "respiratory_follow_up_timing_plan" || field.fieldId === "respiratory_follow_up_responsible_clinician") {
    return draft.followUpNeed === "NEEDED";
  }
  if (field.fieldId === "respiratory_poc_review_reason") {
    return draft.pocReviewNeed === "REVIEW_NEEDED";
  }
  if (field.fieldId === "respiratory_configured_follow_up_status") {
    return draft.configuredRequirementResponse === "FOLLOW_UP_REQUIRED";
  }
  if (field.fieldId === "respiratory_comfort_function_evidence") {
    return draft.comfortFunctionImpact === "IMPACT_PRESENT" || draft.comfortFunctionImpact === "UNABLE_TO_ASSESS";
  }
  if (field.fieldId === "respiratory_sputum_character") {
    return draft.coughType === "Productive";
  }
  if (field.fieldId === "respiratory_exertion_level") {
    // Dyspnea context: only relevant once some level of shortness of
    // breath has actually been documented (Contract v2: never inferred).
    return Boolean(draft.sobSeverity) && draft.sobSeverity !== "None";
  }
  if (field.fieldId === "respiratory_screening_date") {
    return draft.shortnessOfBreathScreened === true;
  }
  if (field.fieldId === "respiratory_treatment_date") {
    return draft.treatmentInitiated === true;
  }
  return true;
}

/** Moderate-or-severe dyspnea, per the usability directive's explicit
 * trigger for showing the intervention/response/urgency/follow-up
 * disposition workflow. "At rest" dyspnea is clinically at least as
 * significant as "Severe" and is included. */
function isDyspneaModerateOrSevere(draft: RespiratoryDraft): boolean {
  return draft.sobSeverity === "Moderate" || draft.sobSeverity === "Severe" || draft.sobSeverity === "At rest";
}

/** True once an intervention has already been documented, regardless of
 * current dyspnea severity — previously-entered data must never be hidden
 * by a later, less-severe re-assessment. */
function hasDocumentedIntervention(draft: RespiratoryDraft): boolean {
  return Boolean(
    draft.treatmentInitiated === true ||
      draft.treatmentDeclined === true ||
      draft.treatmentDecision != null ||
      draft.ventilator?.shortTermVentilator === true ||
      draft.ventilator?.longTermVentilator === true,
  );
}

/**
 * Clinical-thought-order field groupings for the two-column workspace
 * below. These are purely presentational groupings of the SAME verified
 * `RESPIRATORY_FIELD_INVENTORY` fields already rendered pre-refactor — no
 * field was added, renamed, or removed. Fields not present in the current
 * repository-backed inventory (e.g. a separate action/reassessment
 * timestamp, a POC-review toggle, sputum color, or a tri-state
 * "respiratory support status") are intentionally NOT fabricated here; see
 * `RESPIRATORY_NOT_VERIFIED_REQUIREMENTS` for the already-tracked gaps.
 */
const LEFT_COLUMN_FIELD_IDS = new Set([
  "respiratory_shortness_of_breath_screened",
  "respiratory_screening_date",
  "respiratory_sob_severity",
  "respiratory_exertion_level",
  "respiratory_comfort_function_impact",
  "respiratory_comfort_function_evidence",
  "respiratory_comfort_function_screening_date",
  "respiratory_comfort_function_screening_time",
  "respiratory_lung_sounds",
  "respiratory_respiration_pattern",
]);
const OXYGEN_SECTION_FIELD_IDS = new Set([
  "respiratory_oxygen_use",
  "respiratory_oxygen_unable_to_verify_reason",
  "respiratory_oxygen_in_use",
  "respiratory_oxygen_delivery_type",
  "respiratory_oxygen_delivery_device",
  "respiratory_oxygen_other_device",
  "respiratory_oxygen_liters_per_minute",
  "respiratory_oxygen_flow_value",
  "respiratory_oxygen_flow_unit",
  "respiratory_oxygen_frequency",
  "respiratory_oxygen_hours_per_day",
  "respiratory_oxygen_delivery_mode",
  "respiratory_oxygen_sat_on_o2",
  "respiratory_on_room_air",
  "respiratory_spo2_value",
  "respiratory_spo2_measurement_condition",
  "respiratory_spo2_not_obtained_reason",
  "respiratory_measured_oxygen_flow_or_concentration",
  "respiratory_oxygen_measurement_date",
  "respiratory_oxygen_measurement_time",
  "respiratory_oxygen_effectiveness_response",
]);
const COUGH_SECTION_FIELD_IDS = new Set([
  "respiratory_cough_type",
  "respiratory_sputum_character",
  "respiratory_sputum_amount",
  "respiratory_sputum_color",
  "respiratory_sputum_other_specification",
  "respiratory_cough_clinical_significance",
  "respiratory_cough_action_decision",
  "respiratory_cough_action_description",
  "respiratory_cough_decline_reason",
  "respiratory_cough_response",
  "respiratory_cough_action_date_time",
  "respiratory_cough_follow_up_timing_plan",
  "respiratory_cough_follow_up_responsible_clinician",
]);
const SUPPORT_SECTION_FIELD_IDS = new Set([
  "respiratory_support_status",
  "respiratory_support_types",
  "respiratory_ventilator_short_term",
  "respiratory_ventilator_long_term",
  "respiratory_ventilator_duration",
  "respiratory_ventilator_type_and_settings",
  "respiratory_ventilator_settings_source",
  "respiratory_ventilator_settings_date",
  "respiratory_ventilator_settings_time",
  "respiratory_tracheostomy_type",
  "respiratory_tracheostomy_size",
  "respiratory_airway_site_findings",
  "respiratory_support_response",
  "respiratory_support_follow_up_plan",
  "respiratory_support_unable_to_verify_reason",
]);
/**
 * Verified TRUE NURSE-FACING DUPLICATE / LEGACY COMPATIBILITY controls
 * (product-owner-authorized canonical mapping, see
 * `respiratoryBackwardCompatibility.ts`): each is now fully superseded by a
 * canonical field for nurse-facing purposes. The legacy keys remain in the
 * draft/stored shape, are kept in sync by `applyCanonicalLegacyMapping`,
 * and stay readable for history/audit — only their separate visible
 * control is retired here. Removed from document flow (filtered out of
 * the rendered field arrays below), never merely hidden with CSS, so they
 * occupy zero layout space.
 * - respiratory_treatment_initiated / respiratory_treatment_declined ->
 *   superseded by respiratory_treatment_decision.
 * - respiratory_oxygen_in_use -> superseded by respiratory_oxygen_use.
 * - respiratory_on_room_air -> superseded by respiratory_spo2_measurement_condition.
 * - respiratory_ventilator_short_term / respiratory_ventilator_long_term ->
 *   superseded by respiratory_ventilator_duration.
 * - respiratory_oxygen_delivery_type -> superseded by
 *   respiratory_oxygen_delivery_device.
 * - respiratory_oxygen_liters_per_minute -> superseded by
 *   respiratory_oxygen_flow_value / respiratory_oxygen_flow_unit.
 * - respiratory_oxygen_delivery_mode -> superseded by
 *   respiratory_oxygen_frequency.
 * - respiratory_oxygen_sat_on_o2 -> superseded by respiratory_spo2_value
 *   (read together with respiratory_spo2_measurement_condition).
 * - respiratory_oxygen_measurement_date / respiratory_oxygen_measurement_time
 *   -> removed entirely (FINAL PRODUCT-OWNER DIRECTIVE, "REMOVE OXYGEN
 *   MEASUREMENT DATE AND TIME"). RNICA is visit-based: Visit Date / Time
 *   In / Time Out already establish the assessment-date context for an
 *   SpO2 documented during the current visit, so a separate section-level
 *   measurement date/time is unnecessary and must never be fabricated
 *   (not copied from Time In, not derived from save/autosave/audit-log
 *   time). Unlike the four duplicate-concept fields above, these two have
 *   no canonical replacement to keep in sync — they are simply retired
 *   from the active workflow. Historical persisted values are preserved
 *   untouched (no migration, no write path here ever updates them) for
 *   audit/historical-detail view only; they are never required (see the
 *   removed blocks in `respiratoryProductRequirements.ts` /
 *   `respiratory_product_requirements.py`) and never populated going
 *   forward.
 * (Ticket 2, "TOO MUCH REDUNDANCY" directive: these four previously
 * rendered alongside their canonical replacement at the same time because
 * each pair was gated by a different, independently-settable visibility
 * flag — the legacy group by `oxygenTherapy.inUse` (mirrored from
 * `oxygenUse`) and the canonical group by `oxygenUse` directly — so a
 * record with only the legacy flag populated (common for historical data)
 * showed just the legacy controls, and a record with both populated
 * showed both at once, as confirmed live.)
 *
 * HOSPICE-ADMISSION SIMPLIFICATION (product-owner directive, "PRODUCT
 * OWNER CORRECTION"): the Treatment section is deliberately reduced to
 * exactly Treatment Decision, Treatment Narrative
 * (`respiratory_treatment_description`, reused contextually for
 * INITIATED/ALREADY_IN_PLACE/DECLINED/NOT_INDICATED — see
 * `treatmentDescriptionContext()`), and Follow-Up Needed, because a
 * hospital-style requirement to record exact intervention/response clock
 * times and a separate immediate-effectiveness evaluation does not match
 * real hospice admission practice (home, ALF, Board & Care, Memory Care,
 * SNF — intervention is frequently already performed by family,
 * caregiver, or facility staff before the RN arrives, and response is
 * routinely assessed at a later follow-up visit, not at admission). Each
 * field below remains fully intact in the draft/stored shape and backend
 * (so prior admissions that already recorded these values are never lost
 * or altered) — only its separate visible nurse-facing control is
 * retired, exactly like the legacy-duplicate controls above. The
 * corresponding requirement-engine rules in
 * `respiratoryProductRequirements.ts` / `respiratoryWorkflowRules.ts` were
 * updated in lockstep so completion never blocks on a field the nurse can
 * no longer see:
 * - respiratory_treatment_decline_reason -> folded into the shared
 *   Treatment Narrative field (DECLINED context).
 * - respiratory_treatment_action_date / respiratory_treatment_action_time /
 *   respiratory_treatment_response / respiratory_treatment_response_status /
 *   respiratory_treatment_response_time -> removed; hospice admission
 *   never requires exact intervention/response timing or an immediate
 *   effectiveness evaluation.
 * - respiratory_follow_up_timing_plan / respiratory_follow_up_responsible_clinician
 *   -> removed; only whether follow-up is needed is recorded at
 *   admission.
 * - respiratory_poc_review_need / respiratory_poc_review_reason /
 *   respiratory_poc_source_reference -> removed; POC review is handled
 *   through narrative documentation / follow-up, not a separate control.
 * - respiratory_configured_requirement_response / respiratory_configured_follow_up_status
 *   -> removed along with the rest of the Treatment section's secondary
 *   fields.
 * - respiratory_treatment_date ("SOB Treatment Date", legacy source
 *   `respiratory.treatmentDate`) -> removed. This is a *different* field
 *   from respiratory_treatment_action_date above — an earlier-milestone
 *   ported field whose sole consumer is HOPE J2040-B report generation
 *   (`hopeReportMapper.js`); it has zero reference in either requirement
 *   engine, so it is Reporting-Support-only, not Clinical-Workflow
 *   (HOPE-vs-clinical field audit). Since there is no longer a
 *   nurse-facing control for it, `applyCanonicalLegacyMapping` in this
 *   file auto-generates it (today's date, the first time the decision
 *   becomes Initiated) so HOPE reporting keeps working without asking
 *   the nurse for an exact intervention date.
 * - respiratory_comfort_function_screening_time ("Comfort / Function
 *   Screening Time") -> removed entirely (not hidden-but-retained, not
 *   made optional — the field is gone from the nurse workflow). Hospice
 *   documentation is visit-based: Visit Date/Type/Timestamp already
 *   establish the clinical time reference, so a separate exact clock
 *   time for when comfort/functional impact was screened provides no
 *   additional clinical, regulatory, payer, or patient-safety value. The
 *   correct question is "was it assessed during this visit", not "at
 *   what exact minute" — `respiratory_comfort_function_screening_date`
 *   is kept (date-level tracking remains useful), only the Time field is
 *   removed. It has zero reference in either requirement engine and zero
 *   HOPE/reporting consumer, so unlike respiratory_treatment_date above
 *   it needs no auto-generation replacement — nothing downstream reads
 *   it.
 * - respiratory_screening_date ("SOB Screening Date") and
 *   respiratory_comfort_function_screening_date ("Comfort / Function
 *   Screening Date") -> removed from the visible workflow (product-owner
 *   directive, "RNICA is visit-centric... Visit Header = Visit Metadata,
 *   Body Systems = Clinical Findings... do not mix the two"). The RNICA
 *   Visit Header (Visit Date/Time In/Time Out, see `formData.visitMeta`
 *   in RNICA.jsx) is already the source of truth for when the visit —
 *   and therefore the assessment performed during it — occurred; a nurse
 *   documenting SOB screening or a Comfort/Function impact during the
 *   current visit should never be asked to re-enter that same date. Both
 *   fields are auto-filled from the `visitDate` prop (see the
 *   `useEffect` in `RespiratoryPanel` below) the first time their
 *   respective trigger condition becomes true while the date is still
 *   blank, exactly like `respiratory_treatment_date`'s auto-generation —
 *   no popup, no visible control, no mandatory override-reason field.
 *   The one-time-fill is never overwritten, so a date loaded from a
 *   prior save (including one that genuinely differs from the visit
 *   date, e.g. a historical/late-documented assessment) is always
 *   preserved. A true exception (documenting an assessment that
 *   occurred on another date) is recorded narratively in Respiratory
 *   Notes rather than through a separate structured date-override
 *   control, per the same directive.
 *
 * PRODUCT-OWNER DIRECTIVE ("REMOVE Measured Oxygen Flow / Concentration" /
 * "REMOVE O2 EFFECTIVENESS / RESPONSE"): respiratory_measured_oxygen_flow_
 * or_concentration and respiratory_oxygen_effectiveness_response are
 * retired for the same reason as the other oxygen sub-fields above --
 * each duplicated a clinical fact already documented elsewhere in the
 * same Oxygen section (the current Oxygen Flow Rate, and the objective
 * SpO2 Value / Measurement Condition pair, respectively). Both fields
 * remain fully intact in the draft/stored shape and backend; only their
 * nurse-facing controls are removed, with no migration of historical
 * values.
 *
 * PRODUCT-OWNER DIRECTIVE ("RESPIRATORY SUPPORT FOLLOW-UP PLAN -- JUSTIFY
 * WHY THIS FIELD EXISTS"): respiratory_support_follow_up_plan is retired.
 * It was a free-text future-respiratory-intervention narrative -- POC's
 * purpose (goals, interventions, follow-up actions, treatment plans), not
 * RNICA's (assessment, findings, clinical status, clinical response). It
 * was never required by either requirement engine (no `push(...)` exists
 * for it in respiratoryProductRequirements.ts/.py) and is read by no
 * downstream consumer (structured_findings.py, rnica_poc_adapter.py, or
 * hopeReportMapper.js) -- a dead control duplicating content that belongs
 * on the Plan of Care. `respiratory_support_status` (None / In Use /
 * Unable To Verify) remains the sole canonical source fact for Findings /
 * Narrative / HOPE / POC generation; a true follow-up plan is authored on
 * the POC, not re-collected inside the RNICA. The field remains fully
 * intact in the draft/stored shape and backend; only its nurse-facing
 * control is removed, with no migration of historical values.
 *
 * PRODUCT-OWNER DIRECTIVE ("FINAL RESPIRATORY USABILITY REVIEW" --
 * A=Assessment Finding vs B=Future Plan classification):
 * respiratory_cough_follow_up_timing_plan and
 * respiratory_cough_follow_up_responsible_clinician are retired, same
 * reasoning and same disposition as respiratory_follow_up_timing_plan /
 * respiratory_follow_up_responsible_clinician and
 * respiratory_support_follow_up_plan above -- "who will do what, when, in
 * the future" is POC content, not an RNICA assessment finding. Unlike
 * respiratory_support_follow_up_plan, these two WERE actively required
 * (whenever coughActionDecision was ACTION_TAKEN or DECLINED); the
 * requirement pushes have been removed from both
 * respiratoryProductRequirements.ts and
 * respiratory_product_requirements.py, not merely hidden here. Neither
 * field is read by any downstream consumer (structured findings,
 * narrative, HOPE, or POC generation).
 *
 * PRODUCT-OWNER DIRECTIVE ("ALIGN RESPIRATORY TREATMENT AND SFV LOGIC WITH
 * THE APPROVED HOPE/SFV GUIDE", Section 8 -- Cough Action disposition,
 * supersedes the "stays required" note formerly here): Cough Action
 * Decision/Action Description/Decline Reason/Response/Action Date-Time
 * remain nurse-facing, present-tense findings (what was actually
 * assessed/done *this visit*, not a future plan) -- they are NOT retired
 * or hidden -- but a repository-wide consumer audit confirmed none of
 * J2030 (SOB screening), J2040 (SOB treatment), J2051B (SOB impact/SFV
 * trigger), or any narrative/structured-finding/POC generator reads them;
 * their only consumer was this requirement engine's own completion-
 * blocker logic. The requirement pushes for
 * respiratory_cough_action_decision/_description/_response/
 * _date_time/_decline_reason have been removed from both
 * respiratoryProductRequirements.ts and respiratory_product_requirements.py.
 *
 * PRODUCT-OWNER DECISION ("What unique business purpose remains after
 * Treatment Decision / Clinical Response / Follow-Up Need already exist
 * for SOB?"): with no HOPE, SFV, POC, structured-finding, or narrative
 * ownership, Cough Action Decision/Description/Response/Date-Time/Decline
 * Reason are retired from the active Respiratory UI (moved into
 * LEGACY_HIDDEN_FIELD_IDS below), not merely unblocked. SOB's own
 * Treatment Decision / Clinical Response / Follow-Up Need fields already
 * cover the same "was an intervention done, and how did it respond"
 * ground for the symptom that actually drives HOPE/SFV -- a second,
 * cough-specific action/response/date-time workflow duplicated that
 * without feeding any downstream consumer. The underlying fields,
 * contract-v2 definitions, and backend columns are NOT removed; any
 * previously-stored values are preserved and unaffected -- this only
 * removes the nurse-facing controls, per the standing "preserve
 * historical values, do not remove underlying fields until migration and
 * compatibility review" constraint. `respiratory_cough_type` (Productive/
 * Non-productive) and the sputum/hemoptysis findings remain fully active
 * -- those are the actual Respiratory assessment findings; only the
 * cough-specific intervention/response/date-time sub-workflow is retired.
 */
const LEGACY_HIDDEN_FIELD_IDS = new Set([
  "respiratory_treatment_initiated",
  "respiratory_treatment_declined",
  "respiratory_oxygen_in_use",
  "respiratory_on_room_air",
  "respiratory_oxygen_delivery_type",
  "respiratory_oxygen_liters_per_minute",
  "respiratory_oxygen_delivery_mode",
  "respiratory_oxygen_sat_on_o2",
  "respiratory_oxygen_measurement_date",
  "respiratory_oxygen_measurement_time",
  "respiratory_measured_oxygen_flow_or_concentration",
  "respiratory_oxygen_effectiveness_response",
  "respiratory_ventilator_short_term",
  "respiratory_ventilator_long_term",
  "respiratory_treatment_decline_reason",
  "respiratory_treatment_action_date",
  "respiratory_treatment_action_time",
  "respiratory_treatment_response",
  "respiratory_treatment_response_status",
  "respiratory_treatment_response_time",
  "respiratory_follow_up_timing_plan",
  "respiratory_follow_up_responsible_clinician",
  "respiratory_poc_review_need",
  "respiratory_poc_review_reason",
  "respiratory_poc_source_reference",
  "respiratory_configured_requirement_response",
  "respiratory_configured_follow_up_status",
  "respiratory_treatment_date",
  "respiratory_comfort_function_screening_time",
  "respiratory_screening_date",
  "respiratory_comfort_function_screening_date",
  "respiratory_support_follow_up_plan",
  "respiratory_cough_follow_up_timing_plan",
  "respiratory_cough_follow_up_responsible_clinician",
  "respiratory_cough_action_decision",
  "respiratory_cough_action_description",
  "respiratory_cough_response",
  "respiratory_cough_action_date_time",
  "respiratory_cough_decline_reason",
  // PRODUCT-OWNER DECISION ("Permanent Retirement Enforcement" / "Two
  // Authorized Removal States"): Comfort / Function Evidence is
  // RETIRED_FROM_ACTIVE_WORKFLOW -- no HOPE/SFV, structured-finding,
  // Clinical Story, or POC consumer exists; the only consumer was its own
  // completion rule (circular validation). See
  // docs/governance/SNS_RETIRED_FEATURES.json, id
  // "respiratory.comfortFunctionEvidence". Historical values remain
  // readable; this control must never reappear on new assessments without
  // a new explicit Product Owner decision.
  "respiratory_comfort_function_evidence",
]);

/**
 * Collapses a verbose "Record the ..." unresolved-requirement sentence
 * into a short clinical-domain label for the collapsed banner view. Pure
 * keyword matching over the existing message text — no change to the
 * underlying requirement engine, message wording, or completion logic.
 * Falls back to the original message (truncated) if no domain matches, so
 * nothing is ever silently dropped.
 */
const DOMAIN_LABEL_RULES: Array<[RegExp, string]> = [
  [/assessment context/i, "Context"],
  [/comparison/i, "Comparison"],
  [/oxygen/i, "Oxygen"],
  [/sputum/i, "Sputum"],
  [/cough/i, "Cough Action"],
  [/respiratory support|ventilator|tracheostomy|airway/i, "Support"],
  [/follow-?up/i, "Follow-Up"],
  [/poc review/i, "POC Review"],
  [/treatment/i, "Treatment"],
  [/lung sound/i, "Lung Sounds"],
  [/(respiration|breathing) pattern/i, "Pattern"],
  [/comfort|function/i, "Comfort"],
  [/shortness of breath|dyspnea|sob/i, "Dyspnea"],
];

function deriveDomainLabel(message: string): string {
  for (const [pattern, label] of DOMAIN_LABEL_RULES) {
    if (pattern.test(message)) return label;
  }
  return message.length > 24 ? `${message.slice(0, 24)}…` : message;
}

/**
 * Documentation Coverage: a single, top-positioned, actionable summary of
 * what's unresolved. Per the density-optimization pass, the default view
 * is a compact collapsed row (count + deduplicated domain pills); the
 * original full "Record the ..." sentences remain available on demand via
 * "Show details" rather than always consuming vertical space.
 */
function DocumentationCoverageBanner({ blockingMessages }: { blockingMessages: string[] }) {
  const [expanded, setExpanded] = useState(false);

  if (blockingMessages.length === 0) {
    return (
      <section
        className="flex items-center gap-2 rounded-lg border border-rnica-tealSoftBorder bg-rnica-tealSoftBg px-3 py-1.5"
        aria-label="Documentation coverage"
        data-testid="respiratory-completion-blockers"
      >
        <span className="text-xs font-medium text-rnica-textStrong">Documentation coverage complete — no unresolved items.</span>
      </section>
    );
  }

  const domainCounts = new Map<string, number>();
  for (const message of blockingMessages) {
    const label = deriveDomainLabel(message);
    domainCounts.set(label, (domainCounts.get(label) ?? 0) + 1);
  }

  return (
    <section
      className="flex flex-col gap-1 rounded-lg border border-rnica-border bg-rnica-bg px-2.5 py-1"
      aria-label="Documentation coverage"
      data-testid="respiratory-completion-blockers"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <h3 className="text-xs font-semibold uppercase text-rnica-muted">
          Documentation coverage — {blockingMessages.length} unresolved
        </h3>
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="text-[11px] font-medium text-rnica-teal underline-offset-2 hover:underline"
          aria-expanded={expanded}
        >
          {expanded ? "Hide details" : "Show details"}
        </button>
      </div>
      <ul className="flex flex-wrap gap-1">
        {Array.from(domainCounts.entries()).map(([label, count]) => (
          <li
            key={label}
            className="rounded-full border border-rnica-borderWarning bg-rnica-warningBg px-2 py-0.5 text-[11px] leading-tight text-rnica-text"
          >
            {label}
            {count > 1 ? ` (${count})` : ""}
          </li>
        ))}
      </ul>
      {expanded && (
        <ul className="flex flex-col gap-0 border-t border-rnica-border pt-0.5">
          {blockingMessages.map((message) => (
            <li key={message} className="text-[11px] leading-tight text-rnica-text">
              {message}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

const SAVE_STATE_MESSAGE: Record<string, string> = {
  idle: "",
  saving: "Saving…",
  saved: "Saved.",
  error: "Save failed.",
  conflict: "Save blocked — this assessment changed elsewhere.",
};

export function RespiratoryPanel({ assessmentId, readOnly = false, visitDate }: RespiratoryPanelProps) {
  const {
    loadState,
    assessment,
    draft,
    completion,
    updateDraft,
    saveState,
    saveError,
    save,
    completeReview,
    reload,
  } = useRespiratoryAssessment(assessmentId);
  const [notesFocused, setNotesFocused] = useState(false);

  // Hospice visit-based documentation directive: default SOB Screening Date
  // and Comfort/Function Screening Date to the visit date the first time
  // each relevant section is engaged (SOB screened, or a Comfort/Function
  // impact recorded) while its date field is still blank -- mirrors the
  // legacy RNICA.jsx screening/treatment-date auto-fill precedent. This is a
  // one-time fill only: once a date is present (default or nurse-entered),
  // it is never overwritten here, so edits/overrides are always preserved.
  useEffect(() => {
    if (!visitDate) return;
    const patch: Partial<RespiratoryDraft> = {};
    if (draft.shortnessOfBreathScreened === true && !draft.screeningDate) {
      patch.screeningDate = visitDate;
    }
    if (draft.comfortFunctionImpact && !draft.comfortFunctionScreeningDate) {
      patch.comfortFunctionScreeningDate = visitDate;
    }
    if (Object.keys(patch).length > 0) {
      updateDraft(patch);
    }
  }, [
    visitDate,
    draft.shortnessOfBreathScreened,
    draft.screeningDate,
    draft.comfortFunctionImpact,
    draft.comfortFunctionScreeningDate,
    updateDraft,
  ]);

  // One-time migration for records saved before the Cough Type model
  // correction: the retired "Hemoptysis"/"Barrel chest" coughType values
  // never represented cough productivity in the first place -- they were a
  // single-select modeling defect that made Hemoptysis and Barrel chest
  // mutually exclusive with Productive/Non-productive. Migrate them once
  // into the correct independent fields and clear the invalid coughType
  // value (not a real productivity response) rather than leaving data the
  // Cough Type select can no longer represent.
  useEffect(() => {
    const legacyCoughType = draft.coughType;
    if (legacyCoughType !== "Hemoptysis" && legacyCoughType !== "Barrel chest") return;
    const patch: Partial<RespiratoryDraft> = { coughType: undefined };
    if (legacyCoughType === "Hemoptysis" && draft.hemoptysisPresent !== true) {
      patch.hemoptysisPresent = true;
    }
    if (legacyCoughType === "Barrel chest" && draft.barrelChestPresent !== true) {
      patch.barrelChestPresent = true;
    }
    updateDraft(patch);
  }, [draft.coughType, draft.hemoptysisPresent, draft.barrelChestPresent, updateDraft]);

  if (loadState === "loading") {
    return (
      <div data-testid="respiratory-panel" className="p-3 text-xs text-rnica-muted" role="status">
        Loading Respiratory assessment…
      </div>
    );
  }

  if (loadState === "unauthorized") {
    return (
      <div data-testid="respiratory-panel" className="p-3">
        <Alert variant="critical">
          <AlertDescription>You are not authorized to view this patient&apos;s Respiratory assessment.</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loadState === "unavailable") {
    return (
      <div data-testid="respiratory-panel" className="p-3">
        <Alert>
          <AlertDescription>Respiratory assessment is unavailable for this patient.</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loadState === "network_error" || !assessment) {
    return (
      <div data-testid="respiratory-panel" className="flex flex-col gap-2 p-3">
        <Alert variant="critical">
          <AlertDescription>Unable to load the Respiratory assessment. Check your connection.</AlertDescription>
        </Alert>
        <Button variant="outline" size="sm" onClick={() => void reload()}>
          Retry
        </Button>
      </div>
    );
  }

  const isUnableToAssess = draft.respiratoryUnableToAssess === true;
  const unableToAssessReasonValue = getFieldValue(draft, RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD);
  const detailFields = RESPIRATORY_FIELD_INVENTORY.filter(
    (field) =>
      !HANDLED_SEPARATELY_FIELD_IDS.has(field.fieldId) &&
      !INTERVENTION_FIELD_IDS.has(field.fieldId) &&
      !FOLLOW_UP_FIELD_IDS.has(field.fieldId),
  );
  const interventionFields = RESPIRATORY_FIELD_INVENTORY.filter(
    (field) =>
      INTERVENTION_FIELD_IDS.has(field.fieldId) &&
      !LEGACY_HIDDEN_FIELD_IDS.has(field.fieldId) &&
      isFieldCurrentlyRelevant(field, draft),
  );
  const followUpFields = RESPIRATORY_FIELD_INVENTORY.filter((field) => FOLLOW_UP_FIELD_IDS.has(field.fieldId)).filter(
    (field) => !LEGACY_HIDDEN_FIELD_IDS.has(field.fieldId) && isFieldCurrentlyRelevant(field, draft),
  );
  const relevantDetailFields = detailFields.filter(
    (field) => isFieldCurrentlyRelevant(field, draft) && !LEGACY_HIDDEN_FIELD_IDS.has(field.fieldId),
  );
  const leftColumnFields = relevantDetailFields.filter((field) => LEFT_COLUMN_FIELD_IDS.has(field.fieldId));
  const oxygenFields = relevantDetailFields.filter((field) => OXYGEN_SECTION_FIELD_IDS.has(field.fieldId));
  const coughFields = relevantDetailFields.filter((field) => COUGH_SECTION_FIELD_IDS.has(field.fieldId));
  const supportFields = relevantDetailFields.filter((field) => SUPPORT_SECTION_FIELD_IDS.has(field.fieldId));
  const clinicalStatusField = relevantDetailFields.find((field) => field.fieldId === "respiratory_clinical_status_change");

  return (
    // Approved Respiratory production candidate: clinical-thought-order
    // workflow, no independent summary/findings rail. Documentation
    // coverage stays top-positioned and actionable; the desktop working
    // region is a genuine two-column split by clinical content (Dyspnea/
    // pattern/lung sounds left, Treatment/Oxygen right), with Cough and
    // Respiratory Support as full-width workflows below. Stacks to one
    // column below `lg`.
    <div data-testid="respiratory-panel" className="flex flex-col gap-2 p-2.5">
      <DocumentationCoverageBanner blockingMessages={completion.complete ? [] : completion.blockingMessages} />

      {/*
        Assessment context: Contract v2's two explicit, non-gating
        declarations plus the existing clinical-status comparison field,
        grouped as one compact top row (not a gate other fields wait on).
      */}
      <section className="flex flex-wrap items-center gap-3" aria-label="Assessment context" data-testid="respiratory-context-row">
        <BooleanField
          field={RESPIRATORY_NO_CURRENT_CONCERN_FIELD}
          value={draft.respiratoryNoCurrentConcern}
          onChange={(value) => updateDraft({ respiratoryNoCurrentConcern: value })}
          disabled={readOnly}
        />
        <BooleanField
          field={RESPIRATORY_UNABLE_TO_ASSESS_FIELD}
          value={draft.respiratoryUnableToAssess}
          onChange={(value) => updateDraft({ respiratoryUnableToAssess: value })}
          disabled={readOnly}
        />
        {clinicalStatusField && (
          <SingleSelectField
            field={clinicalStatusField}
            value={getFieldValue(draft, clinicalStatusField)}
            onChange={(value) => updateDraft(setFieldValue(draft, clinicalStatusField, value) as Partial<RespiratoryDraft>)}
            disabled={readOnly}
          />
        )}
      </section>

      <section
        className="flex flex-wrap items-start gap-3"
        aria-label="Assessment context and comparison"
        data-testid="respiratory-assessment-context-section"
      >
        <RadioGroupField
          field={RESPIRATORY_ASSESSMENT_CONTEXT_FIELD}
          value={draft.assessmentContext}
          onChange={(value) => updateDraft({ assessmentContext: value as RespiratoryDraft["assessmentContext"] })}
          disabled={readOnly}
        />
        <RadioGroupField
          field={RESPIRATORY_CLINICAL_COMPARISON_FIELD}
          value={draft.clinicalComparison}
          onChange={(value) => updateDraft({ clinicalComparison: value as RespiratoryDraft["clinicalComparison"] })}
          disabled={readOnly}
        />
        {draft.clinicalComparison === "CHANGED_FROM_PRIOR" && (
          <TextField
            field={RESPIRATORY_CLINICAL_STATUS_CHANGE_DETAIL_FIELD}
            value={draft.clinicalStatusChangeDetail}
            onChange={(value) => updateDraft({ clinicalStatusChangeDetail: value })}
            disabled={readOnly}
          />
        )}
      </section>

      {isUnableToAssess && (
        <section className="flex flex-col gap-2" data-testid="respiratory-limitation-section" aria-label="Assessment limitation">
          <h3 className="text-xs font-semibold uppercase text-rnica-muted">Assessment limitation</h3>
          <SingleSelectField
            field={RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD}
            value={unableToAssessReasonValue}
            onChange={(value) => updateDraft({ respiratoryUnableToAssessReason: value })}
            disabled={readOnly}
          />
          {unableToAssessReasonValue === "Other" && (
            <TextField
              field={RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD}
              value={draft.respiratoryUnableToAssessOther}
              onChange={(value) => updateDraft({ respiratoryUnableToAssessOther: value })}
              disabled={readOnly}
            />
          )}
        </section>
      )}

      <div className="grid grid-cols-1 gap-2.5 lg:grid-cols-2 lg:items-start">
        <div className="flex flex-col gap-2.5" data-testid="respiratory-left-column">
          <section
            className="flex flex-col gap-2"
            aria-label="Dyspnea, impact, and observed breathing"
            data-testid="respiratory-current-evidence-section"
          >
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Dyspnea, impact &amp; observed breathing</h3>
            <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5">
              {leftColumnFields.map((field) => (
                <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} visitDate={visitDate} />
              ))}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-2.5" data-testid="respiratory-right-column">
          <section
            className="flex flex-col gap-2"
            aria-label="Treatment decision, response, and follow-up"
            data-testid="respiratory-intervention-section"
          >
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Treatment decision, response &amp; follow-up</h3>
            {(isDyspneaModerateOrSevere(draft) || hasDocumentedIntervention(draft)) && (
              <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5">
                {interventionFields.map((field) => (
                  <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} visitDate={visitDate} />
                ))}
              </div>
            )}
            {/*
              FINAL PRODUCT-OWNER DIRECTIVE, section 16: historical
              Treatment/Intervention free text entered for Initiated/
              Already in Place before this correction is preserved and
              shown read-only ("Legacy Respiratory Treatment
              Documentation") — never deleted, never editable through this
              retired control, and never automatically converted into an
              order or placed on the medication profile.
            */}
            {(draft.treatmentDecision === "INITIATED" || draft.treatmentDecision === "ALREADY_IN_PLACE") &&
              typeof draft.treatmentDescription === "string" &&
              draft.treatmentDescription.trim().length > 0 && (
                <div className="flex flex-col gap-1" data-testid="respiratory-legacy-treatment-documentation">
                  <FieldLabel>Legacy Respiratory Treatment Documentation (read-only)</FieldLabel>
                  <p className="max-w-full whitespace-pre-wrap rounded-lg border border-rnica-border bg-rnica-bg px-2 py-1 text-[11px] text-rnica-muted">
                    {draft.treatmentDescription}
                  </p>
                </div>
              )}
            {/*
              Follow-Up merged visually into the Treatment workflow per
              Density Pass 3 (it is part of the same clinical decision,
              not an independent card). Testid preserved for the existing
              test assertion; renders nothing (zero added height) when
              there are no applicable follow-up fields.
            */}
            {followUpFields.length > 0 && (
              <div
                className="flex flex-wrap items-start gap-x-3 gap-y-1.5"
                data-testid="respiratory-follow-up-section"
                aria-label="Follow-up"
              >
                {followUpFields.map((field) => (
                  <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} visitDate={visitDate} />
                ))}
              </div>
            )}
            {followUpFields.length === 0 && <div data-testid="respiratory-follow-up-section" aria-hidden="true" className="hidden" />}
          </section>

          <section className="flex flex-col gap-2" aria-label="Oxygen use and measurement" data-testid="respiratory-oxygen-section">
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Oxygen use &amp; measurement</h3>
            <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5">
              {oxygenFields.map((field) => (
                <GenericField
                  key={field.fieldId}
                  field={field}
                  draft={draft}
                  updateDraft={updateDraft}
                  // Ticket 3: Continuous oxygen use is, by definition, 24
                  // hours/day — the value is auto-derived (see the
                  // "respiratory_oxygen_frequency" case in
                  // `applyCanonicalLegacyMapping`) and locked read-only so
                  // the nurse can never enter a contradictory number.
                  disabled={
                    readOnly ||
                    (field.fieldId === "respiratory_oxygen_hours_per_day" && draft.oxygenTherapy?.frequency === "CONTINUOUS")
                  }
                  visitDate={visitDate}
                />
              ))}
            </div>
          </section>
        </div>
      </div>

      {/*
        RESPIRATORY FINAL UI OPTIMIZATION (product-owner directive --
        "Place Cough Action and Respiratory Support on same horizontal
        row" / "Convert Secretions & Respiratory Support into a
        two-column layout" / "Utilize unused right-column space" /
        "Minimize vertical scrolling"): Secretions (Cough/Sputum) and
        Respiratory Support render as a true side-by-side 2-column grid
        at `lg` (not two stacked full-width rows), the same column split
        already used for the Dyspnea/Treatment grid above. Progressive
        disclosure is unchanged -- cough/secretions fields only render
        for a Productive cough or hemoptysis (sputum fields specifically
        stay hidden until coughType = Productive, see
        SPUTUM_CHARACTERISTIC_FIELD_IDS gating above); support-detail
        fields only render once Respiratory Support Status = In Use. The
        whole card renders nothing when neither group has anything to
        show (zero added height). `data-testid`s on the inner groups are
        preserved for existing test/debugging hooks.
      */}
      {(coughFields.length > 0 || supportFields.length > 0) && (
        <section className="flex flex-col gap-2" aria-label="Secretions and respiratory support" data-testid="respiratory-secretions-support-section">
          <h3 className="text-xs font-semibold uppercase text-rnica-muted">Secretions &amp; respiratory support</h3>
          <div className="grid grid-cols-1 gap-x-4 gap-y-1.5 lg:grid-cols-2 lg:items-start">
            {coughFields.length > 0 && (
              <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5" data-testid="respiratory-cough-section">
                {coughFields.map((field) => (
                  <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} visitDate={visitDate} />
                ))}
              </div>
            )}
            {supportFields.length > 0 && (
              <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5" data-testid="respiratory-support-section">
                {supportFields.map((field) => (
                  <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} visitDate={visitDate} />
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/*
        RESPIRATORY FINAL UI OPTIMIZATION (product-owner directive --
        "Justify Respiratory Notes" / "Retire Respiratory Notes if
        information is already generated through narrative synthesis"):
        Reviewed and KEPT. Confirmed (grep across
        clinicalNarrativeBuilder.js, structured_findings.py,
        rnica_poc_adapter.py, hopeReportMapper.js) that no narrative-
        synthesis pipeline exists today that reads structured Respiratory
        fields and reproduces an equivalent free-text sentence --
        clinicalNarrativeBuilder.js composes a *different*,
        patient-level summary from sobSeverity/lungSounds and never
        reads this field. Per RNICA_COMPLETION_MATRIX.md this is the
        catch-all "RN-only-by-design... free-text narrative / clinical
        judgment field" for observations that genuinely do not fit any
        structured control (the same category as the retained Cough
        Action fields, not a future-plan field) -- retiring it now, with
        no synthesis feature to replace it, would be a pure data-capture
        loss, not a duplication removal. Retained.
      */}
      <div className="flex flex-col gap-1">
        <FieldLabel htmlFor={RESPIRATORY_NOTES_FIELD.fieldId}>{RESPIRATORY_NOTES_FIELD.label}</FieldLabel>
        <Textarea
          id={RESPIRATORY_NOTES_FIELD.fieldId}
          rows={notesFocused || !!draft.notes ? 4 : 1}
          value={draft.notes ?? ""}
          onChange={(event) => updateDraft({ notes: event.target.value })}
          onFocus={() => setNotesFocused(true)}
          onBlur={() => setNotesFocused(false)}
          disabled={readOnly}
        />
      </div>

      {assessment.openReviewExceptions.length > 0 && (
        <section className="flex flex-col gap-2" aria-label="Review exceptions" data-testid="respiratory-review-exceptions">
          <h3 className="text-xs font-semibold uppercase text-rnica-muted">Review exceptions</h3>
          <ul className="flex flex-col gap-1">
            {assessment.openReviewExceptions.map((exception) => (
              <li key={exception.id} className="text-xs text-rnica-text">
                <a href={exception.fieldPath ? `#${exception.fieldPath}` : undefined}>{exception.message}</a>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex items-center gap-3">
        <Button
          size="sm"
          variant="outline"
          onClick={() => void save()}
          disabled={readOnly || saveState === "saving"}
          data-testid="respiratory-save-button"
        >
          Save draft
        </Button>
        <Button
          size="sm"
          onClick={() => void completeReview()}
          disabled={readOnly || saveState === "saving" || !completion.complete}
          data-testid="respiratory-complete-review-button"
        >
          Complete system review
        </Button>
        <span role="status" data-testid="respiratory-save-status" className="text-xs text-rnica-muted">
          {readOnly ? "This episode is locked — Respiratory is read-only." : SAVE_STATE_MESSAGE[saveState]}
        </span>
        {!readOnly && saveState === "conflict" && (
          <Button variant="outline" size="sm" onClick={() => void reload()}>
            Reload latest
          </Button>
        )}
        {!readOnly && saveState === "error" && (
          <Button variant="outline" size="sm" onClick={() => void save()}>
            Retry
          </Button>
        )}
      </div>
      {saveError && saveState !== "idle" && <p className="text-xs text-rnica-red">{saveError}</p>}
    </div>
  );
}
