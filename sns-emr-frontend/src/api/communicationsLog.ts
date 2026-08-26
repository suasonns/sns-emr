import api from './client';

export type CommunicationLogEntry = {
  id: string;
  patient_id: string;
  event_type: string;
  focus_area: string | null;
  event_time: string;
  summary: string;
  details: Record<string, any> | null;
  created_by: string;
  created_at: string;
  status: 'RECEIVED' | 'ACKNOWLEDGED' | 'VERIFIED' | 'RESOLVED';
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  verified_by: string | null;
  verified_at: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
};

export type CommunicationLogCreatePayload = {
  patient_id: string;
  event_type: string;
  focus_area?: string | null;
  event_time: string;
  summary: string;
  details?: Record<string, any> | null;
};

export async function listPatientCommunicationLog(patientId: string): Promise<CommunicationLogEntry[]> {
  const response = await api.get<CommunicationLogEntry[]>('/communications-log/patients/', {
    params: { patient_id: patientId },
  });
  return response.data;
}

export async function createCommunicationLogEntry(
  payload: CommunicationLogCreatePayload,
): Promise<CommunicationLogEntry> {
  const response = await api.post<CommunicationLogEntry>('/communications-log', payload);
  return response.data;
}

export async function acknowledgeCommunicationLogEntry(
  id: string,
  note?: string,
): Promise<CommunicationLogEntry> {
  const response = await api.post<CommunicationLogEntry>(`/communications-log/${id}/acknowledge`, note ? { note } : {});
  return response.data;
}

export async function verifyCommunicationLogEntry(
  id: string,
  note?: string,
): Promise<CommunicationLogEntry> {
  const response = await api.post<CommunicationLogEntry>(`/communications-log/${id}/verify`, note ? { note } : {});
  return response.data;
}

export async function resolveCommunicationLogEntry(
  id: string,
  note?: string,
): Promise<CommunicationLogEntry> {
  const response = await api.post<CommunicationLogEntry>(`/communications-log/${id}/resolve`, note ? { note } : {});
  return response.data;
}
