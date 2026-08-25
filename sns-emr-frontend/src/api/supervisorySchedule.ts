import api from "./client";

export type SupervisoryCadenceStatus = "SATISFIED" | "DUE" | "OVERDUE" | "NOT_YET_DUE";

export type SupervisoryCadenceResult =
  | { required: false; reason: string }
  | {
      required: true;
      cadence_days: number;
      status: SupervisoryCadenceStatus;
      due_date: string;
      last_satisfying_visit_id: string | null;
      last_satisfying_visit_date: string | null;
    };

export type SupervisorySchedule = {
  chha_supervisory: SupervisoryCadenceResult;
  lvn_supervisory: SupervisoryCadenceResult;
  soc_date: string | null;
  effective_cadence_start?: string;
};

export async function getSupervisorySchedule(patientId: string): Promise<SupervisorySchedule> {
  const response = await api.get<SupervisorySchedule>(`/patients/${patientId}/supervisory-schedule`);
  return response.data;
}
