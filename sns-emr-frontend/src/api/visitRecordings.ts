import api from './client';

export type VisitRecording = {
  id: string;
  patient_id: string;
  visit_id: string | null;
  assessment_id: string | null;
  assessment_type: string | null;
  recorded_by: string;
  recorded_at: string;
  duration_seconds: number | null;
  size_bytes: number | null;
  mime_type: string | null;
  consent_confirmed: boolean;
  transcript_status: 'not_transcribed' | 'pending' | 'complete' | 'failed';
  transcript_text: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
};

export async function uploadVisitRecording(params: {
  patientId: string;
  audioBlob: Blob;
  consentConfirmed: boolean;
  visitId?: string | null;
  assessmentId?: string | null;
  assessmentType?: string | null;
  durationSeconds?: number | null;
  mimeType?: string;
}): Promise<VisitRecording> {
  const form = new FormData();
  form.append('patient_id', params.patientId);
  form.append('consent_confirmed', String(params.consentConfirmed));
  if (params.visitId) form.append('visit_id', params.visitId);
  if (params.assessmentId) form.append('assessment_id', params.assessmentId);
  if (params.assessmentType) form.append('assessment_type', params.assessmentType);
  if (params.durationSeconds != null) form.append('duration_seconds', String(Math.round(params.durationSeconds)));
  const ext = (params.mimeType || params.audioBlob.type || 'audio/webm').includes('webm') ? 'webm' : 'audio';
  form.append('audio', params.audioBlob, `recording.${ext}`);

  const response = await api.post<VisitRecording>('/visit-recordings', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function fetchPatientRecordings(patientId: string): Promise<{ recordings: VisitRecording[] }> {
  const response = await api.get<{ recordings: VisitRecording[] }>(`/visit-recordings/patient/${patientId}`);
  return response.data;
}

export function getRecordingAudioUrl(recordingId: string): string {
  const base = (api.defaults.baseURL || '').replace(/\/$/, '');
  return `${base}/visit-recordings/${recordingId}/audio`;
}

// The audio-stream endpoint requires the same Bearer auth as every other API
// call, which a plain <audio src="..."> can't send. Fetch it as an
// authenticated blob instead and hand the component an object URL to play.
export async function fetchRecordingAudioBlobUrl(recordingId: string): Promise<string> {
  const response = await api.get(`/visit-recordings/${recordingId}/audio`, { responseType: 'blob' });
  return URL.createObjectURL(response.data as Blob);
}

export async function markRecordingReviewed(recordingId: string, reviewNotes?: string): Promise<VisitRecording> {
  const response = await api.post<VisitRecording>(`/visit-recordings/${recordingId}/review`, {
    review_notes: reviewNotes || null,
  });
  return response.data;
}

export async function deleteVisitRecording(recordingId: string): Promise<void> {
  await api.delete(`/visit-recordings/${recordingId}`);
}
