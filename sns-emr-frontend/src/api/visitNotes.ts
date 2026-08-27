import axios from "axios";
import api from "./client";

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (detail && typeof detail === "object") {
      const message =
        "message" in detail && typeof detail.message === "string"
          ? detail.message
          : "detail" in detail && typeof detail.detail === "string"
            ? detail.detail
            : "";
      const errors =
        "errors" in detail && Array.isArray(detail.errors)
          ? detail.errors.filter((item: unknown) => typeof item === "string").join(", ")
          : "";
      const combined = [message, errors].filter(Boolean).join(": ");
      if (combined) return combined;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            const msg = item.msg;
            return typeof msg === "string" ? msg : "";
          }
          return "";
        })
        .filter(Boolean)
        .join(", ");
    }
    if (error.message) {
      return `${fallback}: ${error.message}`;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

async function unwrap<T>(promise: Promise<{ data: T }>, fallback: string): Promise<T> {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, fallback));
  }
}

// =========================================================
// RN / LVN "Visit Notes" module -- Add New Visit / My Visit Notes /
// History of Visit Notes. Backed by a generic Visit + primary
// ClinicalNote (JSONB content) on the backend -- see backend/app/api/
// visits.py (create_visit, get_visit_note, update_visit_note,
// list_visit_notes_for_patient). RN ICA / MSW ICA / SC ICA and the CHHA
// visit note are separate, pre-existing modules and are not touched by
// this client.
// =========================================================

/** Every Form Type the "Add New Visit" workflow can submit. Only ASSESS
 * and ROUTINE_VISIT show the full clinical documentation body -- every
 * other value collapses the visit note down to a narrative-only entry,
 * matching the legacy workflow. */
export const VISIT_NOTE_FORM_TYPES = [
  { value: "ASSESS", label: "Assess", fullBody: true },
  { value: "ROUTINE_VISIT", label: "Routine Visit", fullBody: true },
  { value: "SHORT_FORM", label: "Short Form", fullBody: false },
  { value: "PRE_ADMIT_EVAL", label: "Pre-Admit Eval", fullBody: false },
  { value: "AFTER_DEATH", label: "After Death", fullBody: false },
  { value: "ON_CALL_TRIAGE", label: "On Call-Triage", fullBody: false },
  { value: "MISSED_VISIT", label: "Missed Visit", fullBody: false },
  { value: "DECLINED_VISIT", label: "Declined Visit", fullBody: false },
  { value: "AFTER_HOURS", label: "After Hours", fullBody: false },
  { value: "OFFICE_HOURS", label: "Office Hours", fullBody: false },
  { value: "ANCILLARY_SUPPORT", label: "Ancillary Support", fullBody: false },
  { value: "BEREAVEMENT_VISIT", label: "Bereavement Visit", fullBody: false },
  { value: "DEATH_VISIT", label: "Death Visit", fullBody: false },
  { value: "RESPITE_RELIEF", label: "Respite Relief", fullBody: false },
  { value: "SUPV_VISIT_ONLY", label: "Supv Visit Only", fullBody: false },
  { value: "VOLUNTEER_SUPPORT", label: "Volunteer Support", fullBody: false },
  { value: "WEEKENDS", label: "Weekends", fullBody: false },
] as const;

export type VisitNoteFormType = (typeof VISIT_NOTE_FORM_TYPES)[number]["value"];

export function isFullBodyFormType(formType: string | null | undefined): boolean {
  if (!formType) return true;
  const match = VISIT_NOTE_FORM_TYPES.find((f) => f.value === formType);
  return match ? match.fullBody : false;
}

export const VISIT_NOTE_CARE_LEVELS = [
  "Routine Care",
  "General Inpatient",
  "Continuous Care",
  "Respite Care",
] as const;

export type VisitNotePain = {
  controlled?: string | null;
  pain_level?: number | null;
  other_observation?: string | null;
};

export type VisitNoteVitals = {
  temperature?: string | null;
  temperature_position?: string | null;
  pulse?: string | null;
  respirations?: string | null;
  bp_systolic?: string | null;
  bp_diastolic?: string | null;
  bp_position?: string | null;
  height?: string | null;
  weight?: string | null;
  mac?: string | null;
  bmi?: string | null;
  o2_sat?: string | null;
  o2_delivery?: string | null;
  unable_to_assess?: boolean;
};

export type VisitNoteBodySystem = {
  severity?: string | null; // NONE / MILD / MODERATE / SEVERE
  other_symptom?: string | null;
  assessed_no_issues?: boolean;
  other_observation?: string | null;
  selected_findings?: string[] | null;
  oral_intake?: string | null;
  diet?: string | null;
  diet_specify?: string | null;
  incontinent?: string | null;
  last_bm?: string | null;
  ambulatory_status?: string | null;
  assistive_device?: string | null;
  assistance_level?: string | null;
  endurance?: string | null;
  bedbound_status?: string | null;
  adl_scores?: Record<string, number> | null;
  adl_total_score?: number | null;
};

export const VISIT_NOTE_BODY_SYSTEMS = [
  { key: "neuro_mental_sensory", label: "Neuro/Mental/Sensory" },
  { key: "cardiovascular", label: "Cardiovascular" },
  { key: "respiratory", label: "Respiratory" },
  { key: "immunological_infection", label: "Immunological/Infection" },
  { key: "gi_digestive", label: "GI-Digestive" },
  { key: "nutrition", label: "Nutrition" },
  { key: "endocrine", label: "Endocrine" },
  { key: "gu_reproductive", label: "GU-Reproductive" },
  { key: "sleep_rest", label: "Sleep/Rest" },
  { key: "musculoskeletal", label: "MusculoSkeletal" },
  { key: "integumentary_skin", label: "Integumentary-Skin" },
  { key: "mobility", label: "Mobility" },
  { key: "adl_assessment", label: "ADL Assessment" },
  { key: "fall_incidence", label: "Fall/Incidence" },
  { key: "safety_issues", label: "Safety Issues" },
] as const;

export type VisitNoteBodySystemKey = (typeof VISIT_NOTE_BODY_SYSTEMS)[number]["key"];

export type VisitNoteCareProvided = {
  physical_comfort_support?: boolean;
  structural_functional_activity_support?: boolean;
  emotional_support?: boolean;
  spiritual_support?: boolean;
  safety_instructions?: boolean;
  interpersonal_relationship_support?: boolean;
  environmental_needs?: boolean;
  self_determination_preference_needs?: boolean;
  knowledge_related_needs?: boolean;
  language_communication_related_needs?: boolean;
  other_needs?: boolean;
  other_needs_text?: string | null;
};

export type VisitNoteChecklist = {
  updated_family_pcg?: boolean | null;
  updated_cm_md?: boolean | null;
  comfort_pack_med_checked?: boolean | null;
  dme_inspected?: boolean | null;
  foley_cath_checked?: boolean | null;
  foley_cath_last_changed?: string | null;
  gi_tube_checked?: boolean | null;
  next_visit_confirmed?: boolean | null;
};

export type VisitNoteFunctionalDecline = {
  kps?: number | null;
  pps?: number | null;
  fast?: string | null;
  nyha?: string | null;
};

export type VisitNoteSupervisoryAudit = {
  created_at?: string | null;
  created_by_user_id?: string | null;
  updated_at?: string | null;
  updated_by_user_id?: string | null;
  finalized_at?: string | null;
  finalized_by_user_id?: string | null;
};

export type VisitNoteSupervisorySubform = {
  assigned_staff_user_id?: string | null;
  assigned_staff_name?: string | null;
  supervision_type?: string | null;
  observation_datetime?: string | null;
  rn_supervisor_name?: string | null;
  services_meet_patient_needs?: string | null;
  follows_care_plan?: string | null;
  demonstrates_competency?: string | null;
  communication_appropriate?: string | null;
  infection_control_safety?: string | null;
  patient_family_concerns?: string | null;
  concern_details?: string | null;
  corrective_action_required?: string | null;
  corrective_action_details?: string | null;
  notification_documented?: string | null;
  person_notified?: string | null;
  notification_datetime?: string | null;
  follow_up_required?: string | null;
  follow_up_due_date?: string | null;
  supervisor_comments?: string | null;
  ordered_interventions_completed?: string | null;
  documentation_consistent?: string | null;
  audit?: VisitNoteSupervisoryAudit | null;
};

export type VisitNoteSupervisoryReview = {
  hha?: VisitNoteSupervisorySubform | null;
  lvn_lpn?: VisitNoteSupervisorySubform | null;
};

export type VisitNoteComparableEntry = {
  visit_id: string;
  note_id: string;
  discipline: string;
  form_type: string | null;
  visit_datetime: string | null;
  visit_date: string | null;
  content_snapshot: Partial<VisitNoteContent>;
};

export type VisitNoteSupervisoryAssignment = {
  user_id: string;
  name: string;
  discipline: string;
  is_primary: boolean;
  assigned_at: string | null;
};

export type VisitNoteSupervisoryContext = {
  visible: boolean;
  can_edit: boolean;
  derivation_note?: string | null;
  hha: {
    applicable: boolean;
    service_status: string;
    assignments: VisitNoteSupervisoryAssignment[];
    last_completed?: { visit_id: string; visit_date: string | null; finalized_at: string | null; form_type: string | null } | null;
    next_due?: string | null;
    status_label: string;
  };
  lvn_lpn: {
    applicable: boolean;
    service_status: string;
    assignments: VisitNoteSupervisoryAssignment[];
    last_completed?: { visit_id: string; visit_date: string | null; finalized_at: string | null; form_type: string | null } | null;
    next_due?: string | null;
    status_label: string;
  };
};

export type VisitNoteNarcoticDisposalItem = {
  drug_name?: string | null;
  quantity?: string | null;
  disposal_method?: string | null;
};

export type VisitNoteDeathDisposal = {
  hospice_received_call_at?: string | null;
  pronounced_death_at?: string | null;
  pronounced_by?: string | null;
  pronounced_by_name?: string | null;
  evidenced_by?: string[];
  mortuary_notified_at?: string | null;
  mortuary_name?: string | null;
  physician_idg_notified_at?: string | null;
  family_instructed_on_narcotic_disposal?: boolean;
  narcotics?: VisitNoteNarcoticDisposalItem[];
  witnessed_or_stated_by?: string | null;
};

export type VisitNoteContent = {
  correction?: boolean;
  type_of_visit?: string | null;
  visit_kind?: string | null;
  form_type?: string | null;
  care_level?: string | null;
  visit_date?: string | null;
  time_in?: string | null;
  time_out?: string | null;
  duration?: string | null;
  entered_by?: string | null;
  staff_assigned?: string | null;

  pain?: VisitNotePain | null;
  vitals?: VisitNoteVitals | null;
  functional_decline?: VisitNoteFunctionalDecline | null;
  signs_symptoms?: Partial<Record<VisitNoteBodySystemKey, VisitNoteBodySystem>>;
  supervisory_review?: VisitNoteSupervisoryReview | null;
  care_provided?: VisitNoteCareProvided | null;
  visit_checklist?: VisitNoteChecklist | null;

  death_disposal_notes?: string | null;
  death_disposal?: VisitNoteDeathDisposal | null;
  narrative?: string | null;
};

export type VisitNoteRecord = {
  visit_id: string;
  patient_id: string;
  note_id: string;
  discipline: string;
  form_type: string | null;
  status: string | null;
  visit_status: string | null;
  finalized_at: string | null;
  finalized_by: string | null;
  visit_datetime: string | null;
  created_at: string;
  updated_at: string;
  content: VisitNoteContent;
  comparable_history?: VisitNoteComparableEntry[];
  supervisory_context?: VisitNoteSupervisoryContext;
  permissions?: {
    can_edit_supervisory_review?: boolean;
  };
};

export type VisitNoteTimelineEntry = {
  source: "VISIT_NOTE" | "MSW_ICA" | "SC_ICA";
  id: string;
  visit_id: string | null;
  patient_id: string;
  discipline: string;
  form_type: string | null;
  care_level: string | null;
  visit_date: string | null;
  status: string | null;
  narrative_preview: string | null;
  created_at: string;
};

export type CreateVisitNotePayload = {
  patient_id: string;
  visit_type: "RN" | "LVN" | "SC" | "MSW" | "CHHA";
  service_type?: string;
  form_type?: string | null;
  level_of_care?: string | null;
  visit_schedule_type?: string | null;
  event_type?: string | null;
  clinical_note?: Record<string, unknown> | null;
  /** Staff member this visit is being created for/by — populated by the staff+date picker every "Create Visit" flow now goes through. Defaults server-side to the creating user when omitted. */
  assigned_staff_id?: string | null;
  /** Scheduled/actual visit date-time chosen in the staff+date picker. Defaults server-side to now() when omitted. */
  visit_datetime?: string | null;
};

export type CreateVisitNoteResponse = {
  visit_id: string;
  visit_type: string;
  form_type: string | null;
  form_family: string | null;
  primary_form: string | null;
  attached_forms: string[];
  modules: string[];
  resolved_by: string | null;
  is_supervisory: boolean;
  supervisory_targets: string[];
  request_id: string;
};

/** Creates a new RN/LVN visit (and its backing primary ClinicalNote). */
export async function createVisitNote(
  payload: CreateVisitNotePayload
): Promise<CreateVisitNoteResponse> {
  return unwrap(api.post("/visits/", payload), "Unable to create this visit note");
}

export type AssignableStaffMember = {
  user_id: string;
  name: string;
  discipline: string;
  is_primary: boolean;
  assigned_at: string | null;
};

export type CreateVisitDiscipline = "RN" | "LVN" | "SC" | "MSW" | "CHHA";

/**
 * Lists the staff assigned to this patient for the given discipline, so the
 * "Create Visit" staff+date picker (used by every discipline) can offer a
 * real dropdown instead of always silently defaulting to whoever clicked
 * the button.
 */
export async function listAssignableStaff(
  patientId: string,
  discipline: CreateVisitDiscipline
): Promise<AssignableStaffMember[]> {
  const response = await unwrap<{ discipline: string; staff: AssignableStaffMember[] }>(
    api.get(`/visits/patient/${patientId}/assignable-staff`, { params: { discipline } }),
    "Unable to load assignable staff for this patient"
  );
  return response.staff || [];
}

export type VisitEditHistoryEntry = {
  action: string;
  user_id: string | null;
  user_name: string;
  created_at: string;
};

/** Read-only edit/audit trail for a single visit — who edited it, what action, and when. */
export async function getVisitEditHistory(visitId: string): Promise<VisitEditHistoryEntry[]> {
  return unwrap(api.get(`/visits/${visitId}/edit-history`), "Unable to load this visit's edit history");
}

/** Loads the Visit Details + full clinical content for an existing RN/LVN visit note. */
export async function getVisitNote(visitId: string): Promise<VisitNoteRecord> {
  return unwrap(api.get(`/visits/${visitId}/visit-note`), "Unable to load this visit note");
}

/** Saves the Visit Details + clinical content for an existing RN/LVN visit note. */
export async function updateVisitNote(
  visitId: string,
  content: VisitNoteContent
): Promise<VisitNoteRecord> {
  return unwrap(api.put(`/visits/${visitId}/visit-note`, content), "Unable to save this visit note");
}

/** Signs and locks a visit note (reuses the generic visit finalize endpoint). */
export async function finalizeVisitNote(visitId: string): Promise<unknown> {
  return unwrap(api.post(`/visits/${visitId}/finalize`, {}), "Unable to sign and submit this visit note");
}

/** Combined RN/LVN + MSW ICA + SC ICA timeline for a patient's Visit Notes board. */
export async function listVisitNotesForPatient(patientId: string): Promise<VisitNoteTimelineEntry[]> {
  return unwrap(
    api.get(`/visits/patient/${patientId}/visit-notes`),
    "Unable to load this patient's visit notes"
  );
}
