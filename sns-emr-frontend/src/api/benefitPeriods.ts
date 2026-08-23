import api from "./client";

export type BenefitPeriodRecord = {
  id: string;
  patient_id: string;
  benefit_type: "INITIAL" | "RECERT";
  period_number: number;
  election_date: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
};

export async function listBenefitPeriods(patientId: string): Promise<BenefitPeriodRecord[]> {
  const response = await api.get<BenefitPeriodRecord[]>(`/benefits/patients/${patientId}`);
  return response.data || [];
}
