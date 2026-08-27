import api from './client';

export type PatientDocument = {
  id: string;
  patient_id: string;
  document_type: string;
  source: string;
  file_name: string | null;
  uploaded_at: string;
  uploaded_by: string | null;
  is_flagged: boolean;
  flag_tier: string | null;
  ai_document_type_guess: string | null;
  ai_summary: string | null;
  ai_confidence: number | null;
  ai_key_findings: string[] | null;
  ai_needs_manual_review: boolean | null;
  has_extracted_text: boolean;
};

export type UploadDocumentResponse = PatientDocument & {
  document_id: string;
  size_bytes: number;
  content_type: string;
};

export async function uploadDocument(
  patientId: string,
  documentType: string,
  file: File,
  source = 'EXTERNAL',
  documentPassword?: string,
): Promise<UploadDocumentResponse> {
  const form = new FormData();
  form.append('patient_id', patientId);
  form.append('document_type', documentType);
  form.append('source', source);
  form.append('file', file, file.name);
  if (documentPassword) {
    form.append('document_password', documentPassword);
  }

  const response = await api.post<UploadDocumentResponse>('/documents/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function listPatientDocuments(
  patientId: string,
  documentType?: string,
): Promise<{ documents: PatientDocument[] }> {
  const response = await api.get<{ documents: PatientDocument[] }>(`/documents/patient/${patientId}`, {
    params: documentType ? { document_type: documentType } : undefined,
  });
  return response.data;
}

export function getDocumentDownloadUrl(documentId: string): string {
  const base = (api.defaults.baseURL || '').replace(/\/$/, '');
  return `${base}/documents/${documentId}/download`;
}

export async function fetchDocumentBlobUrl(documentId: string): Promise<string> {
  const response = await api.get(`/documents/${documentId}/download`, { responseType: 'blob' });
  return URL.createObjectURL(response.data as Blob);
}
