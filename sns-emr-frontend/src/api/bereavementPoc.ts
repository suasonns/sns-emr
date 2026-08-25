import api from "./client";

export type BereavementPOCGoal = {
  key: string;
  label: string;
  selected: boolean;
  target_date?: string | null;
  notes?: string | null;
};

export type BereavementPOCIntervention = {
  key: string;
  label: string;
  selected: boolean;
  notes?: string | null;
};

export type BereavementPOCActionPlanEntry = {
  month_offset_days?: number | null;
  label: string;
  contact_type?: string | null;
  planned_date?: string | null;
  completed_date?: string | null;
  completed_by?: string | null;
  notes?: string | null;
  required?: boolean;
  included?: boolean;
};

export type BereavementPOC = {
  id: string;
  tenant_id: string;
  patient_id: string;
  bereavement_assessment_id: string | null;
  status: "DRAFT" | "SIGNED";

  entered_by: string;
  staff_assigned: string | null;
  discipline: string | null;

  date_of_death: string | null;
  risk_level: "LOW" | "MODERATE" | "HIGH" | null;
  risk_source: "SCORED" | "MANUAL" | null;
  risk_score: number | null;

  no_family: boolean;
  primary_first_name: string | null;
  primary_last_name: string | null;
  primary_relationship_to_patient: string | null;
  primary_address: string | null;
  primary_city: string | null;
  primary_state: string | null;
  primary_zip: string | null;
  primary_home_phone: string | null;
  primary_cell_phone: string | null;
  primary_email: string | null;
  primary_was_caregiver: boolean | null;

  goals: BereavementPOCGoal[];
  interventions: BereavementPOCIntervention[];
  other_interventions: string | null;
  action_plan: BereavementPOCActionPlanEntry[];

  narrative: string | null;

  closed_early: boolean;
  closed_reason: string | null;

  signed_by: string | null;
  signed_at: string | null;

  created_at: string;
  updated_at: string | null;
};

export type BereavementPOCPayload = Partial<
  Omit<BereavementPOC, "id" | "tenant_id" | "status" | "entered_by" | "signed_by" | "signed_at" | "created_at" | "updated_at">
> & { patient_id?: string };

export type BereavementPOCDefaults = {
  goals: BereavementPOCGoal[];
  interventions: BereavementPOCIntervention[];
  action_plan: BereavementPOCActionPlanEntry[];
};

export async function fetchBereavementPOCDefaults(riskLevel: string, dateOfDeath?: string | null) {
  const response = await api.get<BereavementPOCDefaults>("/bereavement-poc/defaults", {
    params: { risk_level: riskLevel, date_of_death: dateOfDeath || undefined },
  });
  return response.data;
}

export async function listBereavementPOCs(patientId: string) {
  const response = await api.get<BereavementPOC[]>(`/bereavement-poc/patient/${patientId}`);
  return response.data;
}

export async function getBereavementPOC(pocId: string) {
  const response = await api.get<BereavementPOC>(`/bereavement-poc/${pocId}`);
  return response.data;
}

export async function createBereavementPOC(payload: BereavementPOCPayload & { patient_id: string }) {
  const response = await api.post<BereavementPOC>("/bereavement-poc", payload);
  return response.data;
}

export async function updateBereavementPOC(pocId: string, payload: BereavementPOCPayload) {
  const response = await api.patch<BereavementPOC>(`/bereavement-poc/${pocId}`, payload);
  return response.data;
}

export async function signBereavementPOC(pocId: string) {
  const response = await api.post<BereavementPOC>(`/bereavement-poc/${pocId}/sign`);
  return response.data;
}
