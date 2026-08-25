import api from "./client";

export type PostDeathRiskItemEntry = {
  checked: boolean;
  note?: string | null;
};

export type PostDeathGoal = {
  key: string;
  label: string;
  selected: boolean;
  target_date?: string | null;
  notes?: string | null;
};

export type PostDeathIntervention = {
  key: string;
  label: string;
  selected: boolean;
  notes?: string | null;
};

export type PostDeathBereavementAssessment = {
  id: string;
  tenant_id: string;
  patient_id: string;
  bereavement_assessment_id: string | null;
  bereavement_poc_id: string | null;
  status: "DRAFT" | "SIGNED";

  entered_by: string;
  staff_assigned: string | null;
  discipline: string | null;
  visit_type: string | null;
  visit_mode: string | null;
  visit_date: string | null;
  time_in: string | null;
  time_out: string | null;
  duration_minutes: number | null;

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

  date_of_death: string | null;
  place_of_death: string | null;
  death_expected: boolean | null;
  pcg_present_at_death: boolean | null;
  family_present_at_death: boolean | null;
  funeral_plans_finalized: boolean | null;
  funeral_home_name: string | null;

  condolence_call_date: string | null;
  condolence_call_by: string | null;
  condolence_call_notes: string | null;

  emotional_status_narrative: string | null;

  survivor_support_system_adequate: boolean | null;
  desires_intensive_bereavement_support: boolean | null;
  complicated_grief_reactions_observed: boolean | null;
  additional_risk_factors_since_initial: boolean | null;
  additional_risk_notes: string | null;

  risk_items: Record<string, PostDeathRiskItemEntry>;
  risk_other_note: string | null;
  risk_total_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | null;

  goals: PostDeathGoal[];
  interventions: PostDeathIntervention[];
  other_interventions: string | null;
  plan_of_care_narrative: string | null;

  narrative: string | null;

  signed_by: string | null;
  signed_at: string | null;

  created_at: string;
  updated_at: string | null;
};

export type PostDeathBereavementPayload = Partial<
  Omit<
    PostDeathBereavementAssessment,
    "id" | "tenant_id" | "status" | "entered_by" | "signed_by" | "signed_at" | "created_at" | "updated_at"
  >
> & { patient_id?: string };

export type PostDeathBereavementDefaults = {
  goals: PostDeathGoal[];
  interventions: PostDeathIntervention[];
};

export async function fetchPostDeathRiskItemCatalog() {
  const response = await api.get("/post-death-bereavement/risk-items");
  return response.data;
}

export async function fetchPostDeathBereavementDefaults(riskLevel: string) {
  const response = await api.get<PostDeathBereavementDefaults>("/post-death-bereavement/defaults", {
    params: { risk_level: riskLevel },
  });
  return response.data;
}

export async function listPostDeathBereavement(patientId: string) {
  const response = await api.get<PostDeathBereavementAssessment[]>(`/post-death-bereavement/patient/${patientId}`);
  return response.data;
}

export async function getPostDeathBereavement(recordId: string) {
  const response = await api.get<PostDeathBereavementAssessment>(`/post-death-bereavement/${recordId}`);
  return response.data;
}

export async function createPostDeathBereavement(payload: PostDeathBereavementPayload & { patient_id: string }) {
  const response = await api.post<PostDeathBereavementAssessment>("/post-death-bereavement", payload);
  return response.data;
}

export async function updatePostDeathBereavement(recordId: string, payload: PostDeathBereavementPayload) {
  const response = await api.patch<PostDeathBereavementAssessment>(`/post-death-bereavement/${recordId}`, payload);
  return response.data;
}

export async function signPostDeathBereavement(recordId: string) {
  const response = await api.post<PostDeathBereavementAssessment>(`/post-death-bereavement/${recordId}/sign`);
  return response.data;
}
