import api from "./client";

export type CertificationStatus = "DRAFT" | "PENDING_SIGNATURE" | "FINALIZED" | "SUPERSEDED";

export type CertificationRecord = {
  id: string;
  patient_id: string;
  benefit_period_id: string;
  cert_type: string;
  status: CertificationStatus;
  status_label: string;
  physician_narrative: string | null;
  supporting_evidence: string | null;
  clinical_decline_indicators: string | null;
  narrative_by_name: string | null;
  narrative_at: string | null;
  signed_by_name: string | null;
  signed_by_role: string | null;
  signed_at: string | null;
  effective_date: string | null;
  expires_at: string | null;
  created_by_name: string | null;
  created_at: string | null;
};

export type CertDraftCreate = {
  benefit_period_id: string;
  physician_narrative: string;
  supporting_evidence?: string;
  clinical_decline_indicators?: string;
};

export async function listCertifications(patientId: string): Promise<CertificationRecord[]> {
  const response = await api.get<CertificationRecord[]>(`/certifications/patients/${patientId}`);
  return response.data || [];
}

export async function createCertDraft(
  patientId: string,
  payload: CertDraftCreate,
): Promise<CertificationRecord> {
  const response = await api.post<CertificationRecord>(`/certifications/patients/${patientId}/draft`, payload);
  return response.data;
}

export async function updateCertNarrative(
  certificationId: string,
  payload: Partial<CertDraftCreate>,
): Promise<CertificationRecord> {
  const response = await api.patch<CertificationRecord>(`/certifications/${certificationId}/narrative`, payload);
  return response.data;
}

export async function submitCertForSignature(certificationId: string): Promise<CertificationRecord> {
  const response = await api.post<CertificationRecord>(`/certifications/${certificationId}/submit`, {});
  return response.data;
}

export async function signCertification(certificationId: string): Promise<CertificationRecord> {
  const response = await api.post<CertificationRecord>(`/certifications/${certificationId}/sign`, {});
  return response.data;
}

export async function getCertificationStatusHistory(certificationId: string) {
  const response = await api.get(`/certifications/${certificationId}/status-history`);
  return response.data || [];
}
