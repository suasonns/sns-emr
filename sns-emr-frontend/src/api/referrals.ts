import api from "./client";

export type ReferralIntakePayload = {
  first_name: string;
  last_name: string;
  middle_name?: string;
  date_of_birth: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  gender?: string;
  language?: string;
  religion?: string;
  marital_status?: string;
  primary_payer?: string;
  primary_policy_number?: string;
  authorization_status?: string;
  current_level_of_care?: string;
  primary_diagnosis?: string;
  secondary_diagnoses?: string;
  attending_physician_name?: string;
  attending_physician_npi?: string;
  responsible_party_name?: string;
  responsible_party_relationship?: string;
  responsible_party_phone?: string;
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  referral_source?: string;
  referral_date?: string;
  special_instructions?: string;
};

export type ReferralIntakeResponse = {
  id: string;
  mrn: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  date_of_birth: string;
  primary_diagnosis: string;
  status: string;
  admission_status: string;
  facesheet_created: boolean;
  facesheet_id: string;
  referral_source: string | null;
  referral_date: string | null;
};

export type ReferralStatus = "PENDING" | "ACCEPTED" | "DECLINED";

export type Referral = ReferralIntakePayload & {
  id: string;
  status: ReferralStatus;
  decline_reason: string | null;
  converted_patient_id: string | null;
  created_by: string | null;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
};

/**
 * Creates a PENDING referral awaiting staff review. This is the entry point
 * for the "New Referral Intake" modal -- it does NOT create a Patient record.
 * A reviewer must separately call acceptReferral (which converts it into a
 * full Patient) or declineReferral (which records a reason and closes it out
 * with no patient created).
 */
export async function createReferral(payload: ReferralIntakePayload): Promise<Referral> {
  const response = await api.post<Referral>("/referrals", payload);
  return response.data;
}

export async function listReferrals(status?: ReferralStatus): Promise<Referral[]> {
  const response = await api.get<Referral[]>("/referrals", {
    params: status ? { status } : undefined,
  });
  return response.data;
}

export async function getReferral(referralId: string): Promise<Referral> {
  const response = await api.get<Referral>(`/referrals/${referralId}`);
  return response.data;
}

/**
 * Accepts a pending referral, converting it into a full Patient +
 * PatientFaceSheet + PatientDiagnosis + Admission bundle (same shape as the
 * legacy direct-create response).
 */
export async function acceptReferral(referralId: string): Promise<ReferralIntakeResponse> {
  const response = await api.post<ReferralIntakeResponse>(`/referrals/${referralId}/accept`);
  return response.data;
}

export async function declineReferral(referralId: string, reason: string): Promise<Referral> {
  const response = await api.post<Referral>(`/referrals/${referralId}/decline`, { reason });
  return response.data;
}

/**
 * @deprecated Direct-create path retained for backend API compatibility, but
 * the frontend intake flow should use createReferral so referrals go through
 * staff review before becoming a Patient. Kept as a thin wrapper in case any
 * other caller still needs an immediate conversion.
 */
export async function createPatientFromReferral(
  payload: ReferralIntakePayload,
): Promise<ReferralIntakeResponse> {
  const response = await api.post<ReferralIntakeResponse>("/patients/from-referral", payload);
  return response.data;
}
