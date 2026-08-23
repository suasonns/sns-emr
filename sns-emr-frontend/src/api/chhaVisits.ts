import axios from "axios";
import api from "./client";

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
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

export type AideVisitSummary = {
  visit_id: string;
  visit_datetime: string | null;
  status: string;
  has_outcome: boolean;
  rn_notification_required: boolean;
};

export type CHHATaskResult = {
  section_code: string;
  task_code: string;
  was_assigned: boolean;
  completed: boolean;
  refused: boolean;
  not_done: boolean;
  observation_code: string | null;
  result_note: string | null;
};

export type CHHAVisitOutcome = {
  outcome_id: string;
  visit_id: string;
  poc_reference_id: string | null;
  tolerance_to_care: string;
  condition_during_visit: string;
  skin_outcome: string;
  pain_or_change_observed: boolean;
  rn_notification_required: boolean;
  rn_notified: boolean;
  rn_notified_at: string | null;
  rn_notified_name: string | null;
  caregiver_instruction_provided: boolean;
  caregiver_understanding_confirmed: boolean;
  exception_narrative: string | null;
  updated_at: string;
  task_results: CHHATaskResult[];
};

export type CHHAOutcomeUpsertPayload = {
  poc_reference_id?: string | null;
  tolerance_to_care: string;
  condition_during_visit: string;
  skin_outcome: string;
  pain_or_change_observed: boolean;
  rn_notification_required: boolean;
  rn_notified: boolean;
  rn_notified_name?: string | null;
  caregiver_instruction_provided: boolean;
  caregiver_understanding_confirmed: boolean;
  exception_narrative?: string | null;
  task_results: CHHATaskResult[];
};

export async function listAideVisitsForPatient(patientId: string): Promise<AideVisitSummary[]> {
  return unwrap(api.get(`/visits/patient/${patientId}/aide`), "Unable to load this patient's HA visits");
}

export async function createAideVisit(patientId: string): Promise<{ visit_id: string }> {
  return unwrap(
    api.post(`/visits/`, {
      patient_id: patientId,
      visit_type: "AIDE",
      service_type: "AIDE",
      visit_schedule_type: "SCHEDULED",
    }),
    "Unable to create a new CHHA visit"
  );
}

export async function getChhaVisitOutcome(visitId: string): Promise<CHHAVisitOutcome | null> {
  return unwrap(api.get(`/visits/${visitId}/chha-outcome`), "Unable to load this visit's CHHA note");
}

export async function upsertChhaVisitOutcome(visitId: string, payload: CHHAOutcomeUpsertPayload) {
  return unwrap(api.post(`/visits/${visitId}/chha-outcome`, payload), "Unable to save this CHHA visit note");
}
