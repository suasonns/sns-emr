import api from "./client";

export type Icd10Suggestion = {
  icd10_code: string;
  diagnosis_description: string;
  display_name?: string | null;
  chapter_code?: string | null;
  chapter_name?: string | null;
};

export async function searchIcd10Diagnoses(query: string): Promise<Icd10Suggestion[]> {
  if (!query || query.trim().length < 2) return [];
  const response = await api.get<{ query: string; suggestions: Icd10Suggestion[] }>(
    "/icd10/search",
    { params: { query: query.trim() } },
  );
  return response.data.suggestions || [];
}
