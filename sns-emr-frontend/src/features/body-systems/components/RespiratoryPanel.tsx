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
import { Fragment, type ReactNode } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../components/ui/select";
import { Checkbox } from "../../../components/ui/checkbox";
import { Textarea } from "../../../components/ui/textarea";
import { Button } from "../../../components/ui/button";
import { Alert, AlertDescription } from "../../../components/ui/alert";
import {
  RESPIRATORY_OVERVIEW_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD,
  RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD,
  RESPIRATORY_NOTES_FIELD,
  RESPIRATORY_FIELD_INVENTORY,
  type RespiratoryFieldDefinition,
} from "../../../domain/body-systems/respiratoryFieldInventory";
import { useRespiratoryAssessment, type RespiratoryDraft } from "./useRespiratoryAssessment";

export interface RespiratoryPanelProps {
  patientId: string;
}

const INTERVENTION_FIELD_IDS = new Set(["respiratory_treatment_initiated", "respiratory_treatment_declined"]);
const HANDLED_SEPARATELY_FIELD_IDS = new Set([
  RESPIRATORY_OVERVIEW_FIELD.fieldId,
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
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <Select value={typeof value === "string" ? value : ""} onValueChange={onChange}>
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
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string[]) => void;
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
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: boolean) => void;
}) {
  return (
    <label htmlFor={field.fieldId} className="flex items-center gap-1.5 text-xs text-rnica-text" data-testid={`respiratory-field-${field.fieldId}`}>
      <Checkbox id={field.fieldId} checked={value === true} onCheckedChange={(next) => onChange(next === true)} />
      {field.label}
    </label>
  );
}

function NumberField({
  field,
  value,
  onChange,
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: number | undefined) => void;
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
        className="h-9 w-full rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing"
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
}: {
  field: RespiratoryFieldDefinition;
  value: unknown;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1" data-testid={`respiratory-field-${field.fieldId}`}>
      <FieldLabel htmlFor={field.fieldId}>{field.label}</FieldLabel>
      <input
        id={field.fieldId}
        type="text"
        className="h-9 w-full rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2 text-[11px] text-rnica-text focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-rnica-focusRing"
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
}: {
  field: RespiratoryFieldDefinition;
  draft: RespiratoryDraft;
  updateDraft: (patch: Partial<RespiratoryDraft>) => void;
}) {
  const value = getFieldValue(draft, field);
  const onChange = (next: unknown) => updateDraft(setFieldValue(draft, field, next) as Partial<RespiratoryDraft>);

  switch (field.responseType) {
    case "single_select":
      return <SingleSelectField field={field} value={value} onChange={(v) => onChange(v)} />;
    case "multi_select":
      return <MultiSelectField field={field} value={value} onChange={(v) => onChange(v)} />;
    case "boolean":
      return <BooleanField field={field} value={value} onChange={(v) => onChange(v)} />;
    case "number":
      return <NumberField field={field} value={value} onChange={(v) => onChange(v)} />;
    case "text":
      return <TextField field={field} value={value} onChange={(v) => onChange(v)} />;
    default:
      return null;
  }
}

const SAVE_STATE_MESSAGE: Record<string, string> = {
  idle: "",
  saving: "Saving Respiratory draft…",
  saved: "Respiratory draft saved.",
  error: "Save failed.",
  conflict: "Save blocked — this assessment changed elsewhere.",
};

export function RespiratoryPanel({ patientId }: RespiratoryPanelProps) {
  const { loadState, assessment, draft, situation, updateDraft, saveState, saveError, save, reload } =
    useRespiratoryAssessment(patientId);

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

  const isUnableToAssess = situation === "unable_to_assess";
  const unableToAssessReasonValue = getFieldValue(draft, RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD);
  const detailFields = RESPIRATORY_FIELD_INVENTORY.filter(
    (field) => !HANDLED_SEPARATELY_FIELD_IDS.has(field.fieldId) && !INTERVENTION_FIELD_IDS.has(field.fieldId),
  );
  const interventionFields = RESPIRATORY_FIELD_INVENTORY.filter((field) => INTERVENTION_FIELD_IDS.has(field.fieldId));

  return (
    <div data-testid="respiratory-panel" className="flex flex-col gap-4 p-3">
      <SingleSelectField
        field={RESPIRATORY_OVERVIEW_FIELD}
        value={draft.respiratoryOverview}
        onChange={(value) => updateDraft({ respiratoryOverview: value })}
      />

      {isUnableToAssess ? (
        <section className="flex flex-col gap-3" data-testid="respiratory-limitation-section" aria-label="Limitations">
          <h3 className="text-xs font-semibold uppercase text-rnica-muted">Limitations</h3>
          <SingleSelectField
            field={RESPIRATORY_UNABLE_TO_ASSESS_REASON_FIELD}
            value={unableToAssessReasonValue}
            onChange={(value) => updateDraft({ respiratoryUnableToAssessReason: value })}
          />
          {unableToAssessReasonValue === "Other" && (
            <TextField
              field={RESPIRATORY_UNABLE_TO_ASSESS_OTHER_FIELD}
              value={draft.respiratoryUnableToAssessOther}
              onChange={(value) => updateDraft({ respiratoryUnableToAssessOther: value })}
            />
          )}
        </section>
      ) : (
        <Fragment>
          <section className="flex flex-col gap-3" aria-label="Current evidence" data-testid="respiratory-current-evidence-section">
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Current evidence</h3>
            {detailFields.map((field) => (
              <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} />
            ))}
          </section>

          <section className="flex flex-col gap-3" aria-label="Interventions" data-testid="respiratory-intervention-section">
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Interventions</h3>
            {interventionFields.map((field) => (
              <GenericField key={field.fieldId} field={field} draft={draft} updateDraft={updateDraft} />
            ))}
          </section>

          <section className="flex flex-col gap-2" aria-label="Follow-up" data-testid="respiratory-follow-up-section">
            <h3 className="text-xs font-semibold uppercase text-rnica-muted">Follow-up</h3>
            <p className="text-xs text-rnica-muted">
              No repository-approved follow-up responsibility/timing field exists yet for Respiratory; this is tracked
              as an informational review exception below rather than a blocking requirement.
            </p>
          </section>
        </Fragment>
      )}

      <div className="flex flex-col gap-1">
        <FieldLabel htmlFor={RESPIRATORY_NOTES_FIELD.fieldId}>{RESPIRATORY_NOTES_FIELD.label}</FieldLabel>
        <Textarea
          id={RESPIRATORY_NOTES_FIELD.fieldId}
          value={draft.notes ?? ""}
          onChange={(event) => updateDraft({ notes: event.target.value })}
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
          onClick={() => void save()}
          disabled={saveState === "saving" || !situation}
          data-testid="respiratory-save-button"
        >
          Save draft
        </Button>
        <span role="status" data-testid="respiratory-save-status" className="text-xs text-rnica-muted">
          {SAVE_STATE_MESSAGE[saveState]}
        </span>
        {saveState === "conflict" && (
          <Button variant="outline" size="sm" onClick={() => void reload()}>
            Reload latest
          </Button>
        )}
        {saveState === "error" && (
          <Button variant="outline" size="sm" onClick={() => void save()}>
            Retry
          </Button>
        )}
      </div>
      {saveError && saveState !== "idle" && <p className="text-xs text-rnica-red">{saveError}</p>}
    </div>
  );
}
