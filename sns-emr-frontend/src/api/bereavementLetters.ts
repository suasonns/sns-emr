import api from "./client";

export type BereavementLetterItemStatus =
  | "SENT"
  | "SKIPPED"
  | "UNSCHEDULED"
  | "OVERDUE"
  | "DUE_SOON"
  | "UPCOMING";

export type BereavementLetterContactType = "LETTER" | "PHONE" | "VISIT";
export type BereavementLetterSentMethod = "MAIL" | "EMAIL" | "PHONE" | "IN_PERSON" | "OTHER";

export type BereavementLetterItem = {
  key: string;
  month_offset_days: number;
  label: string;
  contact_type: BereavementLetterContactType;
  required: boolean;
  included: boolean;
  due_date: string | null;
  sent_date: string | null;
  sent_method: BereavementLetterSentMethod | null;
  sent_by: string | null;
  notes: string | null;
  status: BereavementLetterItemStatus;
};

export type BereavementLetterTrackerSummary = {
  total_items: number;
  active_items: number;
  sent_count: number;
  overdue_count: number;
  due_soon_count: number;
  upcoming_count: number;
  unscheduled_count: number;
  skipped_count: number;
  complete: boolean;
};

export type BereavementLetterTracker = {
  id: string;
  tenant_id: string;
  patient_id: string;
  bereavement_poc_id: string | null;
  bereavement_assessment_id: string | null;
  date_of_death: string | null;
  risk_level: "LOW" | "MODERATE" | "HIGH" | null;
  status: "ACTIVE" | "COMPLETE" | "DISCONTINUED";
  discontinued_reason: string | null;
  discontinued_at: string | null;
  discontinued_by: string | null;
  items: BereavementLetterItem[];
  summary: BereavementLetterTrackerSummary;
  created_by: string;
  created_at: string;
  updated_by: string | null;
  updated_at: string | null;
};

export type CreateBereavementLetterTrackerPayload = {
  patient_id: string;
  bereavement_poc_id?: string | null;
  bereavement_assessment_id?: string | null;
  date_of_death?: string | null;
  risk_level?: string | null;
};

export type UpdateBereavementLetterTrackerPayload = {
  status?: "ACTIVE" | "COMPLETE" | "DISCONTINUED";
  discontinued_reason?: string | null;
  date_of_death?: string | null;
  risk_level?: string | null;
  resync_schedule?: boolean;
};

export type UpdateBereavementLetterItemPayload = {
  included?: boolean;
  due_date?: string | null;
  sent_date?: string | null;
  sent_method?: BereavementLetterSentMethod | null;
  notes?: string | null;
  clear_sent?: boolean;
};

export type BereavementLetterAlertEntry = {
  tracker_id: string;
  patient_id: string;
  patient_name: string | null;
  item_key: string;
  label: string;
  contact_type: BereavementLetterContactType;
  due_date: string | null;
  days_overdue: number | null;
  days_until_due: number | null;
  risk_level: string | null;
};

export type BereavementLetterAlerts = {
  as_of: string;
  within_days: number;
  overdue_count: number;
  due_soon_count: number;
  overdue: BereavementLetterAlertEntry[];
  due_soon: BereavementLetterAlertEntry[];
};

export async function listBereavementLetterTrackers(patientId: string) {
  const response = await api.get<BereavementLetterTracker[]>(`/bereavement-letters/patient/${patientId}`);
  return response.data;
}

export async function getBereavementLetterTracker(trackerId: string) {
  const response = await api.get<BereavementLetterTracker>(`/bereavement-letters/${trackerId}`);
  return response.data;
}

export async function createBereavementLetterTracker(payload: CreateBereavementLetterTrackerPayload) {
  const response = await api.post<BereavementLetterTracker>("/bereavement-letters", payload);
  return response.data;
}

export async function updateBereavementLetterTracker(
  trackerId: string,
  payload: UpdateBereavementLetterTrackerPayload,
) {
  const response = await api.patch<BereavementLetterTracker>(`/bereavement-letters/${trackerId}`, payload);
  return response.data;
}

export async function updateBereavementLetterItem(
  trackerId: string,
  itemKey: string,
  payload: UpdateBereavementLetterItemPayload,
) {
  const response = await api.patch<BereavementLetterTracker>(
    `/bereavement-letters/${trackerId}/items/${itemKey}`,
    payload,
  );
  return response.data;
}

export async function fetchBereavementLetterAlerts(withinDays?: number) {
  const response = await api.get<BereavementLetterAlerts>("/bereavement-letters/alerts/overdue", {
    params: withinDays ? { within_days: withinDays } : undefined,
  });
  return response.data;
}
