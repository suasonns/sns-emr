import api from "./client";

export type LCDConfigResponse = {
  disease: string;
  lcd_reference: string;
  source_document: string;
  group_combination_rule?: string;
  eligibility_paths?: Array<{
    path_id?: string;
    description?: string;
    all_of_groups?: string[];
    any_of_groups?: string[];
  }>;
  criteria_groups?: Array<{
    group_id?: string;
    group_name?: string;
    rule?: string;
    criteria?: Array<{
      criterion_id?: string;
      field?: string;
      operator?: string;
      expected?: unknown;
      description?: string;
    }>;
  }>;
};

export type LCDDetectResponse = {
  disease: string;
  lcd_reference: string;
  source_document: string;
};

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

export async function detectLCD(text: string): Promise<LCDDetectResponse> {
  const response = await api.get<LCDDetectResponse>("/eligibility/lcd-config/detect", {
    params: { text },
  });
  return response.data;
}

export async function getLCDConfig(disease: string): Promise<LCDConfigResponse> {
  const response = await api.get<LCDConfigResponse>(`/eligibility/lcd-config/${encodeURIComponent(disease)}`);
  return response.data;
}

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
