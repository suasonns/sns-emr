import api from "./client";

export type BereavementSupportPrimaryBereaved = {
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
} | null;

export type BereavementSupportDeathFacts = {
  date_of_death: string | null;
  place_of_death: string | null;
  death_expected: boolean | null;
  pcg_present_at_death: boolean | null;
  family_present_at_death: boolean | null;
  funeral_plans_finalized: boolean | null;
  funeral_home_name: string | null;
} | null;

export type BereavementSupportGoal = {
  key: string;
  label: string;
  selected: boolean;
  target_date: string | null;
  notes: string | null;
};

export type BereavementSupportIntervention = {
  key: string;
  label: string;
  selected: boolean;
  notes: string | null;
};

export type BereavementSupportSummary = {
  patient_id: string;
  primary_bereaved: BereavementSupportPrimaryBereaved;
  death_facts: BereavementSupportDeathFacts;
  risk_level: "LOW" | "MODERATE" | "HIGH" | null;
  goals: BereavementSupportGoal[];
  interventions: BereavementSupportIntervention[];
  other_interventions: string | null;
  source_post_death_assessment_id: string | null;
  source_bereavement_poc_id: string | null;
};

export type BereavementSupportCalendarEvent = {
  tracker_id: string;
  item_key: string;
  label: string;
  contact_type: "LETTER" | "PHONE" | "VISIT";
  due_date: string;
  risk_level: "LOW" | "MODERATE" | "HIGH" | null;
  status: "SENT" | "SKIPPED" | "UNSCHEDULED" | "OVERDUE" | "DUE_SOON" | "UPCOMING";
  included: boolean;
};

export type BereavementSupportCalendar = {
  patient_id: string;
  events: BereavementSupportCalendarEvent[];
};

export type BereavementCommunicationNoteContactType = "PHONE" | "VISIT" | "LETTER" | "EMAIL" | "OTHER";

export type BereavementCommunicationNote = {
  id: string;
  tenant_id: string;
  patient_id: string;
  bereavement_letter_tracker_id: string | null;
  contact_date: string;
  contact_type: BereavementCommunicationNoteContactType;
  contact_with: string | null;
  summary: string;
  created_by: string;
  created_at: string;
};

export type CreateBereavementCommunicationNotePayload = {
  contact_date: string;
  contact_type: BereavementCommunicationNoteContactType;
  contact_with?: string | null;
  summary: string;
  bereavement_letter_tracker_id?: string | null;
};

export async function fetchBereavementSupportSummary(patientId: string) {
  const response = await api.get<BereavementSupportSummary>(`/bereavement-support/patient/${patientId}/summary`);
  return response.data;
}

export async function fetchBereavementSupportCalendar(patientId: string) {
  const response = await api.get<BereavementSupportCalendar>(`/bereavement-support/patient/${patientId}/calendar`);
  return response.data;
}

export async function listBereavementCommunicationNotes(patientId: string) {
  const response = await api.get<BereavementCommunicationNote[]>(`/bereavement-support/patient/${patientId}/notes`);
  return response.data;
}

export async function createBereavementCommunicationNote(
  patientId: string,
  payload: CreateBereavementCommunicationNotePayload,
) {
  const response = await api.post<BereavementCommunicationNote>(
    `/bereavement-support/patient/${patientId}/notes`,
    payload,
  );
  return response.data;
}
