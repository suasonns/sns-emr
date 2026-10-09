/**
 * SNS Body Systems Workspace — Respiratory persistence field mapping.
 *
 * The single authoritative classification of every field the Respiratory
 * panel (`RespiratorySystemPanel.tsx`) can produce against the backend
 * persistence contract (`backend/app/api/routes/body_systems.py`,
 * `backend/app/models/body_systems.py`). Built so a reviewer can answer
 * "where does this field go, exactly?" for every field without re-deriving
 * it from the route/model source each time, and so any field with no
 * backend destination is a visible, named entry here rather than a silent
 * drop on save.
 *
 * Categories:
 * - DIRECT_BACKEND_MAPPING: round-trips through save/load unchanged.
 * - TRANSFORMED_MAPPING: persisted, but via a defined, reversible transform
 *   (type or shape change), not a 1:1 column.
 * - DISPLAY_ONLY: computed/derived for the UI only; never sent to the API.
 * - HISTORICAL_REFERENCE_ONLY: read from a prior assessment for comparison
 *   display; never written back by this panel.
 * - BACKEND_DESTINATION_MISSING: a real domain field with no backend column
 *   or API field yet. Not silently dropped -- named here, and the save
 *   payload simply does not include it (see RespiratoryPersistenceHook,
 *   once it exists, for the runtime omission point).
 * - LEGACY_FIELD_NOT_USED_BY_WORKSPACE: existed on the old, non-Workspace
 *   `RespiratoryAssessmentValues`/`respiratoryOverview` shape
 *   (`features/body-systems/components/`) but has no equivalent in this
 *   panel's `RespiratoryFieldValues` and is not part of this mapping.
 */

export type RespiratoryFieldMappingCategory =
  | "DIRECT_BACKEND_MAPPING"
  | "TRANSFORMED_MAPPING"
  | "DISPLAY_ONLY"
  | "HISTORICAL_REFERENCE_ONLY"
  | "BACKEND_DESTINATION_MISSING"
  | "LEGACY_FIELD_NOT_USED_BY_WORKSPACE"
  | "UNRESOLVED";

export interface RespiratoryFieldMappingEntry {
  /** Field path on the frontend domain/panel side. */
  field: string;
  category: RespiratoryFieldMappingCategory;
  /** Exact backend destination, or null when there isn't one. */
  backendDestination: string | null;
  note: string;
}

export const RESPIRATORY_PERSISTENCE_MAPPING: readonly RespiratoryFieldMappingEntry[] = [
  // -- Situation / review state --------------------------------------------
  {
    field: "situation",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.situation",
    note: "String enum column; round-trips unchanged.",
  },
  {
    field: "reviewState",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.review_state",
    note: "String enum column; round-trips unchanged.",
  },
  {
    field: "reviewExceptions",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "ReviewException rows (relational)",
    note: "Open exceptions are created/left alone; resolved ones are never clobbered by a later save (see test_resolved_exceptions_are_not_clobbered_by_a_later_save).",
  },
  {
    field: "summary",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.summary",
    note: "Free-text column; round-trips unchanged.",
  },
  {
    field: "version / expectedVersion",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.version",
    note: "Optimistic-concurrency counter; stale expectedVersion is rejected with HTTP 409, not silently overwritten.",
  },

  // -- RespiratoryFieldValues (clinical symptom fields) --------------------
  // All fourteen fields below are stored as an opaque, whole-object JSONB
  // blob (SystemAssessment.data), the same convention already used by
  // RnicaAssessment.form_data -- no per-field backend column exists or is
  // needed; the object is written and read back byte-for-byte.
  { field: "values.sobSeverity", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.sobSeverity", note: "Opaque JSONB passthrough." },
  { field: "values.screeningDateTime", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.screeningDateTime", note: "Opaque JSONB passthrough." },
  { field: "values.priorComparison", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.priorComparison", note: "Opaque JSONB passthrough." },
  { field: "values.onsetOrSource", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.onsetOrSource", note: "Opaque JSONB passthrough." },
  { field: "values.lungSounds", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.lungSounds", note: "Opaque JSONB passthrough." },
  { field: "values.respiratoryPattern", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.respiratoryPattern", note: "Opaque JSONB passthrough." },
  { field: "values.oxygenDelivery", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.oxygenDelivery", note: "Opaque JSONB passthrough." },
  { field: "values.flowRateLpm", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.flowRateLpm", note: "Opaque JSONB passthrough; only rendered when oxygenDelivery is nasal_cannula/mask." },
  { field: "values.ventilatorInfo", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.ventilatorInfo", note: "Opaque JSONB passthrough; only rendered when oxygenDelivery is ventilator." },
  { field: "values.spo2Value", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.spo2Value", note: "Opaque JSONB passthrough." },
  { field: "values.spo2Context", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.spo2Context", note: "Opaque JSONB passthrough." },
  { field: "values.exertionTolerance", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.exertionTolerance", note: "Opaque JSONB passthrough." },
  { field: "values.hopeComfortImpact", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.hopeComfortImpact", note: "Opaque JSONB passthrough. Never derived from sobSeverity by construction -- see panel docstring." },
  { field: "values.hopeFunctionImpact", category: "DIRECT_BACKEND_MAPPING", backendDestination: "SystemAssessment.data.hopeFunctionImpact", note: "Opaque JSONB passthrough. Never derived from sobSeverity by construction -- see panel docstring." },

  // -- AssessmentLimitation (Unable-to-Assess) -----------------------------
  {
    field: "limitation.scope",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.limitation_scope (JSONB)",
    note: "string[] round-trips unchanged.",
  },
  {
    field: "limitation.reason",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.limitation_reason (Text)",
    note: "Round-trips unchanged.",
  },
  {
    field: "limitation.assessedPortion",
    category: "DIRECT_BACKEND_MAPPING",
    backendDestination: "SystemAssessment.limitation_assessed_portion (Text)",
    note: "Round-trips unchanged.",
  },
  {
    field: "limitation.followUpRequired",
    category: "TRANSFORMED_MAPPING",
    backendDestination: "SystemAssessment.limitation_follow_up_required (Text)",
    note:
      'Frontend type is boolean; backend column is Text (not Boolean). Stored/read back as the literal string "true"/"false" ' +
      "(see _text_to_bool in body_systems.py) -- a reversible, non-combining transform, not data loss.",
  },
  {
    field: "limitation.responsibleClinicianId",
    category: "BACKEND_DESTINATION_MISSING",
    backendDestination: null,
    note:
      "No column on SystemAssessment and no field on SaveRespiratoryDraftRequest. Captured in the panel's Unable-to-Assess " +
      "form (local component state) but NOT included in the save payload -- it is not persisted and is lost on reload. " +
      "Reported, not silently invented a column/migration for.",
  },
  {
    field: "limitation.timingOrContingency",
    category: "BACKEND_DESTINATION_MISSING",
    backendDestination: null,
    note:
      "No column on SystemAssessment and no field on SaveRespiratoryDraftRequest. Captured in the panel's Unable-to-Assess " +
      "form (local component state) but NOT included in the save payload -- it is not persisted and is lost on reload. " +
      "Reported, not silently invented a column/migration for.",
  },
] as const;

/** Convenience lookup for callers (e.g. tests) that need one entry by field name. */
export function findRespiratoryMappingEntry(field: string): RespiratoryFieldMappingEntry | undefined {
  return RESPIRATORY_PERSISTENCE_MAPPING.find((entry) => entry.field === field);
}
