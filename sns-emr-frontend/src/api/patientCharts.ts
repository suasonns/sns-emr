import api from "./client";

export type PatientSummaryResponse = {
  patient: {
    id: string;
    mrn: string;
    full_name: string;
    primary_diagnosis: string;
    status: string;
    acuity_state: string;
    admission_status: string;
    hospice_election_date: string | null;
    soc_date: string | null;
  };
  care_team: Array<{
    discipline: string;
    staff_name: string;
    primary: boolean;
    status: string;
    service_area: string | null;
  }>;
  recent_visits: Array<{
    id: string;
    visit_datetime: string | null;
    visit_type: string;
    discipline: string | null;
    status: string;
    provider_name: string;
  }>;
  communication_summary: {
    total: number;
    latest: Array<{
      id: string;
      event_type: string;
      focus_area: string | null;
      event_time: string | null;
      summary: string;
      status: string;
    }>;
  };
  incident_summary: {
    total: number;
    latest: Array<{
      id: string;
      incident_type: string;
      incident_severity: string;
      incident_date: string | null;
      reported_date: string | null;
      narrative: string | null;
    }>;
  };
  compliance_summary: ComplianceResponse;
  volunteer_summary: VolunteerSchedulingResponse;
};

export type PhysicianSummaryResponse = {
  patient: PatientSummaryResponse["patient"];
  metrics: Array<{
    label: string;
    value: number;
  }>;
  cti: Array<{
    id: string;
    cert_type: string;
    signed_at: string | null;
    effective_date: string | null;
    signed_by_role: string;
    status: string;
  }>;
  f2f: Array<{
    id: string;
    encounter_date: string | null;
    performed_by_role: string;
    status: string;
    finalized_at: string | null;
    summary: string | null;
    clinical_decline_summary: string | null;
  }>;
};

export type CommunicationLogResponse = {
  total: number;
  counts_by_type: Record<string, number>;
  entries: Array<{
    id: string;
    event_type: string;
    focus_area: string | null;
    event_time: string | null;
    summary: string;
    details: Record<string, unknown> | null;
    status: string;
    created_at: string | null;
  }>;
};

export type IncidentOccurrenceResponse = {
  total: number;
  counts_by_type: Record<string, number>;
  counts_by_severity: Record<string, number>;
  items: Array<{
    id: string;
    incident_type: string;
    incident_severity: string;
    incident_date: string | null;
    reported_date: string | null;
    incident_time: string | null;
    reported_by: string | null;
    witnessed_by: string | null;
    place: string | null;
    area: string | null;
    surface: string | null;
    medication_used: string | null;
    activity_at_time: string | null;
    injury_level: string | null;
    injury_type: string | null;
    other_injury_text: string | null;
    narrative: string | null;
    signed_at: string | null;
  }>;
};

export type BereavementResponse = {
  patient: PatientSummaryResponse["patient"];
  aggregation: {
    rn_present: boolean;
    sw_present: boolean;
    chaplain_present: boolean;
    reason_codes: string[];
    source_notes: string[];
  };
  supporting_notes: Array<{
    id: string;
    discipline: string | null;
    form_key: string | null;
    created_at: string | null;
    content: string;
  }>;
  supporting_communications: Array<{
    id: string;
    event_type: string;
    event_time: string | null;
    summary: string;
    status: string;
  }>;
};

export type ComplianceResponse = {
  patient: PatientSummaryResponse["patient"];
  eligibility: Record<string, unknown>;
  task_counts: {
    pending: number;
    overdue: number;
    completed: number;
  };
  note_counts: {
    total: number;
    hope: number;
    poc: number;
    f2f: number;
  };
  hope_status: string;
  qies_status: string;
  open_issues: string[];
  recent_notes: Array<{
    id: string;
    form_key: string | null;
    note_type: string;
    status: string | null;
    created_at: string | null;
    content: string;
  }>;
};

export type VolunteerSchedulingResponse = {
  patient: PatientSummaryResponse["patient"];
  visits: Array<{
    id: string;
    visit_datetime: string | null;
    visit_type: string;
    visit_discipline: string | null;
    status: string;
    provider_name: string;
    is_supervisory: boolean;
  }>;
  assignments: Array<{
    id: string;
    discipline: string;
    staff_name: string;
    primary: boolean;
    service_area: string | null;
    status: string;
    assigned_at: string | null;
  }>;
  task_slots: Array<{
    id: string;
    task_type: string;
    status: string;
    due_date: string | null;
    assigned_user_id: string | null;
    assigned_role: string | null;
    alert_reason: string | null;
  }>;
};

export type AssessmentHistoryResponse = {
  patient_id: string;
  items: Array<{
    record_id: string;
    source_table: string;
    discipline: string;
    assessment_type: string;
    phase_hint: string | null;
    visit_date: string | null;
    status: string;
    locked: boolean;
    locked_at: string | null;
    locked_by: string | null;
    created_at: string | null;
    updated_at: string | null;
    record_url_hint: {
      section: string;
      assessment_id: string;
      source_table?: string;
    };
  }>;
  total: number;
  limit: number;
  offset: number;
  sort_order: "asc" | "desc";
  filters: {
    discipline: string | null;
    assessment_type: string | null;
    status: string | null;
    from_date: string | null;
    to_date: string | null;
  };
};


export async function fetchPatientSummary(patientId: string) {
  const response = await api.get<PatientSummaryResponse>(`/patient-charts/${patientId}/summary`);
  return response.data;
}

export async function fetchPhysicianSummary(patientId: string) {
  const response = await api.get<PhysicianSummaryResponse>(`/patient-charts/${patientId}/physician`);
  return response.data;
}

export async function fetchCommunicationLog(patientId: string) {
  const response = await api.get<CommunicationLogResponse>(`/patient-charts/${patientId}/communication-log`);
  return response.data;
}

export async function fetchIncidentOccurrence(patientId: string) {
  const response = await api.get<IncidentOccurrenceResponse>(`/patient-charts/${patientId}/incident-occurrence`);
  return response.data;
}

export async function fetchBereavement(patientId: string) {
  const response = await api.get<BereavementResponse>(`/patient-charts/${patientId}/bereavement`);
  return response.data;
}

export async function fetchCompliance(patientId: string) {
  const response = await api.get<ComplianceResponse>(`/patient-charts/${patientId}/compliance`);
  return response.data;
}

export async function fetchVolunteerScheduling(patientId: string) {
  const response = await api.get<VolunteerSchedulingResponse>(`/patient-charts/${patientId}/volunteer-scheduling`);
  return response.data;
}

export async function fetchAssessmentHistory(
  patientId: string,
  params?: Partial<AssessmentHistoryResponse["filters"]> & { limit?: number; offset?: number; sort_order?: "asc" | "desc" }
) {
  const response = await api.get<AssessmentHistoryResponse>(`/patients/${patientId}/assessment-history`, { params });
  return response.data;
}

export type DischargeChecklist = {
  plan_reviewed: boolean | null;
  notified: boolean | null;
  explained: boolean | null;
  readmission_explained: boolean | null;
  medication_instruction: boolean | null;
  contact_provided: boolean | null;
  referral_provided: boolean | null;
};

export type DischargeState = {
  patient_id: string;
  patient_status: string;
  admission_id: string | null;
  admission_status: string | null;
  discharged: boolean;
  discharge_date: string | null;
  discharge_reason: string | null;
  discharge_initiated_by: string | null;
  discharge_projected_date: string | null;
  discharge_comments: string | null;
  checklist: DischargeChecklist;
  reason_codes: Record<string, string>;
};

export async function fetchDischargePlanning(patientId: string) {
  const response = await api.get<DischargeState>(`/patients/${patientId}/discharge`);
  return response.data;
}

export async function updateDischargePlanning(
  patientId: string,
  payload: Partial<{
    discharge_projected_date: string | null;
    discharge_comments: string | null;
    discharge_plan_reviewed: boolean;
    discharge_notified: boolean;
    discharge_explained: boolean;
    discharge_readmission_explained: boolean;
    discharge_medication_instruction: boolean;
    discharge_contact_provided: boolean;
    discharge_referral_provided: boolean;
  }>
) {
  const response = await api.put<DischargeState>(`/patients/${patientId}/discharge`, payload);
  return response.data;
}

export async function finalizePatientDischarge(
  patientId: string,
  payload: { discharge_date: string; reason_code: string; notes?: string }
) {
  const response = await api.post(`/patients/${patientId}/discharge/finalize`, payload);
  return response.data;
}
