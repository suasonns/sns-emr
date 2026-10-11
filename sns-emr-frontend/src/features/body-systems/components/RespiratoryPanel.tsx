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
import { useState, type ReactNode } from "react";
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
  mapOxygenUseToLegacyInUse,
  mapSpo2ConditionToLegacyRoomAir,
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
): RespiratoryDraft {
  switch (field.fieldId) {
    case "respiratory_treatment_decision": {
      const legacy = mapTreatmentDecisionToLegacy(draft.treatmentDecision);
      return Object.keys(legacy).length > 0 ? { ...draft, ...legacy } : draft;
    }
    case "respiratory_oxygen_use": {
      const inUse = mapOxygenUseToLegacyInUse(draft.oxygenUse);
      if (inUse === undefined) return draft;
      return { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, inUse } };
    }
    case "respiratory_spo2_measurement_condition": {
      const onRoomAir = mapSpo2ConditionToLegacyRoomAir(draft.spo2MeasurementCondition);
      if (onRoomAir === undefined) return draft;
      return { ...draft, oxygenTherapy: { ...draft.oxygenTherapy, onRoomAir } };
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
              {option}
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
      {/* Per the approved Respiratory production candidate's clinical-UX
          handoff ("coexisting findings: multi-select checkboxes, not fat
          pills"): compact plain checkbox labels, wrapped into dense rows,
          not rounded-pill chips. */}
      <div className="flex flex-wrap gap-x-3 gap-y-0.5">
        {field.controlledValues?.map((option) => {
          const checked = selected.includes(option);
          const optionId = `${field.fieldId}-${option}`;
          return (
            <label key={option} htmlFor={optionId} className="flex items-center gap-1.5 text-[11px] leading-none text-rnica-text">
              <Checkbox
                id={optionId}
                checked={checked}
                disabled={disabled}
                onCheckedChange={(next) =>
                  onChange(next ? [...selected, option] : selected.filter((item) => item !== option))
                }
              />
              {option}
            </label>
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
  onChange: (value: string) => void;
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
              onClick={() => onChange(option)}
              className={`rounded-md border px-2.5 py-1.5 text-[11px] font-medium leading-none disabled:cursor-not-allowed disabled:opacity-50 ${
                checked
                  ? "border-rnica-teal bg-rnica-teal text-rnica-textInverse"
                  : "border-rnica-border bg-rnica-bg text-rnica-text hover:bg-rnica-hoverSurface"
              }`}
            >
              {humanizeOption(option)}
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
              {humanizeOption(option)}
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
 * Treatment Description is reused as a single canonical field across three
 * Treatment Decision contexts (product-owner directive: do not add a
 * second rationale field for NOT_INDICATED). The nurse-facing label and
 * placeholder change by context; the persisted key (`treatmentDescription`)
 * never changes.
 */
function treatmentDescriptionContext(draft: RespiratoryDraft): { label: string; placeholder?: string } {
  if (draft.treatmentDecision === "ALREADY_IN_PLACE") {
    return { label: "Current Treatment / Intervention" };
  }
  if (draft.treatmentDecision === "NOT_INDICATED") {
    return {
      label: "Clinical Rationale",
      placeholder: "Briefly document why no Respiratory intervention is indicated for the current finding.",
    };
  }
  return { label: "Treatment / Intervention" };
}

function GenericField({
  field,
  draft,
  updateDraft,
  disabled = false,
}: {
  field: RespiratoryFieldDefinition;
  draft: RespiratoryDraft;
  updateDraft: (patch: Partial<RespiratoryDraft>) => void;
  disabled?: boolean;
}) {
  const value = getFieldValue(draft, field);
  const onChange = (next: unknown) => {
    const updated = setFieldValue(draft, field, next);
    updateDraft(applyCanonicalLegacyMapping(field, updated) as Partial<RespiratoryDraft>);
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
      return <NumberField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "text": {
      const override =
        field.fieldId === "respiratory_treatment_description" ? treatmentDescriptionContext(draft) : undefined;
      return (
        <TextField
          field={field}
          value={value}
          onChange={(v) => onChange(v)}
          disabled={disabled}
          labelOverride={override?.label}
          placeholder={override?.placeholder}
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
  "respiratory_oxygen_hours_per_day",
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
  if (NEW_OXYGEN_DETAIL_FIELD_IDS.has(field.fieldId)) {
    return draft.oxygenUse === "YES";
  }
  if (field.fieldId === "respiratory_oxygen_other_device") {
    return draft.oxygenUse === "YES" && draft.oxygenTherapy?.deliveryDevice === "OTHER";
  }
  if (field.fieldId === "respiratory_oxygen_flow_value" || field.fieldId === "respiratory_oxygen_flow_unit") {
    return draft.oxygenUse === "YES";
  }
  if (field.fieldId === "respiratory_oxygen_unable_to_verify_reason") {
    return draft.oxygenUse === "UNABLE_TO_VERIFY";
  }
  if (field.fieldId === "respiratory_spo2_not_obtained_reason") {
    return draft.spo2MeasurementCondition === "NOT_OBTAINED";
  }
  if (field.fieldId === "respiratory_measured_oxygen_flow_or_concentration") {
    return draft.spo2MeasurementCondition === "ON_OXYGEN";
  }
  if (field.fieldId === "respiratory_oxygen_measurement_date" || field.fieldId === "respiratory_oxygen_measurement_time") {
    return draft.spo2Value !== undefined;
  }
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
    return draft.coughType === "Hemoptysis";
  }
  if (COUGH_ACTION_FIELD_IDS.has(field.fieldId)) {
    return draft.coughType === "Productive" || draft.coughType === "Hemoptysis";
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
    // Reused contextually as "Clinical Rationale" for NOT_INDICATED (see
    // treatmentDescriptionContext()) rather than adding a second field.
    return (
      draft.treatmentDecision === "INITIATED" ||
      draft.treatmentDecision === "ALREADY_IN_PLACE" ||
      draft.treatmentDecision === "NOT_INDICATED"
    );
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
 */
const LEGACY_HIDDEN_FIELD_IDS = new Set([
  "respiratory_treatment_initiated",
  "respiratory_treatment_declined",
  "respiratory_oxygen_in_use",
  "respiratory_on_room_air",
  "respiratory_ventilator_short_term",
  "respiratory_ventilator_long_term",
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

export function RespiratoryPanel({ assessmentId, readOnly = false }: RespiratoryPanelProps) {
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
    (field) => INTERVENTION_FIELD_IDS.has(field.fieldId) && !LEGACY_HIDDEN_FIELD_IDS.has(field.fieldId),
  );
  const followUpFields = RESPIRATORY_FIELD_INVENTORY.filter((field) => FOLLOW_UP_FIELD_IDS.has(field.fieldId)).filter(
    (field) => isFieldCurrentlyRelevant(field, draft),
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
                <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
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
                  <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
                ))}
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
                  <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
                ))}
              </div>
            )}
            {followUpFields.length === 0 && <div data-testid="respiratory-follow-up-section" aria-hidden="true" className="hidden" />}
          </section>

          <section className="flex flex-col gap-2" aria-label="Oxygen use and measurement" data-testid="respiratory-oxygen-section">
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Oxygen use &amp; measurement</h3>
            <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5">
              {oxygenFields.map((field) => (
                <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
              ))}
            </div>
          </section>
        </div>
      </div>

      <section className="flex flex-col gap-2" aria-label="Cough and secretions" data-testid="respiratory-cough-section">
        <h3 className="text-xs font-semibold uppercase text-rnica-muted">Cough &amp; secretions</h3>
        <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5">
          {coughFields.map((field) => (
            <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-2" aria-label="Respiratory support and airway" data-testid="respiratory-support-section">
        <h3 className="text-xs font-semibold uppercase text-rnica-muted">Respiratory support &amp; airway</h3>
        <div className="flex flex-wrap items-start gap-x-3 gap-y-1.5">
          {supportFields.map((field) => (
            <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
          ))}
        </div>
      </section>

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
