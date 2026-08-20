import api from "./client";

// =========================================================
// Types
// =========================================================

export type IDGSessionSummary = {
  meeting_date: string;
  patient_count: number;
};

export type IDGSessionPatientRow = {
  idg_meeting_id: string;
  patient_id: string | null;
  patient_name: string | null;
  mrn: string | null;
  meeting_status: string;
  review_status: "PENDING" | "REVIEWED" | "DEFERRED";
  reviewed_at: string | null;
  defer_reason: string | null;
  batch_signed_at: string | null;
};

export type ReviewStatusPayload = {
  physician_user_id: string;
  review_status: "REVIEWED" | "DEFERRED";
  defer_reason?: string | null;
  defer_note?: string | null;
  poc_reviewed?: boolean;
  medication_list_reviewed?: boolean;
  medication_reconciliation_reviewed?: boolean;
  orders_reviewed?: boolean;
  discussion_reviewed?: boolean;
  notes?: string | null;
};

export type BatchQueueOrder = {
  id: string;
  order_text: string;
  order_category: string;
  source_type: string;
  ordered_by_provider_name: string;
  ordered_by_provider_role: string;
  ordered_at: string | null;
  status: string;
};

export type BatchQueueEntry = {
  patient_id: string;
  review_id: string;
  reviewed_at: string;
  physician_user_id: string;
  orders: BatchQueueOrder[];
};

// =========================================================
// Sessions (IDG Meeting Workspace list view)
// =========================================================

export async function listIdgSessions(): Promise<IDGSessionSummary[]> {
  const res = await api.get<IDGSessionSummary[]>("/idg/sessions");
  return res.data;
}

export async function getIdgSessionPatients(meetingDate: string): Promise<IDGSessionPatientRow[]> {
  const res = await api.get<IDGSessionPatientRow[]>(`/idg/sessions/by-date/${encodeURIComponent(meetingDate)}`);
  return res.data;
}

// =========================================================
// Physician review (Reviewed / Deferred)
// =========================================================

export async function setPatientReviewStatus(
  idgMeetingId: string,
  patientId: string,
  payload: ReviewStatusPayload,
) {
  const res = await api.post(`/idg/sessions/${idgMeetingId}/patients/${patientId}/review`, payload);
  return res.data;
}

// =========================================================
// Batch signature queue
// =========================================================

export async function getBatchSignatureQueue(idgMeetingId: string): Promise<BatchQueueEntry[]> {
  const res = await api.get<BatchQueueEntry[]>(`/idg/sessions/${idgMeetingId}/batch-signature-queue`);
  return res.data;
}

export async function batchSignOrders(
  idgMeetingId: string,
  patientIds: string[],
  signatureMethod = "ELECTRONIC",
) {
  const res = await api.post(`/idg/sessions/${idgMeetingId}/batch-sign`, {
    patient_ids: patientIds,
    signature_method: signatureMethod,
  });
  return res.data;
}
