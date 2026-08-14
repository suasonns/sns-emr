import api from "./client";

export type LCDEvaluationResponse = {
  eligible?: boolean;
  selected_guideline?: string;
  lcd_id?: string;
  lcd_title?: string;
  source_document?: string;
  lcd_reference?: string;
  criteria_summary?: {
    guideline?: string;
    eligible?: boolean;
    group_results?: Array<{
      group_id?: string;
      group_name?: string;
      rule?: string;
      passed?: boolean;
      criteria?: Array<{
        criterion_id?: string;
        description?: string;
        actual?: unknown;
        expected?: unknown;
        matched?: boolean;
      }>;
    }>;
    source_document?: string;
    lcd_reference?: string;
  };
};

export async function evaluateLCD(
  patient: Record<string, unknown>,
  facts: Record<string, unknown> = {},
  admissionDate?: string,
): Promise<LCDEvaluationResponse> {
  const response = await api.post<LCDEvaluationResponse>("/eligibility/lcd-evaluate", {
    patient,
    facts,
    admission_date: admissionDate,
  });

  return response.data;
}
