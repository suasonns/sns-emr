import axios from "axios";
import api from "./client";

export type PocIntervention = {
  discipline: string;
  intervention_text: string;
  frequency?: string | null;
  instructions?: string | null;
  source_kind: string;
  status: string;
  sort_order?: number | null;
};

export type PocGoal = {
  goal_text: string;
  measurable_outcome?: string | null;
  target_timeframe?: string | null;
  source_kind: string;
  status: string;
  sort_order?: number | null;
  interventions: PocIntervention[];
};

export type PocProblem = {
  problem_code: string;
  label: string;
  description?: string | null;
  severity: string;
  source_diagnosis_code?: string | null;
  source_condition?: string | null;
  diagnosis_context: string;
  rule_key?: string | null;
  source_kind: string;
  status: string;
  sort_order?: number | null;
  goals: PocGoal[];
  // Optional UI-only metadata, present when the focus-area/target-date
  // extension fields (see below) are populated by the backend.
  focus_area?: string | null;
  target_date?: string | null;
  resolved_date?: string | null;
};

export type PocContent = {
  problems: PocProblem[];
};

export type PocVersion = {
  version_id: string;
  version_number: number;
  status: string;
  source_kind: string;
  change_reason?: string | null;
  generated_from?: Record<string, unknown> | null;
  reviewed_in_idg: boolean;
  idg_review_id?: string | null;
  poc_content: PocContent;
};

export type PocVersionSummary = {
  version_id: string;
  version_number: number;
  status: string;
  source_kind: string;
  change_reason?: string | null;
  based_on_version_id?: string | null;
  reviewed_in_idg: boolean;
  idg_review_id?: string | null;
  created_at?: string | null;
};

export type CurrentPlanOfCare = {
  plan_of_care_id: string;
  patient_id: string;
  admission_id: string;
  tenant_id: string;
  status: string;
  current_version_id: string;
  current_version: PocVersion;
};

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (error.response?.status === 404) return "not_found";
  }
  if (error instanceof Error && error.message) return error.message;
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

/** Resolve a patient's active Plan of Care + current version. Throws Error("not_found") if none exists yet. */
export async function getCurrentPlanOfCareByPatient(patientId: string): Promise<CurrentPlanOfCare> {
  return unwrap(api.get(`/plan-of-care/by-patient/${patientId}/current/`), "Plan of Care load failed");
}

export async function getPlanOfCareVersions(planOfCareId: string): Promise<PocVersionSummary[]> {
  return unwrap(api.get(`/plan-of-care/${planOfCareId}/versions/`), "Plan of Care history load failed");
}

export async function getPlanOfCareVersion(planOfCareId: string, versionId: string): Promise<PocVersion> {
  return unwrap(api.get(`/plan-of-care/${planOfCareId}/versions/${versionId}`), "Plan of Care version load failed");
}

export async function createPlanOfCare(payload: {
  admission_id: string;
  patient_id: string;
  source_kind?: string;
  change_reason?: string;
  poc_content: PocContent;
}): Promise<{ status: string; plan_of_care_id: string }> {
  return unwrap(api.post("/plan-of-care/", payload), "Plan of Care creation failed");
}

export async function createPlanOfCareVersion(
  planOfCareId: string,
  payload: {
    source_kind: string;
    change_reason?: string;
    reviewed_in_idg?: boolean;
    idg_review_id?: string;
    poc_content: PocContent;
  }
): Promise<{ status: string; plan_of_care_id: string; version_id: string; version_number: number }> {
  return unwrap(api.post(`/plan-of-care/${planOfCareId}/versions/`, payload), "Plan of Care update failed");
}
