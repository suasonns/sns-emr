import api from "./client";
import { normalizeListResponse } from "./normalizeListResponse";

export type PatientIssueStatus = "OPEN" | "ONGOING" | "RESOLVED";

export type PatientIssueRecord = {
  id: string;
  tenant_id: string;
  patient_id: string;
  category: string;
  description: string;
  identified_date: string;
  identified_by: string | null;
  status: PatientIssueStatus;
  outcome_notes: string | null;
  resolved_date: string | null;
  resolved_by: string | null;
  created_at: string;
  updated_at: string;
};

export type CreatePatientIssuePayload = {
  category: string;
  description: string;
  identified_date: string;
  identified_by?: string;
  status?: PatientIssueStatus;
  outcome_notes?: string;
  resolved_date?: string;
  resolved_by?: string;
};

export type UpdatePatientIssuePayload = Partial<{
  category: string;
  description: string;
  identified_date: string;
  identified_by: string;
  status: PatientIssueStatus;
  outcome_notes: string;
  resolved_date: string;
  resolved_by: string;
}>;

export async function listPatientIssues(
  patientId: string,
  status?: PatientIssueStatus,
): Promise<PatientIssueRecord[]> {
  const response = await api.get<unknown>(`/patient-issues/patient/${patientId}`, {
    params: status ? { status } : undefined,
  });
  return normalizeListResponse<PatientIssueRecord>(response.data, ["issues", "items"], "Patient issue");
}

export async function createPatientIssue(
  patientId: string,
  payload: CreatePatientIssuePayload,
): Promise<PatientIssueRecord> {
  const response = await api.post<PatientIssueRecord>("/patient-issues", {
    patient_id: patientId,
    ...payload,
  });
  return response.data;
}

export async function updatePatientIssue(
  issueId: string,
  payload: UpdatePatientIssuePayload,
): Promise<PatientIssueRecord> {
  const response = await api.patch<PatientIssueRecord>(`/patient-issues/${issueId}`, payload);
  return response.data;
}
