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
import { type ReactNode } from "react";
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
  RESPIRATORY_FIELD_INVENTORY,
  type RespiratoryFieldDefinition,
} from "../../../domain/body-systems/respiratoryFieldInventory";
import { useRespiratoryAssessment, type RespiratoryDraft } from "./useRespiratoryAssessment";
import type { AssessmentSituation } from "../../../domain/body-systems";

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

const INTERVENTION_FIELD_IDS = new Set(["respiratory_treatment_initiated", "respiratory_treatment_declined"]);
const HANDLED_SEPARATELY_FIELD_IDS = new Set([
  RESPIRATORY_NO_CURRENT_CONCERN_FIELD.fieldId,
  RESPIRATORY_UNABLE_TO_ASSESS_FIELD.fieldId,
  RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD.fieldId,
  RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD.fieldId,
  RESPIRATORY_NOTES_FIELD.fieldId,
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

function FieldLabel({ children, htmlFor }: { children: ReactNode; htmlFor: string }) {
  return (
    <label htmlFor={htmlFor} className="text-xs font-medium text-rnica-textStrong">
      {children}
    </label>
  );
}

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
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <Select value={typeof value === "string" ? value : ""} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id={field.fieldId} aria-label={field.label}>
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
    <fieldset className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <legend className="text-xs font-medium text-rnica-textStrong">{field.label}</legend>
      <div className="flex flex-wrap gap-3">
        {field.controlledValues?.map((option) => {
          const checked = selected.includes(option);
          const optionId = `${field.fieldId}-${option}`;
          return (
            <label key={option} htmlFor={optionId} className="flex items-center gap-1.5 text-xs text-rnica-text">
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
        className="h-9 w-full rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50"
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
        type="text"
        disabled={disabled}
        className="h-9 w-full rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing disabled:cursor-not-allowed disabled:opacity-50"
        value={typeof value === "string" ? value : ""}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
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
  const onChange = (next: unknown) => updateDraft(setFieldValue(draft, field, next) as Partial<RespiratoryDraft>);

  switch (field.responseType) {
    case "single_select":
      return <SingleSelectField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "multi_select":
      return <MultiSelectField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "boolean":
      return <BooleanField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "number":
      return <NumberField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    case "text":
      return <TextField field={field} value={value} onChange={(v) => onChange(v)} disabled={disabled} />;
    default:
      return null;
  }
}

const OXYGEN_DETAIL_FIELD_IDS = new Set([
  "respiratory_oxygen_delivery_type",
  "respiratory_oxygen_liters_per_minute",
  "respiratory_oxygen_sat_on_o2",
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
  if (field.fieldId === "respiratory_sputum_character") {
    return draft.coughType === "Productive";
  }
  if (field.fieldId === "respiratory_exertion_level") {
    // Dyspnea context: only relevant once some level of shortness of
    // breath has actually been documented (Contract v2: never inferred).
    return Boolean(draft.sobSeverity) && draft.sobSeverity !== "None";
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
      draft.ventilator?.shortTermVentilator === true ||
      draft.ventilator?.longTermVentilator === true,
  );
}

function describeDyspneaBurden(draft: RespiratoryDraft): string {
  if (!draft.sobSeverity) return "Not yet documented";
  if (draft.sobSeverity === "None") return "None reported";
  return `${draft.sobSeverity}${draft.exertionLevel ? ` (${draft.exertionLevel})` : ""}`;
}

function describeLungFindings(draft: RespiratoryDraft): string {
  const sounds = draft.lungSounds ?? [];
  if (sounds.length === 0) return "Not yet documented";
  if (sounds.length === 1 && sounds[0] === "Clear") return "Clear";
  return sounds.join(", ");
}

function describeCough(draft: RespiratoryDraft): string {
  if (!draft.coughType) return "Not yet documented";
  if (draft.coughType === "None") return "None";
  if (draft.coughType === "Productive" && draft.sputumCharacter) {
    return `Productive — ${draft.sputumCharacter}`;
  }
  return draft.coughType;
}

function describeOxygenStatus(draft: RespiratoryDraft): string {
  if (draft.oxygenTherapy?.inUse !== true) {
    return draft.oxygenTherapy?.onRoomAir === true ? "Room air" : "Not yet documented";
  }
  const parts = [draft.oxygenTherapy.type, draft.oxygenTherapy.litersPerMinute != null ? `${draft.oxygenTherapy.litersPerMinute} L/min` : null].filter(
    Boolean,
  );
  return parts.length > 0 ? parts.join(" ") : "In use";
}

function describeRespiratorySupport(draft: RespiratoryDraft): string {
  if (draft.ventilator?.longTermVentilator) return "Long-term ventilator";
  if (draft.ventilator?.shortTermVentilator) return "Short-term ventilator";
  return "None";
}

function describeIntervention(draft: RespiratoryDraft): string {
  if (draft.treatmentInitiated) return "Treatment initiated";
  if (draft.treatmentDeclined) return "Treatment declined";
  return "None documented";
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 text-xs">
      <span className="text-rnica-muted">{label}</span>
      <span className="font-medium text-rnica-textStrong">{value}</span>
    </div>
  );
}

function RespiratorySummary({
  draft,
  situation,
  reviewComplete,
}: {
  draft: RespiratoryDraft;
  situation: AssessmentSituation | null;
  reviewComplete: boolean;
}) {
  const reviewStateLabel = reviewComplete
    ? "Reviewed"
    : situation
      ? "In progress"
      : "Review not yet started";
  return (
    <section
      className="flex flex-col gap-1.5 rounded-lg border border-rnica-border bg-rnica-bg p-3"
      aria-label="Respiratory summary"
      data-testid="respiratory-summary-section"
    >
      <h3 className="text-xs font-semibold uppercase text-rnica-muted">Summary</h3>
      <SummaryRow label="Review state" value={reviewStateLabel} />
      <SummaryRow label="Dyspnea" value={describeDyspneaBurden(draft)} />
      <SummaryRow label="Lung findings" value={describeLungFindings(draft)} />
      <SummaryRow label="Cough / secretions" value={describeCough(draft)} />
      <SummaryRow label="Oxygen" value={describeOxygenStatus(draft)} />
      <SummaryRow label="Respiratory support" value={describeRespiratorySupport(draft)} />
      <SummaryRow label="Intervention" value={describeIntervention(draft)} />
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
    situation,
    completion,
    updateDraft,
    saveState,
    saveError,
    save,
    completeReview,
    reload,
  } = useRespiratoryAssessment(assessmentId);

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
    (field) => !HANDLED_SEPARATELY_FIELD_IDS.has(field.fieldId) && !INTERVENTION_FIELD_IDS.has(field.fieldId),
  );
  const interventionFields = RESPIRATORY_FIELD_INVENTORY.filter((field) => INTERVENTION_FIELD_IDS.has(field.fieldId));

  return (
    <div data-testid="respiratory-panel" className="flex flex-col gap-4 p-3">
      <RespiratorySummary draft={draft} situation={situation} reviewComplete={completion.complete} />
      {/*
        Contract v2: every current-evidence field is always rendered,
        always editable, and never gated behind an upfront selector. The
        "no current concern" and "unable to assess" controls below are
        explicit, independent, non-gating declarations — not a radio/select
        that must be answered first.
      */}
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

      {isUnableToAssess && (
        <section className="flex flex-col gap-3" data-testid="respiratory-limitation-section" aria-label="Assessment limitation">
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

      <section className="flex flex-col gap-3" aria-label="Current evidence" data-testid="respiratory-current-evidence-section">
        <h3 className="text-xs font-semibold uppercase text-rnica-muted">Current evidence</h3>
        {detailFields
          .filter((field) => isFieldCurrentlyRelevant(field, draft))
          .map((field) => (
            <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
          ))}
      </section>

      <section className="flex flex-col gap-3" aria-label="Interventions" data-testid="respiratory-intervention-section">
        <h3 className="text-xs font-semibold uppercase text-rnica-muted">Interventions</h3>
        {isDyspneaModerateOrSevere(draft) || hasDocumentedIntervention(draft) ? (
          interventionFields.map((field) => (
            <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} disabled={readOnly} />
          ))
        ) : (
          <p className="text-xs text-rnica-muted">No intervention required unless dyspnea is moderate or severe.</p>
        )}
      </section>

      <section className="flex flex-col gap-2" aria-label="Follow-up" data-testid="respiratory-follow-up-section">
        <h3 className="text-xs font-semibold uppercase text-rnica-muted">Follow-up</h3>
        <p className="text-xs text-rnica-muted">No follow-up field available yet; tracked below as informational.</p>
      </section>

      <div className="flex flex-col gap-1">
        <FieldLabel htmlFor={RESPIRATORY_NOTES_FIELD.fieldId}>{RESPIRATORY_NOTES_FIELD.label}</FieldLabel>
        <Textarea
          id={RESPIRATORY_NOTES_FIELD.fieldId}
          value={draft.notes ?? ""}
          onChange={(event) => updateDraft({ notes: event.target.value })}
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

      {!completion.complete && (
        <section
          className="flex flex-col gap-1 rounded-lg border border-rnica-border bg-rnica-bg p-2"
          aria-label="Remaining to complete review"
          data-testid="respiratory-completion-blockers"
        >
          <h3 className="text-xs font-semibold uppercase text-rnica-muted">Remaining to complete review</h3>
          <ul className="flex flex-col gap-1">
            {completion.blockingMessages.map((message) => (
              <li key={message} className="text-xs text-rnica-text">
                {message}
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
