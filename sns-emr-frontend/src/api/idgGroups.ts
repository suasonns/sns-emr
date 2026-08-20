import api from "./client";

export type IDGGroup = {
  id: string;
  name: string;
  sort_order: number;
  is_active: boolean;
  created_at: string | null;
};

export type IDGGroupScheduleRule = {
  id: string;
  idg_group_id: string;
  weekday: number; // 0=Monday ... 6=Sunday
  nth_occurrences: number[] | null; // null/empty = every occurrence
  is_active: boolean;
};

export async function listIdgGroups(): Promise<IDGGroup[]> {
  const res = await api.get<IDGGroup[]>("/idg/groups");
  return res.data;
}

export async function createIdgGroup(name: string, sortOrder = 0): Promise<IDGGroup> {
  const res = await api.post<IDGGroup>("/idg/groups", { name, sort_order: sortOrder });
  return res.data;
}

export async function setIdgGroupActive(groupId: string, isActive: boolean): Promise<IDGGroup> {
  const res = await api.patch<IDGGroup>(`/idg/groups/${groupId}/active`, { is_active: isActive });
  return res.data;
}

export async function listIdgGroupScheduleRules(groupId: string): Promise<IDGGroupScheduleRule[]> {
  const res = await api.get<IDGGroupScheduleRule[]>(`/idg/groups/${groupId}/schedule-rules`);
  return res.data;
}

export async function addIdgGroupScheduleRule(
  groupId: string,
  weekday: number,
  nthOccurrences: number[] | null = null,
): Promise<IDGGroupScheduleRule> {
  const res = await api.post<IDGGroupScheduleRule>(`/idg/groups/${groupId}/schedule-rules`, {
    weekday,
    nth_occurrences: nthOccurrences,
  });
  return res.data;
}

export async function deactivateIdgGroupScheduleRule(ruleId: string): Promise<IDGGroupScheduleRule> {
  const res = await api.delete<IDGGroupScheduleRule>(`/idg/groups/schedule-rules/${ruleId}`);
  return res.data;
}

export async function assignPatientsToGroup(groupId: string, patientIds: string[]): Promise<{ assigned_count: number }> {
  const res = await api.post<{ assigned_count: number }>(`/idg/groups/${groupId}/patients`, {
    patient_ids: patientIds,
  });
  return res.data;
}

export async function autoSplitUnassignedPatients(groupIds: string[]): Promise<Record<string, number>> {
  const res = await api.post<Record<string, number>>("/idg/groups/auto-split-unassigned", {
    group_ids: groupIds,
  });
  return res.data;
}

export async function runAutomaticIdgGeneration(horizonDays = 14): Promise<{
  created_count: number;
  groups: { group_id: string; group_name: string; dates: string[]; patient_count: number }[];
}> {
  const res = await api.post(`/idg/groups/run-automatic-generation?horizon_days=${horizonDays}`);
  return res.data;
}

export const WEEKDAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
