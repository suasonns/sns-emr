import api from "./client";

export type BereavementRiskItemEntry = {
  checked: boolean;
  note?: string | null;
};

export type BereavementRiskItemCatalogEntry = {
  key: string;
  points: number;
  label: string;
  note_hint?: string;
  requires_note?: boolean;
};

export type BereavementAdditionalBereaved = {
  name: string;
  relationship_to_patient?: string | null;
  address?: string | null;
  phone?: string | null;
  specific_concerns?: string | null;
};

export type BereavementAssessment = {
  id: string;
  tenant_id: string;
  patient_id: string;
  status: "DRAFT" | "SIGNED";

  entered_by: string;
  staff_assigned: string | null;
  discipline: string | null;
  care_level: string | null;
  visit_type: string | null;
  visit_mode: string | null;
  visit_date: string | null;
  time_in: string | null;
  time_out: string | null;
  duration_minutes: number | null;

  no_family: boolean;
  primary_first_name: string | null;
  primary_last_name: string | null;
  primary_age: number | null;
  primary_gender: string | null;
  primary_address: string | null;
  primary_city: string | null;
  primary_state: string | null;
  primary_zip: string | null;
  primary_home_phone: string | null;
  primary_work_phone: string | null;
  primary_cell_phone: string | null;
  primary_email: string | null;
  primary_relationship_to_patient: string | null;
  primary_was_caregiver: boolean | null;

  risk_items: Record<string, BereavementRiskItemEntry>;
  risk_other_note: string | null;
  risk_total_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | null;

  additional_bereaved: BereavementAdditionalBereaved[];
  narrative: string | null;

  signed_by: string | null;
  signed_at: string | null;

  created_at: string;
  updated_at: string | null;
};

export type BereavementAssessmentPayload = Partial<
  Omit<BereavementAssessment, "id" | "tenant_id" | "status" | "entered_by" | "risk_total_score" | "risk_level" | "signed_by" | "signed_at" | "created_at" | "updated_at">
> & { patient_id?: string };

export async function fetchBereavementRiskCatalog() {
  const response = await api.get<BereavementRiskItemCatalogEntry[]>("/bereavement-assessments/risk-items");
  return response.data;
}

export async function listBereavementAssessments(patientId: string) {
  const response = await api.get<BereavementAssessment[]>(`/bereavement-assessments/patient/${patientId}`);
  return response.data;
}

export async function getBereavementAssessment(assessmentId: string) {
  const response = await api.get<BereavementAssessment>(`/bereavement-assessments/${assessmentId}`);
  return response.data;
}

export async function createBereavementAssessment(payload: BereavementAssessmentPayload & { patient_id: string }) {
  const response = await api.post<BereavementAssessment>("/bereavement-assessments", payload);
  return response.data;
}

export async function updateBereavementAssessment(assessmentId: string, payload: BereavementAssessmentPayload) {
  const response = await api.patch<BereavementAssessment>(`/bereavement-assessments/${assessmentId}`, payload);
  return response.data;
}

export async function signBereavementAssessment(assessmentId: string) {
  const response = await api.post<BereavementAssessment>(`/bereavement-assessments/${assessmentId}/sign`);
  return response.data;
}
