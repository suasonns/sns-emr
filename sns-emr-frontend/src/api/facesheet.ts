import api from './client';

type NullableString = string | null;
type NullableBoolean = boolean | null;

type FacesheetDiagnosis = {
  id: string;
  diagnosis_type: string | null;
  status: string | null;
  source: string | null;
  icd10_code: string | null;
  diagnosis_description: string | null;
  display_name: string | null;
  active: boolean;
  is_terminal: boolean | null;
  is_related_to_terminal: boolean | null;
  effective_date: string | null;
  resolved_date: string | null;
  effective_benefit_period_number: number | null;
  resolved_benefit_period_number: number | null;
  idg_discussion_required: boolean | null;
  idg_discussed: boolean | null;
  idg_discussed_at: string | null;
  idg_meeting_id: string | null;
  idg_summary: string | null;
  hospital_records_reviewed: boolean | null;
  diagnostic_results_reviewed: boolean | null;
  specialist_documentation_reviewed: boolean | null;
  specialist_name: string | null;
  specialist_documentation_date: string | null;
  prior_specialist_certification_present: boolean | null;
  supporting_evidence_summary: string | null;
  physician_signed_document_type: string | null;
  physician_signed_document_id: string | null;
  physician_signed_at: string | null;
  physician_signature_notes: string | null;
  change_reason: string | null;
  rejected_reason: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type FaceSheetPayload = {
  first_name: string;
  middle_name?: NullableString;
  last_name: string;
  ssn?: NullableString;
  dob?: NullableString;
  gender?: NullableString;
  race?: NullableString;
  ethnicity?: NullableString;
  language?: NullableString;
  religion?: NullableString;
  marital_status?: NullableString;
  phone?: NullableString;
  address?: NullableString;
  city?: NullableString;
  state?: NullableString;
  zip?: NullableString;
  current_pos_type?: NullableString;
  current_pos_name?: NullableString;
  current_pos_address?: NullableString;
  room_number?: NullableString;
  pos_start_date?: NullableString;
  pos_end_date?: NullableString;
  current_level_of_care?: NullableString;
  loc_effective_date?: NullableString;
  primary_payer?: NullableString;
  primary_policy_number?: NullableString;
  mbi_number?: NullableString;
  secondary_payer?: NullableString;
  secondary_policy_number?: NullableString;
  requires_prior_authorization?: NullableBoolean;
  authorization_required_for?: NullableString;
  authorization_number?: NullableString;
  authorization_status?: NullableString;
  authorization_start_date?: NullableString;
  authorization_end_date?: NullableString;
  primary_diagnosis?: NullableString;
  secondary_diagnoses?: NullableString;
  has_allergies?: NullableBoolean;
  allergies?: NullableString;
  ref_date?: NullableString;
  recert_date?: NullableString;
  responsible_party_name?: NullableString;
  responsible_party_relationship?: NullableString;
  responsible_party_phone?: NullableString;
  emergency_contact_name?: NullableString;
  emergency_contact_relationship?: NullableString;
  emergency_contact_phone?: NullableString;
  attending_physician_name?: NullableString;
  attending_physician_address?: NullableString;
  attending_physician_phone?: NullableString;
  attending_physician_fax?: NullableString;
  attending_physician_npi?: NullableString;
  attending_physician_following?: NullableBoolean;
  medical_director_name?: NullableString;
  medical_director_address?: NullableString;
  medical_director_phone?: NullableString;
  medical_director_fax?: NullableString;
  medical_director_npi?: NullableString;
  medical_director_designee_name?: NullableString;
  medical_director_designee_npi?: NullableString;
  associate_medical_director_name?: NullableString;
  associate_medical_director_npi?: NullableString;
  pharmacy_name?: NullableString;
  pharmacy_phone?: NullableString;
  pharmacy_fax?: NullableString;
  dme_vendor_name?: NullableString;
  dme_vendor_phone?: NullableString;
  mortuary_name?: NullableString;
  mortuary_phone?: NullableString;
  special_instructions?: NullableString;
};

export type FacesheetResponse = {
  patient_id: string;
  mrn: string | null;
  identity: {
    first_name: string;
    middle_name: NullableString;
    last_name: string;
    dob: NullableString;
    ssn: NullableString;
    gender: NullableString;
    race: NullableString;
    ethnicity: NullableString;
    language: NullableString;
    religion: NullableString;
    marital_status: NullableString;
    phone: NullableString;
  };
  address: {
    address: NullableString;
    city: NullableString;
    state: NullableString;
    zip: NullableString;
  };
  insurance: {
    primary_payer: NullableString;
    primary_policy_number: NullableString;
    mbi_number: NullableString;
    secondary_payer: NullableString;
    secondary_policy_number: NullableString;
  };
  authorization: {
    requires_prior_authorization: NullableBoolean;
    authorization_required_for: NullableString;
    authorization_number: NullableString;
    authorization_status: NullableString;
    authorization_start_date: NullableString;
    authorization_end_date: NullableString;
  };
  clinical: {
    primary_diagnosis: NullableString;
    secondary_diagnoses: NullableString;
    diagnoses: {
      primary: FacesheetDiagnosis | null;
      secondary: FacesheetDiagnosis[];
      comorbidities: FacesheetDiagnosis[];
    };
    active_primary_diagnosis: FacesheetDiagnosis | null;
    active_secondary_diagnoses: FacesheetDiagnosis[];
    active_comorbidities: FacesheetDiagnosis[];
    has_allergies: NullableBoolean;
    allergies: NullableString;
  };
  level_of_care: {
    current_level_of_care: NullableString;
    loc_effective_date: NullableString;
  };
  place_of_service: {
    current_pos_type: NullableString;
    current_pos_name: NullableString;
    current_pos_address: NullableString;
    room_number: NullableString;
    pos_start_date: NullableString;
    pos_end_date: NullableString;
  };
  contacts: {
    responsible_party: {
      name: NullableString;
      relationship: NullableString;
      phone: NullableString;
    };
    emergency_contact: {
      name: NullableString;
      relationship: NullableString;
      phone: NullableString;
    };
  };
  physicians: {
    attending: {
      name: NullableString;
      address: NullableString;
      phone: NullableString;
      fax: NullableString;
      npi: NullableString;
      following: NullableBoolean;
    };
    medical_director: {
      name: NullableString;
      address: NullableString;
      phone: NullableString;
      fax: NullableString;
      npi: NullableString;
    };
    medical_director_designee: {
      name: NullableString;
      npi: NullableString;
    };
    associate_medical_director: {
      name: NullableString;
      npi: NullableString;
    };
  };
  vendors: {
    pharmacy: {
      name: NullableString;
      phone: NullableString;
      fax: NullableString;
    };
    dme: {
      name: NullableString;
      phone: NullableString;
    };
    mortuary: {
      name: NullableString;
      phone: NullableString;
    };
  };
  service_dates: {
    admission_status: string | null;
    soc_date: NullableString;
    effective_date: NullableString;
    admission_date: NullableString;
    ref_date: NullableString;
    recert_date: NullableString;
  };
  notes: {
    special_instructions: NullableString;
  };
};

export type SaveFacesheetResponse = {
  status: string;
  facesheet_id: string;
  patient_id: string;
};

export type PosHistoryEntry = {
  id: string;
  pos_type: string;
  pos_name: NullableString;
  pos_address: NullableString;
  room_number: NullableString;
  start_date: NullableString;
  end_date: NullableString;
  reason: NullableString;
  status: string | null;
  is_current: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type PosHistoryPayload = {
  pos_type: string;
  pos_name?: NullableString;
  pos_address?: NullableString;
  room_number?: NullableString;
  start_date: string;
  end_date?: NullableString;
  reason?: NullableString;
};

export type PosHistoryResponse = {
  patient_id: string;
  current_entry: PosHistoryEntry | null;
  entries: PosHistoryEntry[];
};

export type PerformanceHistoryEntry = {
  id: string;
  source: string;
  status: string | null;
  date: string | null;
  pps: number | null;
  kps: number | null;
  fast_stage: NullableString;
  weight: number | null;
  adl_dependency_count: number | null;
};

export type PerformanceHistoryResponse = {
  history: PerformanceHistoryEntry[];
};

export type PatientAllergyEntry = {
  allergy_id: string;
  allergen_text: string;
  allergen_type: string;
  drug_class: NullableString;
  reaction_description: NullableString;
  severity: NullableString;
};

export async function fetchAllergies(patientId: string) {
  const response = await api.get<PatientAllergyEntry[]>(`/patients/${patientId}/allergies`);
  return response.data;
}

export async function addAllergy(
  patientId: string,
  payload: { allergen_text: string; allergen_type?: string; reaction_description?: string; severity?: string },
) {
  // Backend endpoint declares these as plain scalar params (not a Pydantic
  // body model), so FastAPI binds them as query parameters.
  const response = await api.post<PatientAllergyEntry>(`/patients/${patientId}/allergies`, null, { params: payload });
  return response.data;
}

export async function removeAllergy(patientId: string, allergyId: string) {
  const response = await api.delete(`/patients/${patientId}/allergies/${allergyId}`);
  return response.data;
}

export async function fetchPerformanceHistory(patientId: string) {
  const response = await api.get<PerformanceHistoryResponse>(`/patients/${patientId}/performance-history`);
  return response.data;
}

export async function fetchFacesheet(patientId: string) {
  const response = await api.get<FacesheetResponse>(`/patients/${patientId}/facesheet`);
  return response.data;
}

export async function saveFacesheet(patientId: string, payload: FaceSheetPayload) {
  const response = await api.post<SaveFacesheetResponse>(`/patients/${patientId}/facesheet`, payload);
  return response.data;
}

export type CodeStatusEntry = {
  code_status_id: string;
  code_status: string;
  effective_date: NullableString;
  source: string;
  notes: NullableString;
  is_current: boolean;
  created_at: NullableString;
};

export type CodeStatusHistoryResponse = {
  current: CodeStatusEntry | null;
  history: CodeStatusEntry[];
};

export async function fetchCodeStatusHistory(patientId: string) {
  const response = await api.get<CodeStatusHistoryResponse>(`/patients/${patientId}/code-status`);
  return response.data;
}

export type PhysicianAssignmentEntry = {
  role: string;
  name: NullableString;
  address: NullableString;
  phone: NullableString;
  fax: NullableString;
  npi: NullableString;
  will_follow_in_hospice: boolean | null;
  source: NullableString;
  updated_at: NullableString;
  created_at: NullableString;
};

export type PatientPhysiciansResponse = {
  attending: PhysicianAssignmentEntry | null;
  medical_director: PhysicianAssignmentEntry | null;
  associate_medical_director: PhysicianAssignmentEntry | null;
};

export async function fetchPatientPhysicians(patientId: string) {
  const response = await api.get<PatientPhysiciansResponse>(`/patients/${patientId}/physicians`);
  return response.data;
}

export type PatientContactEntry = {
  role: string;
  name: NullableString;
  relationship: NullableString;
  phone: NullableString;
  address: NullableString;
  source: NullableString;
  updated_at: NullableString;
  created_at: NullableString;
};

export type PatientContactsResponse = {
  responsible_party: PatientContactEntry | null;
  emergency_contact: PatientContactEntry | null;
  primary_caregiver: PatientContactEntry | null;
  dpoa: PatientContactEntry | null;
  healthcare_agent: PatientContactEntry | null;
  decision_maker: PatientContactEntry | null;
};

export async function fetchPatientContacts(patientId: string) {
  const response = await api.get<PatientContactsResponse>(`/patients/${patientId}/contacts`);
  return response.data;
}


export async function fetchPosHistory(patientId: string) {
  const response = await api.get<PosHistoryResponse>(`/patients/${patientId}/pos-history`);
  return response.data;
}

export async function createPosHistory(patientId: string, payload: PosHistoryPayload) {
  const response = await api.post<PosHistoryEntry>(`/patients/${patientId}/pos-history`, payload);
  return response.data;
}

export async function updatePosHistory(patientId: string, entryId: string, payload: Partial<PosHistoryPayload>) {
  const response = await api.put<PosHistoryEntry>(`/patients/${patientId}/pos-history/${entryId}`, payload);
  return response.data;
}
