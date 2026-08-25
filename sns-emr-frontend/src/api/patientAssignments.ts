import api from "./client";

export type PatientAssignmentRecord = {
  id: string;
  patient_id: string;
  tenant_id: string;
  discipline: string;
  user_id: string;
  staff_name: string | null;
  staff_full_name: string | null;
  staff_role: string | null;
  staff_discipline: string | null;
  is_primary: boolean;
  active: boolean;
  status: string;
  service_area: string | null;
  assigned_at: string | null;
  assigned_by_user_id: string | null;
  assigned_by_name: string | null;
  note: string | null;
  deactivated_at: string | null;
};

export type PatientAssignmentListResponse = {
  patient_id: string;
  include_inactive: boolean;
  assignments: PatientAssignmentRecord[];
};

export type PatientAssignmentWrite = {
  patient_id: string;
  discipline: string;
  user_id: string;
  service_area?: string | null;
  note?: string | null;
  is_primary?: boolean;
};

export type PatientAssignmentDeactivatePayload = {
  note?: string | null;
};

export async function listPatientAssignments(
  patientId: string,
  params?: { include_inactive?: boolean },
): Promise<PatientAssignmentListResponse> {
  const response = await api.get<PatientAssignmentListResponse>(
    `/patient-assignments/patient/${patientId}`,
    { params },
  );
  return response.data;
}

export async function assignPatientStaff(
  payload: PatientAssignmentWrite,
): Promise<PatientAssignmentRecord> {
  const response = await api.post<PatientAssignmentRecord>(
    "/patient-assignments/",
    payload,
  );
  return response.data;
}

export async function deactivatePatientAssignment(
  assignmentId: string,
  payload: PatientAssignmentDeactivatePayload = {},
): Promise<PatientAssignmentRecord> {
  const response = await api.patch<PatientAssignmentRecord>(
    `/patient-assignments/${assignmentId}/deactivate`,
    payload,
  );
  return response.data;
}
